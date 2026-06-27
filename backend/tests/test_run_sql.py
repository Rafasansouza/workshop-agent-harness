"""Testes dos guardrails da tool run_sql."""

from __future__ import annotations

import pytest

from backend.agent.tools.run_sql import (
    SqlGuardrailError,
    prepare_sql,
    validate_sql,
)


class TestValidateSql:
    """Testes de validação SQL."""

    def test_select_simples_passa(self) -> None:
        """SELECT simples é aceito."""
        validate_sql("SELECT * FROM negocio.regioes")

    def test_select_com_where_passa(self) -> None:
        """SELECT com WHERE é aceito."""
        validate_sql("SELECT nome FROM negocio.regioes WHERE id = 1")

    def test_with_cte_passa(self) -> None:
        """CTE com WITH é aceito."""
        validate_sql("""
            WITH vendas AS (
                SELECT * FROM negocio.pedidos
            )
            SELECT * FROM vendas
        """)

    def test_insert_rejeitado(self) -> None:
        """INSERT é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="INSERT"):
            validate_sql("INSERT INTO negocio.regioes (nome) VALUES ('teste')")

    def test_update_rejeitado(self) -> None:
        """UPDATE é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="UPDATE"):
            validate_sql("UPDATE negocio.regioes SET nome = 'x'")

    def test_delete_rejeitado(self) -> None:
        """DELETE é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="DELETE"):
            validate_sql("DELETE FROM negocio.regioes")

    def test_drop_rejeitado(self) -> None:
        """DROP é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="DROP"):
            validate_sql("DROP TABLE negocio.regioes")

    def test_truncate_rejeitado(self) -> None:
        """TRUNCATE é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="TRUNCATE"):
            validate_sql("TRUNCATE TABLE negocio.regioes")

    def test_alter_rejeitado(self) -> None:
        """ALTER é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="ALTER"):
            validate_sql("ALTER TABLE negocio.regioes ADD COLUMN x INT")

    def test_create_rejeitado(self) -> None:
        """CREATE é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="CREATE"):
            validate_sql("CREATE TABLE teste (id INT)")

    def test_multiplos_statements_rejeitado(self) -> None:
        """Múltiplos statements são rejeitados."""
        with pytest.raises(SqlGuardrailError, match="Múltiplos"):
            validate_sql("SELECT 1; DROP TABLE negocio.regioes")

    def test_select_com_delete_no_corpo_rejeitado(self) -> None:
        """DELETE escondido no corpo é detectado (como múltiplos statements)."""
        with pytest.raises(SqlGuardrailError, match="Múltiplos"):
            validate_sql("SELECT * FROM t; DELETE FROM t")

    def test_sql_vazio_rejeitado(self) -> None:
        """SQL vazio é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="vazio"):
            validate_sql("")

    def test_sql_so_espacos_rejeitado(self) -> None:
        """SQL só com espaços é rejeitado."""
        with pytest.raises(SqlGuardrailError, match="vazio"):
            validate_sql("   ")

    def test_comentario_nao_esconde_comando(self) -> None:
        """Comentários não escondem comandos proibidos."""
        # O INSERT após o comentário deve ser detectado
        with pytest.raises(SqlGuardrailError, match="INSERT"):
            validate_sql("-- SELECT * FROM t\nINSERT INTO t VALUES (1)")


class TestPrepareSql:
    """Testes de preparação SQL (validação + LIMIT)."""

    def test_injeta_limit_quando_ausente(self) -> None:
        """LIMIT é injetado se ausente."""
        result = prepare_sql("SELECT * FROM negocio.regioes")
        assert "LIMIT 1000" in result

    def test_preserva_limit_existente(self) -> None:
        """LIMIT existente é preservado."""
        sql = "SELECT * FROM negocio.regioes LIMIT 10"
        result = prepare_sql(sql)
        assert "LIMIT 10" in result
        assert "LIMIT 1000" not in result

    def test_limit_custom(self) -> None:
        """Limite customizado funciona."""
        result = prepare_sql("SELECT * FROM negocio.regioes", limit=50)
        assert "LIMIT 50" in result

    def test_remove_ponto_virgula_antes_limit(self) -> None:
        """Ponto e vírgula é removido antes de injetar LIMIT."""
        result = prepare_sql("SELECT * FROM negocio.regioes;")
        assert result.endswith("LIMIT 1000")
        assert not result.endswith("; LIMIT 1000")
