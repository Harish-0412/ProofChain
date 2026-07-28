"""Standard explainable-decision record."""

from __future__ import annotations

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class DecisionExplanation(BaseModel):
    explanation_id: str
    run_id: str
    goal_id: str
    agent_name: str
    decision: str
    goal: str
    inputs_considered: list[str] = Field(default_factory=list)
    evidence_considered: list[str] = Field(default_factory=list)
    rules_applied: list[str] = Field(default_factory=list)
    policies_applied: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    reason: str
    next_action: str | None = None
    human_approval_required: bool = False
    completion_proof_id: str | None = None
    schema_version: str = SCHEMA_VERSION

