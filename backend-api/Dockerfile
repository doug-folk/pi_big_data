# ===========================
# Etapa 1: Composer dependencies
# ===========================
FROM composer:2 AS vendor

WORKDIR /app

# Copia apenas os arquivos de dependência primeiro (melhor cache)
COPY backend-api/composer.json backend-api/composer.lock ./

# Evita o erro do artisan no build (Laravel ainda não copiado)
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

# Agora sim executa os scripts do composer com o Laravel completo
RUN composer dump-autoload --optimize && php artisan package:discover --ansi || true

# Gera a APP_KEY caso não exista
RUN php artisan key:generate --show || true

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=${PORT}"]