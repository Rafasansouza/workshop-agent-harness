"""Entrypoint FastAPI — aplicação principal."""

from __future__ import annotations

from fastapi import FastAPI

from backend.app.routers.chat import router as chat_router

app = FastAPI(
    title="Agente Analítico de Vendas",
    description="Assistente agêntico para relatórios de melhoria de vendas.",
    version="0.1.0",
)


app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check simples."""
    return {"status": "ok"}
