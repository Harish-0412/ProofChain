"""Append-only JSONL workflow event repository."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from uuid import uuid4

from proofchain.core.paths import get_workflow_events_path
from proofchain.repositories.json_store import jsonable
from proofchain.schemas.events import WorkflowEvent


_EVENT_LOCKS: dict[str, threading.RLock] = {}
_EVENT_LOCKS_GUARD = threading.Lock()


def _event_lock(run_id: str) -> threading.RLock:
    with _EVENT_LOCKS_GUARD:
        return _EVENT_LOCKS.setdefault(run_id, threading.RLock())


class JsonEventRepository:
    def append(
        self,
        *,
        run_id: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        actor: str = "system",
        payload: dict | None = None,
    ) -> WorkflowEvent:
        path = get_workflow_events_path(run_id)
        with _event_lock(run_id):
            previous = self.list(run_id)
            previous_event = previous[-1] if previous else None
            event = WorkflowEvent(
                event_id=f"EVT-{uuid4().hex[:12].upper()}",
                run_id=run_id,
                sequence=(
                    (previous_event.sequence or len(previous)) + 1
                    if previous_event
                    else 1
                ),
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                actor=actor,
                payload=payload or {},
                previous_event_id=previous_event.event_id if previous_event else None,
                previous_event_hash=previous_event.event_hash if previous_event else None,
            )
            digest_payload = json.dumps(jsonable(event), sort_keys=True, default=str)
            event.event_hash = hashlib.sha256(
                digest_payload.encode("utf-8")
            ).hexdigest()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(
                    json.dumps(jsonable(event), ensure_ascii=True, sort_keys=True)
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        return event

    @staticmethod
    def list(run_id: str) -> list[WorkflowEvent]:
        path = get_workflow_events_path(run_id)
        if not path.exists():
            return []
        events: list[WorkflowEvent] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    events.append(WorkflowEvent.model_validate_json(line))
        return events

    @staticmethod
    def validate_chain(run_id: str) -> list[str]:
        path = get_workflow_events_path(run_id)
        if not path.exists():
            return [f"Workflow event stream missing: {path}"]
        errors: list[str] = []
        previous: dict | None = None
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    event = WorkflowEvent.model_validate(payload)
                except Exception as exc:
                    errors.append(f"Invalid workflow event at line {line_number}: {exc}")
                    continue
                if event.sequence is not None and event.sequence != line_number:
                    errors.append(
                        f"Workflow event sequence mismatch at line {line_number}."
                    )
                if previous is None:
                    if event.previous_event_id is not None:
                        errors.append("First workflow event has a previous_event_id.")
                    if event.previous_event_hash is not None:
                        errors.append("First workflow event has a previous_event_hash.")
                else:
                    if event.previous_event_id != previous.get("event_id"):
                        errors.append(
                            f"Workflow event link mismatch at line {line_number}."
                        )
                    if (
                        event.previous_event_hash is not None
                        and event.previous_event_hash != previous.get("event_hash")
                    ):
                        errors.append(
                            f"Workflow event hash link mismatch at line {line_number}."
                        )
                claimed_hash = payload.get("event_hash")
                hash_payload = dict(payload)
                hash_payload["event_hash"] = None
                digest_payload = json.dumps(
                    hash_payload,
                    ensure_ascii=True,
                    sort_keys=True,
                    default=str,
                )
                expected_hash = hashlib.sha256(
                    digest_payload.encode("utf-8")
                ).hexdigest()
                if claimed_hash != expected_hash:
                    errors.append(
                        f"Workflow event checksum mismatch at line {line_number}."
                    )
                previous = payload
        return errors
