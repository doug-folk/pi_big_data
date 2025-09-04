import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from fastapi import FastAPI, HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import uvicorn
import numpy as np
import traceback
from annoy import AnnoyIndex

# --- 3. INICIALIZAÇÃO DO SERVIÇO (Sua versão, está ótima!) ---

app = FastAPI(title="GameFinder Recommendation Service", version="2.2.0")
MODELS = {}
GAMES_DF = None

@app.get("/debug/for-game/{game_id}", summary="Debug detalhado do processo de recomendação para um jogo")
def debug_for_game(game_id: int, top_n: int = 10):
    if not MODELS:
        raise HTTPException(503, "Modelos não estão prontos.")
    if game_id not in MODELS["game_map"]:
        raise HTTPException(404, f"Jogo com ID {game_id} não encontrado no modelo.")

    game_idx = MODELS["game_map"][game_id]
    # Busca vizinhos aproximados via Annoy (colaborativo)
    annoy_indices = MODELS["annoy_index"].get_nns_by_item(game_idx, top_n * 2, include_distances=False)
    annoy_indices = [idx for idx in annoy_indices if idx != game_idx]

    # Busca vizinhos aproximados via Annoy de conteúdo
    annoy_content_indices = MODELS["annoy_content_index"].get_nns_by_item(game_idx, top_n * 2, include_distances=False)
    annoy_content_indices = [idx for idx in annoy_content_indices if idx != game_idx]

    import random, time
    # Combina resultados (prioridade máxima para Annoy colaborativo, depois conteúdo)
    combined_indices = list(dict.fromkeys(annoy_indices + annoy_content_indices))
    # Garante que a seed é diferente a cada requisição
    random.seed(time.time_ns())
    # Aumenta o pool de candidatos para embaralhar
    random_indices = combined_indices[:top_n*10]
    before_shuffle = [MODELS["game_idx_to_id"][idx] for idx in random_indices]
    random.shuffle(random_indices)
    after_shuffle = [MODELS["game_idx_to_id"][idx] for idx in random_indices]
    shuffled_recommendations = [MODELS["game_idx_to_id"][idx] for idx in random_indices[:top_n]]

    columns_to_show = [
        'title', 'brand', 'genre', 'tags', 'description', 'platform', 'developer', 'release_date'
    ]
    columns_to_show = [col for col in columns_to_show if col in GAMES_DF.columns]
    def game_info(game_id):
        row = GAMES_DF.loc[game_id]
        return {"id": int(game_id), **{col: row[col] for col in columns_to_show}}

    return {
        "annoy_collaborative_candidates": [MODELS["game_idx_to_id"][idx] for idx in annoy_indices],
        "annoy_content_candidates": [MODELS["game_idx_to_id"][idx] for idx in annoy_content_indices],
        "combined_pool": [MODELS["game_idx_to_id"][idx] for idx in combined_indices],
        "pool_before_shuffle": before_shuffle,
        "pool_after_shuffle": after_shuffle,
        "recommendations": [game_info(gid) for gid in shuffled_recommendations],
    }
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from fastapi import FastAPI, HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import uvicorn
import numpy as np
import traceback
from annoy import AnnoyIndex

# --- 1. CONFIGURAÇÃO E CARREGAMENTO DE DADOS (Sua versão, está ótima!) ---

def get_db_engine():
    """Cria e retorna uma engine de conexão com o banco de dados PostgreSQL."""
    load_dotenv()
    # Sua alteração para DATABASE_URL está perfeita.
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL não definida no arquivo .env")
    return create_engine(db_url)

# Substitua a função inteira por esta versão corrigida

