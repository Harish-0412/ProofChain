"""Canonical persistence for Phase 1 cognition and decision-ledger artifacts."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from proofchain.core.paths import get_run_dir
from proofchain.repositories.json_store import AtomicJsonStore, jsonable


_LOCKS: dict[str, threading.RLock] = {}
_LOCK_GUARD = threading.Lock()


def _lock(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _LOCK_GUARD:
        return _LOCKS.setdefault(key, threading.RLock())


class AdvancedCognitionRepository:
    def __init__(
        self,
        *,
        run_id: str,
        agent_name: str,
        goal_id: str,
        store: AtomicJsonStore | None = None,
    ):
        self.run_id = run_id
        self.agent_name = agent_name
        self.goal_id = goal_id
        self.store = store or AtomicJsonStore()
        self.root = (
            get_run_dir(run_id) / "agents" / agent_name / goal_id
        )

    def write(self, name: str, value: Any) -> Path:
        path = self.root / name
        self.store.write(path, value)
        return path

    def append(self, name: str, value: Any) -> Path:
        path = self.root / name
        self._append_jsonl(path, value)
        return path

    def append_decision_ledger(self, value: Any) -> Path:
        path = get_run_dir(self.run_id) / "agent_decisions.jsonl"
        self._append_jsonl(path, value)
        return path

    @staticmethod
    def _append_jsonl(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(jsonable(value), ensure_ascii=True, sort_keys=True) + "\n"
        with _lock(path):
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
