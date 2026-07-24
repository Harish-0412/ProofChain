"""Specialist that creates severity-aware escalation paths."""

from __future__ import annotations

from proofchain.schemas.gaps import ResolutionPortfolio
from proofchain.schemas.ownership import EscalationStep


class EscalationPlanningSpecialist:
    specialist_name = "escalation_planning"
    goal = "Create controlled escalation recommendations without sending messages."

    def run(self, portfolio: ResolutionPortfolio) -> dict[str, list[EscalationStep]]:
        results = {}
        for gap in portfolio.gaps:
            first = 24 if gap.blocking else 48
            results[gap.gap_id] = [
                EscalationStep(
                    level=1,
                    after_hours=first,
                    target_role="Department Accreditation Coordinator",
                    action="recommend_reminder",
                ),
                EscalationStep(
                    level=2,
                    after_hours=first * 2,
                    target_role="Head of Department",
                    action="recommend_delay_review",
                ),
                EscalationStep(
                    level=3,
                    after_hours=first * 3,
                    target_role="IQAC Coordinator",
                    action="request_human_intervention",
                ),
            ]
        return results
