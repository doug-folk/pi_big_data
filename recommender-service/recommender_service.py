import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from fastapi import FastAPI, HTTPException, Query
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, balanced_accuracy_score
from annoy import AnnoyIndex
import uvicorn
import numpy as np
import random
from tqdm import tqdm

app = FastAPI(title="GameFinder Recommendation Service", version="minimal")


GAMES_DF = None
ANNOY_INDEX = None
GAME_IDX_TO_ID = None
KMEANS_MODEL = None
ITEM_SIM_MATRIX = None
INTERACTION_MATRIX = None


@app.on_event("startup")
def startup_event():
    global GAMES_DF, ANNOY_INDEX, GAME_IDX_TO_ID, KMEANS_MODEL, ITEM_SIM_MATRIX, INTERACTION_MATRIX
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL não definida no arquivo .env")

    engine = create_engine(db_url)
    print("[STARTUP] Carregando dados do banco...")
    games_df = pd.read_sql("SELECT * FROM games", engine)
    if games_df.empty:
        print("Nenhum jogo encontrado no banco.")
        return

    GAMES_DF = games_df.set_index('id')


    print("[STARTUP] Processando TF-IDF...")
    features_text = (
        GAMES_DF['title'].fillna('') + ' ' +
        GAMES_DF['genre'].fillna('') + ' ' +
        GAMES_DF['tags'].fillna('') + ' ' +
        GAMES_DF['categoria'].fillna('')
    )
    tfidf = TfidfVectorizer(stop_words='english', max_features=1000, min_df=5)
    tfidf_matrix = tfidf.fit_transform(features_text)
    tfidf_array = tfidf_matrix.toarray().astype(np.float32)

    annoy_dim = tfidf_array.shape[1]
    ANNOY_INDEX = AnnoyIndex(annoy_dim, 'angular')
    for idx in tqdm(range(tfidf_array.shape[0]), desc="Construindo Annoy"):
        ANNOY_INDEX.add_item(idx, tfidf_array[idx])
    ANNOY_INDEX.build(20)
    GAME_IDX_TO_ID = {idx: game_id for idx, game_id in enumerate(GAMES_DF.index)}
    print("[STARTUP] Annoy pronto.")


    print("[STARTUP] Clusterizando com KMeans...")
    n_clusters = 5
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(tfidf_matrix)
    GAMES_DF['cluster'] = clusters
    KMEANS_MODEL = kmeans
    print("[STARTUP] Clusterização concluída.")


    print("[STARTUP] Preparando modelo colaborativo...")
    GAMES_DF['user_id'] = GAMES_DF.index % 50  # usuários fictícios
    GAMES_DF['rating'] = GAMES_DF['reviews'].apply(lambda x: 1 if 'positive' in str(x).lower() else 0)

    interaction_matrix = GAMES_DF.pivot_table(index="user_id", columns="id", values="rating", fill_value=0)
    INTERACTION_MATRIX = interaction_matrix
    ITEM_SIM_MATRIX = cosine_similarity(interaction_matrix.T)
    ITEM_SIM_MATRIX = pd.DataFrame(ITEM_SIM_MATRIX, index=interaction_matrix.columns, columns=interaction_matrix.columns)
    print("[STARTUP] Modelo colaborativo pronto. Serviço iniciado.")


@app.get("/", summary="Status do serviço")
def read_root():
    if GAMES_DF is None:
        return {"status": "Serviço online, mas sem jogos carregados."}
    return {"status": "Serviço online e pronto para recomendações."}


