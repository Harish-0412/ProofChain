"""Transactional SQLite/PostgreSQL event store with replayable snapshots."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator
from uuid import uuid4

from proofchain.repositories.json_store import jsonable
from proofchain.schemas.events import WorkflowEvent


ConnectionFactory = Callable[[], Any]


class SqlEventRepository:
    """DB-API event store used directly by SQLite and subclassed for PostgreSQL."""

    placeholder = "?"

    def __init__(self, connection_factory: ConnectionFactory):
        self.connection_factory = connection_factory
        self.ensure_schema()

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        connection = self.connection_factory()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def ensure_schema(self) -> None:
        with self._connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS proofchain_events (
                    event_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_event_id TEXT,
                    previous_event_hash TEXT,
                    event_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    UNIQUE(run_id, sequence)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS proofchain_snapshots (
                    run_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    state_json TEXT NOT NULL,
                    state_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def append_event(self, event: WorkflowEvent) -> WorkflowEvent:
        with self._connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT sequence, event_id, event_hash FROM proofchain_events "
                f"WHERE run_id={self.placeholder} ORDER BY sequence DESC LIMIT 1",
                (event.run_id,),
            )
            row = cursor.fetchone()
            next_sequence = int(row[0]) + 1 if row else 1
            if event.sequence is not None and event.sequence != next_sequence:
                raise ValueError(
                    f"Event sequence conflict: expected {next_sequence}, got {event.sequence}."
                )
            event.sequence = next_sequence
            event.previous_event_id = row[1] if row else None
            event.previous_event_hash = row[2] if row else None
            event.event_hash = self._hash_event(event)
            cursor.execute(
                f"""
                INSERT INTO proofchain_events (
                    event_id, run_id, sequence, event_type, aggregate_type,
                    aggregate_id, actor, payload_json, previous_event_id,
                    previous_event_hash, event_hash, created_at, schema_version
                ) VALUES ({",".join([self.placeholder] * 13)})
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.sequence,
                    event.event_type,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.actor,
                    json.dumps(event.payload, sort_keys=True, default=str),
                    event.previous_event_id,
                    event.previous_event_hash,
                    event.event_hash,
                    event.created_at.isoformat(),
                    event.schema_version,
                ),
            )
        return event

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
        return self.append_event(
            WorkflowEvent(
                event_id=f"EVT-{uuid4().hex[:12].upper()}",
                run_id=run_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                actor=actor,
                payload=payload or {},
            )
        )

    def list(self, run_id: str) -> list[WorkflowEvent]:
        with self._connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                SELECT event_id, run_id, sequence, event_type, aggregate_type,
                       aggregate_id, actor, payload_json, previous_event_id,
                       previous_event_hash, event_hash, created_at, schema_version
                FROM proofchain_events WHERE run_id={self.placeholder}
                ORDER BY sequence
                """,
                (run_id,),
            )
            rows = cursor.fetchall()
        return [
            WorkflowEvent(
                event_id=row[0],
                run_id=row[1],
                sequence=row[2],
                event_type=row[3],
                aggregate_type=row[4],
                aggregate_id=row[5],
                actor=row[6],
                payload=json.loads(row[7]),
                previous_event_id=row[8],
                previous_event_hash=row[9],
                event_hash=row[10],
                created_at=datetime.fromisoformat(row[11]),
                schema_version=row[12],
            )
            for row in rows
        ]

    def import_events(self, events: list[WorkflowEvent]) -> int:
        existing_ids = {event.event_id for event in self.list(events[0].run_id)} if events else set()
        imported = 0
        for source in events:
            if source.event_id in existing_ids:
                continue
            copy = source.model_copy(update={"sequence": None, "event_hash": None})
            self.append_event(copy)
            imported += 1
        return imported

    def create_snapshot(self, run_id: str) -> tuple[int, str]:
        events = self.list(run_id)
        state = self.rebuild_state(run_id)
        state_json = json.dumps(state, sort_keys=True, separators=(",", ":"))
        state_hash = hashlib.sha256(state_json.encode("utf-8")).hexdigest()
        version = len(events)
        with self._connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"DELETE FROM proofchain_snapshots WHERE run_id={self.placeholder}",
                (run_id,),
            )
            cursor.execute(
                f"""
                INSERT INTO proofchain_snapshots
                    (run_id, version, state_json, state_hash, created_at)
                VALUES ({",".join([self.placeholder] * 5)})
                """,
                (
                    run_id,
                    version,
                    state_json,
                    state_hash,
                    datetime.now(tz=timezone.utc).isoformat(),
                ),
            )
        return version, state_hash

    def rebuild_state(self, run_id: str) -> dict[str, Any]:
        aggregates: dict[str, dict[str, Any]] = {}
        for event in self.list(run_id):
            key = f"{event.aggregate_type}:{event.aggregate_id}"
            aggregate = aggregates.setdefault(key, {"version": 0, "events": []})
            aggregate["version"] += 1
            aggregate["events"].append(
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "payload": event.payload,
                }
            )
        return {"run_id": run_id, "aggregates": aggregates}

    def validate_chain(self, run_id: str) -> list[str]:
        errors: list[str] = []
        previous: WorkflowEvent | None = None
        for expected, event in enumerate(self.list(run_id), 1):
            if event.sequence != expected:
                errors.append(f"Event sequence mismatch at {expected}.")
            if previous and event.previous_event_id != previous.event_id:
                errors.append(f"Event link mismatch at {expected}.")
            if previous and event.previous_event_hash != previous.event_hash:
                errors.append(f"Event hash link mismatch at {expected}.")
            if event.event_hash != self._hash_event(event):
                errors.append(f"Event checksum mismatch at {expected}.")
            previous = event
        return errors

    @staticmethod
    def _hash_event(event: WorkflowEvent) -> str:
        payload = jsonable(event)
        payload["event_hash"] = None
        serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SqliteEventRepository(SqlEventRepository):
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(lambda: sqlite3.connect(path))


class PostgresEventRepository(SqlEventRepository):
    placeholder = "%s"

    def __init__(self, database_url: str):
        if not database_url.startswith(("postgresql://", "postgres://")):
            raise ValueError("A PostgreSQL connection URL is required.")
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL support requires: pip install 'proofchain[postgres]'"
            ) from exc
        super().__init__(lambda: psycopg.connect(database_url))

