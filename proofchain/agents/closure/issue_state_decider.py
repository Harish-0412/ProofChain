"""Issue state transition specialist module."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.closure import ClosureCheck
from proofchain.schemas.issues import CanonicalIssue, IssueTransition


class IssueStateDecisionSpecialist:
    specialist_name = "issue_state_decider"

    def run(
        self, issues: list[CanonicalIssue], checks: list[ClosureCheck]
    ) -> tuple[list[CanonicalIssue], list[IssueTransition]]:
        check_by_issue = {check.issue_id: check for check in checks}
        updated = []
        transitions = []
        for issue in issues:
            check = check_by_issue.get(issue.issue_id)
            if not check:
                updated.append(issue)
                continue
            to_status = {
                "resolved": "RESOLVED",
                "rejected": "REJECTED",
                "under_revalidation": "UNDER_REVALIDATION",
                "waiting_for_evidence": "ASSIGNED_PENDING_APPROVAL",
            }[check.status]
            if issue.status == "RESOLVED" and check.status != "resolved":
                to_status = "REOPENED"
            updated_issue = issue.model_copy(update={"status": to_status}, deep=True)
            updated.append(updated_issue)
            transitions.append(
                IssueTransition(
                    transition_id=f"TRANS-{uuid4().hex[:12].upper()}",
                    run_id=issue.run_id,
                    issue_id=issue.issue_id,
                    from_status=issue.status,
                    to_status=to_status,
                    reason="; ".join(check.reasons) or "Closure policy satisfied.",
                )
            )
        return updated, transitions
