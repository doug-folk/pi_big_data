# ===========================
# Etapa 1: Build das dependências
# ===========================
FROM composer:2 AS vendor

WORKDIR /app
COPY backend-api/composer.json backend-api/composer.lock ./
RUN composer install --no-dev --no-interaction --no-progress --prefer-dist

# ===========================
# Etapa 2: Configuração do PHP
# ===========================
FROM php:8.2-cli

# Instala extensões necessárias
RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências do Composer
COPY --from=vendor /app/vendor /var/www/html/vendor

# Copia o restante do código da aplicação
COPY backend-api /var/www/html

WORKDIR /var/www/html

# Gera APP_KEY se não existir
RUN php artisan key:generate --show || true

# Expõe a porta padrão do Laravel
EXPOSE 8000

# Comando de inicialização
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=${PORT}"]