"""Create and update explicit competing hypotheses."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.agent_context import AgentContext
from proofchain.schemas.agentic import Goal
from proofchain.schemas.cognition import NormalizedToolObservation
from proofchain.schemas.hypotheses import Hypothesis


class HypothesisManager:
    def form(self, goal: Goal, context: AgentContext) -> list[Hypothesis]:
        return [
            Hypothesis(
                hypothesis_id=f"HYP-{uuid4().hex[:12].upper()}",
                run_id=goal.run_id,
                goal_id=goal.goal_id,
                statement="Available inputs are sufficient to satisfy the governed goal.",
                assumptions=["Validated inputs accurately represent the current scope."],
                confidence=context.context_completeness,
                status="proposed",
                discriminating_actions=["Execute the approved deterministic stage."],
            ),
            Hypothesis(
                hypothesis_id=f"HYP-{uuid4().hex[:12].upper()}",
                run_id=goal.run_id,
                goal_id=goal.goal_id,
                statement="Missing, contradictory, or low-quality evidence prevents completion.",
                assumptions=["At least one required condition may remain unproven."],
                confidence=1.0 - context.context_completeness,
                status="unresolved",
                discriminating_actions=["Evaluate completion conditions and blockers."],
            ),
        ]

    def update(
        self,
        hypotheses: list[Hypothesis],
        observation: NormalizedToolObservation,
    ) -> list[Hypothesis]:
        if not hypotheses:
            return hypotheses
        sufficient = observation.sufficient_for_step and not observation.contradictions
        hypotheses[0].status = "supported" if sufficient else "weakened"
        hypotheses[0].confidence = observation.confidence
        hypotheses[0].supporting_observations = (
            [observation.observation_id] if sufficient else []
        )
        hypotheses[0].contradicting_observations = (
            [] if sufficient else [observation.observation_id]
        )
        hypotheses[1].status = "weakened" if sufficient else "supported"
        hypotheses[1].confidence = 1.0 - observation.confidence
        return hypotheses
