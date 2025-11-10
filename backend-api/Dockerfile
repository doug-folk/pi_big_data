# ===========================
# Etapa 1: Composer dependencies
# ===========================
FROM composer:2 AS vendor

WORKDIR /app

# Copia apenas os arquivos de dependência primeiro (melhor cache)
COPY backend-api/composer.json backend-api/composer.lock ./

# Evita erro do artisan no build (Laravel ainda não copiado)
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist


# ===========================
# Etapa 2: PHP Application
# ===========================
FROM php:8.2-cli

# Corrige ambiente não interativo e erros do debconf
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Instala dependências do sistema e extensões PHP necessárias
RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências do composer (da etapa anterior)
COPY --from=vendor /app/vendor /var/www/html/vendor

# Copia o restante da aplicação
COPY backend-api /var/www/html

WORKDIR /var/www/html

# ===========================
# Corrige cache e permissões
# ===========================
RUN php artisan config:clear || true && \
    php artisan cache:clear || true && \
    php artisan route:clear || true && \
    php artisan view:clear || true && \
    chmod -R 777 /var/www/html/storage /var/www/html/bootstrap/cache

# ===========================
# Garante conexão com o banco PostgreSQL (não SQLite)
# ===========================
ENV DB_CONNECTION=pgsql
ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}
ENV DB_DATABASE=${DB_DATABASE}
ENV DB_USERNAME=${DB_USERNAME}
ENV DB_PASSWORD=${DB_PASSWORD}

# ===========================
# Expor porta 8080
# ===========================
EXPOSE 8080

# ===========================
# Comando de inicialização (respeita variável PORT do Railway)
# ===========================
CMD ["sh", "-c", "php artisan serve --host=0.0.0.0 --port=${PORT:-8080}"]