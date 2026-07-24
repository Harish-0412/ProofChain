"""Adversarial audit package quality review contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from proofchain.schemas.claims import ClaimDecision
from proofchain.schemas.packages import AuditPackageManifest
from proofchain.schemas.workflow import WorkflowContext


class ClaimChallenge(BaseModel):
    claim_id: str
    result: Literal["passed", "warning", "failed"]
    reason: str


class QualityReviewInput(BaseModel):
    workflow: WorkflowContext
    package_manifest: AuditPackageManifest
    claim_decisions: list[ClaimDecision] = Field(default_factory=list)


class QualityReviewAgentResult(BaseModel):
    run_id: str
    agent_run_id: str
    agent_name: str = "adversarial_quality_review"
    agent_version: str = "1.0.0"
    status: str
    package_id: str
    package_hash: str | None
    quality_status: Literal[
        "pass_for_human_approval",
        "pass_with_warnings",
        "return_for_correction",
        "block_package",
    ]
    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    claim_challenges: list[ClaimChallenge] = Field(default_factory=list)
    broken_references: int = 0
    omitted_material_findings: int = 0
    duplicate_evidence_risks: int = 0
    privacy_findings: int = 0
    reviewer_friction_score: float = Field(default=0.0, ge=0.0, le=100.0)
    audit_failure_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    required_corrections: list[str] = Field(default_factory=list)
    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
