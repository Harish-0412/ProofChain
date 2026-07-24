"""Least-disclosure communication scope specialist module."""

from __future__ import annotations

from proofchain.schemas.issues import CanonicalIssue
from proofchain.schemas.ownership import OwnershipAssignment


class CommunicationScopeSpecialist:
    specialist_name = "communication_scope"

    def run(
        self,
        issue: CanonicalIssue,
        assignment: OwnershipAssignment,
    ) -> list[str]:
        fields = ["task_id", "gap_id", "required_action", "closure_evidence", "deadline"]
        if assignment.primary_owner and "approve" in assignment.primary_owner.role.lower():
            fields.append("approval_context")
        if issue.blocking:
            fields.append("blocking_status")
        if issue.affected_requirement_ids:
            fields.append("requirement_id")
        return fields