@app.get("/recommendations/for-game/{game_id}", summary="Recomenda jogos similares a um jogo (conteúdo)")
def recommend_for_game(game_id: int, top_n: int = 10):
    if GAMES_DF is None or ANNOY_INDEX is None:
        raise HTTPException(503, "Dados não carregados.")
    if game_id not in GAMES_DF.index:
        raise HTTPException(404, f"Jogo com ID {game_id} não encontrado.")
    
    idx = list(GAMES_DF.index).index(game_id)
    n_neighbors = max(top_n * 3, 20)
    annoy_indices = ANNOY_INDEX.get_nns_by_item(idx, n_neighbors, include_distances=False)
    annoy_indices = [i for i in annoy_indices if i != idx]
    annoy_indices = random.sample(annoy_indices, min(top_n, len(annoy_indices)))

    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'image_url', 'normalized_name']
    result = []
    for i in annoy_indices:
        game_id_similar = GAME_IDX_TO_ID[i]
        row = GAMES_DF.loc[game_id_similar]
        result.append({"id": int(game_id_similar), **{col: row[col] for col in columns_to_show if col in row}})
    return result


@app.get("/discover/by-cluster/{game_id}", summary="Descoberta por cluster")
def discover_by_cluster(game_id: int, top_n: int = 10):
    if GAMES_DF is None:
        raise HTTPException(503, "Dados não carregados.")
    if game_id not in GAMES_DF.index:
        raise HTTPException(404, f"Jogo com ID {game_id} não encontrado.")
    
    cluster_id = GAMES_DF.loc[game_id, 'cluster']
    df = GAMES_DF[(GAMES_DF['cluster'] == cluster_id) & (GAMES_DF.index != game_id)]
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'image_url', 'normalized_name']
    indices = list(df.index)
    indices = random.sample(indices, min(top_n, len(indices)))
    return [{"id": int(idx), **{col: df.loc[idx][col] for col in columns_to_show if col in df.loc[idx]}} for idx in indices]


@app.get("/recommendations/collaborative/{game_id}", summary="Recomenda baseado em Item-Based CF")
def recommend_collaborative(game_id: int, top_n: int = 10):
    if ITEM_SIM_MATRIX is None or INTERACTION_MATRIX is None:
        raise HTTPException(503, "Modelo colaborativo não carregado")
    if game_id not in ITEM_SIM_MATRIX.index:
        raise HTTPException(404, "Jogo não encontrado")
    
    similar_scores = ITEM_SIM_MATRIX[game_id].sort_values(ascending=False)
    similar_ids = similar_scores.index[1:top_n+1]  
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'image_url', 'normalized_name']
    return [{"id": int(idx), **{col: GAMES_DF.loc[idx][col] for col in columns_to_show if col in GAMES_DF.loc[idx]}} for idx in similar_ids]

@app.get("/evaluate/collaborative-realistic", summary="Avaliação realista do modelo colaborativo")
def evaluate_collaborative_realistic(top_n: int = 10):
    if ITEM_SIM_MATRIX is None or INTERACTION_MATRIX is None:
        raise HTTPException(503, "Modelo colaborativo não carregado")

    precisions = []
    recalls = []
    balanced_accuracies = []

    for user_id in INTERACTION_MATRIX.index:
        user_ratings = INTERACTION_MATRIX.loc[user_id]
        positive_games = user_ratings[user_ratings > 0].index.tolist()
        all_games = user_ratings.index.tolist()

        if not positive_games:
            continue

        recommended = []
        for game_id in positive_games:
            similar_scores = ITEM_SIM_MATRIX[game_id].sort_values(ascending=False)
            recommended.extend(similar_scores.index[1:top_n+1])
        recommended = list(set(recommended))

        y_true = [1 if g in positive_games else 0 for g in recommended]
        y_pred = [1] * len(recommended)

        if len(y_true) > 0:
            precisions.append(precision_score(y_true, y_pred, zero_division=0))
            recalls.append(recall_score(y_true, y_pred, zero_division=0))
            balanced_accuracies.append(balanced_accuracy_score(y_true, y_pred))

    return {
        "precision": np.mean(precisions) if precisions else None,
        "recall": np.mean(recalls) if recalls else None,
        "balanced_accuracy": np.mean(balanced_accuracies) if balanced_accuracies else None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
