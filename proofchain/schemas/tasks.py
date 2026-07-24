"""Resolution task contracts for governed department liaison."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, Field

from proofchain.schemas.gaps import ResolutionPortfolio
from proofchain.schemas.issues import CanonicalIssue
from proofchain.schemas.ownership import OwnershipAgentResult
from proofchain.schemas.workflow import WorkflowContext


TaskStatus = Literal[
    "draft",
    "approval_required",
    "active",
    "acknowledged",
    "evidence_submitted",
    "blocked",
    "escalated",
    "closed",
]


class ResolutionTask(BaseModel):
    task_id: str
    issue_id: str
    gap_id: str
    approved_strategy_id: str
    primary_owner_id: str
    backup_owner_id: str | None = None
    approver_id: str | None = None
    title: str
    objective: str
    required_actions: list[str]
    required_closure_evidence: list[str]
    priority: str
    due_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc) + timedelta(days=7)
    )
    status: TaskStatus
    disclosure_scope: list[str] = Field(default_factory=list)
    approval_event_ids: list[str] = Field(default_factory=list)
    escalation_policy_id: str = "default-gap-sla"
    dispatch_channel: str = "in_app"
    delivery_status: str = "not_sent"
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class TaskResponse(BaseModel):
    response_id: str
    task_id: str
    responder_id: str
    response_type: str
    message: str | None = None
    submitted_artifact_ids: list[str] = Field(default_factory=list)
    received_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    requires_agent_action: bool = True


class ResolutionTaskState(BaseModel):
    run_id: str
    task_id: str
    issue_id: str
    gap_id: str
    status: TaskStatus
    approval_ids: list[str] = Field(default_factory=list)
    approval_event_ids: list[str] = Field(default_factory=list)
    response_event_ids: list[str] = Field(default_factory=list)
    submitted_artifacts: list[str] = Field(default_factory=list)
    last_event_id: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class LiaisonInput(BaseModel):
    workflow: WorkflowContext
    portfolio: ResolutionPortfolio
    ownership: OwnershipAgentResult
    canonical_issues: list[CanonicalIssue] = Field(default_factory=list)
    approval_event_ids: list[str] = Field(default_factory=list)


class LiaisonAgentResult(BaseModel):
    run_id: str
    agent_run_id: str
    agent_name: str = "department_liaison"
    agent_version: str = "1.0.0"
    status: str
    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    tasks: list[ResolutionTask] = Field(default_factory=list)
    responses: list[TaskResponse] = Field(default_factory=list)
    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
