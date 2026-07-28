"""Deterministic telemetry correlation and governed recovery recommendations."""

from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from proofchain.schemas.production import IncidentRecord, TelemetryRecord


def analyze_telemetry(
    telemetry: list[TelemetryRecord], retry_budget: int
) -> tuple[list[IncidentRecord], int, int, list[str]]:
    grouped: dict[str, list[TelemetryRecord]] = defaultdict(list)
    for record in telemetry:
        if record.status != "healthy":
            grouped[record.correlation_id or record.source].append(record)

    incidents: list[IncidentRecord] = []
    retries = 0
    failovers = 0
    paused: list[str] = []
    for records in grouped.values():
        statuses = {record.status for record in records}
        sources = sorted({record.source for record in records})
        critical = "failed" in statuses and any(
            record.attributes.get("integrity_risk") for record in records
        )
        retryable = all(record.retryable for record in records)
        fallback = any(record.attributes.get("fallback_available") for record in records)
        if critical:
            severity = "critical"
            action = "pause"
            paused.extend(sources)
        elif retryable and retries < retry_budget:
            severity = "warning"
            action = "retry"
            retries += 1
        elif fallback:
            severity = "high"
            action = "failover"
            failovers += 1
        else:
            severity = "high"
            action = "human_escalation"
        incidents.append(
            IncidentRecord(
                incident_id=f"INC-{uuid4().hex[:12].upper()}",
                severity=severity,
                affected_sources=sources,
                hypothesis="; ".join(sorted({record.message for record in records})),
                recovery_action=action,
                recovered=action in {"retry", "failover"},
                integrity_verified=not critical,
            )
        )
    return incidents, retries, failovers, sorted(set(paused))

