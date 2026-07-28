"""Decomposed uncertainty and automatic-action policy."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class UncertaintyAssessment(BaseModel):
    assessment_id: str
    run_id: str
    goal_id: str
    agent_name: str
    plan_step_id: str | None = None
    input_confidence: float = Field(ge=0, le=1)
    tool_confidence: float = Field(ge=0, le=1)
    interpretation_confidence: float = Field(ge=0, le=1)
    decision_confidence: float = Field(ge=0, le=1)
    completion_confidence: float = Field(ge=0, le=1)
    uncertainty_types: list[
        Literal[
            "input",
            "extraction",
            "classification",
            "rule",
            "policy",
            "identity",
            "ownership",
            "temporal",
            "source_authority",
            "completion",
        ]
    ] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    recommended_action: Literal[
        "continue",
        "continue_with_warning",
        "retrieve_or_ask_peer",
        "request_human",
        "prohibit_positive_decision",
    ]
    deterministic_block: bool = False
    schema_version: str = SCHEMA_VERSION

    @property
    def aggregate_confidence(self) -> float:
        values = [
            self.input_confidence,
            self.tool_confidence,
            self.interpretation_confidence,
            self.decision_confidence,
            self.completion_confidence,
        ]
        return sum(values) / len(values)

