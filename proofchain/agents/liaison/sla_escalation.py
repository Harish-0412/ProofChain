"""SLA and escalation monitoring specialist module."""

from __future__ import annotations

from datetime import datetime, timezone

from proofchain.schemas.tasks import ResolutionTask


class SlaEscalationSpecialist:
    specialist_name = "sla_escalation"

    def run(self, tasks: list[ResolutionTask]) -> list[str]:
        now = datetime.now(tz=timezone.utc)
        return [
            task.task_id
            for task in tasks
            if task.due_at < now and task.status not in {"closed", "evidence_submitted"}
        ]
