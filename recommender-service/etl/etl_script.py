import os
import re
import time
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from rapidfuzz import fuzz, process
from tqdm import tqdm
import numpy as np


def connect_to_db():
    """Carrega variáveis de ambiente e estabelece conexão com o banco de dados PostgreSQL."""
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
        with engine.connect() as connection:
            print("Conexão com o banco de dados estabelecida com sucesso!")
        return engine
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        return None


def extract_data(base_dir):
    """Carrega os datasets da Steam e da Amazon a partir dos arquivos."""
    print("\nIniciando fase de extração...")
    steam_path = os.path.join(base_dir, 'etl/data', 'steam-games-complete-dataset.csv')
    amazon_meta_path = os.path.join(base_dir, 'etl/data', 'meta_Video_Games.json')
    amazon_ratings_path = os.path.join(base_dir, 'etl/data', 'Video_Games.json')

    try:
        steam_df = pd.read_csv(steam_path)
        print(f"{len(steam_df)} registros carregados do dataset da Steam.")

        amazon_meta_df = pd.read_json(amazon_meta_path, lines=True, convert_dates=False)
        print(f"{len(amazon_meta_df)} registros carregados de metadados da Amazon.")

        return steam_df, amazon_meta_df, amazon_ratings_path
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado. {e}")
        return None, None, None


def normalize_name(name):
    """Limpa e padroniza o nome de um jogo para facilitar a correspondência."""
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r'\(.*\)|\[.*\]', '', name) 
    name = re.sub(r'[^a-z0-9\s]', '', name)   
    name = re.sub(r'\s+', ' ', name).strip() 
    return name

def transform_and_unify_games(steam_df, amazon_meta_df):
    """
    Unifica os dataframes da Steam e Amazon, tratando duplicatas e consolidando informações.
    """
    print("\nIniciando fase de transformação e unificação...")

    steam_df['normalized_name'] = steam_df['name'].apply(normalize_name)
    amazon_meta_df['normalized_name'] = amazon_meta_df['title'].apply(normalize_name)

    # Inclui colunas extras se existirem
    extra_cols = ['genre', 'tags', 'description', 'platform', 'developer', 'release_date']
    for col in extra_cols:
        if col not in steam_df.columns:
            steam_df[col] = ''
        if col not in amazon_meta_df.columns:
            amazon_meta_df[col] = ''

    steam_df_norm = steam_df[['name', 'normalized_name'] + extra_cols].rename(columns={'name': 'title_steam'}).copy()
    amazon_df_norm = amazon_meta_df[['asin', 'title', 'normalized_name', 'imageURLHighRes', 'brand'] + extra_cols].rename(columns={'title': 'title_amazon', 'imageURLHighRes': 'image_url'}).copy()

    steam_df_norm.dropna(subset=['normalized_name'], inplace=True)
    amazon_df_norm.dropna(subset=['normalized_name'], inplace=True)
    steam_df_norm = steam_df_norm[steam_df_norm['normalized_name'] != '']
    amazon_df_norm = amazon_df_norm[amazon_df_norm['normalized_name'] != '']

    unified_df = pd.merge(steam_df_norm, amazon_df_norm, on='normalized_name', how='outer', suffixes=('_steam', '_amazon'))
    print(f"{len(unified_df)} registros brutos após a junção inicial.")

    print("Consolidando jogos duplicados...")

    unified_df['sort_key'] = unified_df['title_steam'].notna().astype(int) + unified_df['image_url'].notna().astype(int)
    unified_df.sort_values(by='sort_key', ascending=False, inplace=True)

    # Agrega todas as colunas extras pegando o valor não nulo prioritário
    agg_dict = {
        'title_steam': ('title_steam', 'first'),
        'title_amazon': ('title_amazon', 'first'),
        'amazon_asins': ('asin', lambda x: list(x.dropna().unique())),
        'image_url': ('image_url', 'first'),
        'brand': ('brand', 'first'),
    }
    for col in extra_cols:
        agg_dict[col] = (f'{col}_steam', 'first') if f'{col}_steam' in unified_df.columns else (f'{col}_amazon', 'first')

    for col in extra_cols:
        if f'{col}_steam' in unified_df.columns and f'{col}_amazon' in unified_df.columns:
            unified_df[col] = unified_df[f'{col}_steam'].combine_first(unified_df[f'{col}_amazon'])
        elif f'{col}_steam' in unified_df.columns:
            unified_df[col] = unified_df[f'{col}_steam']
        elif f'{col}_amazon' in unified_df.columns:
            unified_df[col] = unified_df[f'{col}_amazon']

    consolidated_games = unified_df.groupby('normalized_name').agg(
        title_steam=('title_steam', 'first'),
        title_amazon=('title_amazon', 'first'),
        amazon_asins=('asin', lambda x: list(x.dropna().unique())),
        image_url=('image_url', 'first'),
        brand=('brand', 'first'),
        genre=('genre', 'first'),
        tags=('tags', 'first'),
        description=('description', 'first'),
        platform=('platform', 'first'),
        developer=('developer', 'first'),
        release_date=('release_date', 'first')
    ).reset_index()

    consolidated_games['title'] = consolidated_games['title_steam'].fillna(consolidated_games['title_amazon'])
    consolidated_games.dropna(subset=['title'], inplace=True)

    final_games = consolidated_games[['title', 'normalized_name', 'amazon_asins', 'image_url', 'brand', 'genre', 'tags', 'description', 'platform', 'developer', 'release_date']].copy()
    final_games.reset_index(drop=True, inplace=True)
    final_games.insert(0, 'id', final_games.index) 

    print(f"Transformação concluída. Total de {len(final_games)} jogos únicos.")
    print("Exemplo dos 5 primeiros jogos consolidados:")
    print(final_games.head())
    return final_games


