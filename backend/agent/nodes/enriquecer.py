"""Nó enriquecer — busca diagnóstico e prescrição no Qdrant.

Este nó:
1. Para cada KPI fraco, busca na coleção `diagnostico` (por quê)
2. Busca na coleção `prescricao` (o que fazer)
3. Garante que toda recomendação tem fonte rastreável (grounding)
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from backend.agent.state import AgentState, Diagnostico, KpiFraco, Prescricao
from backend.agent.tools.search import SearchResult, search

logger = logging.getLogger(__name__)


def _extrair_periodo_referencia(periodo_alvo: dict[str, int]) -> str:
    """Converte periodo_alvo em periodo_referencia para filtro."""
    ano = periodo_alvo.get("ano", 2025)
    mes = periodo_alvo.get("mes", 7)
    return f"{ano}-{mes:02d}"


async def _buscar_diagnosticos(
    kpis_fracos: list[KpiFraco],
    periodo_referencia: str,
    search_fn: Callable[..., SearchResult] | None = None,
) -> tuple[list[Diagnostico], list[dict[str, Any]]]:
    """Busca diagnósticos para os KPIs fracos."""
    diagnosticos: list[Diagnostico] = []
    fontes: list[dict[str, Any]] = []

    search_func = search_fn or search

    for kpi in kpis_fracos:
        filtros = {
            "kpi_alvo": kpi["kpi"],
        }
        # Adiciona dimensão se disponível
        if kpi["dimensao"]:
            filtros["regiao"] = kpi["dimensao"]

        try:
            result = search_func(
                "diagnostico",
                f"causa da queda de {kpi['kpi']} na região {kpi['dimensao']}",
                filtros=filtros,
                top_k=3,
            )

            fontes.append(
                {
                    "colecao": "diagnostico",
                    "query": result.query,
                    "hits": len(result.hits),
                }
            )

            for hit in result.hits:
                if hit.score > 0.3:  # Threshold mínimo de relevância
                    diagnosticos.append(
                        Diagnostico(
                            kpi=kpi["kpi"],
                            explicacao=hit.documento,
                            fonte=hit.fonte,
                        )
                    )
        except Exception as e:
            logger.warning(f"Erro ao buscar diagnóstico para {kpi['kpi']}: {e}")

    return diagnosticos, fontes


async def _buscar_prescricoes(
    kpis_fracos: list[KpiFraco],
    periodo_referencia: str,
    search_fn: Callable[..., SearchResult] | None = None,
) -> tuple[list[Prescricao], list[dict[str, Any]]]:
    """Busca prescrições para os KPIs fracos.

    REGRA DE OURO: toda recomendação deve ter fonte rastreável.
    Se não há prescrição com fonte, não inventa.
    """
    prescricoes: list[Prescricao] = []
    fontes: list[dict[str, Any]] = []

    search_func = search_fn or search

    for kpi in kpis_fracos:
        filtros = {
            "kpi_alvo": kpi["kpi"],
        }

        try:
            result = search_func(
                "prescricao",
                f"como melhorar {kpi['kpi']} recomendação ação",
                filtros=filtros,
                top_k=5,
            )

            fontes.append(
                {
                    "colecao": "prescricao",
                    "query": result.query,
                    "hits": len(result.hits),
                }
            )

            for hit in result.hits:
                # GROUNDING: só inclui se tem fonte e score relevante
                if hit.score > 0.35 and hit.fonte:
                    resultado_anterior = hit.payload.get("resultado", None)
                    prescricoes.append(
                        Prescricao(
                            kpi=kpi["kpi"],
                            recomendacao=hit.documento,
                            fonte=hit.fonte,
                            resultado_anterior=resultado_anterior,
                        )
                    )
        except Exception as e:
            logger.warning(f"Erro ao buscar prescrição para {kpi['kpi']}: {e}")

    return prescricoes, fontes


async def enriquecer(
    state: AgentState,
    *,
    search_fn: Callable[..., SearchResult] | None = None,
) -> AgentState:
    """Nó enriquecer: busca diagnóstico e prescrição.

    Args:
        state: Estado atual do grafo (deve ter kpis_fracos)
        search_fn: Função de busca (opcional, para testes)

    Returns:
        Estado atualizado com diagnosticos e prescricoes
    """
    kpis_fracos = state.get("kpis_fracos", [])
    periodo_alvo = state.get("periodo_alvo", {"ano": 2025, "mes": 7})
    periodo_referencia = _extrair_periodo_referencia(periodo_alvo)

    fontes_consultadas = list(state.get("fontes_consultadas", []))

    # Busca diagnósticos
    diagnosticos, fontes_diag = await _buscar_diagnosticos(
        kpis_fracos, periodo_referencia, search_fn
    )
    fontes_consultadas.extend(fontes_diag)

    # Busca prescrições
    prescricoes, fontes_presc = await _buscar_prescricoes(
        kpis_fracos, periodo_referencia, search_fn
    )
    fontes_consultadas.extend(fontes_presc)

    # Retorna estado atualizado
    new_state: AgentState = {
        "pergunta": state.get("pergunta", ""),
        "thread_id": state.get("thread_id", ""),
        "periodo_alvo": periodo_alvo,
        "premissas": state.get("premissas", []),
        "kpis_fracos": kpis_fracos,
        "analise_quantitativa": state.get("analise_quantitativa", []),
        "diagnosticos": diagnosticos,
        "prescricoes": prescricoes,
        "sql_executados": state.get("sql_executados", []),
        "fontes_consultadas": fontes_consultadas,
    }
    return new_state
