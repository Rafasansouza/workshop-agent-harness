"""Testes do endpoint /chat SSE."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.chat import formatar_sse


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste síncrono."""
    return TestClient(app)


class TestFormatarSse:
    """Testes da função formatar_sse."""

    def test_formata_evento_status(self) -> None:
        """Formata evento de status corretamente."""
        evento = {"event": "status", "data": {"node": "planejar", "message": "Identificando KPIs..."}}
        resultado = formatar_sse(evento)
        assert resultado == 'event: status\ndata: {"node": "planejar", "message": "Identificando KPIs..."}\n\n'

    def test_formata_evento_chunk(self) -> None:
        """Formata evento de chunk corretamente."""
        evento = {"event": "chunk", "data": {"content": "Texto do relatório"}}
        resultado = formatar_sse(evento)
        assert resultado == 'event: chunk\ndata: {"content": "Texto do relatório"}\n\n'

    def test_formata_evento_done(self) -> None:
        """Formata evento done corretamente."""
        evento = {"event": "done", "data": {"thread_id": "abc-123"}}
        resultado = formatar_sse(evento)
        assert resultado == 'event: done\ndata: {"thread_id": "abc-123"}\n\n'

    def test_formata_evento_error(self) -> None:
        """Formata evento de erro corretamente."""
        evento = {"event": "error", "data": {"message": "Algo deu errado"}}
        resultado = formatar_sse(evento)
        assert resultado == 'event: error\ndata: {"message": "Algo deu errado"}\n\n'

    def test_evento_sem_tipo_usa_message(self) -> None:
        """Evento sem tipo usa 'message' como default."""
        evento = {"data": {"info": "teste"}}
        resultado = formatar_sse(evento)
        assert resultado.startswith("event: message\n")

    def test_evento_com_caracteres_especiais(self) -> None:
        """Formata corretamente caracteres especiais em português."""
        evento = {"event": "chunk", "data": {"content": "Relatório com acentuação: é, ã, ç"}}
        resultado = formatar_sse(evento)
        assert "Relatório" in resultado
        assert "acentuação" in resultado


class TestChatEndpoint:
    """Testes do endpoint POST /chat."""

    def test_chat_retorna_sse_content_type(self, client: TestClient) -> None:
        """Endpoint retorna content-type de SSE."""

        async def mock_executar_grafo(
            mensagem: str, thread_id: str | None = None
        ) -> AsyncGenerator[dict[str, Any], None]:
            yield {"event": "done", "data": {"thread_id": "test-123"}}

        with patch(
            "backend.app.routers.chat.executar_grafo", new=mock_executar_grafo
        ):
            with client.stream("POST", "/chat", json={"mensagem": "teste"}) as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers["content-type"]

    def test_chat_emite_eventos_sse(self, client: TestClient) -> None:
        """Endpoint emite eventos SSE formatados corretamente."""

        async def mock_executar_grafo(
            mensagem: str, thread_id: str | None = None
        ) -> AsyncGenerator[dict[str, Any], None]:
            yield {"event": "status", "data": {"node": "planejar", "message": "Planejando..."}}
            yield {"event": "chunk", "data": {"content": "Texto"}}
            yield {"event": "done", "data": {"thread_id": thread_id or "gen-123"}}

        with patch(
            "backend.app.routers.chat.executar_grafo", new=mock_executar_grafo
        ):
            with client.stream("POST", "/chat", json={"mensagem": "teste"}) as response:
                content = response.read().decode("utf-8")

        assert "event: status" in content
        assert "event: chunk" in content
        assert "event: done" in content
        assert "planejar" in content
        assert "Texto" in content

    def test_chat_aceita_thread_id(self, client: TestClient) -> None:
        """Endpoint aceita thread_id para conversas de acompanhamento."""
        thread_id_recebido: list[str | None] = []

        async def mock_executar_grafo(
            mensagem: str, thread_id: str | None = None
        ) -> AsyncGenerator[dict[str, Any], None]:
            thread_id_recebido.append(thread_id)
            yield {"event": "done", "data": {"thread_id": thread_id}}

        with patch(
            "backend.app.routers.chat.executar_grafo", new=mock_executar_grafo
        ):
            with client.stream(
                "POST", "/chat", json={"mensagem": "teste", "thread_id": "meu-thread-123"}
            ) as response:
                response.read()

        assert thread_id_recebido[0] == "meu-thread-123"

    def test_chat_mensagem_obrigatoria(self, client: TestClient) -> None:
        """Endpoint requer campo mensagem."""
        response = client.post("/chat", json={})
        assert response.status_code == 422  # Validation error

    def test_chat_headers_sse(self, client: TestClient) -> None:
        """Endpoint inclui headers corretos para SSE."""

        async def mock_executar_grafo(
            mensagem: str, thread_id: str | None = None
        ) -> AsyncGenerator[dict[str, Any], None]:
            yield {"event": "done", "data": {}}

        with patch(
            "backend.app.routers.chat.executar_grafo", new=mock_executar_grafo
        ):
            with client.stream("POST", "/chat", json={"mensagem": "teste"}) as response:
                assert response.headers.get("cache-control") == "no-cache"
                assert response.headers.get("connection") == "keep-alive"
                response.read()

    def test_chat_propaga_erro_como_evento(self, client: TestClient) -> None:
        """Erros durante execução são emitidos como evento de erro."""

        async def mock_executar_grafo(
            mensagem: str, thread_id: str | None = None
        ) -> AsyncGenerator[dict[str, Any], None]:
            yield {"event": "error", "data": {"message": "Erro simulado"}}

        with patch(
            "backend.app.routers.chat.executar_grafo", new=mock_executar_grafo
        ):
            with client.stream("POST", "/chat", json={"mensagem": "teste"}) as response:
                content = response.read().decode("utf-8")

        assert "event: error" in content
        assert "Erro simulado" in content
