"""Testes do nó planejar."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agent.nodes.planejar import _resolver_periodo_alvo, planejar
from backend.agent.state import AgentState


class TestResolverPeriodoAlvo:
    """Testes da resolução de período-alvo."""

    def test_proximo_mes_normal(self) -> None:
        """Em junho, período-alvo é julho."""
        with patch("backend.agent.nodes.planejar.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            periodo, premissas = _resolver_periodo_alvo("como melhorar vendas?")

            assert periodo == {"ano": 2025, "mes": 7}
            assert any("07/2025" in p for p in premissas)

    def test_virada_de_ano(self) -> None:
        """Em dezembro, período-alvo é janeiro do próximo ano."""
        with patch("backend.agent.nodes.planejar.date") as mock_date:
            mock_date.today.return_value = date(2025, 12, 15)
            periodo, premissas = _resolver_periodo_alvo("como melhorar vendas?")

            assert periodo == {"ano": 2026, "mes": 1}
            assert any("01/2026" in p for p in premissas)

    def test_premissas_incluem_escopo(self) -> None:
        """Premissas incluem informação sobre escopo."""
        with patch("backend.agent.nodes.planejar.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            _, premissas = _resolver_periodo_alvo("como melhorar vendas?")

            assert len(premissas) >= 2
            assert any("escopo" in p.lower() for p in premissas)


class TestPlanejar:
    """Testes do nó planejar."""

    @pytest.mark.asyncio
    async def test_planejar_sem_conexao(self) -> None:
        """Planejar funciona sem conexão (para testes)."""
        state = AgentState(pergunta="como melhorar vendas?", thread_id="test-123")

        with patch("backend.agent.nodes.planejar.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            result = await planejar(state)

        assert result["pergunta"] == "como melhorar vendas?"
        assert result["periodo_alvo"] == {"ano": 2025, "mes": 7}
        assert len(result["premissas"]) >= 1
        assert result["kpis_fracos"] == []

    @pytest.mark.asyncio
    async def test_planejar_com_conexao_mock(self) -> None:
        """Planejar busca KPIs fracos quando tem conexão."""
        state = AgentState(pergunta="como melhorar vendas?", thread_id="test-123")

        # Mock da conexão
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {
                "kpi": "faturamento",
                "dimensao": "Sul",
                "valor_atual": 80000.0,
                "valor_meta": 100000.0,
                "gap_percentual": 20.0,
            }
        ]
        mock_conn.execute.return_value = mock_result

        with patch("backend.agent.nodes.planejar.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            result = await planejar(state, conn=mock_conn)

        assert len(result["kpis_fracos"]) == 1
        assert result["kpis_fracos"][0]["kpi"] == "faturamento"
        assert result["kpis_fracos"][0]["dimensao"] == "Sul"
        assert result["kpis_fracos"][0]["gap_percentual"] == 20.0

    @pytest.mark.asyncio
    async def test_planejar_registra_sql_executado(self) -> None:
        """Planejar registra SQL executado para observabilidade."""
        state = AgentState(pergunta="teste", thread_id="test-123")

        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_conn.execute.return_value = mock_result

        with patch("backend.agent.nodes.planejar.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            result = await planejar(state, conn=mock_conn)

        assert len(result["sql_executados"]) == 1
        assert "sql" in result["sql_executados"][0]

    @pytest.mark.asyncio
    async def test_planejar_preserva_thread_id(self) -> None:
        """Planejar preserva thread_id no state."""
        state = AgentState(pergunta="teste", thread_id="meu-thread-id")

        with patch("backend.agent.nodes.planejar.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            result = await planejar(state)

        assert result["thread_id"] == "meu-thread-id"
