#!/bin/sh
set -e

SERVICE_TYPE=${SERVICE_TYPE:-backend}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-${DB_USERNAME:-postgres}}
DB_PASSWORD=${DB_PASSWORD:-postgres}
DB_NAME=${DB_DATABASE:-gamefinder}

wait_for_postgres() {
    echo "[$SERVICE_TYPE] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
        sleep 2
    done
}

wait_for_games_table() {
    echo "[$SERVICE_TYPE] Waiting for games table to be ready..."
    until psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM games LIMIT 1;" >/dev/null 2>&1; do
        sleep 3
    done
}

if [ -n "$DB_HOST" ]; then
    export PGPASSWORD="$DB_PASSWORD"
    wait_for_postgres
fi

case "$SERVICE_TYPE" in
    backend)
        php artisan package:discover --ansi || true
        php artisan migrate --force || true
        if [ "${WAIT_FOR_GAMES_TABLE:-true}" = "true" ] && [ -n "$DB_HOST" ]; then
            wait_for_games_table
        fi
        ;;
    recommender|etl)
        if [ "${WAIT_FOR_GAMES_TABLE:-true}" = "true" ] && [ -n "$DB_HOST" ]; then
            wait_for_games_table
        fi
        ;;
    *)
        echo "[$SERVICE_TYPE] Unknown SERVICE_TYPE '${SERVICE_TYPE}', skipping service-specific steps."
        ;;
esac

if [ -n "$DB_HOST" ]; then
    unset PGPASSWORD
fi

exec "$@"
