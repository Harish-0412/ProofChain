"""Specialist that prioritizes gaps using governed weighted factors."""

from __future__ import annotations

from proofchain.schemas.gaps import GapResolutionPlan, PrioritizedGap, ResolutionGap


class GapPrioritizationSpecialist:
    specialist_name = "gap_prioritization"
    goal = "Order gaps by severity, blocking impact, dependencies, and feasibility."

    def run(
        self, gaps: list[ResolutionGap], plans: list[GapResolutionPlan]
    ) -> list[PrioritizedGap]:
        plan_by_gap = {plan.gap_id: plan for plan in plans}
        priorities = []
        severity_score = {"critical": 100, "high": 80, "medium": 55, "low": 25}
        for gap in gaps:
            plan = plan_by_gap[gap.gap_id]
            best_confidence = max(
                item.expected_resolution_confidence for item in plan.strategies
            )
            score = (
                0.30 * severity_score[gap.severity]
                + 0.25 * (100 if gap.blocking else 20)
                + 0.15 * (85 if gap.blocking else 40)
                + 0.10 * min(100, len(gap.affected_claims) * 25)
                + 0.10 * best_confidence * 100
                + 0.10 * 50
            )
            score = round(min(100.0, score), 2)
            priority = (
                "critical"
                if score >= 85
                else "high"
                if score >= 70
                else "medium"
                if score >= 45
                else "low"
            )
            priorities.append(
                PrioritizedGap(
                    gap_id=gap.gap_id,
                    priority_score=score,
                    priority=priority,
                    reason=(
                        f"severity={gap.severity}, blocking={gap.blocking}, "
                        f"affected_claims={len(gap.affected_claims)}"
                    ),
                )
            )
        return sorted(priorities, key=lambda item: (-item.priority_score, item.gap_id))
