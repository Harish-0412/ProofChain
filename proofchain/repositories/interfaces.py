"""Persistence ports used by production adapters and the JSON MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from proofchain.schemas.agentic import CoordinationPatch, CoordinationState
from proofchain.schemas.events import WorkflowEvent


class EventRepository(Protocol):
    def append(
        self,
        *,
        run_id: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        actor: str = "system",
        payload: dict | None = None,
    ) -> WorkflowEvent: ...

    def list(self, run_id: str) -> list[WorkflowEvent]: ...

    def validate_chain(self, run_id: str) -> list[str]: ...


class CoordinationRepository(Protocol):
    def load_state(self, run_id: str) -> CoordinationState: ...

    def update_state(
        self,
        run_id: str,
        expected_version: int,
        patch: CoordinationPatch,
    ) -> CoordinationState: ...


class ArtifactStore(Protocol):
    def read(self, path: Path, default: Any = None) -> Any: ...

    def write(self, path: Path, value: Any) -> str: ...
