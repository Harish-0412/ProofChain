"""Risk-aware plan contracts used by the advanced cognition profile."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


SCHEMA_VERSION = "1.0.0"


class AdvancedPlanStep(BaseModel):
    step_id: str
    sequence: int = Field(ge=1)
    objective: str
    preferred_tool: str | None = None
    fallback_tools: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    expected_observations: list[str] = Field(default_factory=list)
    success_condition: str
    failure_condition: str
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    reversible: bool = True
    requires_approval: bool = False
    on_success: str | None = None
    on_failure: str | None = None
    on_uncertainty: str | None = None
    expected_information_gain: float = Field(default=0.5, ge=0, le=1)
    status: Literal[
        "pending", "running", "completed", "failed", "skipped", "waiting"
    ] = "pending"


class AdvancedAgentPlan(BaseModel):
    plan_id: str
    run_id: str
    goal_id: str
    agent_name: str
    revision: int = Field(ge=1)
    rationale: str
    assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    success_condition_coverage: dict[str, list[str]] = Field(default_factory=dict)
    steps: list[AdvancedPlanStep]
    expected_outputs: list[str] = Field(default_factory=list)
    estimated_runtime_seconds: int = Field(default=0, ge=0)
    status: Literal[
        "draft", "critic_rejected", "approved", "executing", "completed", "abandoned"
    ] = "draft"
    schema_version: str = SCHEMA_VERSION

    @model_validator(mode="after")
    def validate_sequence(self) -> "AdvancedAgentPlan":
        sequences = [step.sequence for step in self.steps]
        if sequences != sorted(set(sequences)):
            raise ValueError("Advanced plan steps must have unique ordered sequences.")
        return self

