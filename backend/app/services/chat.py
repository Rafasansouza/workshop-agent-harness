"""Service de chat — orquestra o grafo do agente."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from backend.agent.nodes import enriquecer, perna_quantitativa, planejar, relatorio
from backend.agent.state import AgentState

logger = logging.getLogger(__name__)


async def executar_grafo(
    mensagem: str,
    thread_id: str | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Executa o grafo do agente com streaming de eventos.

    Args:
        mensagem: Pergunta do usuário
        thread_id: ID do thread para conversas de acompanhamento

    Yields:
        Eventos SSE com status, chunks e resultado final
    """
    thread_id = thread_id or str(uuid.uuid4())

    # Estado inicial
    state: AgentState = {
        "pergunta": mensagem,
        "thread_id": thread_id,
    }

    try:
        # 1. Planejar
        yield {"event": "status", "data": {"node": "planejar", "message": "Identificando KPIs..."}}
        await asyncio.sleep(0.1)  # Permite flush do evento
        state = await planejar(state)

        # 2. Perna quantitativa
        yield {
            "event": "status",
            "data": {"node": "perna_quantitativa", "message": "Analisando tendências..."},
        }
        await asyncio.sleep(0.1)
        state = await perna_quantitativa(state)

        # 3. Enriquecer
        yield {"event": "status", "data": {"node": "enriquecer", "message": "Buscando contexto..."}}
        await asyncio.sleep(0.1)
        state = await enriquecer(state)

        # 4. Relatório
        yield {"event": "status", "data": {"node": "relatorio", "message": "Gerando relatório..."}}
        await asyncio.sleep(0.1)
        state = await relatorio(state)

        # Streaming do relatório em chunks
        texto = state.get("relatorio", "")
        chunk_size = 100
        for i in range(0, len(texto), chunk_size):
            chunk = texto[i : i + chunk_size]
            yield {"event": "chunk", "data": {"content": chunk}}
            await asyncio.sleep(0.02)  # Simula streaming

        # Evento final
        yield {
            "event": "done",
            "data": {
                "thread_id": thread_id,
                "premissas": state.get("premissas", []),
                "kpis_fracos": state.get("kpis_fracos", []),
                "sql_executados": state.get("sql_executados", []),
                "fontes_consultadas": state.get("fontes_consultadas", []),
            },
        }

    except Exception as e:
        logger.exception(f"Erro ao executar grafo: {e}")
        yield {"event": "error", "data": {"message": str(e)}}


def formatar_sse(event: dict[str, Any]) -> str:
    """Formata evento para SSE."""
    event_type = event.get("event", "message")
    data = json.dumps(event.get("data", {}), ensure_ascii=False)
    return f"event: {event_type}\ndata: {data}\n\n"
