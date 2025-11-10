# ===========================
# Etapa 1: Instalação de dependências via Composer
# ===========================
FROM composer:2 AS vendor

WORKDIR /app

# Copia apenas os arquivos de dependência primeiro (melhor uso de cache)
COPY backend-api/composer.json backend-api/composer.lock ./

# Instala dependências PHP (sem scripts ainda, para evitar erros do artisan)
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist


# ===========================
# Etapa 2: Aplicação Laravel (PHP 8.2)
# ===========================
FROM php:8.2-cli

# Corrige ambiente não interativo e erros do debconf
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Instala dependências e extensões PHP necessárias
RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências do Composer da etapa anterior
COPY --from=vendor /app/vendor /var/www/html/vendor

# Copia o restante da aplicação Laravel
COPY backend-api /var/www/html

WORKDIR /var/www/html

# ===========================
# Limpeza e permissões
# ===========================
RUN chmod -R 777 /var/www/html/storage /var/www/html/bootstrap/cache

# ===========================
# Configuração do banco de dados PostgreSQL (Railway)
# ===========================
ENV DB_CONNECTION=pgsql
ENV DB_HOST=shinkansen.proxy.rlwy.net
ENV DB_PORT=43572
ENV DB_DATABASE=railway
ENV DB_USERNAME=postgres
ENV DB_PASSWORD=CsOQcmVGWvMNhuDFStcdTRYwsMCLJHSL

# ⚠️ Sobrescreve DATABASE_URL do Railway (para evitar conflitos)
ENV DATABASE_URL=""

# ===========================
# Porta e inicialização
# ===========================
EXPOSE 8080

# ===========================
# Inicialização com limpeza de cache automática
# ===========================
CMD sh -c "echo '🚀 Iniciando aplicação Laravel...' && \
           php artisan config:clear && \
           php artisan cache:clear && \
           php artisan route:clear && \
           php artisan view:clear && \
           php artisan config:cache && \
           echo '✅ Cache limpo com sucesso!' && \
           php artisan serve --host=0.0.0.0 --port=${PORT:-8080}"