"""Accountability, ownership, and escalation contracts."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from proofchain.schemas.gaps import ResolutionPortfolio
from proofchain.schemas.workflow import WorkflowContext


class OrganisationMember(BaseModel):
    user_id: str
    display_name: str
    role: str
    department: str
    permissions: list[str] = Field(default_factory=list)
    active_tasks: int = Field(default=0, ge=0)
    available: bool = True
    reports_to: str | None = None


class ProvenanceCandidate(BaseModel):
    user_id: str
    relationship: str
    confidence: float = Field(ge=0.0, le=1.0)


class OwnerReference(BaseModel):
    user_id: str
    display_name: str
    role: str
    confidence: float = Field(ge=0.0, le=1.0)
    selection_reasons: list[str] = Field(default_factory=list)


class EscalationStep(BaseModel):
    level: int = Field(ge=1)
    after_hours: int = Field(ge=1)
    target_role: str
    action: str


class OwnershipAssignment(BaseModel):
    assignment_id: str
    gap_id: str
    primary_owner: OwnerReference | None = None
    backup_owner: OwnerReference | None = None
    approver: OwnerReference | None = None
    assignment_confidence: float = Field(ge=0.0, le=1.0)
    workload_assessment: dict[str, Any] = Field(default_factory=dict)
    conflict_checks: dict[str, bool] = Field(default_factory=dict)
    escalation_plan: list[EscalationStep] = Field(default_factory=list)
    due_date_recommendation: date | None = None
    communication_data_scope: list[str] = Field(default_factory=list)
    status: Literal[
        "recommended", "needs_human_review", "unresolved", "approved", "rejected"
    ]
    human_approval_required: bool = True


class OwnershipInput(BaseModel):
    workflow: WorkflowContext
    portfolio: ResolutionPortfolio
    organisation_members: list[OrganisationMember] = Field(default_factory=list)


class OwnershipAgentResult(BaseModel):
    run_id: str
    agent_run_id: str
    agent_name: str = "accountability_ownership"
    agent_version: str = "1.0.0"
    status: str
    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    assignments: list[OwnershipAssignment] = Field(default_factory=list)
    unresolved_ownership: list[str] = Field(default_factory=list)
    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[Any] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0

