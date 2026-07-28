"""Cognition profile, state transition, and core precision assessment."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class CognitionProfile(BaseModel):
    profile_version: str
    profile_name: str
    goal_interpretation_required: bool
    input_gate_required: bool
    context_required: bool
    hypotheses_required: bool
    plan_critique_required: bool
    normalized_observations_required: bool
    structured_reflection_required: bool
    uncertainty_proof_required: bool
    completion_proof_required: bool
    decision_explanation_required: bool
    schema_version: str = SCHEMA_VERSION


class AgentStateTransition(BaseModel):
    transition_id: str
    run_id: str
    goal_id: str
    agent_name: str
    from_state: str | None = None
    to_state: Literal[
        "CREATED",
        "INTERPRETING_GOAL",
        "VALIDATING_INPUTS",
        "BUILDING_CONTEXT",
        "FORMING_HYPOTHESES",
        "PLANNING",
        "CRITIQUING_PLAN",
        "EXECUTING",
        "OBSERVING",
        "REFLECTING",
        "WAITING_FOR_PEER",
        "WAITING_FOR_HUMAN",
        "REPLANNING",
        "VERIFYING_COMPLETION",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "BLOCKED",
        "FAILED",
        "CANCELLED",
    ]
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION


class NormalizedToolObservation(BaseModel):
    observation_id: str
    run_id: str
    goal_id: str
    agent_name: str
    plan_step_id: str
    source_tool: str
    source_version: str
    summary: str
    structured_data: dict[str, Any] = Field(default_factory=dict)
    source_references: list[str] = Field(default_factory=list)
    data_quality: Literal["high", "medium", "low", "invalid"]
    confidence: float = Field(ge=0, le=1)
    contradictions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    sufficient_for_step: bool
    schema_version: str = SCHEMA_VERSION


class StructuredReflection(BaseModel):
    reflection_id: str
    run_id: str
    goal_id: str
    agent_name: str
    plan_revision: int
    new_facts: list[str] = Field(default_factory=list)
    hypotheses_supported: list[str] = Field(default_factory=list)
    hypotheses_rejected: list[str] = Field(default_factory=list)
    success_conditions_met: list[str] = Field(default_factory=list)
    success_conditions_remaining: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    decision: Literal[
        "continue",
        "retry",
        "replan",
        "ask_peer",
        "ask_human",
        "complete",
        "block",
        "fail",
    ]
    reason_summary: str
    confidence: float = Field(ge=0, le=1)
    schema_version: str = SCHEMA_VERSION


class CorePrecisionAssessment(BaseModel):
    run_id: str
    goal_id: str
    agent_name: str
    unique_feature: str
    feature_status: Literal["satisfied", "partial", "blocked"]
    metrics: dict[str, Any] = Field(default_factory=dict)
    coverage: list[dict[str, Any]] = Field(default_factory=list)
    lineage: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    completion_requirements: list[str] = Field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
