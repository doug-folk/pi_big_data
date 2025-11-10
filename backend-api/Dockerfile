# ===========================
# Etapa 1: Build do FRONTEND
# ===========================
FROM node:18 AS frontend

WORKDIR /app/frontend

# Copia apenas os arquivos essenciais do frontend (ajuste o caminho conforme o seu projeto)
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps

COPY frontend ./
RUN npm run build

# ===========================
# Etapa 2: Dependências do Laravel (Composer)
# ===========================
FROM composer:2 AS vendor

WORKDIR /app
COPY backend-api/composer.json backend-api/composer.lock ./
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist

# ===========================
# Etapa 3: Aplicação PHP (Laravel)
# ===========================
FROM php:8.2-cli

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Instala dependências do PHP
RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev tzdata \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências do Laravel (Composer)
COPY --from=vendor /app/vendor /var/www/html/vendor

# Copia a aplicação Laravel
COPY backend-api /var/www/html

# Copia o build do frontend para o public/ do Laravel
COPY --from=frontend /app/frontend/dist /var/www/html/public

WORKDIR /var/www/html

# Ajusta permissões
RUN mkdir -p storage/framework/{cache,sessions,views,testing} \
    && chmod -R 777 storage bootstrap/cache

# Remove cache antigo e recompila configs
RUN php artisan config:clear || true && \
    php artisan cache:clear || true && \
    php artisan route:clear || true && \
    php artisan view:clear || true && \
    php artisan config:cache || true

# Define a porta padrão
EXPOSE 8080

# Inicialização
CMD ["sh", "-c", "php artisan serve --host=0.0.0.0 --port=${PORT:-8080}"]