def load_data_from_db(engine, min_ratings_per_game=3, min_ratings_per_user=1):
    """
    Carrega dados do PostgreSQL, com filtros mais brandos e correção para o tipo numpy.int64.
    """
    print(f"Carregando dados: min {min_ratings_per_game} avaliações/jogo, min {min_ratings_per_user} avaliações/usuário.")
    try:
        query = text("""
            WITH RelevantGameIDs AS (
                SELECT game_id FROM ratings GROUP BY game_id HAVING COUNT(user_id) >= :min_g
            )
            SELECT r.user_id, r.game_id, r.rating
            FROM ratings r
            WHERE r.game_id IN (SELECT game_id FROM RelevantGameIDs);
        """)
        params = {"min_g": min_ratings_per_game}
        
        print("Executando query para avaliações filtradas...")
        ratings_df = pd.read_sql(query, engine, params=params)
        
        if ratings_df.empty:
            print("AVISO CRÍTICO: Nenhum dado de avaliação restou após a filtragem.")
            return None, None

        # --- INÍCIO DA CORREÇÃO ---
        # Pega os IDs únicos do DataFrame (que são do tipo numpy.int64)
        unique_game_ids_numpy = ratings_df['game_id'].unique()
        
        # Converte cada ID para o tipo 'int' padrão do Python
        relevant_game_ids_python = tuple(int(gid) for gid in unique_game_ids_numpy)
        # --- FIM DA CORREÇÃO ---

        # Agora, passamos a tupla de inteiros Python para a query
        games_query = text("SELECT id, title, brand FROM games WHERE id IN :game_ids")
        games_df = pd.read_sql(games_query, engine, params={"game_ids": relevant_game_ids_python})

        if games_df.empty:
            print("AVISO CRÍTICO: Nenhum jogo correspondente foi encontrado para as avaliações filtradas.")
            return None, None

        print(f"Dados filtrados carregados: {len(games_df)} jogos e {len(ratings_df)} avaliações.")
        return games_df, ratings_df

    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        traceback.print_exc()
        return None, None


# --- 2. CRIAÇÃO DOS MODELOS (PREENCHIDO) ---
def create_models(games_df, ratings_df, annoy_trees=30):
    print("Iniciando criação de todos os modelos...")
    user_ids = sorted(ratings_df['user_id'].unique())
    game_ids = sorted(games_df['id'].unique())
    user_map = {id: i for i, id in enumerate(user_ids)}
    game_map = {id: i for i, id in enumerate(game_ids)}
    user_idx_to_id = {i: id for id, i in user_map.items()}
    game_idx_to_id = {i: id for id, i in game_map.items()}

    ratings_df['user_idx'] = ratings_df['user_id'].map(user_map)
    ratings_df['game_idx'] = ratings_df['game_id'].map(game_map)
    user_item_matrix = csr_matrix((ratings_df['rating'], (ratings_df['user_idx'], ratings_df['game_idx'])), shape=(len(user_ids), len(game_ids)))

    # --- Annoy para similaridade aproximada (Item-Item) usando embeddings SVD ---
    print(f"1/3: Criando índice Annoy para similaridade colaborativa (Item-Item) com {annoy_trees} árvores (usando SVD)...")
    print("2/3: Criando modelo de Fatoração de Matrizes (SVD)...")
    svd = TruncatedSVD(n_components=50, random_state=42)
    user_factors = svd.fit_transform(user_item_matrix)
    item_factors = svd.components_.T

    annoy_dim = item_factors.shape[1]  # 50
    from tqdm import tqdm
    annoy_index = AnnoyIndex(annoy_dim, 'angular')
    print(f"Adicionando {item_factors.shape[0]} jogos ao índice Annoy (usando embeddings SVD)...")
    for game_idx in tqdm(range(item_factors.shape[0]), desc="Annoy - add_item (SVD)"):
        vector = item_factors[game_idx].astype(np.float32)
        annoy_index.add_item(game_idx, vector)
    print(f"Construindo {annoy_trees} árvores Annoy...")
    annoy_index.build(annoy_trees)

    print("3/3: Criando índice Annoy para similaridade baseada em conteúdo (TF-IDF expandido)...")
    games_df_indexed = games_df.set_index('id').loc[game_ids]
    # Preenche colunas que podem não existir
    for col in ['title', 'brand', 'genre', 'tags', 'description', 'platform', 'developer', 'release_date']:
        if col not in games_df_indexed.columns:
            games_df_indexed[col] = ''
    games_df_indexed['features_text'] = (
        games_df_indexed['title'].fillna('') + ' ' +
        games_df_indexed['brand'].fillna('') + ' ' +
        games_df_indexed['genre'].fillna('') + ' ' +
        games_df_indexed['tags'].fillna('') + ' ' +
        games_df_indexed['description'].fillna('') + ' ' +
        games_df_indexed['platform'].fillna('') + ' ' +
        games_df_indexed['developer'].fillna('') + ' ' +
        games_df_indexed['release_date'].fillna('')
    )
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(games_df_indexed['features_text'])
    tfidf_array = tfidf_matrix.toarray().astype(np.float32)
    annoy_content_dim = tfidf_array.shape[1]
    annoy_content_index = AnnoyIndex(annoy_content_dim, 'angular')
    print(f"Adicionando {tfidf_array.shape[0]} jogos ao índice Annoy de conteúdo...")
    for game_idx in tqdm(range(tfidf_array.shape[0]), desc="Annoy - add_item (conteúdo)"):
        annoy_content_index.add_item(game_idx, tfidf_array[game_idx])
    print(f"Construindo {annoy_trees} árvores Annoy (conteúdo)...")
    annoy_content_index.build(annoy_trees)

    print("Todos os modelos foram criados com sucesso!")
    return {
        "user_map": user_map, "game_map": game_map,
        "user_idx_to_id": user_idx_to_id, "game_idx_to_id": game_idx_to_id,
        "annoy_index": annoy_index,
        "annoy_content_index": annoy_content_index,
        "user_factors": user_factors, "item_factors": item_factors,
        "user_item_matrix": user_item_matrix
    }

