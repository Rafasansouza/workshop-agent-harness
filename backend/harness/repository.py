"""Repository para operacoes CRUD no schema harness."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.harness.models import Run, RunStatus, RunStep, RunTrace


class HarnessRepository:
    """Repository para persistencia de runs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_run(self, thread_id: str) -> Run:
        """Cria uma nova run."""
        run = Run(thread_id=thread_id, status=RunStatus.RUNNING)
        self.session.add(run)
        await self.session.flush()
        return run

    async def complete_run(self, run_id: int, duration_ms: int) -> None:
        """Marca uma run como completa."""
        run = await self.session.get(Run, run_id)
        if run:
            run.status = RunStatus.COMPLETED
            run.finished_at = datetime.now(timezone.utc)
            run.duration_ms = duration_ms

    async def fail_run(self, run_id: int, error_message: str, duration_ms: int) -> None:
        """Marca uma run como falha."""
        run = await self.session.get(Run, run_id)
        if run:
            run.status = RunStatus.FAILED
            run.finished_at = datetime.now(timezone.utc)
            run.duration_ms = duration_ms
            run.error_message = error_message

    async def add_step(
        self,
        run_id: int,
        node_name: str,
        input_state: dict[str, Any] | None = None,
    ) -> RunStep:
        """Adiciona um step a uma run."""
        step = RunStep(
            run_id=run_id,
            node_name=node_name,
            input_state=input_state,
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def complete_step(
        self,
        step_id: int,
        output_state: dict[str, Any] | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Marca um step como completo."""
        step = await self.session.get(RunStep, step_id)
        if step:
            step.finished_at = datetime.now(timezone.utc)
            step.output_state = output_state
            step.duration_ms = duration_ms

    async def add_trace(
        self,
        run_id: int,
        tool_name: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        error: str | None = None,
    ) -> RunTrace:
        """Adiciona um trace de tool a uma run."""
        trace = RunTrace(
            run_id=run_id,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            error=error,
        )
        self.session.add(trace)
        await self.session.flush()
        return trace

    async def get_run(self, run_id: int) -> Run | None:
        """Busca uma run por ID."""
        return await self.session.get(Run, run_id)

    async def get_run_with_details(self, run_id: int) -> Run | None:
        """Busca uma run com steps e traces."""
        stmt = select(Run).where(Run.id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        if run:
            # Carrega relacionamentos
            await self.session.refresh(run, ["steps", "traces"])
        return run

    async def list_runs_by_thread(self, thread_id: str, limit: int = 10) -> list[Run]:
        """Lista runs de um thread."""
        stmt = (
            select(Run)
            .where(Run.thread_id == thread_id)
            .order_by(Run.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class RunTracker:
    """Contexto para tracking de uma run."""

    def __init__(self, repo: HarnessRepository, thread_id: str) -> None:
        self.repo = repo
        self.thread_id = thread_id
        self.run: Run | None = None
        self.start_time: float = 0
        self._current_step: RunStep | None = None
        self._step_start_time: float = 0

    async def start(self) -> int:
        """Inicia a run e retorna o ID."""
        self.start_time = time.perf_counter()
        self.run = await self.repo.create_run(self.thread_id)
        return self.run.id

    async def complete(self) -> None:
        """Marca a run como completa."""
        if self.run:
            duration_ms = int((time.perf_counter() - self.start_time) * 1000)
            await self.repo.complete_run(self.run.id, duration_ms)

    async def fail(self, error_message: str) -> None:
        """Marca a run como falha."""
        if self.run:
            duration_ms = int((time.perf_counter() - self.start_time) * 1000)
            await self.repo.fail_run(self.run.id, error_message, duration_ms)

    async def start_step(self, node_name: str, input_state: dict[str, Any] | None = None) -> None:
        """Inicia um step."""
        if self.run:
            self._step_start_time = time.perf_counter()
            self._current_step = await self.repo.add_step(
                self.run.id, node_name, input_state
            )

    async def end_step(self, output_state: dict[str, Any] | None = None) -> None:
        """Finaliza o step atual."""
        if self._current_step:
            duration_ms = int((time.perf_counter() - self._step_start_time) * 1000)
            await self.repo.complete_step(
                self._current_step.id, output_state, duration_ms
            )
            self._current_step = None

    async def trace_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        error: str | None = None,
    ) -> None:
        """Registra um trace de tool."""
        if self.run:
            await self.repo.add_trace(
                self.run.id, tool_name, input_data, output_data, duration_ms, error
            )


@asynccontextmanager
async def track_run(session: AsyncSession, thread_id: str):
    """Context manager para tracking de uma run.

    Uso:
        async with track_run(session, thread_id) as tracker:
            await tracker.start_step("planejar")
            # ... executa o no
            await tracker.end_step(state)
    """
    repo = HarnessRepository(session)
    tracker = RunTracker(repo, thread_id)
    await tracker.start()
    try:
        yield tracker
        await tracker.complete()
    except Exception as e:
        await tracker.fail(str(e))
        raise
