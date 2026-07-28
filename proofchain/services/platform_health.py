"""Platform health checks separated from accreditation readiness decisions."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from proofchain.agentic.agentic_run_validator import AgenticRunValidator
from proofchain.core.paths import OUTPUTS_DIR, RUNS_DIR
from proofchain.services.ingestion_capabilities import IngestionCapabilityService
from proofchain.services.run_projection import RunProjectionService


class PlatformHealthService:
    def __init__(self, runs_dir: Path | None = None):
        self.runs_dir = (runs_dir or RUNS_DIR).resolve()
        self.projections = RunProjectionService(self.runs_dir)

    def inspect(self, run_id: str | None = None) -> dict[str, Any]:
        selected = run_id or self._latest_run_id()
        checks = [
            self._check(
                "artifact_store",
                OUTPUTS_DIR.is_dir(),
                f"{OUTPUTS_DIR.resolve()}",
            ),
            self._check(
                "ingestion_registry",
                bool(IngestionCapabilityService().report().native_extensions),
                "Explicit native, metadata-only, unsupported, and rejected outcomes.",
            ),
        ]
        if selected:
            checks.extend(
                [
                    self._proof_check(selected),
                    self._event_check(selected),
                    self._database_check(selected),
                    self._artifact_status_check(
                        selected,
                        "notification_delivery_report.json",
                        "notification_delivery",
                    ),
                    self._artifact_status_check(
                        selected,
                        "external_submission_report.json",
                        "submission_adapter",
                        domain_refusal_is_healthy=True,
                    ),
                    self._artifact_status_check(
                        selected,
                        "incident_reliability_report.json",
                        "reliability_monitor",
                    ),
                ]
            )
        else:
            checks.append(
                {
                    "name": "latest_run",
                    "status": "warning",
                    "healthy": False,
                    "detail": "No completed run is available for run-scoped checks.",
                }
            )
        failures = [item for item in checks if item["status"] == "error"]
        warnings = [item for item in checks if item["status"] == "warning"]
        return {
            "status": "unhealthy" if failures else "degraded" if warnings else "healthy",
            "runId": selected,
            "checks": checks,
            "summary": {
                "passed": sum(item["status"] == "healthy" for item in checks),
                "warnings": len(warnings),
                "failed": len(failures),
            },
            "domainReadinessIsSeparate": True,
        }

    def _latest_run_id(self) -> str | None:
        runs = self.projections.list_runs()
        return runs[0]["id"] if runs else None

    @staticmethod
    def _check(name: str, healthy: bool, detail: str) -> dict[str, Any]:
        return {
            "name": name,
            "status": "healthy" if healthy else "error",
            "healthy": healthy,
            "detail": detail,
        }

    def _proof_check(self, run_id: str) -> dict[str, Any]:
        try:
            result = AgenticRunValidator().validate(run_id)
        except Exception as exc:
            return self._check("agentic_proofs", False, str(exc))
        return self._check(
            "agentic_proofs",
            bool(result.get("valid")),
            (
                "All required cognition and completion-proof links validate."
                if result.get("valid")
                else "; ".join(result.get("errors", [])[:5])
            ),
        )

    def _event_check(self, run_id: str) -> dict[str, Any]:
        events = self.projections.events(run_id, limit=1000)
        valid = bool(events)
        for previous, current in zip(events, events[1:]):
            if current.get("previousEventHash") != previous.get("eventHash"):
                valid = False
                break
        return self._check(
            "event_chain",
            valid,
            f"{len(events)} hash-linked workflow events inspected.",
        )

    def _database_check(self, run_id: str) -> dict[str, Any]:
        path = self.runs_dir / run_id / "operational_state.db"
        if not path.is_file():
            return self._check("operational_database", False, "Database artifact is missing.")
        try:
            connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
            connection.execute("PRAGMA integrity_check").fetchone()
            connection.close()
        except sqlite3.Error as exc:
            return self._check("operational_database", False, str(exc))
        return self._check(
            "operational_database",
            True,
            "SQLite operational state opened read-only and passed integrity inspection.",
        )

    def _artifact_status_check(
        self,
        run_id: str,
        filename: str,
        name: str,
        *,
        domain_refusal_is_healthy: bool = False,
    ) -> dict[str, Any]:
        payload = self.projections.raw(run_id, filename, None)
        if payload is None:
            return {
                "name": name,
                "status": "warning",
                "healthy": False,
                "detail": f"{filename} is not present for this run.",
            }
        status = payload.get("status", "unknown") if isinstance(payload, dict) else "unknown"
        healthy = status not in {"failed"}
        if domain_refusal_is_healthy and status == "completed_with_warnings":
            healthy = True
        return {
            "name": name,
            "status": "healthy" if healthy else "error",
            "healthy": healthy,
            "detail": (
                f"Artifact status={status}. A governed domain refusal is not a service failure."
                if domain_refusal_is_healthy
                else f"Artifact status={status}."
            ),
        }
