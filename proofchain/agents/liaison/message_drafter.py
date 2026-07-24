"""Task communication drafting specialist module."""

from __future__ import annotations

import hashlib

from proofchain.schemas.communications import CommunicationRecord
from proofchain.schemas.tasks import ResolutionTask


class MessageDraftingSpecialist:
    specialist_name = "message_drafting"

    def run(self, task: ResolutionTask) -> CommunicationRecord:
        payload = "|".join([task.task_id, task.title, ",".join(task.disclosure_scope)])
        return CommunicationRecord(
            communication_id=f"COM-{task.task_id}",
            task_id=task.task_id,
            message_type="initial_assignment",
            recipient_ids=[task.primary_owner_id],
            channel=task.dispatch_channel,
            content_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            disclosure_fields=task.disclosure_scope,
            approval_event_id=task.approval_event_ids[0] if task.approval_event_ids else None,
            delivery_status="queued" if task.approval_event_ids else "blocked_by_approval",
        )
