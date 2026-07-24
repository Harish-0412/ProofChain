"""Task activation approval gate specialist module."""

from __future__ import annotations

from proofchain.schemas.communications import CommunicationRecord
from proofchain.schemas.tasks import ResolutionTask


class ApprovalGateSpecialist:
    specialist_name = "approval_gate"

    def run(self, task: ResolutionTask, communication: CommunicationRecord) -> tuple[bool, list[str]]:
        blockers = []
        if not task.approval_event_ids:
            blockers.append("Task has no approval event.")
        if task.primary_owner_id == "UNRESOLVED":
            blockers.append("Task has no authorized primary owner.")
        if not communication.disclosure_fields:
            blockers.append("Communication has no approved disclosure scope.")
        return not blockers, blockers
