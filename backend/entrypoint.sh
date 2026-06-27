#!/bin/bash
set -e

echo "Aguardando postgres..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "Postgres disponível!"

echo "Rodando migrations..."
uv run alembic upgrade head

echo "Iniciando API..."
exec uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
