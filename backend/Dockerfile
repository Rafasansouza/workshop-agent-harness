# Backend FastAPI — Python 3.13 + uv
FROM python:3.13-slim

WORKDIR /app

# Instala uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copia arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala dependências (sem o projeto em si ainda)
RUN uv sync --frozen --no-install-project

# Copia o código do backend
COPY backend/ ./backend/

# Instala o projeto
RUN uv sync --frozen

# Porta da API
EXPOSE 8000

# Comando de execução
CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
