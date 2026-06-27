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


MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}


def _resolver_periodo_alvo(pergunta: str) -> tuple[dict[str, int], list[str]]:
    """Resolve o período-alvo a partir da pergunta.

    Tenta extrair mês/ano da pergunta. Default: próximo mês.

    Returns:
        Tuple de (periodo_alvo, premissas)
    """
    import re

    pergunta_lower = pergunta.lower()
    ano_extraido = None
    mes_extraido = None

    # Tenta extrair ano (4 dígitos)
    match_ano = re.search(r"\b(20\d{2})\b", pergunta)
    if match_ano:
        ano_extraido = int(match_ano.group(1))

    # Tenta extrair mês por nome
    for nome_mes, num_mes in MESES.items():
        if nome_mes in pergunta_lower:
            mes_extraido = num_mes
            break

    # Tenta extrair mês numérico (ex: "05/2026", "2026-05")
    if mes_extraido is None:
        match_mes_num = re.search(r"\b(0?[1-9]|1[0-2])[/-](20\d{2})\b", pergunta)
        if match_mes_num:
            mes_extraido = int(match_mes_num.group(1))
            ano_extraido = int(match_mes_num.group(2))
        else:
            match_mes_num2 = re.search(r"\b(20\d{2})[/-](0?[1-9]|1[0-2])\b", pergunta)
            if match_mes_num2:
                ano_extraido = int(match_mes_num2.group(1))
                mes_extraido = int(match_mes_num2.group(2))

    # Se não extraiu, usa default (próximo mês)
    hoje = date.today()
    if mes_extraido is None:
        mes = hoje.month + 1
        ano = hoje.year if mes <= 12 else hoje.year + 1
        mes = mes if mes <= 12 else 1
        premissa_periodo = f"Período-alvo assumido: {mes:02d}/{ano} (próximo mês)"
    else:
        mes = mes_extraido
        ano = ano_extraido if ano_extraido else hoje.year
        premissa_periodo = f"Período-alvo: {mes:02d}/{ano} (extraído da pergunta)"

    periodo = {"ano": ano, "mes": mes}
    premissas = [
        premissa_periodo,
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
