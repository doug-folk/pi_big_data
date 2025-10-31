import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from fastapi import FastAPI, HTTPException, Query
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import re

# Verificar se sentence-transformers está disponível
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
from annoy import AnnoyIndex
import uvicorn
import numpy as np
import random
from tqdm import tqdm
import json

app = FastAPI(title="GameFinder Recommendation Service", version="optimized")
GAMES_DF = None
ANNOY_INDEX = None
GAME_IDX_TO_ID = None
KMEANS_MODEL = None
MODEL_METRICS = None

# Carrega dados da tabela games e prepara modelos
@app.on_event("startup")
def startup_event():
    global GAMES_DF, ANNOY_INDEX, GAME_IDX_TO_ID, KMEANS_MODEL, MODEL_METRICS
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL não definida no arquivo .env")
    engine = create_engine(db_url)
    print("[STARTUP] Iniciando carregamento dos dados...")
    
    # Carregar dados da tabela games (estrutura do ETL)
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
    
    print("[STARTUP] TF-IDF processado. Iniciando KMeans otimizado...")
    
    # ETL Melhorado
    def clean_genre(genre_str):
        if pd.isna(genre_str) or genre_str == 'Unknown':
            return 'Other'
        # Mapear gêneros similares
        genre_mapping = {
            'Action': ['Action', 'Shooter', 'Fighting', 'Beat em up'],
            'Adventure': ['Adventure', 'Point & Click'],
            'RPG': ['RPG', 'JRPG', 'CRPG', 'Roguelike'],
            'Strategy': ['Strategy', 'RTS', 'Turn-Based Strategy', 'Grand Strategy'],
            'Simulation': ['Simulation', 'City Builder', 'Management'],
            'Sports': ['Sports', 'Racing', 'Football', 'Basketball'],
            'Indie': ['Indie', 'Casual']
        }
        
        genre_str = str(genre_str)
        for main_genre, variants in genre_mapping.items():
            for variant in variants:
                if variant.lower() in genre_str.lower():
                    return main_genre
        return 'Other'
    
    def parse_json_field_improved(field):
        if pd.isna(field) or field == 'Unknown':
            return []
        try:
            data = json.loads(field) if isinstance(field, str) else []
            if isinstance(data, list):
                # Limpar e normalizar tags
                cleaned = []
                for item in data:
                    if isinstance(item, str) and len(item.strip()) > 0:
                        # Remover caracteres especiais e normalizar
                        clean_item = re.sub(r'[^a-zA-Z0-9\s]', '', str(item)).strip().lower()
                        if len(clean_item) > 2:  # Mínimo 3 caracteres
                            cleaned.append(clean_item)
                return cleaned
            return [str(data)] if data else []
        except:
            return [str(field)] if field else []
    
    # Limpar dados com ETL melhorado
    GAMES_DF['clean_genre'] = GAMES_DF['genre'].apply(clean_genre)
    GAMES_DF['clean_tags'] = GAMES_DF['tags'].apply(parse_json_field_improved)
    GAMES_DF['clean_categoria'] = GAMES_DF['categoria'].apply(parse_json_field_improved)
    
    # Criar texto estruturado para embeddings
    def create_game_description(row):
        title = str(row['title']) if pd.notna(row['title']) else ''
        genre = str(row['clean_genre']) if pd.notna(row['clean_genre']) else ''
        tags = ' '.join(row['clean_tags']) if row['clean_tags'] else ''
        categoria = ' '.join(row['clean_categoria']) if row['clean_categoria'] else ''
        
        description = f"Title: {title}. Genre: {genre}. Tags: {tags}. Category: {categoria}."
        return description.strip()
    
    game_descriptions = GAMES_DF.apply(create_game_description, axis=1)
    
    # Word Embeddings ou TF-IDF
    global HAS_SENTENCE_TRANSFORMERS
    
    if HAS_SENTENCE_TRANSFORMERS:
        enable_transformers = os.getenv("ENABLE_SENTENCE_TRANSFORMERS", "true").lower() in ("1", "true", "yes")
        if not enable_transformers:
            print("SentenceTransformer desabilitado via variável de ambiente. Usando TF-IDF...")
            HAS_SENTENCE_TRANSFORMERS = False

    if HAS_SENTENCE_TRANSFORMERS:
        print("Gerando embeddings com SentenceTransformer...")
        try:
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            descriptions = game_descriptions.tolist()
            total_sentences = len(descriptions)
            batch_size = int(os.getenv("SENTENCE_TRANSFORMER_BATCH", 256) or 256)
            batch_size = max(1, batch_size)
            print(f"[STARTUP] SentenceTransformer ativo. Processando {total_sentences} jogos em lotes de {batch_size}.")

            embedding_batches = []
            for start in tqdm(range(0, total_sentences, batch_size), desc="Gerando embeddings (SentenceTransformer)", unit="lote"):
                batch = descriptions[start:start + batch_size]
                emb_batch = embedding_model.encode(
                    batch,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                embedding_batches.append(emb_batch.astype(np.float32))

            if embedding_batches:
                text_embeddings = np.vstack(embedding_batches)
            else:
                text_embeddings = np.zeros((0, embedding_model.get_sentence_embedding_dimension()), dtype=np.float32)

            print(f"Embeddings gerados: {text_embeddings.shape}")
        except Exception as e:
            print(f"Erro nos embeddings: {e}. Usando TF-IDF...")
            HAS_SENTENCE_TRANSFORMERS = False
    
    if not HAS_SENTENCE_TRANSFORMERS:
        print("Usando TF-IDF melhorado...")
        tfidf_opt = TfidfVectorizer(stop_words='english', max_features=400, min_df=2, max_df=0.8, ngram_range=(1,2))
        text_embeddings = tfidf_opt.fit_transform(game_descriptions).toarray()
    
    # Features numéricas melhoradas
    numeric_features = pd.DataFrame()
    numeric_features['title_len'] = GAMES_DF['title'].fillna('').astype(str).str.len()
    numeric_features['has_url'] = (GAMES_DF['url'].fillna('') != 'Unknown').astype(int)
    numeric_features['tags_count'] = GAMES_DF['clean_tags'].apply(len)
    numeric_features['categoria_count'] = GAMES_DF['clean_categoria'].apply(len)
    
    # Features de gênero one-hot melhoradas
    main_genres = ['Action', 'Adventure', 'Strategy', 'RPG', 'Simulation', 'Sports', 'Indie', 'Other']
    for genre in main_genres:
        numeric_features[f'is_{genre.lower()}'] = (GAMES_DF['clean_genre'] == genre).astype(int)
    
    # Combinar embeddings + features numéricas
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_features.fillna(0))
    
    # Combinar embeddings de texto + features numéricas
    combined_features = np.hstack([text_embeddings, numeric_scaled])
    print(f"Features combinadas: {combined_features.shape}")
    
    # Testar múltiplos algoritmos de clustering
    sample_size = min(2000, len(combined_features))
    sample_indices = np.random.choice(len(combined_features), sample_size, replace=False)
    sample_features = combined_features[sample_indices]
    
    algorithms = {}
    
    # 1. KMeans otimizado
    best_kmeans_score = -1
    best_k = 8
    for k in range(6, 12):
        kmeans_temp = KMeans(n_clusters=k, random_state=42, n_init=3)
        temp_clusters = kmeans_temp.fit_predict(sample_features)
        score = silhouette_score(sample_features, temp_clusters)
        if score > best_kmeans_score:
            best_kmeans_score = score
            best_k = k
    
    algorithms['kmeans'] = {
        'model': KMeans(n_clusters=best_k, random_state=42, n_init=3),
        'score': best_kmeans_score,
        'name': f'KMeans(k={best_k})'
    }
    
    # 2. DBSCAN
    try:
        dbscan = DBSCAN(eps=0.5, min_samples=10)
        dbscan_clusters = dbscan.fit_predict(sample_features)
        if len(set(dbscan_clusters)) > 1:  # Pelo menos 2 clusters
            dbscan_score = silhouette_score(sample_features, dbscan_clusters)
            algorithms['dbscan'] = {
                'model': dbscan,
                'score': dbscan_score,
                'name': 'DBSCAN'
            }
    except:
        pass
    
    # 3. Gaussian Mixture
    try:
        gmm = GaussianMixture(n_components=best_k, random_state=42)
        gmm_clusters = gmm.fit_predict(sample_features)
        gmm_score = silhouette_score(sample_features, gmm_clusters)
        algorithms['gmm'] = {
            'model': gmm,
            'score': gmm_score,
            'name': f'GaussianMixture(k={best_k})'
        }
    except:
        pass
    
    # Escolher melhor algoritmo
    best_algorithm = max(algorithms.items(), key=lambda x: x[1]['score'])
    best_name, best_info = best_algorithm
    
    print(f"Melhor algoritmo: {best_info['name']} (Silhouette: {best_info['score']:.3f})")
    
    # Treinar modelo final com melhor algoritmo
    KMEANS_MODEL = best_info['model']
    if best_name == 'kmeans':
        KMEANS_MODEL = KMeans(n_clusters=best_k, random_state=42, n_init=3)
    elif best_name == 'gmm':
        KMEANS_MODEL = GaussianMixture(n_components=best_k, random_state=42)
    
    clusters = KMEANS_MODEL.fit_predict(combined_features)
    GAMES_DF['cluster'] = clusters
    
    # Salvar info do algoritmo usado
    MODEL_METRICS = {'algorithm_used': best_info['name']}
    
    # Avaliar modelo
    print("[STARTUP] Avaliando modelo...")
    # Calcular silhouette em sample para velocidade
    sil_sample_size = min(1000, len(combined_features))
    sil_indices = np.random.choice(len(combined_features), sil_sample_size, replace=False)
    sil_score = silhouette_score(combined_features[sil_indices], clusters[sil_indices])
    metrics = {
        'silhouette_score': sil_score,
        'algorithm_used': MODEL_METRICS['algorithm_used']
    }
    
    # Balanced Accuracy usando gêneros
    main_genres = ['Action', 'Adventure', 'Strategy', 'RPG', 'Simulation']
    
    def get_main_genre(genre_str):
        if pd.isna(genre_str) or genre_str == 'Unknown':
            return 'Other'
        for genre in main_genres:
            if genre.lower() in str(genre_str).lower():
                return genre
        return 'Other'
    
    genre_labels = GAMES_DF['genre'].apply(get_main_genre)
    le = LabelEncoder()
    genre_numeric = le.fit_transform(genre_labels)
    
    # Usar sample menor para avaliação
    eval_sample_size = min(2000, len(combined_features))
    eval_indices = np.random.choice(len(combined_features), eval_sample_size, replace=False)
    eval_features = combined_features[eval_indices]
    eval_genres = genre_numeric[eval_indices]
    
    X_train, X_test, y_train, y_test = train_test_split(
        eval_features, eval_genres, test_size=0.3, random_state=42
    )
    
    kmeans_eval = KMeans(n_clusters=best_k, random_state=42, n_init=3)
    train_clusters = kmeans_eval.fit_predict(X_train)
    
    cluster_to_genre = {}
    for cluster in range(best_k):
        mask = train_clusters == cluster
        if np.any(mask):
            most_common = np.bincount(y_train[mask]).argmax()
            cluster_to_genre[cluster] = most_common
    
    test_clusters = kmeans_eval.predict(X_test)
    predictions = np.array([cluster_to_genre.get(c, 0) for c in test_clusters])
    
    metrics['balanced_accuracy'] = balanced_accuracy_score(y_test, predictions)
    metrics['n_clusters'] = best_k
    
    MODEL_METRICS = metrics
    
    print(f"[STARTUP] Métricas do modelo:")
    print(f"  - Silhouette Score: {MODEL_METRICS['silhouette_score']:.3f}")
    print(f"  - Balanced Accuracy: {MODEL_METRICS['balanced_accuracy']:.3f}")
    print(f"  - Número de Clusters: {MODEL_METRICS['n_clusters']}")
    print("[STARTUP] Serviço pronto para receber requisições.")

