"""Plan-critic decision contract."""

from __future__ import annotations

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class PlanCritique(BaseModel):
    critique_id: str
    run_id: str
    goal_id: str
    plan_id: str
    plan_revision: int
    approved: bool
    missing_steps: list[str] = Field(default_factory=list)
    unsafe_steps: list[str] = Field(default_factory=list)
    unsupported_assumptions: list[str] = Field(default_factory=list)
    policy_conflicts: list[str] = Field(default_factory=list)
    efficiency_warnings: list[str] = Field(default_factory=list)
    required_revisions: list[str] = Field(default_factory=list)
    critique_confidence: float = Field(ge=0, le=1)
    schema_version: str = SCHEMA_VERSION

