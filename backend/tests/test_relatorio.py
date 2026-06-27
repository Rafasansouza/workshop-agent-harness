"""Testes do nó relatorio."""

from __future__ import annotations

import pytest

from backend.agent.nodes.relatorio import gerar_relatorio_simples, relatorio
from backend.agent.state import (
    AgentState,
    AnaliseQuantitativa,
    Diagnostico,
    KpiFraco,
    Prescricao,
)


@pytest.fixture
def state_completo() -> AgentState:
    """State completo para testes."""
    return AgentState(
        pergunta="como melhorar vendas?",
        thread_id="test-123",
        periodo_alvo={"ano": 2025, "mes": 7},
        premissas=[
            "Período-alvo assumido: 07/2025 (próximo mês)",
            "Escopo: todas as regiões",
        ],
        kpis_fracos=[
            KpiFraco(
                kpi="faturamento",
                dimensao="Sul",
                valor_atual=80000,
                valor_meta=100000,
                gap_percentual=20.0,
            )
        ],
        analise_quantitativa=[
            AnaliseQuantitativa(
                kpi="faturamento",
                tendencia_recente="Tendência de queda (-15% nos últimos 3 meses)",
                historico_sazonal="Queda significativa vs histórico (-20%)",
                e_queda_real=True,
            )
        ],
        diagnosticos=[
            Diagnostico(
                kpi="faturamento",
                explicacao="Atrasos na entrega causaram insatisfação.",
                fonte="minio://corpus/diagnostico/doc1.md",
            )
        ],
        prescricoes=[
            Prescricao(
                kpi="faturamento",
                recomendacao="Oferecer frete grátis para clientes recorrentes.",
                fonte="minio://corpus/prescricao/presc1.md",
                resultado_anterior="Aumentou recompra em 15%",
            )
        ],
    )


class TestGerarRelatorioSimples:
    """Testes da geração de relatório simples."""

    def test_inclui_premissas(self, state_completo: AgentState) -> None:
        """Relatório inclui premissas no topo."""
        texto = gerar_relatorio_simples(state_completo)
        assert "Premissas" in texto
        assert "07/2025" in texto

    def test_inclui_kpis_fracos(self, state_completo: AgentState) -> None:
        """Relatório inclui KPIs fracos."""
        texto = gerar_relatorio_simples(state_completo)
        assert "faturamento" in texto.lower()
        assert "Sul" in texto
        assert "20" in texto  # gap percentual

    def test_inclui_analise_quantitativa(self, state_completo: AgentState) -> None:
        """Relatório inclui análise quantitativa."""
        texto = gerar_relatorio_simples(state_completo)
        assert "Tendência" in texto
        assert "queda" in texto.lower()

    def test_inclui_diagnostico(self, state_completo: AgentState) -> None:
        """Relatório inclui diagnóstico."""
        texto = gerar_relatorio_simples(state_completo)
        assert "Atrasos" in texto
        assert "minio://corpus/diagnostico" in texto

    def test_prescricao_cita_fonte(self, state_completo: AgentState) -> None:
        """Cada prescrição cita a fonte (regra de ouro)."""
        texto = gerar_relatorio_simples(state_completo)
        assert "frete grátis" in texto.lower()
        assert "minio://corpus/prescricao" in texto

    def test_inclui_resultado_anterior(self, state_completo: AgentState) -> None:
        """Relatório inclui resultado anterior quando disponível."""
        texto = gerar_relatorio_simples(state_completo)
        assert "15%" in texto

    def test_formato_markdown(self, state_completo: AgentState) -> None:
        """Relatório é formatado em markdown."""
        texto = gerar_relatorio_simples(state_completo)
        assert texto.startswith("#")
        assert "##" in texto


class TestRelatorio:
    """Testes do nó relatorio."""

    @pytest.mark.asyncio
    async def test_gera_relatorio_no_state(self, state_completo: AgentState) -> None:
        """Relatorio adiciona texto ao state."""
        result = await relatorio(state_completo)
        assert "relatorio" in result
        assert len(result["relatorio"]) > 100

    @pytest.mark.asyncio
    async def test_preserva_state_anterior(self, state_completo: AgentState) -> None:
        """Preserva campos do state anterior."""
        result = await relatorio(state_completo)
        assert result["pergunta"] == "como melhorar vendas?"
        assert len(result["premissas"]) == 2
        assert len(result["kpis_fracos"]) == 1

    @pytest.mark.asyncio
    async def test_sem_kpis_relatorio_indica(self) -> None:
        """Sem KPIs fracos, relatório indica."""
        state = AgentState(
            pergunta="teste",
            thread_id="test-123",
            periodo_alvo={"ano": 2025, "mes": 7},
            kpis_fracos=[],
        )
        result = await relatorio(state)
        assert "Nenhum KPI" in result["relatorio"]

    @pytest.mark.asyncio
    async def test_sem_prescricoes_indica(self) -> None:
        """Sem prescrições, relatório indica."""
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
            prescricoes=[],
        )
        result = await relatorio(state)
        assert "Nenhuma recomendação" in result["relatorio"]

    @pytest.mark.asyncio
    async def test_usa_llm_quando_solicitado(self) -> None:
        """Usa LLM quando usar_llm=True."""
        state = AgentState(
            pergunta="teste",
            thread_id="test-123",
            periodo_alvo={"ano": 2025, "mes": 7},
            premissas=["premissa"],
            kpis_fracos=[],
        )

        def mock_llm(prompt: str) -> str:
            return "# Relatório gerado pelo LLM\n\nConteúdo mockado."

        result = await relatorio(state, llm_fn=mock_llm, usar_llm=True)
        assert "LLM" in result["relatorio"]
