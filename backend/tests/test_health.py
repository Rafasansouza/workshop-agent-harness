"""Testes do health check."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste síncrono."""
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    """Health check retorna status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
