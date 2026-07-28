"""Agentic behavior scorecards used by later release gates."""

from __future__ import annotations

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class AgenticScorecard(BaseModel):
    run_id: str
    agent_name: str
    goal_interpretation_accuracy: float = Field(ge=0, le=1)
    input_validation_accuracy: float = Field(ge=0, le=1)
    plan_completeness: float = Field(ge=0, le=1)
    plan_critique_effectiveness: float = Field(ge=0, le=1)
    tool_selection_accuracy: float = Field(ge=0, le=1)
    replan_success_rate: float = Field(ge=0, le=1)
    peer_request_usefulness: float = Field(ge=0, le=1)
    uncertainty_calibration: float = Field(ge=0, le=1)
    completion_proof_accuracy: float = Field(ge=0, le=1)
    decision_explanation_quality: float = Field(ge=0, le=1)
    human_escalation_precision: float = Field(ge=0, le=1)
    schema_version: str = SCHEMA_VERSION

