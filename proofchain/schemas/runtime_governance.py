"""Contracts for policy, scheduler, model-governance, and observability artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class PolicyFileRecord(BaseModel):
    policy_id: str
    path: str
    sha256: str
    schema_version: str


class GovernancePolicyManifest(BaseModel):
    run_id: str
    policy_set_version: str = "1.0.0"
    policy_fingerprint: str
    policies: list[PolicyFileRecord]
    loaded_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class AgentExecutionProfile(BaseModel):
    agent_name: str
    execution_mode: Literal["deterministic", "model_assisted", "human"]
    model_provider: str | None = None
    model_id: str | None = None
    prompt_version: str | None = None
    external_model_calls: int = 0
    high_impact_actions_require_approval: bool = True
    fallback_behavior: Literal["block", "request_human", "deterministic_only"] = "block"


class ModelGovernanceManifest(BaseModel):
    run_id: str
    policy_fingerprint: str
    profiles: list[AgentExecutionProfile]
    total_external_model_calls: int = 0
    generated_content_is_evidence: bool = False
    unconfigured_model_use_is_blocked: bool = True
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class SupervisorRoundRecord(BaseModel):
    run_id: str
    round_number: int = Field(ge=0)
    phase: Literal["preflight", "coordination", "terminal"]
    goal_status_counts: dict[str, int] = Field(default_factory=dict)
    runnable_goal_ids: list[str] = Field(default_factory=list)
    waiting_goal_ids: list[str] = Field(default_factory=list)
    blocked_dependency_goal_ids: list[str] = Field(default_factory=list)
    open_message_ids: list[str] = Field(default_factory=list)
    messages_processed: int = 0
    decision: str
    deadlock_detected: bool = False
    circular_goal_ids: list[str] = Field(default_factory=list)
    budget_exhausted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class RunObservabilitySnapshot(BaseModel):
    run_id: str
    status: str
    duration_ms: int = Field(ge=0)
    primary_agent_count: int = Field(ge=0)
    specialist_module_count: int = Field(ge=0)
    checkpoint_count: int = Field(ge=0)
    workflow_event_count: int = Field(ge=0)
    supervisor_rounds: int = Field(ge=0)
    goals_total: int = Field(ge=0)
    goals_completed: int = Field(ge=0)
    goals_blocked: int = Field(ge=0)
    goals_needing_human_review: int = Field(ge=0)
    open_coordination_messages: int = Field(ge=0)
    canonical_issue_count: int = Field(ge=0)
    unresolved_issue_count: int = Field(ge=0)
    quality_required_corrections: int = Field(ge=0)
    policy_fingerprint: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
