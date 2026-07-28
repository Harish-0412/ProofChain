"""Append-only cognition state machine."""

from __future__ import annotations

from uuid import uuid4

from proofchain.repositories.advanced_cognition_repository import (
    AdvancedCognitionRepository,
)
from proofchain.schemas.cognition import AgentStateTransition


class AgentCognitionStateMachine:
    def __init__(
        self,
        repository: AdvancedCognitionRepository,
        *,
        run_id: str,
        goal_id: str,
        agent_name: str,
    ):
        self.repository = repository
        self.run_id = run_id
        self.goal_id = goal_id
        self.agent_name = agent_name
        self.current_state: str | None = None

    def transition(self, state: str, reason: str) -> AgentStateTransition:
        record = AgentStateTransition(
            transition_id=f"STA-{uuid4().hex[:12].upper()}",
            run_id=self.run_id,
            goal_id=self.goal_id,
            agent_name=self.agent_name,
            from_state=self.current_state,
            to_state=state,
            reason=reason,
        )
        self.repository.append("state_transitions.jsonl", record)
        self.current_state = state
        return record
