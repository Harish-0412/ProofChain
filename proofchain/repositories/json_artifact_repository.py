"""Repositories for run-scoped typed artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.common import ArtifactReference

ModelType = TypeVar("ModelType", bound=BaseModel)


class JsonArtifactRepository:
    def __init__(self, store: AtomicJsonStore | None = None):
        self.store = store or AtomicJsonStore()

    def save(
        self,
        path: Path,
        value: Any,
        *,
        stage_name: str,
        record_count: int,
        agent_run_id: str | None,
    ) -> ArtifactReference:
        digest = self.store.write(path, value)
        return ArtifactReference(
            stage_name=stage_name,
            path=str(path.resolve()),
            sha256=digest,
            record_count=record_count,
            agent_run_id=agent_run_id,
        )

    def load_models(self, path: Path, model: type[ModelType]) -> list[ModelType]:
        payload = self.store.read(path, default=[])
        if not isinstance(payload, list):
            raise ValueError(f"Expected a JSON list in {path}")
        return [model.model_validate(item) for item in payload]

    def load(self, path: Path, default: Any = None) -> Any:
        return self.store.read(path, default)
