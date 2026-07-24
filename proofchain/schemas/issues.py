"""Canonical issue and governed lifecycle contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

IssueLifecycleStatus = Literal[
    "OPEN",
    "PLANNED",
    "ASSIGNED_PENDING_APPROVAL",
    "ASSIGNED",
    "IN_PROGRESS",
    "EVIDENCE_SUBMITTED",
    "UNDER_REVALIDATION",
    "RESOLVED",
    "REJECTED",
    "REOPENED",
    "WAIVED_WITH_APPROVAL",
    "CANCELLED",
]


class CanonicalIssue(BaseModel):
    issue_id: str
    run_id: str
    issue_type: str
    root_entity_type: str
    root_entity_id: str
    source_finding_ids: list[str] = Field(default_factory=list)
    source_gap_ids: list[str] = Field(default_factory=list)
    source_claim_ids: list[str] = Field(default_factory=list)
    affected_requirement_ids: list[str] = Field(default_factory=list)
    affected_evidence_ids: list[str] = Field(default_factory=list)
    severity: str
    blocking: bool
    status: IssueLifecycleStatus = "OPEN"
    root_cause_id: str | None = None
    resolution_task_ids: list[str] = Field(default_factory=list)
    canonical_key: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class IssueLedger(BaseModel):
    run_id: str
    raw_findings: int = 0
    claim_failures: int = 0
    raw_gaps: int = 0
    canonical_issues: int = 0
    blocking_canonical_issues: int = 0
    resolution_tasks: int = 0
    issues: list[CanonicalIssue] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class IssueTransition(BaseModel):
    transition_id: str
    run_id: str
    issue_id: str
    from_status: IssueLifecycleStatus
    to_status: IssueLifecycleStatus
    reason: str
    authorized_by_event_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
