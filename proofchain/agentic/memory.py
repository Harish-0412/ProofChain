"""Bounded working/run memory without storing unrestricted model reasoning."""

from __future__ import annotations

from typing import Any

from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.schemas.agentic import (
    AgentPlan,
    DecisionRationale,
    Goal,
    Observation,
)


class AgentMemory:
    def __init__(self, repository: JsonCoordinationRepository):
        self.repository = repository

    def checkpoint(
        self,
        *,
        goal: Goal,
        plan: AgentPlan,
        recent_observations: list[Observation],
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.repository.save_working_memory(
            run_id=goal.run_id,
            agent_name=goal.assigned_agent,
            payload={
                "goal_id": goal.goal_id,
                "goal_status": goal.status,
                "plan_id": plan.plan_id,
                "plan_revision": plan.revision,
                "plan_status": plan.status,
                "recent_observation_ids": [
                    item.observation_id for item in recent_observations[-5:]
                ],
                "extra": extra or {},
            },
        )

    def record_rationale(self, rationale: DecisionRationale) -> None:
        self.repository.append_rationale(rationale)
