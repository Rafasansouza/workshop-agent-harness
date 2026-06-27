"""Tool search — busca semântica no Qdrant com filtros obrigatórios.

A tool é parametrizada pela coleção. O NÓ do grafo escolhe a coleção
(camada_semantica, diagnostico, prescricao); o LLM não fica num laço escolhendo.

Filtros obrigatórios:
- periodo_referencia (nunca data_ingestao — são conceitos diferentes)
- Dimensão relevante (regiao, canal, produto, etc.)
- kpi_alvo quando aplicável
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient, models

from backend.app.config import settings

# Coleções válidas
VALID_COLLECTIONS = frozenset({"camada_semantica", "diagnostico", "prescricao"})

# Campos que NUNCA devem ser usados como filtro (invariante do projeto)
FORBIDDEN_FILTERS = frozenset({"data_ingestao"})


class SearchError(Exception):
    """Erro na busca semântica."""


@dataclass
class SearchHit:
    """Um resultado da busca."""

    score: float
    fonte: str
    documento: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Resultado de uma busca semântica."""

    colecao: str
    query: str
    hits: list[SearchHit]
    filtros_aplicados: dict[str, Any]


def _validate_collection(colecao: str) -> None:
    """Valida que a coleção é válida."""
    if colecao not in VALID_COLLECTIONS:
        raise SearchError(
            f"Coleção '{colecao}' inválida. Válidas: {', '.join(sorted(VALID_COLLECTIONS))}"
        )


def _validate_filters(filtros: dict[str, Any]) -> None:
    """Valida que os filtros não usam campos proibidos."""
    for key in filtros:
        if key in FORBIDDEN_FILTERS:
            raise SearchError(
                f"Filtro por '{key}' não permitido. Use 'periodo_referencia' para "
                f"filtrar por período do negócio (periodo_referencia ≠ data_ingestao)."
            )


def _embed_query(query: str) -> list[float]:
    """Gera embedding da query usando OpenAI."""
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.embed_model,
        input=query,
        dimensions=settings.embed_dim,
    )
    return response.data[0].embedding


def _build_filter(filtros: dict[str, Any]) -> models.Filter | None:
    """Constrói filtro Qdrant a partir do dict."""
    if not filtros:
        return None

    conditions: list[models.FieldCondition] = []
    for key, value in filtros.items():
        conditions.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))

    return models.Filter(must=conditions)  # type: ignore[arg-type]


def search(
    colecao: str,
    query: str,
    filtros: dict[str, Any] | None = None,
    top_k: int = 5,
    *,
    qdrant_client: QdrantClient | None = None,
    embed_fn: Any | None = None,
) -> SearchResult:
    """Busca semântica no Qdrant.

    Args:
        colecao: Nome da coleção (camada_semantica, diagnostico, prescricao)
        query: Texto da consulta
        filtros: Filtros a aplicar (periodo_referencia, regiao, kpi_alvo, etc.)
        top_k: Número máximo de resultados
        qdrant_client: Cliente Qdrant (opcional, para testes)
        embed_fn: Função de embedding (opcional, para testes)

    Returns:
        SearchResult com hits ordenados por score

    Raises:
        SearchError: Se coleção inválida ou filtro proibido
    """
    filtros = filtros or {}

    # Validações
    _validate_collection(colecao)
    _validate_filters(filtros)

    # Embedding
    if embed_fn:
        query_vector = embed_fn(query)
    else:
        query_vector = _embed_query(query)

    # Cliente Qdrant
    if qdrant_client is None:
        qdrant_client = QdrantClient(url=settings.qdrant_url)

    # Filtro
    qdrant_filter = _build_filter(filtros)

    # Busca
    results = qdrant_client.query_points(
        collection_name=colecao,
        query=query_vector,
        query_filter=qdrant_filter,
        limit=top_k,
    )

    # Monta resposta
    hits = []
    for point in results.points:
        payload = point.payload or {}
        hits.append(
            SearchHit(
                score=point.score,
                fonte=payload.get("fonte", ""),
                documento=payload.get("document", ""),
                payload=payload,
            )
        )

    return SearchResult(
        colecao=colecao,
        query=query,
        hits=hits,
        filtros_aplicados=filtros,
    )
