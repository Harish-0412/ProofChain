"""Controlled dispatch specialist module."""

from __future__ import annotations

from datetime import datetime, timezone

from proofchain.schemas.communications import CommunicationRecord
from proofchain.schemas.tasks import ResolutionTask


class DispatchDeliverySpecialist:
    specialist_name = "dispatch_delivery"

    def run(
        self, task: ResolutionTask, communication: CommunicationRecord, allowed: bool
    ) -> tuple[ResolutionTask, CommunicationRecord]:
        if not allowed:
            return task, communication
        return (
            task.model_copy(update={"delivery_status": "delivered"}),
            communication.model_copy(
                update={"delivery_status": "delivered", "sent_at": datetime.now(tz=timezone.utc)}
            ),
        )
