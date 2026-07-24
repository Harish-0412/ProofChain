"""Evidence closure and targeted revalidation contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from proofchain.schemas.classification import ClassifiedEvidence
from proofchain.schemas.claims import ClaimDecision
from proofchain.schemas.gaps import ResolutionPortfolio
from proofchain.schemas.integrity import IntegrityFinding
from proofchain.schemas.issues import CanonicalIssue, IssueTransition
from proofchain.schemas.tasks import ResolutionTask
from proofchain.schemas.workflow import WorkflowContext


class ClosureCheck(BaseModel):
    check_id: str
    issue_id: str
    task_id: str | None = None
    evidence_submitted: bool
    evidence_registered: bool
    classification_complete: bool
    integrity_rules_passed: bool
    affected_claims_revalidated: bool
    closure_policy_satisfied: bool
    status: Literal["resolved", "rejected", "under_revalidation", "waiting_for_evidence"]
    reasons: list[str] = Field(default_factory=list)


class ClosureInput(BaseModel):
    workflow: WorkflowContext
    canonical_issues: list[CanonicalIssue]
    tasks: list[ResolutionTask] = Field(default_factory=list)
    classified_evidence: list[ClassifiedEvidence] = Field(default_factory=list)
    integrity_findings: list[IntegrityFinding] = Field(default_factory=list)
    claim_decisions: list[ClaimDecision] = Field(default_factory=list)
    portfolio: ResolutionPortfolio | None = None


class ClosureAgentResult(BaseModel):
    run_id: str
    agent_run_id: str
    agent_name: str = "closure_revalidation"
    agent_version: str = "1.0.0"
    status: str
    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    closure_checks: list[ClosureCheck] = Field(default_factory=list)
    issue_transitions: list[IssueTransition] = Field(default_factory=list)
    updated_issues: list[CanonicalIssue] = Field(default_factory=list)
    current_verified_readiness: float = Field(default=0.0, ge=0.0, le=100.0)
    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
