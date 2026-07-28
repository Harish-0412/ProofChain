"""Machine-readable proof that a goal may terminate."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class CompletionConditionResult(BaseModel):
    condition: str
    evaluated: bool
    satisfied: bool
    evidence: list[str] = Field(default_factory=list)
    explanation: str


class CompletionProof(BaseModel):
    proof_id: str
    run_id: str
    goal_id: str
    agent_name: str
    all_success_conditions_evaluated: bool
    condition_results: list[CompletionConditionResult]
    mandatory_inputs_valid: bool
    output_schema_valid: bool
    unresolved_blockers: list[str] = Field(default_factory=list)
    unresolved_peer_requests: list[str] = Field(default_factory=list)
    policy_conflicts: list[str] = Field(default_factory=list)
    artifact_references: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    rule_references: list[str] = Field(default_factory=list)
    completion_confidence: float = Field(ge=0, le=1)
    proof_valid: bool
    final_status: Literal[
        "completed",
        "completed_with_warnings",
        "blocked",
        "needs_human_review",
        "failed",
        "cancelled",
    ]
    proof_metadata: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