# --- 3. INICIALIZAÇÃO DO SERVIÇO (Sua versão, está ótima!) ---

app = FastAPI(title="GameFinder Recommendation Service", version="2.2.0")
MODELS = {}
GAMES_DF = None

@app.on_event("startup")
def startup_event():
    global MODELS, GAMES_DF
    engine = get_db_engine()
    # Parâmetros ajustáveis para máxima precisão
    ANNOY_TREES = 30  # Mais árvores = mais precisão
    print("--- INICIANDO SERVIÇO DE RECOMENDAÇÃO ---")
    games_df, ratings_df = load_data_from_db(engine)
    if games_df is not None and not games_df.empty and ratings_df is not None and not ratings_df.empty:
        GAMES_DF = games_df.set_index('id')
        MODELS = create_models(games_df, ratings_df, annoy_trees=ANNOY_TREES)
        if MODELS:
            print("--- SERVIÇO PRONTO E MODELOS CARREGADOS ---")
        else:
            print("--- AVISO: FALHA NA CRIAÇÃO DOS MODELOS ---")
    else:
        print("--- ERRO CRÍTICO: DADOS INSUFICIENTES APÓS FILTRAGEM. O SERVIÇO FUNCIONARÁ EM MODO DEGRADADO. ---")

# --- 4. ENDPOINTS DA API (PREENCHIDO) ---

@app.get("/", summary="Verifica o status do serviço")
def read_root():
    if not MODELS:
        return {"status": "Serviço online, mas em MODO DEGRADADO. Modelos de recomendação não foram carregados."}
    return {"status": "Serviço online e modelos carregados com sucesso."}

@app.get("/recommendations/for-game/{game_id}", summary="Recomenda jogos similares a um jogo específico (Híbrido)")
def get_for_game_recommendations(game_id: int, top_n: int = 10, user_id: int = None):
    if not MODELS:
        raise HTTPException(503, "Modelos não estão prontos.")
    if game_id not in MODELS["game_map"]:
        raise HTTPException(404, f"Jogo com ID {game_id} não encontrado no modelo.")

    game_idx = MODELS["game_map"][game_id]
    # Busca vizinhos aproximados via Annoy (colaborativo)
    annoy_indices = MODELS["annoy_index"].get_nns_by_item(game_idx, top_n * 2, include_distances=False)
    annoy_indices = [idx for idx in annoy_indices if idx != game_idx]

    # Busca vizinhos aproximados via Annoy de conteúdo
    annoy_content_indices = MODELS["annoy_content_index"].get_nns_by_item(game_idx, top_n * 2, include_distances=False)
    annoy_content_indices = [idx for idx in annoy_content_indices if idx != game_idx]

    import random, time
    # Combina resultados (prioridade máxima para Annoy colaborativo, depois conteúdo)
    combined_indices = list(dict.fromkeys(annoy_indices + annoy_content_indices))
    # Garante que a seed é diferente a cada requisição
    random.seed(time.time_ns())
    # Aumenta o pool de candidatos para embaralhar
    random_indices = combined_indices[:top_n*10]
    random.shuffle(random_indices)
    shuffled_recommendations = [MODELS["game_idx_to_id"][idx] for idx in random_indices[:top_n]]
    # Seleciona colunas relevantes para análise de diversidade
    columns_to_show = [
        'title', 'brand', 'genre', 'tags', 'description', 'platform', 'developer', 'release_date'
    ]
    columns_to_show = [col for col in columns_to_show if col in GAMES_DF.columns]
    result = []
    for game_id in shuffled_recommendations:
        row = GAMES_DF.loc[game_id]
        result.append({"id": int(game_id), **{col: row[col] for col in columns_to_show}})
    return result

    # Remove jogos já avaliados pelo usuário, se user_id fornecido
    if user_id is not None and user_id in MODELS["user_map"]:
        user_idx = MODELS["user_map"][user_id]
        rated_indices = set(MODELS["user_item_matrix"][user_idx].indices)
        combined_indices = [idx for idx in combined_indices if idx not in rated_indices]

    import random, time
    # Garante que a seed é diferente a cada requisição
    random.seed(time.time_ns())
    # Aumenta o pool de candidatos para embaralhar
    random_indices = combined_indices[:top_n*10]  # pega mais candidatos para embaralhar
    random.shuffle(random_indices)
    # Diversidade: prioriza gêneros diferentes
    diverse_recommendations = []
    genres_seen = set()
    for idx in random_indices:
        game_id_candidate = MODELS["game_idx_to_id"][idx]
        genre = GAMES_DF.loc[game_id_candidate]["genre"] if "genre" in GAMES_DF.columns else None
        if genre not in genres_seen:
            diverse_recommendations.append(game_id_candidate)
            genres_seen.add(genre)
        if len(diverse_recommendations) == top_n:
            break
    # Se não houver gêneros suficientes, completa com os próximos
    if len(diverse_recommendations) < top_n:
        for idx in random_indices:
            game_id_candidate = MODELS["game_idx_to_id"][idx]
            if game_id_candidate not in diverse_recommendations:
                diverse_recommendations.append(game_id_candidate)
            if len(diverse_recommendations) == top_n:
                break
    # Embaralha a lista final para garantir variação
    random.shuffle(diverse_recommendations)
    return GAMES_DF.loc[diverse_recommendations].to_dict('index')