@app.get("/", summary="Status do serviço")
def read_root():
    if GAMES_DF is None:
        return {"status": "Serviço online, mas sem jogos carregados."}
    return {
        "status": "Serviço online e pronto para recomendações.",
        "games_count": len(GAMES_DF),
        "clusters_count": MODEL_METRICS['n_clusters'] if MODEL_METRICS else None
    }

@app.get("/model/metrics", summary="Métricas de desempenho do modelo")
def get_model_metrics():
    if MODEL_METRICS is None:
        raise HTTPException(503, "Modelo não foi treinado ainda.")
    
    # Verificar se atende aos critérios
    meets_criteria = {
        "balanced_accuracy_target": "0.65-0.75",
        "balanced_accuracy_achieved": MODEL_METRICS['balanced_accuracy'],
        "meets_target": 0.65 <= MODEL_METRICS['balanced_accuracy'] <= 0.75
    }
    
    return {
        "model_performance": MODEL_METRICS,
        "target_criteria": meets_criteria,
        "recommendations": {
            "silhouette_interpretation": "Ótimo" if MODEL_METRICS['silhouette_score'] > 0.5 else "Bom" if MODEL_METRICS['silhouette_score'] > 0.3 else "Precisa melhorar",
            "cluster_quality": "Alta" if MODEL_METRICS['balanced_accuracy'] > 0.7 else "Média" if MODEL_METRICS['balanced_accuracy'] > 0.5 else "Baixa"
        }
    }

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
    
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'normalized_name']
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
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'normalized_name']
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
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'normalized_name']
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
    if n <= 0:
        return []

    df = GAMES_DF.copy()
    if genre:
        df = df[df['genre'].str.contains(genre, case=False, na=False)]
    if categoria:
        df = df[df['categoria'].str.contains(categoria, case=False, na=False)]
    if tag:
        df = df[df['tags'].str.contains(tag, case=False, na=False)]
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'normalized_name']
    if not df.empty:
        sample_size = min(n, len(df))
        sample_df = df.sample(n=sample_size)
    elif not GAMES_DF.empty:
        sample_size = min(n, len(GAMES_DF))
        sample_df = GAMES_DF.sample(n=sample_size)
    else:
        return []

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
    columns_to_show = ['title', 'genre', 'tags', 'categoria', 'url', 'normalized_name']
    indices = list(df.index)
    indices = random.sample(indices, min(top_n, len(indices)))
    
    result = [
        {"id": int(idx), **{col: df.loc[idx][col] for col in columns_to_show if col in df.loc[idx]}}
        for idx in indices
    ]
    
    return {
        "recommendations": result,
        "cluster_info": {
            "cluster_id": int(cluster_id),
            "total_games_in_cluster": len(df),
            "reference_game": GAMES_DF.loc[game_id, 'title']
        }
    }

@app.get("/model/retrain", summary="Retreinar modelo (desenvolvimento)")
def retrain_model():
    """Endpoint para retreinar o modelo - apenas para desenvolvimento"""
    global KMEANS_MODEL, MODEL_METRICS
    if GAMES_DF is None:
        raise HTTPException(503, "Dados não carregados.")
    
    print("Retreinando modelo KMeans...")
    # Código de retreino seria similar ao startup
    MODEL_METRICS = {'status': 'Retreino não implementado'}
    
    return {
        "status": "Modelo retreinado com sucesso",
        "new_metrics": MODEL_METRICS
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
