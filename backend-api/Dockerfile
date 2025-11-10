# ===========================
# Etapa 1: Composer dependencies
# ===========================
FROM composer:2 AS vendor

WORKDIR /app
COPY backend-api/composer.json backend-api/composer.lock ./
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist

# ===========================
# Etapa 2: PHP + Laravel
# ===========================
FROM php:8.2-cli

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm
ENV TZ=UTC

RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev tzdata \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

COPY --from=vendor /app/vendor /var/www/html/vendor
COPY backend-api /var/www/html

RUN mkdir -p storage/framework/{cache,sessions,views,testing} \
    && chmod -R 777 storage bootstrap/cache

# Impede parse automático do DATABASE_URL
ENV DATABASE_URL=""

EXPOSE 8080

# ===========================
# Inicialização segura e robusta
# ===========================
CMD sh -eu -c '\
  echo "🚀 Iniciando aplicação Laravel..." ; \
  # 1) Gera .env se não existir
  if [ ! -f ".env" ]; then \
    echo "ℹ️  Gerando novo .env..." ; \
    : "${APP_NAME:=Laravel}"; \
    : "${APP_ENV:=production}"; \
    : "${APP_DEBUG:=true}"; \
    : "${APP_URL:=https://pibigdata-production-3c8e.up.railway.app}"; \
    if [ -z "${APP_KEY:-}" ]; then \
      APP_KEY="base64:$(php -r '\''echo base64_encode(random_bytes(32));'\'')"; \
      echo "ℹ️  APP_KEY gerada automaticamente."; \
    fi; \
    printf "APP_NAME=%s\nAPP_ENV=%s\nAPP_DEBUG=%s\nAPP_KEY=%s\nAPP_URL=%s\n\nDB_CONNECTION=%s\nDB_HOST=%s\nDB_PORT=%s\nDB_DATABASE=%s\nDB_USERNAME=%s\nDB_PASSWORD=%s\n\nSESSION_DRIVER=%s\nCACHE_DRIVER=%s\nQUEUE_CONNECTION=%s\n\nAPP_TRUSTED_PROXIES=%s\nAPP_TRUSTED_HOSTS=%s\n\nPORT=%s\n" \
      "$APP_NAME" "$APP_ENV" "$APP_DEBUG" "$APP_KEY" "$APP_URL" \
      "${DB_CONNECTION:-}" "${DB_HOST:-}" "${DB_PORT:-}" "${DB_DATABASE:-}" "${DB_USERNAME:-}" "${DB_PASSWORD:-}" \
      "${SESSION_DRIVER:-file}" "${CACHE_DRIVER:-file}" "${QUEUE_CONNECTION:-sync}" \
      "${APP_TRUSTED_PROXIES:-*}" "${APP_TRUSTED_HOSTS:-pibigdata-production-3c8e.up.railway.app}" \
      "${PORT:-8080}" > .env; \
  fi ; \
  # 2) Pré-checks de variáveis
  needvars="DB_CONNECTION DB_HOST DB_PORT DB_DATABASE DB_USERNAME DB_PASSWORD"; \
  for v in $needvars; do \
    if [ -z "${!v:-}" ]; then \
      echo "❌ Variável $v ausente. Configure nas Variables do Railway."; \
      exit 1; \
    fi; \
  done; \
  if [ "${DB_CONNECTION}" != "pgsql" ]; then \
    echo "❌ DB_CONNECTION deve ser pgsql. Valor atual: ${DB_CONNECTION}"; \
    exit 1; \
  fi; \
  # 3) Limpa cache antigo e recompila
  rm -f bootstrap/cache/config.php bootstrap/cache/*.php || true; \
  php artisan config:clear || true; \
  php artisan cache:clear || true; \
  php artisan route:clear || true; \
  php artisan view:clear || true; \
  php artisan config:cache || true; \
  echo "✅ Cache recompilado com sucesso!" ; \
  # 4) Sobe servidor
  php artisan serve --host=0.0.0.0 --port=${PORT:-8080} \