"""Specialist that estimates readiness deltas without marking gaps resolved."""

from __future__ import annotations

from proofchain.schemas.gaps import (
    GapResolutionPlan,
    ReadinessScenario,
    ReadinessSimulation,
    ResolutionGap,
)


class ReadinessSimulationSpecialist:
    specialist_name = "readiness_simulation"
    goal = "Estimate the readiness effect of each proposed strategy."

    def run(
        self,
        gaps: list[ResolutionGap],
        plans: list[GapResolutionPlan],
        current_readiness: float,
    ) -> tuple[list[ResolutionGap], list[GapResolutionPlan], ReadinessSimulation]:
        gap_by_id = {gap.gap_id: gap for gap in gaps}
        remaining_blockers = sum(gap.blocking for gap in gaps)
        scenarios = []
        total_delta = 0.0
        updated_plans = []
        for plan in plans:
            gap = gap_by_id[plan.gap_id]
            base = {"critical": 16.0, "high": 12.0, "medium": 7.0, "low": 3.0}[gap.severity]
            if gap.blocking:
                base += 4.0
            delta = min(base, max(0.0, 100.0 - current_readiness))
            total_delta += delta
            gap.readiness_impact = delta
            updated_plans.append(
                plan.model_copy(update={"expected_readiness_delta": delta}, deep=True)
            )
            for strategy in plan.strategies:
                scenarios.append(
                    ReadinessScenario(
                        gap_id=gap.gap_id,
                        strategy_id=strategy.strategy_id,
                        expected_readiness=min(100.0, current_readiness + delta),
                        readiness_delta=delta,
                        remaining_blockers=max(
                            0, remaining_blockers - (1 if gap.blocking else 0)
                        ),
                    )
                )
        return (
            gaps,
            updated_plans,
            ReadinessSimulation(
                current_readiness=current_readiness,
                projected_readiness=min(
                    96.0 if gaps else 100.0,
                    current_readiness + total_delta,
                ),
                unresolved_dependencies=list(
                    dict.fromkeys(
                        dependency
                        for plan in updated_plans
                        for dependency in plan.dependencies
                    )
                ),
                scenario_bands={
                    "conservative": round(
                        min(100.0, current_readiness + total_delta * 0.5), 2
                    ),
                    "expected": round(
                        min(96.0 if gaps else 100.0, current_readiness + total_delta),
                        2,
                    ),
                    "optimistic": round(
                        min(100.0, current_readiness + total_delta * 1.1), 2
                    ),
                },
                scenarios=scenarios,
            ),
        )
