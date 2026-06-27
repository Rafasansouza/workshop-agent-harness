"""State do grafo LangGraph — TypedDict com todos os campos."""

from __future__ import annotations

from typing import TypedDict


class KpiFraco(TypedDict):
    """Um KPI identificado como abaixo da meta."""

    kpi: str
    dimensao: str  # regiao, canal, produto, categoria
    valor_atual: float
    valor_meta: float
    gap_percentual: float  # (meta - atual) / meta * 100


class AnaliseQuantitativa(TypedDict):
    """Análise quantitativa de um KPI."""

    kpi: str
    tendencia_recente: str  # descrição da tendência
    historico_sazonal: str  # comparação com mesmo período anos anteriores
    e_queda_real: bool  # True se queda real, False se variação sazonal


class Diagnostico(TypedDict):
    """Diagnóstico qualitativo de um KPI."""

    kpi: str
    explicacao: str
    fonte: str


class Prescricao(TypedDict):
    """Recomendação prescritiva com fonte."""

    kpi: str
    recomendacao: str
    fonte: str
    resultado_anterior: str | None  # o que aconteceu quando foi aplicada antes


class AgentState(TypedDict, total=False):
    """Estado do grafo do agente analítico.

    Campos são adicionados progressivamente pelos nós:
    - planejar: pergunta, periodo_alvo, premissas, kpis_fracos
    - perna_quantitativa: analise_quantitativa
    - enriquecer: diagnosticos, prescricoes
    - relatorio: relatorio
    """

    # Input
    pergunta: str
    thread_id: str

    # Planejar
    periodo_alvo: dict[str, int]  # {"ano": 2025, "mes": 7}
    premissas: list[str]
    kpis_fracos: list[KpiFraco]

    # Perna quantitativa
    analise_quantitativa: list[AnaliseQuantitativa]

    # Enriquecer
    diagnosticos: list[Diagnostico]
    prescricoes: list[Prescricao]

    # Relatório
    relatorio: str

    # Metadados para observabilidade
    sql_executados: list[dict[str, str]]  # {"sql": ..., "resultado": ...}
    fontes_consultadas: list[dict[str, str]]  # {"colecao": ..., "query": ..., "hits": ...}
