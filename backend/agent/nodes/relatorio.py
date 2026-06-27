"""Nó relatorio — compila o state em relatório markdown.

Este nó:
1. Recebe o state completo com análises
2. Usa LLM para redigir relatório estruturado
3. Garante que cada recomendação cita a fonte
"""

from __future__ import annotations

import logging
from typing import Callable

from backend.agent.state import AgentState

logger = logging.getLogger(__name__)


def _formatar_premissas(premissas: list[str]) -> str:
    """Formata premissas para o relatório."""
    if not premissas:
        return ""
    items = "\n".join(f"- {p}" for p in premissas)
    return f"## Premissas assumidas\n\n{items}\n"


def _formatar_kpis_fracos(state: AgentState) -> str:
    """Formata KPIs fracos para o relatório."""
    kpis = state.get("kpis_fracos", [])
    if not kpis:
        return "## KPIs\n\nNenhum KPI abaixo da meta identificado.\n"

    linhas = ["## KPIs abaixo da meta\n"]
    for kpi in kpis:
        linhas.append(
            f"- **{kpi['kpi']}** na região {kpi['dimensao']}: "
            f"R$ {kpi['valor_atual']:,.0f} vs meta R$ {kpi['valor_meta']:,.0f} "
            f"(gap de {kpi['gap_percentual']:.1f}%)"
        )
    return "\n".join(linhas) + "\n"


def _formatar_analise_quantitativa(state: AgentState) -> str:
    """Formata análise quantitativa para o relatório."""
    analises = state.get("analise_quantitativa", [])
    if not analises:
        return ""

    linhas = ["## Análise quantitativa\n"]
    for a in analises:
        status = "**queda real**" if a["e_queda_real"] else "variação sazonal"
        linhas.append(f"### {a['kpi']}")
        linhas.append(f"- Tendência: {a['tendencia_recente']}")
        linhas.append(f"- Sazonalidade: {a['historico_sazonal']}")
        linhas.append(f"- Diagnóstico: {status}")
        linhas.append("")
    return "\n".join(linhas)


def _formatar_diagnosticos(state: AgentState) -> str:
    """Formata diagnósticos para o relatório."""
    diagnosticos = state.get("diagnosticos", [])
    if not diagnosticos:
        return ""

    linhas = ["## Diagnóstico (por quê)\n"]
    for d in diagnosticos:
        linhas.append(f"**{d['kpi']}**: {d['explicacao']}")
        linhas.append(f"*Fonte: {d['fonte']}*\n")
    return "\n".join(linhas)


def _formatar_prescricoes(state: AgentState) -> str:
    """Formata prescrições para o relatório.

    REGRA DE OURO: cada recomendação deve citar a fonte.
    """
    prescricoes = state.get("prescricoes", [])
    if not prescricoes:
        return "## Recomendações\n\nNenhuma recomendação encontrada com fonte verificável.\n"

    linhas = ["## Recomendações priorizadas\n"]
    for i, p in enumerate(prescricoes, 1):
        linhas.append(f"### {i}. {p['kpi']}")
        linhas.append(f"{p['recomendacao']}")
        if p.get("resultado_anterior"):
            linhas.append(f"*Histórico: {p['resultado_anterior']}*")
        linhas.append(f"*Fonte: {p['fonte']}*\n")
    return "\n".join(linhas)


def gerar_relatorio_simples(state: AgentState) -> str:
    """Gera relatório sem usar LLM (para testes e fallback)."""
    periodo = state.get("periodo_alvo", {"ano": 2025, "mes": 7})
    titulo = f"# Relatório de Melhoria de Vendas — {periodo['mes']:02d}/{periodo['ano']}\n\n"

    secoes = [
        titulo,
        _formatar_premissas(state.get("premissas", [])),
        _formatar_kpis_fracos(state),
        _formatar_analise_quantitativa(state),
        _formatar_diagnosticos(state),
        _formatar_prescricoes(state),
    ]

    return "\n".join(s for s in secoes if s)


async def gerar_relatorio_com_llm(
    state: AgentState,
    llm_fn: Callable[[str], str] | None = None,
) -> str:
    """Gera relatório usando LLM para redação."""
    # Monta contexto para o LLM
    contexto = gerar_relatorio_simples(state)

    prompt = f"""Você é um analista de vendas. Reescreva o relatório abaixo de forma mais fluida e profissional,
mantendo TODAS as informações, especialmente:
- As premissas assumidas no topo
- Cada recomendação com sua fonte citada
- O diagnóstico de queda real vs sazonal

NÃO invente informações. Mantenha todas as fontes citadas.

Relatório atual:
{contexto}

Relatório reescrito:"""

    if llm_fn:
        return llm_fn(prompt)

    # Fallback: retorna versão simples
    return contexto


async def relatorio(
    state: AgentState,
    *,
    llm_fn: Callable[[str], str] | None = None,
    usar_llm: bool = False,
) -> AgentState:
    """Nó relatorio: compila state em relatório markdown.

    Args:
        state: Estado atual do grafo (deve ter todas as análises)
        llm_fn: Função de LLM (opcional, para testes)
        usar_llm: Se True, usa LLM para redigir (default False para testes)

    Returns:
        Estado atualizado com relatorio
    """
    if usar_llm:
        texto = await gerar_relatorio_com_llm(state, llm_fn)
    else:
        texto = gerar_relatorio_simples(state)

    # Retorna estado atualizado
    new_state: AgentState = {
        "pergunta": state.get("pergunta", ""),
        "thread_id": state.get("thread_id", ""),
        "periodo_alvo": state.get("periodo_alvo", {"ano": 2025, "mes": 7}),
        "premissas": state.get("premissas", []),
        "kpis_fracos": state.get("kpis_fracos", []),
        "analise_quantitativa": state.get("analise_quantitativa", []),
        "diagnosticos": state.get("diagnosticos", []),
        "prescricoes": state.get("prescricoes", []),
        "relatorio": texto,
        "sql_executados": state.get("sql_executados", []),
        "fontes_consultadas": state.get("fontes_consultadas", []),
    }
    return new_state
