# ===========================
# Etapa 1: Composer (vendor)
# ===========================
FROM composer:2 AS vendor
WORKDIR /app

# Copia os manifests do Laravel
COPY backend-api/composer.json backend-api/composer.lock ./
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist

# ===========================
# Etapa 2: Vite (Node 18)
# ===========================
FROM node:18 AS vite
WORKDIR /app/backend-api

# Instala dependências do Vite
COPY backend-api/package*.json ./
RUN npm install --legacy-peer-deps

# Copia o restante do backend (inclui recursos e vite.config.js)
COPY backend-api/ ./
RUN npm run build || echo "⚠️ Build do Vite falhou, mas continuando..."

# ===========================
# Etapa 3: PHP Runtime
# ===========================
FROM php:8.2-cli

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev tzdata \
 && docker-php-ext-install pdo pdo_pgsql zip \
 && pecl install redis \
 && docker-php-ext-enable redis \
 && rm -rf /var/lib/apt/lists/*

# Copia dependências e aplicação
COPY --from=vendor /app/vendor /var/www/html/vendor
COPY --from=vite /app/backend-api /var/www/html

WORKDIR /var/www/html

# Permissões e cache Laravel
RUN mkdir -p storage/framework/{cache,sessions,views,testing} \
 && chmod -R 777 storage bootstrap/cache public \
 && php artisan config:clear || true \
 && php artisan cache:clear  || true \
 && php artisan route:clear  || true \
 && php artisan view:clear   || true \
 && php artisan config:cache || true

EXPOSE 8080

CMD ["sh", "-c", "php artisan serve --host=0.0.0.0 --port=${PORT:-8080}"]