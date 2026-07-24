"""Resolution task composition specialist module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from proofchain.schemas.gaps import GapResolutionPlan, ResolutionGap
from proofchain.schemas.issues import CanonicalIssue
from proofchain.schemas.ownership import OwnershipAssignment
from proofchain.schemas.tasks import ResolutionTask


class TaskCompositionSpecialist:
    specialist_name = "task_composition"

    def run(
        self,
        *,
        issue: CanonicalIssue,
        gap: ResolutionGap,
        plan: GapResolutionPlan,
        assignment: OwnershipAssignment,
        disclosure_scope: list[str],
        approval_event_ids: list[str],
    ) -> ResolutionTask:
        strategy = next(
            item for item in plan.strategies if item.strategy_id == plan.recommended_strategy_id
        )
        primary = assignment.primary_owner.user_id if assignment.primary_owner else "UNRESOLVED"
        return ResolutionTask(
            task_id=f"TASK-{gap.gap_id}",
            issue_id=issue.issue_id,
            gap_id=gap.gap_id,
            approved_strategy_id=strategy.strategy_id,
            primary_owner_id=primary,
            backup_owner_id=assignment.backup_owner.user_id if assignment.backup_owner else None,
            approver_id=assignment.approver.user_id if assignment.approver else None,
            title=strategy.title,
            objective=gap.description,
            required_actions=strategy.actions,
            required_closure_evidence=plan.required_completion_evidence,
            priority="critical" if gap.blocking else "medium",
            due_at=datetime.now(tz=timezone.utc) + timedelta(days=3 if gap.blocking else 7),
            status="approval_required" if not approval_event_ids else "active",
            disclosure_scope=disclosure_scope,
            approval_event_ids=approval_event_ids,
            delivery_status="queued" if approval_event_ids else "not_sent",
        )
