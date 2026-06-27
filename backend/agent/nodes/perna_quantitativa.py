"""Nó perna_quantitativa — analisa tendência e sazonalidade.

Este nó:
1. Para cada KPI fraco, analisa tendência recente (últimos 6 meses)
2. Compara com mesmo período em anos anteriores (sazonalidade)
3. Separa queda real de variação sazonal esperada
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.agent.state import AgentState, AnaliseQuantitativa, KpiFraco

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

# SQL para tendência dos últimos 6 meses
SQL_TENDENCIA = """
SELECT
    EXTRACT(YEAR FROM p.data_pedido)::int AS ano,
    EXTRACT(MONTH FROM p.data_pedido)::int AS mes,
    SUM(p.valor_total) AS faturamento
FROM negocio.pedidos p
JOIN negocio.regioes r ON r.id = p.regiao_id
WHERE p.status = 'pago'
  AND r.nome = :regiao
  AND p.data_pedido >= (DATE_TRUNC('month', MAKE_DATE(:ano, :mes, 1)) - INTERVAL '6 months')
  AND p.data_pedido < DATE_TRUNC('month', MAKE_DATE(:ano, :mes, 1))
GROUP BY 1, 2
ORDER BY 1, 2
"""

# SQL para mesmo mês em anos anteriores (sazonalidade)
SQL_SAZONALIDADE = """
SELECT
    EXTRACT(YEAR FROM p.data_pedido)::int AS ano,
    SUM(p.valor_total) AS faturamento
FROM negocio.pedidos p
JOIN negocio.regioes r ON r.id = p.regiao_id
WHERE p.status = 'pago'
  AND r.nome = :regiao
  AND EXTRACT(MONTH FROM p.data_pedido) = :mes
GROUP BY 1
ORDER BY 1
"""


def _analisar_tendencia(valores: list[float]) -> str:
    """Analisa tendência dos valores."""
    if len(valores) < 2:
        return "Dados insuficientes para análise de tendência"

    # Compara média da primeira metade com segunda metade
    meio = len(valores) // 2
    media_inicio = sum(valores[:meio]) / meio if meio > 0 else 0
    media_fim = sum(valores[meio:]) / (len(valores) - meio) if len(valores) > meio else 0

    if media_fim == 0:
        return "Sem dados recentes"

    variacao = ((media_fim - media_inicio) / media_inicio * 100) if media_inicio > 0 else 0

    if variacao > 10:
        return f"Tendência de alta (+{variacao:.1f}% nos últimos 3 meses)"
    elif variacao < -10:
        return f"Tendência de queda ({variacao:.1f}% nos últimos 3 meses)"
    else:
        return f"Tendência estável ({variacao:+.1f}% nos últimos 3 meses)"


def _analisar_sazonalidade(
    valores_por_ano: dict[int, float], ano_atual: int, mes: int
) -> tuple[str, bool]:
    """Analisa sazonalidade comparando com anos anteriores.

    Returns:
        Tuple de (descrição, é_queda_real)
    """
    if len(valores_por_ano) < 2:
        return "Histórico insuficiente para análise sazonal", True

    # Pega valor do ano atual/anterior
    valor_recente = valores_por_ano.get(ano_atual - 1, 0)

    # Média dos anos anteriores (exceto o mais recente)
    anos_anteriores = [v for a, v in valores_por_ano.items() if a < ano_atual - 1]
    if not anos_anteriores:
        return "Sem dados históricos suficientes", True

    media_historica = sum(anos_anteriores) / len(anos_anteriores)

    if media_historica == 0:
        return "Sem dados históricos", True

    variacao_vs_historico = (valor_recente - media_historica) / media_historica * 100

    # Se o mês historicamente é fraco (média baixa) e estamos igual, é sazonal
    meses_fracos = {1, 2, 7}  # Janeiro, fevereiro, julho tipicamente mais fracos
    e_mes_sazonal = mes in meses_fracos

    if abs(variacao_vs_historico) < 15 and e_mes_sazonal:
        return (
            f"Variação dentro do padrão sazonal para o mês {mes:02d} "
            f"({variacao_vs_historico:+.1f}% vs média histórica)",
            False,  # Não é queda real, é sazonal
        )
    elif variacao_vs_historico < -15:
        return (
            f"Queda significativa vs histórico ({variacao_vs_historico:.1f}% abaixo da média)",
            True,  # É queda real
        )
    else:
        return (
            f"Dentro ou acima do padrão histórico ({variacao_vs_historico:+.1f}%)",
            False,
        )


async def _analisar_kpi(
    conn: "AsyncConnection",
    kpi: KpiFraco,
    ano: int,
    mes: int,
) -> AnaliseQuantitativa:
    """Analisa um KPI específico."""
    from sqlalchemy import text

    # Busca tendência
    result_tendencia = await conn.execute(
        text(SQL_TENDENCIA),
        {"regiao": kpi["dimensao"], "ano": ano, "mes": mes},
    )
    valores_tendencia = [float(r["faturamento"]) for r in result_tendencia.mappings().all()]
    tendencia = _analisar_tendencia(valores_tendencia)

    # Busca sazonalidade
    result_sazonal = await conn.execute(
        text(SQL_SAZONALIDADE),
        {"regiao": kpi["dimensao"], "mes": mes},
    )
    valores_sazonal = {
        int(r["ano"]): float(r["faturamento"]) for r in result_sazonal.mappings().all()
    }
    sazonalidade, e_queda_real = _analisar_sazonalidade(valores_sazonal, ano, mes)

    return AnaliseQuantitativa(
        kpi=kpi["kpi"],
        tendencia_recente=tendencia,
        historico_sazonal=sazonalidade,
        e_queda_real=e_queda_real,
    )


async def perna_quantitativa(
    state: AgentState,
    *,
    conn: "AsyncConnection | None" = None,
) -> AgentState:
    """Nó perna_quantitativa: analisa tendência e sazonalidade.

    Args:
        state: Estado atual do grafo (deve ter kpis_fracos)
        conn: Conexão async do SQLAlchemy (opcional, para testes)

    Returns:
        Estado atualizado com analise_quantitativa
    """
    kpis_fracos = state.get("kpis_fracos", [])
    periodo = state.get("periodo_alvo", {"ano": 2025, "mes": 7})
    sql_executados = state.get("sql_executados", [])

    analises: list[AnaliseQuantitativa] = []

    if conn is not None and kpis_fracos:
        for kpi in kpis_fracos:
            analise = await _analisar_kpi(conn, kpi, periodo["ano"], periodo["mes"])
            analises.append(analise)

        sql_executados.extend(
            [
                {"sql": SQL_TENDENCIA, "resultado": f"Tendência para {len(kpis_fracos)} KPIs"},
                {
                    "sql": SQL_SAZONALIDADE,
                    "resultado": f"Sazonalidade para {len(kpis_fracos)} KPIs",
                },
            ]
        )

    # Retorna estado atualizado preservando campos anteriores
    new_state: AgentState = {
        "pergunta": state.get("pergunta", ""),
        "thread_id": state.get("thread_id", ""),
        "periodo_alvo": state.get("periodo_alvo", {"ano": 2025, "mes": 7}),
        "premissas": state.get("premissas", []),
        "kpis_fracos": state.get("kpis_fracos", []),
        "analise_quantitativa": analises,
        "sql_executados": sql_executados,
        "fontes_consultadas": state.get("fontes_consultadas", []),
    }
    return new_state
