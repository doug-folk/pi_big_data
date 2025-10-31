import os
import re
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def connect_to_db():
    load_dotenv()
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_DATABASE")
    if not all([db_user, db_password, db_host, db_port, db_name]):
        print("Erro: Variáveis de ambiente do banco de dados não estão definidas.")
        return None
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    try:
        engine = create_engine(database_url)
        with engine.connect() as _:
            print("Conexão com o banco de dados estabelecida com sucesso!")
        return engine
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        return None

def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r'\(.*\)|\[.*\]', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

def ensure_list(val):
    if val is None or (isinstance(val, (float, np.floating)) and np.isnan(val)):
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, str):
        try:
            loaded = json.loads(val)
            return loaded if isinstance(loaded, list) else [loaded]
        except:
            return [val]
    return [val]

def sanitize_url(val):
    if isinstance(val, (float, np.floating)) and np.isnan(val):
        return None
    if isinstance(val, str):
        trimmed = val.strip()
        if not trimmed or trimmed.lower() in {'unknown', 'nan', 'null', 'none'}:
            return None
        if re.match(r'^https?://', trimmed):
            return trimmed
    return None

def normalize_scalar_value(val):
    if val is None:
        return 'Unknown'
    if isinstance(val, (float, np.floating)) and np.isnan(val):
        return 'Unknown'
    if isinstance(val, str):
        trimmed = val.strip()
        if not trimmed or trimmed.lower() in {'nan', 'null', 'none'}:
            return 'Unknown'
        return trimmed
    return str(val)

def main():
    base_dir = os.getcwd()
    engine = connect_to_db()
    if engine is None:
        return
    steam_path = os.path.join(base_dir, 'etl/data', 'steam-games-complete-dataset.csv')
    amazon_meta_path = os.path.join(base_dir, 'etl/data', 'meta_Video_Games.json')
    try:
        steam_df = pd.read_csv(steam_path)
        amazon_meta_df = pd.read_json(amazon_meta_path, lines=True, convert_dates=False)
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        return

    # Apaga e recria a tabela 'games' antes de popular
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS games"))
        conn.execute(text("""
            CREATE TABLE games (
                id INTEGER PRIMARY KEY,
                title TEXT,
                name TEXT,
                url TEXT,
                reviews TEXT,
                genre TEXT,
                categoria TEXT,
                tags TEXT,
                image_url TEXT,
                normalized_name TEXT
            )
        """))
    steam_cols = ['name', 'url', 'reviews', 'genre', 'popular_tags', 'image_url']
    amazon_cols = ['title', 'category']
    steam_df['normalized_name'] = steam_df['name'].apply(normalize_name)
    amazon_meta_df['normalized_name'] = amazon_meta_df['title'].apply(normalize_name)
    for col in steam_cols:
        if col not in steam_df.columns:
            steam_df[col] = ''
    steam_df_norm = steam_df[['normalized_name'] + steam_cols].copy()
    amazon_df_norm = amazon_meta_df[['normalized_name'] + amazon_cols].copy()
    steam_df_norm.dropna(subset=['normalized_name'], inplace=True)
    amazon_df_norm.dropna(subset=['normalized_name'], inplace=True)
    steam_df_norm = steam_df_norm[steam_df_norm['normalized_name'] != '']
    amazon_df_norm = amazon_df_norm[amazon_df_norm['normalized_name'] != '']
    unified_df = pd.merge(steam_df_norm, amazon_df_norm, on='normalized_name', how='outer')
    print(f"{len(unified_df)} registros após junção.")
    final_games = pd.DataFrame()
    final_games['title'] = unified_df['title'].fillna(unified_df['name'])
    final_games['name'] = unified_df['name']
    final_games['url'] = unified_df['url'].apply(sanitize_url)
    final_games['reviews'] = unified_df['reviews']
    final_games['genre'] = unified_df['genre']
    final_games['categoria'] = unified_df['category'].apply(lambda x: json.dumps(ensure_list(x)) if x else json.dumps(['Unknown']))
    final_games['tags'] = unified_df['popular_tags'].apply(lambda x: json.dumps(ensure_list(x)) if x else json.dumps(['Unknown']))
    final_games['image_url'] = unified_df['image_url'].apply(sanitize_url)
    final_games['normalized_name'] = unified_df['normalized_name']
    final_games.reset_index(drop=True, inplace=True)
    final_games.insert(0, 'id', final_games.index)
    migration_cols = [
        'id', 'title', 'name', 'url', 'reviews', 'genre', 'categoria', 'tags', 'image_url', 'normalized_name'
    ]
    final_games = final_games.reindex(columns=migration_cols)
    textual_columns = ['title', 'name', 'reviews', 'genre', 'categoria', 'tags', 'normalized_name']
    for col in textual_columns:
        final_games[col] = final_games[col].apply(normalize_scalar_value)

    final_games['url'] = final_games['url'].apply(sanitize_url)
    final_games['image_url'] = final_games['image_url'].apply(sanitize_url)

    valid_url_count = final_games['url'].notna().sum()
    missing_url_count = len(final_games) - valid_url_count
    print(f"URLs válidas: {valid_url_count}. Registros sem URL: {missing_url_count}.")
    print(f"Transformação concluída. {len(final_games)} jogos únicos.")
    print(final_games.head())
    for start in range(0, len(final_games), 200):
        batch_df = final_games.iloc[start:start+200]
        batch_df.to_sql('games', engine, if_exists='append', index=False)
    print("Carga para 'games' concluída.")

if __name__ == "__main__":
    main()
