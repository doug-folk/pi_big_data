    # Guia de Instalação e Configuração - GameFinder

Este documento descreve os passos necessários para configurar o ambiente de desenvolvimento do projeto GameFinder em sua máquina local.

## 1. Pré-requisitos (Software)

Certifique-se de ter as seguintes ferramentas instaladas em seu sistema. É crucial usar as versões especificadas para evitar conflitos de compatibilidade.

- **Git:** [https://git-scm.com/](https://git-scm.com/)
- **PHP:** `8.4`
- **Composer:** `2.x`
- **PostgreSQL:** `17`
- **Redis:** `7.2`
- **Python:** `3.13`
- **Node.js:** `22.x (LTS)`

## 2. Instalação (Instruções por Sistema Operacional)

### Para macOS (via Homebrew)
```bash
# Atualiza o Homebrew
brew update

# Instala as ferramentas
brew install php
brew install postgresql@17
brew install redis
brew install python@3.13
brew install node@22

# Inicia os serviços do PostgreSQL e Redis para que rodem em background
brew services start postgresql@17
brew services start redis
```

### Para Linux
```bash
# Atualiza os pacotes
sudo apt update && sudo apt upgrade -y

# Adiciona repositórios de terceiros para versões recentes (PPA)
sudo add-apt-repository ppa:ondrej/php -y
sudo apt-get update
curl -fsSL [https://deb.nodesource.com/setup_22.x](https://deb.nodesource.com/setup_22.x) | sudo -E bash -

# Instala as ferramentas
sudo apt install -y git php8.4 php8.4-pgsql php8.4-redis php8.4-xml composer
sudo apt install -y postgresql-17
sudo apt install -y redis-server
sudo apt install -y python3.13 python3-pip python3.13-venv
sudo apt install -y nodejs

# Inicia e habilita os serviços do PostgreSQL e Redis
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Para Windows(WSL2)
A forma recomendada para desenvolver no Windows é usando o Windows Subsystem for Linux (WSL2) com uma distribuição como o Ubuntu.

Abra o PowerShell como Administrador e execute: 

```bash
wsl --install
```

Após a instalação, configure seu usuário e senha.

Dentro do ambiente WSL2 (Ubuntu), siga as mesmas instruções da seção "Para Linux" acima.

O Visual Studio Code possui uma integração excelente com o WSL2, permitindo que você edite o código no Windows enquanto ele é executado no Linux.

## 3.  Configuração do Projeto

Após instalar todos os pré-requisitos, siga estes passos para configurar o projeto:

1. Clone o repositório:

```bash
git clone https://github.com/doug-folk/pi_big_data.git
cd pi_big_data
```

2. Configure o Backend (Laravel):

# Navegue até a pasta da API
```bash
cd backend-api
```

# Copie o arquivo de ambiente
```bash
cp .env.example .env
```

# Edite o .env e configure suas credenciais do PostgreSQL
# Exemplo:
# DB_CONNECTION=pgsql
# DB_HOST=127.0.0.1
# DB_PORT=5432
# DB_DATABASE=gamefinder
# DB_USERNAME=seu_usuario_postgres
# DB_PASSWORD=sua_senha_postgres

# Instale as dependências do PHP
```bash
composer install
```

# Gere a chave da aplicação
```bash
php artisan key:generate
```

3. Configure o Serviço de Recomendações (Python):

# Volte para a raiz e entre na pasta do serviço de ML
```bash
cd ../recommendation-service
```

# Crie e ative um ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate
# No Windows (Git Bash/CMD): venv\Scripts\activate
```

# Instale as dependências do Python
```bash
pip install -r requirements.txt
```
4. Configure o Frontend (React):

```bash
# Volte para a raiz e entre na pasta do frontend
cd ../frontend
```

# Instale as dependências do JavaScript
```bash
npm install
```

##4. Populando o Banco de Dados (ETL)

#obs: Os datasets são muito grandes para serem versionados. Faça o download manual dos arquivos e coloque-os na pasta correta: 

```bash
/pi_big_data/recommendation-service/etl/data/
```

- `meta_Video_Games.json` (https://www.kaggle.com/datasets/gabrielfreddi/amazon-reviews-de-vdeo-games)
- `Video_Games.json` (https://www.kaggle.com/datasets/gabrielfreddi/amazon-reviews-de-vdeo-games)
- `steam-games-complete-dataset.csv` (https://www.kaggle.com/datasets/trolukovich/steam-games-complete-dataset)

1. Crie a estrutura do banco (Migrations do Laravel):

# Dentro da pasta backend-api/
```bash
php artisan migrate
```
2. Execute o script ETL para popular os dados:
```bash
# Dentro da pasta recommendation-service/ (com o venv ativado)
python etl/etl_script.py
```
##5. Executando o Projeto

- Terminal 1: Backend API (Laravel)

```bash
cd backend-api
php artisan serve --port=8000
# > API estará rodando em [http://127.0.0.1:8000](http://127.0.0.1:8000)
```
- Terminal 2: Serviço de Recomendações (Python/FastAPI)
```bash
cd recommendation-service
source venv/activate # Ative o ambiente virtual
uvicorn app.main:app --reload --port=8001
# > Serviço de ML estará rodando em [http://127.0.0.1:8001](http://127.0.0.1:8001)
```

- Terminal 3: Frontend (React)
```bash
cd frontend
npm start
# > Aplicação web estará rodando em http://localhost:3000
```