@app.get("/recommendations/for-user/{user_id}", summary="Gera recomendações personalizadas para um usuário (SVD)")
def get_for_user_recommendations(user_id: int, top_n: int = 10):
    if not MODELS: raise HTTPException(503, "Modelos não estão prontos.")
    if user_id not in MODELS["user_map"]: raise HTTPException(404, f"Usuário com ID {user_id} não tem dados suficientes para recomendações.")

    user_idx = MODELS["user_map"][user_id]
    user_factor = MODELS["user_factors"][user_idx]
    predicted_ratings = user_factor.dot(MODELS["item_factors"].T)

    user_rated_games_indices = MODELS["user_item_matrix"][user_idx].indices
    predicted_ratings[user_rated_games_indices] = -np.inf

    # Seleciona um pool maior de candidatos para permitir randomização/diversidade
    pool_size = max(top_n * 10, 50)
    candidate_indices = np.argsort(predicted_ratings)[::-1][:pool_size]

    import random, time
    random.seed(time.time_ns())
    candidate_indices = list(candidate_indices)
    random.shuffle(candidate_indices)

    # Diversidade: prioriza gêneros diferentes
    diverse_recommendations = []
    genres_seen = set()
    for idx in candidate_indices:
        game_id_candidate = MODELS["game_idx_to_id"][idx]
        genre = GAMES_DF.loc[game_id_candidate]["genre"] if "genre" in GAMES_DF.columns else None
        if genre not in genres_seen:
            diverse_recommendations.append(game_id_candidate)
            genres_seen.add(genre)
        if len(diverse_recommendations) == top_n:
            break
    # Se não houver gêneros suficientes, completa com os próximos
    if len(diverse_recommendations) < top_n:
        for idx in candidate_indices:
            game_id_candidate = MODELS["game_idx_to_id"][idx]
            if game_id_candidate not in diverse_recommendations:
                diverse_recommendations.append(game_id_candidate)
            if len(diverse_recommendations) == top_n:
                break
    # Embaralha a lista final para garantir variação
    random.shuffle(diverse_recommendations)

    columns_to_show = [
        'title', 'brand', 'genre', 'tags', 'description', 'platform', 'developer', 'release_date'
    ]
    columns_to_show = [col for col in columns_to_show if col in GAMES_DF.columns]
    result = []
    for game_id in diverse_recommendations:
        row = GAMES_DF.loc[game_id]
        result.append({"id": int(game_id), **{col: row[col] for col in columns_to_show}})
    return result

@app.get("/debug/valid-ids", summary="Lista IDs válidos para teste")
def get_valid_ids():
    if not MODELS:
        raise HTTPException(503, "Modelos não estão prontos.")
    def to_pyint(x):
        try:
            return int(x)
        except Exception:
            return x
    sample_game_ids = [to_pyint(x) for x in list(MODELS["game_map"].keys())[:20]]
    sample_user_ids = [to_pyint(x) for x in list(MODELS["user_map"].keys())[:20]]
    return {
        "message": "Use estes IDs para testar os endpoints.",
        "sample_game_ids": sample_game_ids,
        "sample_user_ids": sample_user_ids
    }
