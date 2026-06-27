"""Nó planejar — identifica KPIs fracos e resolve período-alvo.

Este nó:
1. Resolve o período-alvo (default: mês atual + 1)
2. Declara premissas assumidas
3. Consulta metas vs realizado via SQL
4. Identifica KPIs abaixo da meta
"""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING


from backend.agent.state import AgentState, KpiFraco

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

# SQL para buscar KPIs abaixo da meta
SQL_KPIS_FRACOS = """
WITH faturamento_por_regiao AS (
    SELECT
        r.nome AS regiao,
        SUM(p.valor_total) AS valor_atual
    FROM negocio.pedidos p
    JOIN negocio.regioes r ON r.id = p.regiao_id
    WHERE p.status = 'pago'
      AND EXTRACT(YEAR FROM p.data_pedido) = :ano
      AND EXTRACT(MONTH FROM p.data_pedido) = :mes
    GROUP BY r.nome
),
metas_faturamento AS (
    SELECT
        r.nome AS regiao,
        m.valor_meta
    FROM negocio.metas m
    JOIN negocio.regioes r ON r.id = m.regiao_id
    WHERE m.kpi = 'faturamento'
      AND m.ano = :ano
      AND m.mes = :mes
)
SELECT
    'faturamento' AS kpi,
    f.regiao AS dimensao,
    COALESCE(f.valor_atual, 0) AS valor_atual,
    COALESCE(m.valor_meta, 0) AS valor_meta,
    CASE
        WHEN m.valor_meta > 0 THEN
            ROUND(((m.valor_meta - COALESCE(f.valor_atual, 0)) / m.valor_meta * 100)::numeric, 2)
        ELSE 0
    END AS gap_percentual
FROM metas_faturamento m
LEFT JOIN faturamento_por_regiao f ON f.regiao = m.regiao
WHERE COALESCE(f.valor_atual, 0) < m.valor_meta
ORDER BY gap_percentual DESC
LIMIT 10
"""


def _resolver_periodo_alvo(pergunta: str) -> tuple[dict[str, int], list[str]]:
    """Resolve o período-alvo a partir da pergunta.

    Default: próximo mês (mês atual + 1), tratando virada de ano.

    Returns:
        Tuple de (periodo_alvo, premissas)
    """
    hoje = date.today()
    ano = hoje.year
    mes = hoje.month + 1

    # Trata virada de ano
    if mes > 12:
        mes = 1
        ano += 1

    periodo = {"ano": ano, "mes": mes}
    premissas = [
        f"Período-alvo assumido: {mes:02d}/{ano} (próximo mês)",
        "Escopo: todas as regiões e canais (pergunta não especificou filtro)",
    ]

    return periodo, premissas


async def _buscar_kpis_fracos(
    conn: "AsyncConnection",
    ano: int,
    mes: int,
) -> list[KpiFraco]:
    """Busca KPIs abaixo da meta no banco."""
    from sqlalchemy import text

    # Busca mês anterior para ter dados (período atual pode não ter fechado)
    mes_consulta = mes - 1 if mes > 1 else 12
    ano_consulta = ano if mes > 1 else ano - 1

    result = await conn.execute(
        text(SQL_KPIS_FRACOS),
        {"ano": ano_consulta, "mes": mes_consulta},
    )
    rows = result.mappings().all()

    kpis: list[KpiFraco] = []
    for row in rows:
        kpis.append(
            KpiFraco(
                kpi=row["kpi"],
                dimensao=row["dimensao"],
                valor_atual=float(row["valor_atual"]),
                valor_meta=float(row["valor_meta"]),
                gap_percentual=float(row["gap_percentual"]),
            )
        )

    return kpis


async def planejar(
    state: AgentState,
    *,
    conn: "AsyncConnection | None" = None,
) -> AgentState:
    """Nó planejar: identifica KPIs fracos e resolve período-alvo.

    Args:
        state: Estado atual do grafo
        conn: Conexão async do SQLAlchemy (opcional, para testes)

    Returns:
        Estado atualizado com periodo_alvo, premissas e kpis_fracos
    """
    pergunta = state.get("pergunta", "")

    # 1. Resolve período-alvo e premissas
    periodo_alvo, premissas = _resolver_periodo_alvo(pergunta)

    # 2. Busca KPIs fracos se tiver conexão
    kpis_fracos: list[KpiFraco] = []
    sql_executados: list[dict[str, str]] = state.get("sql_executados", [])

    if conn is not None:
        kpis_fracos = await _buscar_kpis_fracos(
            conn,
            periodo_alvo["ano"],
            periodo_alvo["mes"],
        )
        sql_executados.append(
            {
                "sql": SQL_KPIS_FRACOS,
                "resultado": f"{len(kpis_fracos)} KPIs fracos encontrados",
            }
        )

    # 3. Atualiza state
    return AgentState(
        pergunta=pergunta,
        thread_id=state.get("thread_id", ""),
        periodo_alvo=periodo_alvo,
        premissas=premissas,
        kpis_fracos=kpis_fracos,
        sql_executados=sql_executados,
        fontes_consultadas=state.get("fontes_consultadas", []),
    )
