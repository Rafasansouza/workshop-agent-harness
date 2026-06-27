"""Testes do modulo harness."""

from __future__ import annotations


from backend.harness.models import Run, RunStatus, RunStep, RunTrace


class TestRunModel:
    """Testes do modelo Run."""

    def test_run_status_enum(self) -> None:
        """RunStatus tem os valores esperados."""
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"

    def test_run_has_required_fields(self) -> None:
        """Run tem os campos obrigatorios."""
        assert hasattr(Run, "id")
        assert hasattr(Run, "thread_id")
        assert hasattr(Run, "created_at")
        assert hasattr(Run, "status")
        assert hasattr(Run, "duration_ms")
        assert hasattr(Run, "error_message")
        assert hasattr(Run, "steps")
        assert hasattr(Run, "traces")


class TestRunStepModel:
    """Testes do modelo RunStep."""

    def test_run_step_has_required_fields(self) -> None:
        """RunStep tem os campos obrigatorios."""
        assert hasattr(RunStep, "id")
        assert hasattr(RunStep, "run_id")
        assert hasattr(RunStep, "node_name")
        assert hasattr(RunStep, "started_at")
        assert hasattr(RunStep, "finished_at")
        assert hasattr(RunStep, "duration_ms")
        assert hasattr(RunStep, "input_state")
        assert hasattr(RunStep, "output_state")


class TestRunTraceModel:
    """Testes do modelo RunTrace."""

    def test_run_trace_has_required_fields(self) -> None:
        """RunTrace tem os campos obrigatorios."""
        assert hasattr(RunTrace, "id")
        assert hasattr(RunTrace, "run_id")
        assert hasattr(RunTrace, "tool_name")
        assert hasattr(RunTrace, "called_at")
        assert hasattr(RunTrace, "duration_ms")
        assert hasattr(RunTrace, "input_data")
        assert hasattr(RunTrace, "output_data")
        assert hasattr(RunTrace, "error")
