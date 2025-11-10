# ===========================
# Etapa 1: Instalação de dependências via Composer
# ===========================
FROM composer:2 AS vendor

WORKDIR /app
COPY backend-api/composer.json backend-api/composer.lock ./
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist

# ===========================
# Etapa 2: Aplicação Laravel (PHP 8.2)
# ===========================
FROM php:8.2-cli

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

COPY --from=vendor /app/vendor /var/www/html/vendor
COPY backend-api /var/www/html

WORKDIR /var/www/html

# Permissões
RUN chmod -R 777 /var/www/html/storage /var/www/html/bootstrap/cache

# ⚙️ Ignora DATABASE_URL do Railway (para não sobrescrever seu .env)
ENV DATABASE_URL=""

EXPOSE 8080

# 🚀 Inicialização com limpeza de cache automática
CMD sh -c "echo '🚀 Iniciando aplicação Laravel...' && \
           php artisan config:clear && \
           php artisan cache:clear && \
           php artisan route:clear && \
           php artisan view:clear && \
           php artisan config:cache && \
           echo '✅ Cache limpo com sucesso!' && \
           php artisan serve --host=0.0.0.0 --port=${PORT:-8080}"