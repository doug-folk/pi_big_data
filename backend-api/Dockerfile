# ===========================
# Etapa 1: Composer dependencies
# ===========================
FROM composer:2 AS vendor

WORKDIR /app
# Copia só o necessário p/ cache eficiente
COPY backend-api/composer.json backend-api/composer.lock ./
RUN composer install --no-dev --no-scripts --no-interaction --no-progress --prefer-dist


# ===========================
# Etapa 2: PHP + Laravel
# ===========================
FROM php:8.2-cli

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm
# Opcional (melhor logs de hora local): TZ=America/Fortaleza
ENV TZ=UTC

# Dependências do sistema + extensões PHP
RUN apt-get update && apt-get install -y \
    git unzip zip libpq-dev libzip-dev libssl-dev libpng-dev libonig-dev tzdata \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && rm -rf /var/lib/apt/lists/*

# App
WORKDIR /var/www/html
COPY --from=vendor /app/vendor /var/www/html/vendor
COPY backend-api /var/www/html

# 👇 Garante que o .env entre na imagem (evita fallback p/ sqlite)
#    Se o .env estiver gitignored, essa linha garante a cópia.
COPY backend-api/.env /var/www/html/.env

# Diretórios e permissões (evita 500 por permissão)
RUN mkdir -p storage/framework/{cache,sessions,views,testing} \
    && chmod -R 777 storage bootstrap/cache

# 🚫 Impede o Laravel de parsear o DATABASE_URL injetado pelo provedor
#    (esse URL costuma ter querystring que confunde o parser)
ENV DATABASE_URL=""

# Porta HTTP interna
EXPOSE 8080

# ===========================
# Inicialização com pré-checagens
# ===========================
# - Remove config cache antigo (que poderia apontar p/ sqlite)
# - Valida presence de variáveis críticas
# - Limpa caches e recompila config
# - Sobe o servidor na PORT do Railway (fallback 8080)
CMD sh -eu -c '\
  echo "🚀 Iniciando aplicação Laravel..." ; \
  if [ ! -f ".env" ]; then \
    echo "❌ .env não encontrado em /var/www/html/.env"; \
    ls -la ; \
    exit 1; \
  fi ; \
  # Pré-checks de DB para evitar boot com sqlite
  needvars="DB_CONNECTION DB_HOST DB_PORT DB_DATABASE DB_USERNAME DB_PASSWORD"; \
  for v in $needvars; do \
    if [ -z "${!v:-}" ]; then \
      echo "❌ Variável $v ausente. Defina nas Variables do Railway."; \
      exit 1; \
    fi; \
  done ; \
  if [ "${DB_CONNECTION}" != "pgsql" ]; then \
    echo "❌ DB_CONNECTION deve ser pgsql. Valor atual: ${DB_CONNECTION}"; \
    exit 1; \
  fi ; \
  # Zera lixo de cache e força recompilar com env atual
  rm -f bootstrap/cache/config.php bootstrap/cache/*.php || true; \
  php artisan config:clear || true; \
  php artisan cache:clear || true; \
  php artisan route:clear || true; \
  php artisan view:clear || true; \
  php artisan config:cache || true; \
  echo "✅ Cache recompilado com sucesso!" ; \
  # Opcional: rodar migrations automaticamente se quiser (descomentando a linha abaixo)
  # php artisan migrate --force || true ; \
  php artisan serve --host=0.0.0.0 --port=${PORT:-8080} \
'