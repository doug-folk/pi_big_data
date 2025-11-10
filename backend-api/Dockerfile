# ===========================
# Etapa 1: Composer dependencies
# ===========================
FROM composer:2 AS vendor

WORKDIR /app
# Cache eficiente: copia só os manifests
COPY backend-api/composer.json backend-api/composer.lock ./
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist


# ===========================
# Etapa 2: PHP + Laravel
# ===========================
FROM php:8.2-cli

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm
ENV TZ=UTC

# Dependências e extensões necessárias
RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev tzdata \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

# Código da aplicação e vendor
COPY --from=vendor /app/vendor /var/www/html/vendor
COPY backend-api /var/www/html

# Permissões (evita 500 por permissão)
RUN mkdir -p storage/framework/{cache,sessions,views,testing} \
    && chmod -R 777 storage bootstrap/cache

# Impede que o Laravel parseie DATABASE_URL do provedor (pode quebrar)
ENV DATABASE_URL=""

EXPOSE 8080

# ===========================
# Startup robusto
# ===========================
CMD sh -eu -c '\
  echo "🚀 Iniciando aplicação Laravel..." ; \
  # 1) Se .env não existir, gera um a partir das variáveis do ambiente
  if [ ! -f ".env" ]; then \
    echo "ℹ️  .env não encontrado, gerando a partir das variáveis de ambiente..." ; \
    : "${APP_NAME:=Laravel}"; \
    : "${APP_ENV:=production}"; \
    : "${APP_DEBUG:=true}"; \
    : "${APP_URL:=https://pibigdata-production-3c8e.up.railway.app}"; \
    # Gera APP_KEY se não vier do ambiente (formato base64:xxxxx)
    if [ -z "${APP_KEY:-}" ]; then \
      APP_KEY="base64:$(php -r 'echo base64_encode(random_bytes(32));')"; \
      echo "ℹ️  APP_KEY gerada automaticamente."; \
    fi; \
    cat > .env <<EOF
APP_NAME=${APP_NAME}
APP_ENV=${APP_ENV}
APP_DEBUG=${APP_DEBUG}
APP_KEY=${APP_KEY}
APP_URL=${APP_URL}

DB_CONNECTION=${DB_CONNECTION:-}
DB_HOST=${DB_HOST:-}
DB_PORT=${DB_PORT:-}
DB_DATABASE=${DB_DATABASE:-}
DB_USERNAME=${DB_USERNAME:-}
DB_PASSWORD=${DB_PASSWORD:-}

SESSION_DRIVER=${SESSION_DRIVER:-file}
SESSION_LIFETIME=${SESSION_LIFETIME:-120}
SESSION_SECURE_COOKIE=${SESSION_SECURE_COOKIE:-true}
CACHE_DRIVER=${CACHE_DRIVER:-file}
QUEUE_CONNECTION=${QUEUE_CONNECTION:-sync}

APP_TRUSTED_PROXIES=${APP_TRUSTED_PROXIES:-*}
APP_TRUSTED_HOSTS=${APP_TRUSTED_HOSTS:-pibigdata-production-3c8e.up.railway.app}

PORT=${PORT:-8080}
EOF
  fi ; \
  # 2) Pré-checagens: DB_* obrigatórias e DB_CONNECTION=pgsql
  needvars="DB_CONNECTION DB_HOST DB_PORT DB_DATABASE DB_USERNAME DB_PASSWORD"; \
  for v in $needvars; do \
    if [ -z "${!v:-}" ]; then \
      echo "❌ Variável $v ausente. Defina nas Variables do Railway."; \
      echo "   Requeridas: $needvars"; \
      exit 1; \
    fi; \
  done ; \
  if [ "${DB_CONNECTION}" != "pgsql" ]; then \
    echo "❌ DB_CONNECTION deve ser pgsql. Valor atual: ${DB_CONNECTION}"; \
    exit 1; \
  fi ; \
  # 3) Limpa caches antigos (evita fallback para sqlite)
  rm -f bootstrap/cache/config.php bootstrap/cache/*.php || true; \
  php artisan config:clear || true; \
  php artisan cache:clear || true; \
  php artisan route:clear || true; \
  php artisan view:clear || true; \
  php artisan config:cache || true; \
  echo "✅ Cache recompilado com sucesso!" ; \
  # 4) (Opcional) Rodar migrations em boot - descomente se quiser
  # php artisan migrate --force || true ; \
  # 5) Sobe o servidor
  php artisan serve --host=0.0.0.0 --port=${PORT:-8080} \