"""Normalized goal interpretation contract."""

from __future__ import annotations

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class InterpretedGoal(BaseModel):
    goal_id: str
    run_id: str
    normalized_objective: str
    subject_entities: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    prohibited_actions: list[str] = Field(default_factory=list)
    success_conditions: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)
    ambiguity_flags: list[str] = Field(default_factory=list)
    clarification_required: bool = False
    interpretation_confidence: float = Field(ge=0, le=1)
    policy_version_known: bool = False
    scope_complete: bool = False
    schema_version: str = SCHEMA_VERSION

