# ===========================
# Etapa 1: Dependências PHP (Composer)
# ===========================
FROM composer:2 AS vendor

WORKDIR /app
COPY composer.json composer.lock ./ 
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist


# ===========================
# Etapa 2: Build do Frontend com Vite (Node 18)
# ===========================
FROM node:18 AS vite

WORKDIR /app/backend-api

# Copia apenas arquivos essenciais para cache eficiente
COPY backend-api/package*.json ./ 
RUN npm cache clean --force && npm install --legacy-peer-deps

# Copia o backend (onde está o Vite configurado)
COPY backend-api ./ 

# Executa build do Vite
RUN npm run build || echo "⚠️ Build do Vite falhou, continuando mesmo assim..."


# ===========================
# Etapa 3: Aplicação Laravel (PHP)
# ===========================
FROM php:8.2-cli

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Instala dependências do PHP e extensões necessárias
RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev tzdata \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências PHP (vendor)
COPY --from=vendor /app/vendor /var/www/html/vendor

# Copia aplicação (Laravel + build Vite)
COPY --from=vite /app/backend-api /var/www/html

WORKDIR /var/www/html

# Ajusta permissões
RUN mkdir -p storage/framework/{cache,sessions,views,testing} \
    && chmod -R 777 storage bootstrap/cache public

# Limpa e recompila cache Laravel
RUN php artisan config:clear || true \
 && php artisan cache:clear || true \
 && php artisan route:clear || true \
 && php artisan view:clear || true \
 && php artisan config:cache || true

EXPOSE 8080

# Inicia o servidor Laravel
CMD ["sh", "-c", "php artisan serve --host=0.0.0.0 --port=${PORT:-8080}"]