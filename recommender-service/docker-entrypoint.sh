#!/bin/sh
set -e

if [ -n "$DB_HOST" ]; then
    DB_PORT=${DB_PORT:-5432}
    DB_USER=${DB_USER:-${DB_USERNAME:-postgres}}
    DB_PASSWORD=${DB_PASSWORD:-postgres}
    DB_NAME=${DB_DATABASE:-gamefinder}

    export PGPASSWORD="$DB_PASSWORD"

    echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
        sleep 2
    done

    if [ "${WAIT_FOR_GAMES_TABLE:-true}" = "true" ]; then
        echo "Waiting for games table to be ready..."
        until psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM games LIMIT 1;" >/dev/null 2>&1; do
            sleep 3
        done
    fi

    unset PGPASSWORD
fi

exec "$@"
