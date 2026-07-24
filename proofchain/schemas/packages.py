"""Audit package composition contracts."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from proofchain.schemas.claims import ClaimDecision
from proofchain.schemas.closure import ClosureAgentResult
from proofchain.schemas.evidence import EvidenceRecord
from proofchain.schemas.issues import CanonicalIssue
from proofchain.schemas.workflow import WorkflowContext


class PackageEvidenceItem(BaseModel):
    evidence_id: str
    source_path: str
    sha256: str
    included: bool
    reason: str


class AuditPackageManifest(BaseModel):
    package_id: str
    run_id: str
    requirement_ids: list[str]
    departments: list[str]
    academic_year: str
    status: str = "DRAFT_READY_FOR_QUALITY_REVIEW"
    eligible_evidence: list[PackageEvidenceItem] = Field(default_factory=list)
    excluded_evidence: list[PackageEvidenceItem] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    unresolved_warning_issue_ids: list[str] = Field(default_factory=list)
    package_lineage: dict[str, list[str]] = Field(default_factory=dict)
    package_hash: str | None = None
    bundle_path: str | None = None
    bundle_sha256: str | None = None
    bundle_format: str | None = None
    bundle_contains_original_evidence: bool = False
    external_submission_approved: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class AuditPackageInput(BaseModel):
    workflow: WorkflowContext
    evidence_records: list[EvidenceRecord]
    claim_decisions: list[ClaimDecision]
    canonical_issues: list[CanonicalIssue]
    closure_result: ClosureAgentResult | None = None


class AuditPackageAgentResult(BaseModel):
    run_id: str
    agent_run_id: str
    agent_name: str = "audit_package_composer"
    agent_version: str = "1.0.0"
    status: str
    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    manifest: AuditPackageManifest
    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