def load_to_postgres(df, table_name, engine, if_exists='replace', chunksize=1000):
    """Carrega um DataFrame para uma tabela no PostgreSQL de forma eficiente."""
    print(f"\nCarregando {len(df)} registros para a tabela '{table_name}'...")
    try:
        df.to_sql(table_name, engine, if_exists=if_exists, index=False, method='multi', chunksize=chunksize)
        print(f"Carga para '{table_name}' concluída com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar dados para '{table_name}': {e}")

def process_and_load_ratings(games_df, ratings_file_path, engine, chunk_size=100_000):
    """Processa e carrega as avaliações em chunks para economizar memória."""
    print("\nIniciando processamento e carga das avaliações...")

    print("Extraindo usuários únicos do arquivo de avaliações...")
    all_user_ids = set()
    ratings_iterator_for_users = pd.read_json(ratings_file_path, lines=True, chunksize=chunk_size, dtype=False)
    for chunk in tqdm(ratings_iterator_for_users, desc="Lendo usuários"):
        all_user_ids.update(chunk['reviewerID'].unique())

    users_df = pd.DataFrame(list(all_user_ids), columns=['amazon_user_id'])
    users_df.reset_index(drop=True, inplace=True)
    users_df.insert(0, 'id', users_df.index)
    print(f"Encontrados {len(users_df)} usuários únicos.")
    load_to_postgres(users_df, 'users', engine)

    print("Preparando mapeamentos de ID...")
    
    exploded_asins = games_df.explode('amazon_asins')
    
    unique_asins_map_df = exploded_asins.drop_duplicates(subset=['amazon_asins'], keep='first')
    
    asin_to_game_id = unique_asins_map_df.set_index('amazon_asins')['id']

    user_to_user_id = users_df.set_index('amazon_user_id')['id']

    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS ratings;'))
        conn.commit() 
    print("Tabela 'ratings' antiga removida.")

    total_ratings_loaded = 0
    ratings_iterator = pd.read_json(ratings_file_path, lines=True, chunksize=chunk_size, dtype=False)
    for i, chunk in enumerate(tqdm(ratings_iterator, desc="Processando avaliações")):
        chunk.rename(columns={'reviewerID': 'amazon_user_id', 'asin': 'amazon_asin', 'overall': 'rating', 'unixReviewTime': 'timestamp'}, inplace=True)

        chunk['user_id'] = chunk['amazon_user_id'].map(user_to_user_id)
        chunk['game_id'] = chunk['amazon_asin'].map(asin_to_game_id)

        final_chunk = chunk[['user_id', 'game_id', 'rating', 'timestamp']].dropna()
        
        if final_chunk.empty:
            continue

        final_chunk = final_chunk.astype({'user_id': 'int64', 'game_id': 'int64', 'rating': 'int8'})
        final_chunk.drop_duplicates(subset=['user_id', 'game_id'], keep='last', inplace=True)

        if not final_chunk.empty:
            final_chunk.to_sql('ratings', engine, if_exists='append', index=False, method='multi')
            total_ratings_loaded += len(final_chunk)

    print(f"\nCarregamento de avaliações concluído. Total de {total_ratings_loaded} registros únicos carregados.")




def main():
    """Orquestra todo o processo de ETL."""
    start_time = time.time()
    print("Iniciando o pipeline ETL completo...")

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

    engine = connect_to_db()
    if engine is None:
        return


    steam_df, amazon_meta_df, ratings_file_path = extract_data(script_dir)
    if steam_df is None or amazon_meta_df is None:
        return

    final_games_df = transform_and_unify_games(steam_df, amazon_meta_df)

    load_to_postgres(final_games_df.drop(columns=['amazon_asins', 'normalized_name']), 'games', engine)
    process_and_load_ratings(final_games_df, ratings_file_path, engine)

    end_time = time.time()
    print(f"\nPipeline ETL concluído com sucesso em {end_time - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()
