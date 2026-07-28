"""Agent 11: durable event persistence, snapshot reconstruction, and recovery."""

from __future__ import annotations

import hashlib
import json

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.core.paths import get_run_dir
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.sql_event_repository import (
    PostgresEventRepository,
    SqliteEventRepository,
)
from proofchain.schemas.production import PersistenceInput, PersistenceResult


class OperationalPersistenceAgent(
    ProductionGoalAgent[PersistenceInput, PersistenceResult]
):
    agent_name = "operational_persistence"
    agent_version = "1.0.0"
    expected_artifact = "persistence_recovery_report.json"
    tool_specs = (
        (
            "check_database_health",
            "Verify the configured operational event store.",
            "The database schema is reachable and transactional.",
        ),
        (
            "reconcile_event_stream",
            "Import missing append-only workflow events.",
            "Every source event is durably represented once.",
        ),
        (
            "rebuild_and_validate_state",
            "Rebuild snapshots and validate sequence and hash links.",
            "State reconstruction and integrity checks complete.",
        ),
        (
            "evaluate_persistence_completion",
            "Evaluate persistence and recovery completion conditions.",
            "A persisted recovery report is produced.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._check_database(input_data)
        self._reconcile(input_data)
        self._rebuild(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "check_database_health": lambda: self._check_database(input_data),
            "reconcile_event_stream": lambda: self._reconcile(input_data),
            "rebuild_and_validate_state": lambda: self._rebuild(input_data),
            "evaluate_persistence_completion": lambda: self._complete(input_data),
        }

    def _repository(self, input_data):
        if "repository" not in self._state:
            if input_data.backend == "postgres":
                if not input_data.database_url:
                    raise ValueError("database_url is required for PostgreSQL.")
                repository = PostgresEventRepository(input_data.database_url)
            else:
                repository = SqliteEventRepository(
                    get_run_dir(input_data.workflow.run_id) / "operational_state.db"
                )
            self._state["repository"] = repository
        return self._state["repository"]

    def _check_database(self, input_data):
        repository = self._repository(input_data)
        repository.ensure_schema()
        self._state["health"] = "healthy"
        return {"status": "completed", "backend": input_data.backend}

    def _reconcile(self, input_data):
        source_events = JsonEventRepository.list(input_data.workflow.run_id)
        repository = self._repository(input_data)
        imported = repository.import_events(source_events)
        self._state["source_events"] = source_events
        self._state["imported"] = imported
        return {
            "status": "completed",
            "source_events": len(source_events),
            "imported": imported,
        }

    def _rebuild(self, input_data):
        repository = self._repository(input_data)
        version, state_hash = repository.create_snapshot(input_data.workflow.run_id)
        errors = repository.validate_chain(input_data.workflow.run_id)
        source_state = self._state_from_events(self._state.get("source_events", []))
        source_hash = hashlib.sha256(
            json.dumps(source_state, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self._state.update(
            {
                "version": version,
                "state_hash": state_hash,
                "source_hash": source_hash,
                "errors": errors,
            }
        )
        return {"status": "failed" if errors else "completed", "errors": errors}

    def _complete(self, input_data):
        errors = self._state.get("errors", [])
        parity = self._state.get("state_hash") == self._state.get("source_hash")
        warnings = [] if parity else ["Reconstructed state differs from the JSON event source."]
        result = PersistenceResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="failed" if errors else "completed_with_warnings" if warnings else "completed",
            backend=input_data.backend,
            database_health=self._state.get("health", "unavailable"),
            imported_events=self._state.get("imported", 0),
            persisted_events=self._state.get("version", 0),
            snapshot_version=self._state.get("version", 0),
            reconstructed_state_hash=self._state.get("state_hash"),
            source_state_hash=self._state.get("source_hash"),
            recovery_verified=not errors and (parity or not input_data.verify_recovery),
            corruption_findings=errors,
            input_count=len(self._state.get("source_events", [])),
            success_count=self._state.get("version", 0),
            warning_count=len(warnings),
            failure_count=len(errors),
            warnings=warnings,
            errors=errors,
        )
        return self._persist(result)

    @staticmethod
    def _state_from_events(events):
        aggregates = {}
        for event in events:
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
        return {"run_id": events[0].run_id if events else None, "aggregates": aggregates}

