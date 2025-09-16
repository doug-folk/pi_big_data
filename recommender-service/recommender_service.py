import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from fastapi import FastAPI, HTTPException, Query
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from annoy import AnnoyIndex
import uvicorn
import numpy as np
import random
from tqdm import tqdm

app = FastAPI(title="GameFinder Recommendation Service", version="minimal")
GAMES_DF = None
ANNOY_INDEX = None
GAME_IDX_TO_ID = None

# Carrega dados da tabela games e prepara modelos
@app.on_event("startup")
def startup_event():
    global GAMES_DF, ANNOY_INDEX, GAME_IDX_TO_ID, KMEANS_MODEL
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL não definida no arquivo .env")
    engine = create_engine(db_url)
    print("[STARTUP] Iniciando carregamento dos dados...")
    games_df = pd.read_sql("SELECT * FROM games", engine)
    if games_df.empty:
        print("Nenhum jogo encontrado no banco.")
        return
    GAMES_DF = games_df.set_index('id')
    print("[STARTUP] Dados carregados. Iniciando processamento TF-IDF...")
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
    print("[STARTUP] TF-IDF processado. Iniciando clusterização KMeans...")
    n_clusters = 5  # Menos clusters
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(tfidf_matrix)
    GAMES_DF['cluster'] = clusters
    print("[STARTUP] Clusterização concluída.")
    print("[STARTUP] Índice Annoy construído. Serviço pronto para receber requisições.")

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
    
    # Pega mais vizinhos para randomizar
    n_neighbors = max(top_n * 3, 20)  # ex: 3 vezes top_n ou no mínimo 20
    annoy_indices = ANNOY_INDEX.get_nns_by_item(idx, n_neighbors, include_distances=False)
    annoy_indices = [i for i in annoy_indices if i != idx]
    
    # Sorteia top_n de forma aleatória
    annoy_indices = random.sample(annoy_indices, min(top_n, len(annoy_indices)))
    
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'image_url', 'normalized_name']
    result = []
    for i in annoy_indices:
        game_id_similar = GAME_IDX_TO_ID[i]
        row = GAMES_DF.loc[game_id_similar]
        result.append({"id": int(game_id_similar), **{col: row[col] for col in columns_to_show if col in row}})
    return result

@app.get("/recommendations/by-mood", summary="Recomenda jogos por gênero/tags/categoria")
def recommend_by_mood(mood: str = "Unknown", top_n: int = 10):
    if GAMES_DF is None:
        raise HTTPException(503, "Dados não carregados.")
    filtered = GAMES_DF[GAMES_DF.apply(
        lambda row: mood.lower() in str(row.get("genre", "")).lower() or mood.lower() in str(row.get("tags", "")).lower() or mood.lower() in str(row.get("categoria", "")).lower(),
        axis=1
    )]
    sample = filtered.sample(n=min(top_n, len(filtered))) if not filtered.empty else GAMES_DF.sample(n=top_n)
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'image_url', 'normalized_name']
    return [
        {"id": int(idx), **{col: sample.loc[idx][col] for col in columns_to_show if col in sample.loc[idx]}}
        for idx in sample.index
    ]

@app.get("/discover/by-filter", summary="Descoberta por filtros manuais")
def discover_by_filter(
    genre: str = Query(None),
    categoria: str = Query(None),
    tag: str = Query(None),
    top_n: int = 20
):
    if GAMES_DF is None:
        raise HTTPException(503, "Dados não carregados.")
    df = GAMES_DF.copy()
    if genre:
        df = df[df['genre'].str.contains(genre, case=False, na=False)]
    if categoria:
        df = df[df['categoria'].str.contains(categoria, case=False, na=False)]
    if tag:
        df = df[df['tags'].str.contains(tag, case=False, na=False)]
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'image_url', 'normalized_name']
    indices = list(df.index)
    indices = random.sample(indices, min(top_n, len(indices)))
    return [
        {"id": int(idx), **{col: df.loc[idx][col] for col in columns_to_show if col in df.loc[idx]}}
        for idx in indices
    ]

@app.get("/discover/random", summary="Descoberta aleatória controlada")
def discover_random(
    genre: str = Query(None),
    categoria: str = Query(None),
    tag: str = Query(None),
    n: int = Query(5)
):
    if GAMES_DF is None:
        raise HTTPException(503, "Dados não carregados.")
    df = GAMES_DF.copy()
    if genre:
        df = df[df['genre'].str.contains(genre, case=False, na=False)]
    if categoria:
        df = df[df['categoria'].str.contains(categoria, case=False, na=False)]
    if tag:
        df = df[df['tags'].str.contains(tag, case=False, na=False)]
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'image_url', 'normalized_name']
    sample_df = df.sample(n=min(n, len(df))) if not df.empty else GAMES_DF.sample(n=n)
    return [
        {"id": int(idx), **{col: sample_df.loc[idx][col] for col in columns_to_show if col in sample_df.loc[idx]}}
        for idx in sample_df.index
    ]

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
    return [
        {"id": int(idx), **{col: df.loc[idx][col] for col in columns_to_show if col in df.loc[idx]}}
        for idx in indices
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
