"""Grafo LangGraph — topologia determinística do agente.

O grafo tem topologia FIXA:
    planejar → perna_quantitativa → enriquecer → relatorio

O LLM decide DENTRO de cada nó; o roteamento entre nós é código.
"""

from __future__ import annotations

from langgraph.graph import StateGraph

from backend.agent.state import AgentState


def criar_grafo() -> StateGraph:
    """Cria o grafo do agente analítico.

    Returns:
        StateGraph configurado (ainda não compilado)
    """
    grafo = StateGraph(AgentState)

    # Nós serão adicionados conforme implementados
    # Por enquanto, grafo vazio para compilar

    return grafo
