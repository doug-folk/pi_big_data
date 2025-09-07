import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from fastapi import FastAPI, HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer
from annoy import AnnoyIndex
import uvicorn
import numpy as np
import random, time

app = FastAPI(title="GameFinder Recommendation Service", version="minimal")
GAMES_DF = None
ANNOY_INDEX = None
GAME_IDX_TO_ID = None

# Carrega dados da tabela games
@app.on_event("startup")
def startup_event():
    global GAMES_DF, ANNOY_INDEX, GAME_IDX_TO_ID
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
    # Cria índice Annoy baseado em conteúdo
    features_text = (
        GAMES_DF['title'].fillna('') + ' ' +
        GAMES_DF['genre'].fillna('') + ' ' +
        GAMES_DF['tags'].fillna('') + ' ' +
        GAMES_DF['categoria'].fillna('')
    )
    tfidf = TfidfVectorizer(stop_words='english', max_features=5000, min_df=2)
    tfidf_matrix = tfidf.fit_transform(features_text)
    tfidf_array = tfidf_matrix.toarray().astype(np.float32)
    annoy_dim = tfidf_array.shape[1]
    ANNOY_INDEX = AnnoyIndex(annoy_dim, 'angular')
    for idx in range(tfidf_array.shape[0]):
        ANNOY_INDEX.add_item(idx, tfidf_array[idx])
    ANNOY_INDEX.build(20)
    GAME_IDX_TO_ID = {idx: game_id for idx, game_id in enumerate(GAMES_DF.index)}
    print("[STARTUP] TF-IDF processado. Iniciando construção do índice Annoy...")
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
    annoy_indices = ANNOY_INDEX.get_nns_by_item(idx, top_n + 1, include_distances=False)
    annoy_indices = [i for i in annoy_indices if i != idx][:top_n]
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
