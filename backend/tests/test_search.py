"""Testes da tool search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from backend.agent.tools.search import (
    SearchError,
    search,
)


@dataclass
class MockPoint:
    """Mock de um ponto retornado pelo Qdrant."""

    score: float
    payload: dict[str, Any]


@dataclass
class MockQueryResult:
    """Mock do resultado de query_points."""

    points: list[MockPoint]


@pytest.fixture
def mock_qdrant() -> MagicMock:
    """Cliente Qdrant mockado."""
    client = MagicMock()
    client.query_points.return_value = MockQueryResult(
        points=[
            MockPoint(
                score=0.9,
                payload={
                    "fonte": "minio://corpus/diagnostico/doc1.md",
                    "document": "Conteúdo do documento 1",
                    "periodo_referencia": "2025-06",
                    "regiao": "Sul",
                },
            ),
            MockPoint(
                score=0.7,
                payload={
                    "fonte": "minio://corpus/diagnostico/doc2.md",
                    "document": "Conteúdo do documento 2",
                    "periodo_referencia": "2025-06",
                    "regiao": "Sul",
                },
            ),
        ]
    )
    return client


@pytest.fixture
def mock_embed() -> Any:
    """Função de embedding mockada."""
    return lambda query: [0.1] * 3072


class TestSearchValidation:
    """Testes de validação da busca."""

    def test_colecao_invalida_rejeita(self, mock_qdrant: MagicMock, mock_embed: Any) -> None:
        """Coleção inválida é rejeitada."""
        with pytest.raises(SearchError, match="inválida"):
            search(
                "colecao_inexistente",
                "teste",
                qdrant_client=mock_qdrant,
                embed_fn=mock_embed,
            )

    def test_colecoes_validas_aceitas(self, mock_qdrant: MagicMock, mock_embed: Any) -> None:
        """Coleções válidas são aceitas."""
        for colecao in ["camada_semantica", "diagnostico", "prescricao"]:
            result = search(
                colecao,
                "teste",
                qdrant_client=mock_qdrant,
                embed_fn=mock_embed,
            )
            assert result.colecao == colecao

    def test_filtro_data_ingestao_rejeitado(self, mock_qdrant: MagicMock, mock_embed: Any) -> None:
        """Filtro por data_ingestao é rejeitado (invariante do projeto)."""
        with pytest.raises(SearchError, match="data_ingestao"):
            search(
                "diagnostico",
                "teste",
                filtros={"data_ingestao": "2025-06-01"},
                qdrant_client=mock_qdrant,
                embed_fn=mock_embed,
            )

    def test_filtro_periodo_referencia_aceito(
        self, mock_qdrant: MagicMock, mock_embed: Any
    ) -> None:
        """Filtro por periodo_referencia é aceito."""
        result = search(
            "diagnostico",
            "teste",
            filtros={"periodo_referencia": "2025-06"},
            qdrant_client=mock_qdrant,
            embed_fn=mock_embed,
        )
        assert result.filtros_aplicados == {"periodo_referencia": "2025-06"}


class TestSearchResults:
    """Testes dos resultados da busca."""

    def test_retorna_hits_ordenados(self, mock_qdrant: MagicMock, mock_embed: Any) -> None:
        """Hits são retornados com score."""
        result = search(
            "diagnostico",
            "queda de recompra",
            filtros={"regiao": "Sul"},
            qdrant_client=mock_qdrant,
            embed_fn=mock_embed,
        )

        assert len(result.hits) == 2
        assert result.hits[0].score == 0.9
        assert result.hits[1].score == 0.7

    def test_hit_contem_fonte_e_documento(self, mock_qdrant: MagicMock, mock_embed: Any) -> None:
        """Cada hit contém fonte e documento."""
        result = search(
            "diagnostico",
            "teste",
            qdrant_client=mock_qdrant,
            embed_fn=mock_embed,
        )

        hit = result.hits[0]
        assert hit.fonte == "minio://corpus/diagnostico/doc1.md"
        assert hit.documento == "Conteúdo do documento 1"
        assert hit.payload["regiao"] == "Sul"

    def test_result_contem_metadados(self, mock_qdrant: MagicMock, mock_embed: Any) -> None:
        """SearchResult contém metadados da busca."""
        result = search(
            "diagnostico",
            "minha query",
            filtros={"regiao": "Sul", "kpi_alvo": "taxa_recompra"},
            qdrant_client=mock_qdrant,
            embed_fn=mock_embed,
        )

        assert result.colecao == "diagnostico"
        assert result.query == "minha query"
        assert result.filtros_aplicados == {"regiao": "Sul", "kpi_alvo": "taxa_recompra"}

    def test_busca_sem_filtros(self, mock_qdrant: MagicMock, mock_embed: Any) -> None:
        """Busca sem filtros funciona."""
        result = search(
            "camada_semantica",
            "como calcular taxa de recompra",
            qdrant_client=mock_qdrant,
            embed_fn=mock_embed,
        )

        assert result.filtros_aplicados == {}
        assert len(result.hits) == 2
