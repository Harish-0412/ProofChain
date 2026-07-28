"""Atomic artifact persistence for Phase 1 production agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from proofchain.core.paths import get_run_dir
from proofchain.repositories.json_store import AtomicJsonStore


class ProductionArtifactRepository:
    def __init__(self, store: AtomicJsonStore | None = None):
        self.store = store or AtomicJsonStore()

    def save(self, run_id: str, name: str, value: Any) -> tuple[Path, str]:
        path = get_run_dir(run_id) / name
        digest = self.store.write(path, value)
        return path, digest

    def read(self, run_id: str, name: str, default: Any = None) -> Any:
        return self.store.read(get_run_dir(run_id) / name, default=default)

