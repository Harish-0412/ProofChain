"""Immutable context snapshot used for planning."""

from __future__ import annotations

from pydantic import BaseModel, Field

from proofchain.schemas.interpreted_goal import InterpretedGoal


SCHEMA_VERSION = "1.0.0"


class AgentContext(BaseModel):
    run_id: str
    goal_id: str
    agent_name: str
    goal: InterpretedGoal
    relevant_entities: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    applicable_policies: list[str] = Field(default_factory=list)
    applicable_rules: list[str] = Field(default_factory=list)
    prior_observations: list[str] = Field(default_factory=list)
    open_peer_requests: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    validated_case_ids: list[str] = Field(default_factory=list)
    context_completeness: float = Field(ge=0, le=1)
    unresolved_questions: list[str] = Field(default_factory=list)
    policy_fingerprint: str | None = None
    schema_version: str = SCHEMA_VERSION

