"""Router do chat — endpoint SSE."""

from __future__ import annotations

from pydantic import BaseModel
from starlette.responses import StreamingResponse

from fastapi import APIRouter

from backend.app.services.chat import executar_grafo, formatar_sse

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Request do chat."""

    mensagem: str
    thread_id: str | None = None


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Endpoint de chat com streaming SSE.

    Recebe uma mensagem e retorna eventos SSE conforme o grafo executa:
    - event: status (qual nó está executando)
    - event: chunk (pedaços do relatório)
    - event: done (fim com metadados)
    - event: error (se falhar)
    """

    async def generate():
        async for event in executar_grafo(request.mensagem, request.thread_id):
            yield formatar_sse(event)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Desabilita buffering no nginx
        },
    )
