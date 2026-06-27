"""Tool run_sql — executa queries SQL com guardrails determinísticos.

Guardrails aplicados ANTES de enviar ao banco:
1. Allowlist: apenas SELECT e WITH (CTEs)
2. Rejeita INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE
3. Apenas uma instrução SQL por chamada
4. Injeta LIMIT se ausente (default 1000)

No banco:
- Usa papel agente_ro (somente leitura)
- SET TRANSACTION READ ONLY
- statement_timeout configurável
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

# Palavras-chave proibidas (início de statement)
_FORBIDDEN_KEYWORDS = frozenset(
    {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE",
        "VACUUM",
        "ANALYZE",
        "REINDEX",
        "CLUSTER",
    }
)

# Palavras-chave permitidas (início de statement)
_ALLOWED_KEYWORDS = frozenset({"SELECT", "WITH"})

# Limite default de linhas
DEFAULT_LIMIT = 1000

# Timeout default em ms
DEFAULT_TIMEOUT_MS = 30000


class SqlGuardrailError(Exception):
    """Erro de violação dos guardrails de SQL."""


@dataclass
class SqlResult:
    """Resultado de uma query SQL."""

    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int


def _normalize_sql(sql: str) -> str:
    """Remove comentários e normaliza whitespace."""
    # Remove comentários de linha
    sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    # Remove comentários de bloco
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    # Normaliza whitespace
    return " ".join(sql.split()).strip()


def _get_first_keyword(sql: str) -> str:
    """Extrai a primeira palavra-chave do SQL normalizado."""
    normalized = _normalize_sql(sql)
    if not normalized:
        return ""
    # Pega a primeira palavra
    match = re.match(r"(\w+)", normalized, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _count_statements(sql: str) -> int:
    """Conta o número de statements SQL (separados por ;)."""
    normalized = _normalize_sql(sql)
    # Remove strings entre aspas para não contar ; dentro delas
    # Simplificação: conta ; fora de strings
    in_string = False
    quote_char = None
    count = 1
    i = 0
    while i < len(normalized):
        c = normalized[i]
        if not in_string and c in ("'", '"'):
            in_string = True
            quote_char = c
        elif in_string and c == quote_char:
            # Verifica escape
            if i + 1 < len(normalized) and normalized[i + 1] == quote_char:
                i += 1  # Skip escaped quote
            else:
                in_string = False
                quote_char = None
        elif not in_string and c == ";":
            # Verifica se há algo depois do ;
            rest = normalized[i + 1 :].strip()
            if rest:
                count += 1
        i += 1
    return count


def _has_limit(sql: str) -> bool:
    """Verifica se o SQL já tem LIMIT."""
    normalized = _normalize_sql(sql).upper()
    # Procura LIMIT seguido de número ou ALL
    return bool(re.search(r"\bLIMIT\s+(\d+|ALL)\b", normalized))


def _inject_limit(sql: str, limit: int = DEFAULT_LIMIT) -> str:
    """Injeta LIMIT se não existir."""
    if _has_limit(sql):
        return sql
    normalized = _normalize_sql(sql)
    # Remove ; final se houver
    if normalized.endswith(";"):
        normalized = normalized[:-1].strip()
    return f"{normalized} LIMIT {limit}"


def validate_sql(sql: str) -> None:
    """Valida SQL contra os guardrails. Levanta SqlGuardrailError se inválido."""
    if not sql or not sql.strip():
        raise SqlGuardrailError("SQL vazio")

    # 1. Verifica primeira palavra-chave
    first_kw = _get_first_keyword(sql)
    if not first_kw:
        raise SqlGuardrailError("SQL inválido: não foi possível identificar o comando")

    if first_kw in _FORBIDDEN_KEYWORDS:
        raise SqlGuardrailError(
            f"Comando {first_kw} não permitido. Apenas SELECT e WITH são aceitos."
        )

    if first_kw not in _ALLOWED_KEYWORDS:
        raise SqlGuardrailError(
            f"Comando {first_kw} não reconhecido. Apenas SELECT e WITH são aceitos."
        )

    # 2. Verifica múltiplos statements
    stmt_count = _count_statements(sql)
    if stmt_count > 1:
        raise SqlGuardrailError(
            f"Múltiplos statements detectados ({stmt_count}). Apenas um statement por chamada."
        )

    # 3. Verifica palavras proibidas no corpo (proteção extra)
    normalized_upper = _normalize_sql(sql).upper()
    for kw in _FORBIDDEN_KEYWORDS:
        # Procura a palavra como token separado (não parte de nome de coluna)
        pattern = rf"\b{kw}\b"
        if re.search(pattern, normalized_upper):
            raise SqlGuardrailError(
                f"Palavra-chave {kw} detectada no SQL. Operações de escrita não são permitidas."
            )


def prepare_sql(sql: str, limit: int = DEFAULT_LIMIT) -> str:
    """Valida e prepara o SQL para execução."""
    validate_sql(sql)
    return _inject_limit(sql, limit)


async def run_sql(
    conn: AsyncConnection,
    sql: str,
    *,
    limit: int = DEFAULT_LIMIT,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> SqlResult:
    """Executa SQL com guardrails.

    Args:
        conn: Conexão async do SQLAlchemy
        sql: Query SQL a executar
        limit: Limite de linhas (default 1000)
        timeout_ms: Timeout em milissegundos (default 30000)

    Returns:
        SqlResult com colunas, linhas e contagem

    Raises:
        SqlGuardrailError: Se o SQL violar os guardrails
    """
    # Valida e prepara
    prepared = prepare_sql(sql, limit)

    # Configura timeout e modo read-only
    await conn.execute(sa.text(f"SET LOCAL statement_timeout = {timeout_ms}"))
    await conn.execute(sa.text("SET TRANSACTION READ ONLY"))

    # Executa
    result = await conn.execute(sa.text(prepared))
    rows = result.mappings().all()

    return SqlResult(
        columns=list(result.keys()),
        rows=[dict(r) for r in rows],
        row_count=len(rows),
    )
