"""Testes do nó perna_quantitativa."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agent.nodes.perna_quantitativa import (
    _analisar_sazonalidade,
    _analisar_tendencia,
    perna_quantitativa,
)
from backend.agent.state import AgentState, KpiFraco


class TestAnalisarTendencia:
    """Testes da análise de tendência."""

    def test_tendencia_alta(self) -> None:
        """Detecta tendência de alta."""
        valores = [100.0, 105.0, 110.0, 130.0, 140.0, 150.0]
        resultado = _analisar_tendencia(valores)
        assert "alta" in resultado.lower()

    def test_tendencia_queda(self) -> None:
        """Detecta tendência de queda."""
        valores = [150.0, 140.0, 130.0, 110.0, 105.0, 100.0]
        resultado = _analisar_tendencia(valores)
        assert "queda" in resultado.lower()

    def test_tendencia_estavel(self) -> None:
        """Detecta tendência estável."""
        valores = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0]
        resultado = _analisar_tendencia(valores)
        assert "estável" in resultado.lower()

    def test_dados_insuficientes(self) -> None:
        """Retorna mensagem para dados insuficientes."""
        valores = [100.0]
        resultado = _analisar_tendencia(valores)
        assert "insuficientes" in resultado.lower()


class TestAnalisarSazonalidade:
    """Testes da análise de sazonalidade."""

    def test_queda_real(self) -> None:
        """Detecta queda real vs histórico."""
        valores = {2022: 100000.0, 2023: 95000.0, 2024: 70000.0}
        resultado, e_queda_real = _analisar_sazonalidade(valores, 2025, 6)
        assert e_queda_real is True
        assert "queda" in resultado.lower() or "abaixo" in resultado.lower()

    def test_variacao_sazonal(self) -> None:
        """Detecta variação sazonal esperada."""
        # Janeiro é mês sazonal fraco
        valores = {2022: 80000.0, 2023: 82000.0, 2024: 79000.0}
        resultado, e_queda_real = _analisar_sazonalidade(valores, 2025, 1)
        assert e_queda_real is False
        assert "sazonal" in resultado.lower() or "padrão" in resultado.lower()

    def test_historico_insuficiente(self) -> None:
        """Retorna mensagem para histórico insuficiente."""
        valores = {2024: 100000.0}
        resultado, e_queda_real = _analisar_sazonalidade(valores, 2025, 6)
        assert "insuficiente" in resultado.lower()


class TestPernaQuantitativa:
    """Testes do nó perna_quantitativa."""

    @pytest.mark.asyncio
    async def test_sem_conexao_retorna_vazio(self) -> None:
        """Sem conexão, retorna lista vazia de análises."""
        state = AgentState(
            pergunta="teste",
            thread_id="test-123",
            periodo_alvo={"ano": 2025, "mes": 7},
            kpis_fracos=[
                KpiFraco(
                    kpi="faturamento",
                    dimensao="Sul",
                    valor_atual=80000,
                    valor_meta=100000,
                    gap_percentual=20.0,
                )
            ],
        )

        result = await perna_quantitativa(state)
        assert result["analise_quantitativa"] == []

    @pytest.mark.asyncio
    async def test_com_conexao_analisa_kpis(self) -> None:
        """Com conexão, analisa cada KPI fraco."""
        state = AgentState(
            pergunta="teste",
            thread_id="test-123",
            periodo_alvo={"ano": 2025, "mes": 7},
            kpis_fracos=[
                KpiFraco(
                    kpi="faturamento",
                    dimensao="Sul",
                    valor_atual=80000,
                    valor_meta=100000,
                    gap_percentual=20.0,
                )
            ],
            sql_executados=[],
        )

        # Mock da conexão
        mock_conn = AsyncMock()

        # Mock para tendência
        mock_result_tendencia = MagicMock()
        mock_result_tendencia.mappings.return_value.all.return_value = [
            {"ano": 2025, "mes": 1, "faturamento": 90000},
            {"ano": 2025, "mes": 2, "faturamento": 85000},
            {"ano": 2025, "mes": 3, "faturamento": 80000},
        ]

        # Mock para sazonalidade
        mock_result_sazonal = MagicMock()
        mock_result_sazonal.mappings.return_value.all.return_value = [
            {"ano": 2023, "faturamento": 100000},
            {"ano": 2024, "faturamento": 95000},
        ]

        mock_conn.execute.side_effect = [mock_result_tendencia, mock_result_sazonal]

        result = await perna_quantitativa(state, conn=mock_conn)

        assert len(result["analise_quantitativa"]) == 1
        assert result["analise_quantitativa"][0]["kpi"] == "faturamento"
        assert "tendencia_recente" in result["analise_quantitativa"][0]
        assert "historico_sazonal" in result["analise_quantitativa"][0]
        assert "e_queda_real" in result["analise_quantitativa"][0]

    @pytest.mark.asyncio
    async def test_preserva_state_anterior(self) -> None:
        """Preserva campos do state anterior."""
        state = AgentState(
            pergunta="minha pergunta",
            thread_id="test-123",
            periodo_alvo={"ano": 2025, "mes": 7},
            premissas=["premissa 1"],
            kpis_fracos=[],
            sql_executados=[{"sql": "SELECT 1", "resultado": "ok"}],
        )

        result = await perna_quantitativa(state)

        assert result["pergunta"] == "minha pergunta"
        assert result["premissas"] == ["premissa 1"]
        assert len(result["sql_executados"]) == 1
