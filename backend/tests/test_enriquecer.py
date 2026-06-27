"""Testes do nó enriquecer."""

from __future__ import annotations

import pytest

from backend.agent.nodes.enriquecer import enriquecer
from backend.agent.state import AgentState, KpiFraco
from backend.agent.tools.search import SearchHit, SearchResult


def mock_search_fn(
    colecao: str,
    query: str,
    filtros: dict | None = None,
    top_k: int = 5,
    **kwargs,
) -> SearchResult:
    """Mock da função search."""
    hits = []

    if colecao == "diagnostico":
        hits = [
            SearchHit(
                score=0.8,
                fonte="minio://corpus/diagnostico/doc1.md",
                documento="Atrasos na entrega causaram queda na recompra.",
                payload={"regiao": "Sul", "kpi_alvo": "faturamento"},
            ),
        ]
    elif colecao == "prescricao":
        hits = [
            SearchHit(
                score=0.7,
                fonte="minio://corpus/prescricao/presc1.md",
                documento="Oferecer frete grátis para clientes recorrentes.",
                payload={"kpi_alvo": "faturamento", "resultado": "Aumentou recompra em 15%"},
            ),
            SearchHit(
                score=0.5,
                fonte="minio://corpus/prescricao/presc2.md",
                documento="Programa de fidelidade com pontos.",
                payload={"kpi_alvo": "faturamento"},
            ),
        ]

    return SearchResult(
        colecao=colecao,
        query=query,
        hits=hits,
        filtros_aplicados=filtros or {},
    )


def mock_search_fn_sem_resultados(
    colecao: str,
    query: str,
    filtros: dict | None = None,
    top_k: int = 5,
    **kwargs,
) -> SearchResult:
    """Mock da função search sem resultados."""
    return SearchResult(
        colecao=colecao,
        query=query,
        hits=[],
        filtros_aplicados=filtros or {},
    )


def mock_search_fn_score_baixo(
    colecao: str,
    query: str,
    filtros: dict | None = None,
    top_k: int = 5,
    **kwargs,
) -> SearchResult:
    """Mock com scores abaixo do threshold."""
    return SearchResult(
        colecao=colecao,
        query=query,
        hits=[
            SearchHit(
                score=0.1,  # Abaixo do threshold
                fonte="minio://corpus/doc.md",
                documento="Documento irrelevante",
                payload={},
            ),
        ],
        filtros_aplicados=filtros or {},
    )


class TestEnriquecer:
    """Testes do nó enriquecer."""

    @pytest.mark.asyncio
    async def test_busca_diagnosticos_e_prescricoes(self) -> None:
        """Enriquecer busca diagnósticos e prescrições."""
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

        result = await enriquecer(state, search_fn=mock_search_fn)

        assert len(result["diagnosticos"]) >= 1
        assert len(result["prescricoes"]) >= 1

    @pytest.mark.asyncio
    async def test_diagnostico_tem_fonte(self) -> None:
        """Cada diagnóstico tem fonte rastreável."""
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

        result = await enriquecer(state, search_fn=mock_search_fn)

        for diag in result["diagnosticos"]:
            assert diag["fonte"], "Diagnóstico deve ter fonte"
            assert diag["fonte"].startswith("minio://")

    @pytest.mark.asyncio
    async def test_prescricao_tem_fonte_obrigatoria(self) -> None:
        """Toda prescrição DEVE ter fonte (regra de ouro do grounding)."""
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

        result = await enriquecer(state, search_fn=mock_search_fn)

        for presc in result["prescricoes"]:
            assert presc["fonte"], "Prescrição DEVE ter fonte (grounding)"

    @pytest.mark.asyncio
    async def test_sem_kpis_fracos_retorna_vazio(self) -> None:
        """Sem KPIs fracos, retorna listas vazias."""
        state = AgentState(
            pergunta="teste",
            thread_id="test-123",
            periodo_alvo={"ano": 2025, "mes": 7},
            kpis_fracos=[],
        )

        result = await enriquecer(state, search_fn=mock_search_fn)

        assert result["diagnosticos"] == []
        assert result["prescricoes"] == []

    @pytest.mark.asyncio
    async def test_filtra_resultados_baixo_score(self) -> None:
        """Resultados com score baixo são filtrados."""
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

        result = await enriquecer(state, search_fn=mock_search_fn_score_baixo)

        # Com score 0.1 (abaixo do threshold), não deve incluir
        assert result["diagnosticos"] == []
        assert result["prescricoes"] == []

    @pytest.mark.asyncio
    async def test_registra_fontes_consultadas(self) -> None:
        """Registra fontes consultadas para observabilidade."""
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
            fontes_consultadas=[],
        )

        result = await enriquecer(state, search_fn=mock_search_fn)

        assert len(result["fontes_consultadas"]) >= 2  # diagnostico + prescricao
        coleções = [f["colecao"] for f in result["fontes_consultadas"]]
        assert "diagnostico" in coleções
        assert "prescricao" in coleções

    @pytest.mark.asyncio
    async def test_preserva_state_anterior(self) -> None:
        """Preserva campos do state anterior."""
        state = AgentState(
            pergunta="minha pergunta",
            thread_id="test-123",
            periodo_alvo={"ano": 2025, "mes": 7},
            premissas=["premissa 1"],
            kpis_fracos=[],
            analise_quantitativa=[],
            sql_executados=[{"sql": "SELECT 1", "resultado": "ok"}],
        )

        result = await enriquecer(state, search_fn=mock_search_fn)

        assert result["pergunta"] == "minha pergunta"
        assert result["premissas"] == ["premissa 1"]
        assert len(result["sql_executados"]) == 1
