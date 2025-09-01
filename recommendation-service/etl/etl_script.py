import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import time

def connect_to_db():
    
    dotenv_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=dotenv_path)

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_DATABASE")

    if not all([db_user, db_password, db_host, db_port, db_name]):
        print(" Erro: Uma ou mais variáveis de ambiente do banco de dados não foram definidas.")
        return None

    # URL de conexão para PostgreSQL
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    try:
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        print(" Conexão com o banco de dados estabelecida com sucesso!")
        return engine
    except Exception as e:
        print(f" Erro ao conectar com o banco de dados: {e}")
        return None

def main():
    """
    Função principal que orquestra o processo ETL.
    """
    start_time = time.time()
    print(" Iniciando o script ETL...")

    engine = connect_to_db()

    if engine is None:
        print(" Abortando o script devido a erro na conexão com o banco de dados.")
        return

    # (Extract, Transform, Load)

    end_time = time.time()
    print(f" Script ETL concluído em {end_time - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()