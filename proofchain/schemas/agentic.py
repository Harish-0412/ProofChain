"""Typed contracts for ProofChain's governed agentic control layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


SCHEMA_VERSION = "1.0.0"

GoalStatus = Literal[
    "created",
    "planning",
    "executing",
    "waiting_on_peer",
    "needs_human_review",
    "blocked",
    "completed",
    "failed",
    "waiting_for_approval",
    "waiting_for_task_acknowledgement",
    "waiting_for_evidence_submission",
    "waiting_for_human_review",
    "waiting_for_external_system",
    "cancelled",
]
TerminalStatus = Literal[
    "completed",
    "completed_with_warnings",
    "blocked",
    "needs_human_review",
    "failed",
    "cancelled",
]


class Goal(BaseModel):
    goal_id: str
    run_id: str
    parent_goal_id: str | None = None
    assigned_agent: str
    objective: str
    goal_type: str
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    input_references: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    success_conditions: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    status: GoalStatus = "created"
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    deadline: datetime | None = None
    schema_version: str = SCHEMA_VERSION


class PlanStep(BaseModel):
    step_id: str
    sequence: int = Field(ge=1)
    objective: str
    proposed_tool: str | None = None
    required_inputs: list[str] = Field(default_factory=list)
    expected_observation: str
    completion_condition: str
    status: Literal[
        "pending", "running", "completed", "failed", "skipped", "waiting"
    ] = "pending"


class AgentPlan(BaseModel):
    plan_id: str
    run_id: str
    goal_id: str
    agent_name: str
    revision: int = Field(default=1, ge=1)
    rationale: str
    steps: list[PlanStep]
    assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    status: Literal[
        "draft", "approved", "executing", "replanning", "completed", "abandoned"
    ] = "draft"
    schema_version: str = SCHEMA_VERSION

    @model_validator(mode="after")
    def validate_step_sequence(self) -> "AgentPlan":
        sequences = [step.sequence for step in self.steps]
        if sequences != sorted(set(sequences)):
            raise ValueError("Plan step sequence values must be unique and ordered.")
        return self


class Observation(BaseModel):
    observation_id: str
    run_id: str
    goal_id: str
    agent_name: str
    plan_step_id: str
    observation_type: str
    summary: str
    structured_data: dict[str, Any] = Field(default_factory=dict)
    source_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty_reasons: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION


class ActionProposal(BaseModel):
    action_id: str
    run_id: str
    goal_id: str
    agent_name: str
    action_type: str
    selected_tool: str
    step_id: str | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    alternatives: list[str] = Field(default_factory=list)
    reason: str
    expected_effect: str
    expected_information_gain: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high"] = "low"
    reversible: bool = True
    requires_approval: bool = False
    schema_version: str = SCHEMA_VERSION


class ReflectionDecision(BaseModel):
    reflection_id: str
    run_id: str
    goal_id: str
    agent_name: str
    plan_revision: int = Field(ge=1)
    observations_considered: list[str]
    progress_assessment: str
    confidence: float = Field(ge=0.0, le=1.0)
    decision: Literal[
        "continue", "retry", "replan", "request_peer", "request_human", "complete", "block"
    ]
    reason: str
    next_action: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION


class CoordinationMessage(BaseModel):
    message_id: str
    run_id: str
    goal_id: str
    source_agent: str
    target_agent: str
    message_type: Literal[
        "information_request",
        "reclassification_request",
        "additional_evidence_request",
        "verification_request",
        "conflict_notification",
        "completion_notification",
    ]
    reason: str
    related_evidence_ids: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    status: Literal[
        "open", "accepted", "in_progress", "resolved", "rejected", "expired"
    ] = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    resolved_at: datetime | None = None
    resolution: str | None = None
    schema_version: str = SCHEMA_VERSION


class CompletionDecision(BaseModel):
    decision_id: str
    run_id: str
    goal_id: str
    agent_name: str
    goal_satisfied: bool
    success_conditions_met: list[str] = Field(default_factory=list)
    success_conditions_unmet: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    final_status: TerminalStatus
    explanation: str
    supporting_artifacts: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION

    @model_validator(mode="after")
    def validate_claim(self) -> "CompletionDecision":
        if self.goal_satisfied and self.final_status in {
            "blocked",
            "needs_human_review",
            "failed",
        }:
            raise ValueError("A satisfied goal cannot have a negative terminal status.")
        if not self.explanation.strip():
            raise ValueError("Completion decisions require an explanation.")
        return self


class AgentBudget(BaseModel):
    max_plan_revisions: int = Field(default=3, ge=1)
    max_action_rounds: int = Field(default=10, ge=1)
    max_tool_retries_per_step: int = Field(default=2, ge=0)
    max_peer_requests: int = Field(default=4, ge=0)
    max_runtime_seconds: int = Field(default=180, ge=1)


class ToolResult(BaseModel):
    tool_name: str
    tool_version: str = "1.0.0"
    status: Literal["success", "partial", "failed"]
    output: dict[str, Any] = Field(default_factory=dict)
    source_references: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    execution_time_ms: int = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class DecisionRationale(BaseModel):
    run_id: str
    goal_id: str
    agent_name: str
    decision: str
    evidence_considered: list[str] = Field(default_factory=list)
    rules_applied: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    justification: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION


class CoordinationState(BaseModel):
    run_id: str
    top_level_goal_id: str
    active_goals: list[str] = Field(default_factory=list)
    completed_goals: list[str] = Field(default_factory=list)
    blocked_goals: list[str] = Field(default_factory=list)
    human_review_goals: list[str] = Field(default_factory=list)
    current_plans: dict[str, str] = Field(default_factory=dict)
    open_messages: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    completion_claims: list[str] = Field(default_factory=list)
    state_version: int = Field(default=1, ge=1)
    supervisor_round: int = Field(default=0, ge=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION


class CoordinationPatch(BaseModel):
    activate_goals: list[str] = Field(default_factory=list)
    complete_goals: list[str] = Field(default_factory=list)
    block_goals: list[str] = Field(default_factory=list)
    human_review_goals: list[str] = Field(default_factory=list)
    current_plans: dict[str, str] = Field(default_factory=dict)
    add_open_messages: list[str] = Field(default_factory=list)
    resolve_messages: list[str] = Field(default_factory=list)
    add_questions: list[str] = Field(default_factory=list)
    resolve_questions: list[str] = Field(default_factory=list)
    add_blockers: list[str] = Field(default_factory=list)
    resolve_blockers: list[str] = Field(default_factory=list)
    add_completion_claims: list[str] = Field(default_factory=list)
    supervisor_round_increment: int = Field(default=0, ge=0)


class GoalGraph(BaseModel):
    run_id: str
    top_level_goal_id: str
    goals: list[Goal]
    schema_version: str = SCHEMA_VERSION


class AgenticRunSummary(BaseModel):
    run_id: str
    top_level_goal_id: str
    supervisor_rounds: int
    goals_total: int
    goals_completed: int
    goals_blocked: int
    open_messages: int
    final_status: TerminalStatus
    final_decision_path: str
