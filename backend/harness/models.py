"""Modelos SQLAlchemy para o schema harness."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base para modelos do harness."""

    pass


class RunStatus(enum.Enum):
    """Status de uma execução."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Run(Base):
    """Uma execução do grafo do agente."""

    __tablename__ = "runs"
    __table_args__ = {"schema": "harness"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus), default=RunStatus.RUNNING, nullable=False
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    steps: Mapped[list["RunStep"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    traces: Mapped[list["RunTrace"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RunStep(Base):
    """Um passo (nó) executado dentro de uma run."""

    __tablename__ = "run_steps"
    __table_args__ = {"schema": "harness"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("harness.runs.id"), nullable=False, index=True)
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relacionamento
    run: Mapped["Run"] = relationship(back_populates="steps")


class RunTrace(Base):
    """Um trace de tool executada dentro de uma run."""

    __tablename__ = "run_traces"
    __table_args__ = {"schema": "harness"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("harness.runs.id"), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    called_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamento
    run: Mapped["Run"] = relationship(back_populates="traces")
