# GameFinder - Sistema de Recomendação de Jogos

## Sobre o Projeto

O GameFinder é uma aplicação web de recomendação de jogos desenvolvida para ajudar os jogadores a descobrir novos títulos alinhados aos seus gostos pessoais. O sistema utiliza uma **abordagem híbrida**, combinando:

* **Filtragem Colaborativa:** Analisa o comportamento de usuários com gostos similares para fazer recomendações.
* **Filtragem Baseada em Conteúdo:** Recomenda jogos que compartilham características com os jogos que o usuário já gostou.

Essa combinação garante recomendações mais robustas e personalizadas, superando as limitações de sistemas de recomendação genéricos.

## Stack de Tecnologias

O projeto é construído com uma stack moderna e distribuída, organizada em três componentes principais:

###  **Backend (API Principal)**
* **Linguagem:** PHP 8.x
* **Framework:** Laravel 10.x
* **Banco de Dados:** PostgreSQL e Redis (para cache)

###  **Serviço de Recomendações**
* **Linguagem:** Python 3.10+
* **Framework:** FastAPI
* **Bibliotecas:** Pandas, NumPy, Scikit-learn, SciPy

###  **Frontend (Interface do Usuário)**
* **Framework:** React 18.x
* **Roteamento:** React Router DOM
* **Estilização:** Tailwind CSS (ou CSS Modules, dependendo da implementação)

## Estrutura do Projeto

O projeto é organizado em uma arquitetura de monorepo, com cada componente residindo em seu próprio diretório.

        /pi_big_data/
        
        ├── /backend/
        
        │   ├── ... (API principal em Laravel)
        ├── /recommender-service/
        
        │   ├── ... (Serviço de recomendação em Python)
        └── /frontend/
            └── ... (Interface do usuário em React)

## Como Rodar o Projeto

Siga as instruções abaixo para configurar e iniciar cada parte da aplicação. Certifique-se de que você já tem o **PHP**, **Composer**, **Python**, **pip**, **Node.js** e **npm** instalados em sua máquina.

### 1. Configuração do Backend (Laravel)

1.  Entre no diretório do backend:
    ```bash
    cd backend
    ```

2.  Instale as dependências:
    ```bash
    composer install
    ```

3.  Copie o arquivo de exemplo do ambiente e configure as credenciais do banco de dados no arquivo `.env`:
    ```bash
    cp .env.example .env
    ```

4.  Execute as migrações e seeders para popular o banco de dados com dados de teste:
    ```bash
    php artisan migrate --seed
    ```

5.  Inicie o servidor local do Laravel:
    ```bash
    php artisan serve
    ```

### 2. Configuração do Serviço de Recomendações (Python)

1.  Entre no diretório do serviço:
    ```bash
    cd ../recommender-service
    ```

2.  Crie e ative o ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Para Linux/macOS
    # venv\Scripts\activate   # Para Windows
    ```
2.1.  Crie um arquivo .env com a variável DATABASE_URL apontando para o banco de dados do Laravel, por exemplo:
```bash
DATABASE_URL="postgresql://postgres:root@127.0.0.1:5432/gamefinder"
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=gamefinder
DB_USER=postgres
DB_PASSWORD=root
```

3.  Instale as bibliotecas necessárias:
    ```bash
    pip install -r requirements.txt
    ```
3.1.  Rode o script etl:
    ```bash
    pip python3 etl_scripty.py
    ```
    
4.  Inicie o servidor da API com Uvicorn:
    ```bash
    uvicorn recommender_service:app --reload --port 8001
    ```

### 3. Configuração do Frontend (React) -- NÃO IMPLEMENTADO AINDA - frontend atual fetio em css e js puro - rode um servidor local ou usa a extensão do vscode "Go live"

1.  Entre no diretório do frontend:
    ```bash
    cd ../frontend
    ```

2.  Instale as dependências do Node.js:
    ```bash
    npm install
    ```

3.  Inicie o servidor de desenvolvimento do React:
    ```bash
    npm start
    ```

Se tudo estiver configurado corretamente, o backend estará acessível em `http://localhost:8000`, o serviço de Python em `http://localhost:8001` (ou a porta que você configurar no Uvicorn) e o frontend em `http://localhost:3000`.

## Execução com Docker

Para subir toda a stack com um único comando:

1. Garanta que Docker e Docker Compose estejam instalados.
2. Se tiver um stack anterior rodando, pare-o:
   ```bash
   docker compose down
   ```
3. Na raiz do projeto, suba a stack reconstruindo as imagens:
   ```bash
   docker compose up --build
   ```
4. Aguarde os logs mostrarem o término do serviço `etl` (responsável por popular a tabela `games` com os datasets de Steam/Amazon). Assim que ele finalizar, os serviços ficarão ativos em:
   - Frontend: `http://localhost:3000`
   - Backend Laravel: `http://localhost:8000`
   - Serviço de recomendações (FastAPI): `http://localhost:8001`

O PostgreSQL e o Redis ficam acessíveis apenas dentro da rede Docker (por exemplo, `docker compose exec postgres psql -U postgres gamefinder`). Caso precise um acesso externo, exponha as portas manualmente no `docker-compose.yml`.

O volume `postgres_data` preserva o banco entre reinicializações. Para zerar tudo, use `docker compose down -v`.
