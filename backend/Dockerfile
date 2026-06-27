# Backend FastAPI — Python 3.13 + uv
FROM python:3.13-slim

WORKDIR /app

# Instala uv e netcat (para health check do postgres)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copia arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala dependências (sem o projeto em si ainda)
RUN uv sync --frozen --no-install-project

# Copia o código do backend e alembic
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Instala o projeto
RUN uv sync --frozen

# Copia e configura entrypoint
COPY backend/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Porta da API
EXPOSE 8000

# Entrypoint que roda migrations antes de iniciar
ENTRYPOINT ["./entrypoint.sh"]
