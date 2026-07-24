"""Claim intelligence and defensibility contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from proofchain.schemas.classification import ClassifiedEvidence
from proofchain.schemas.integrity import EvidenceBundle, EvidenceGap, IntegrityFinding
from proofchain.schemas.workflow import WorkflowContext


ClaimStatus = Literal[
    "supported",
    "partially_supported",
    "contradicted",
    "unsupported",
    "insufficient_evidence",
    "needs_human_review",
]


class AtomicClaim(BaseModel):
    atomic_claim_id: str
    claim_id: str
    attribute: str
    operator: Literal["equals", "at_least", "at_most", "contains"] = "equals"
    expected_value: str | int | float | bool
    qualifiers: dict[str, str] = Field(default_factory=dict)
    mandatory: bool = True


class InstitutionalClaim(BaseModel):
    claim_id: str
    requirement_id: str
    original_claim: str
    department: str
    academic_year: str
    atomic_claims: list[AtomicClaim] = Field(default_factory=list)
    source: Literal["user", "derived_from_evidence"] = "user"


class EvidenceSupportLink(BaseModel):
    atomic_claim_id: str
    evidence_id: str
    extracted_field_id: str | None = None
    relation: Literal[
        "supports",
        "partially_supports",
        "contradicts",
        "irrelevant",
        "uncertain",
    ]
    strength: float = Field(ge=0.0, le=1.0)
    observed_value: str | int | float | bool | None = None
    authority: str
    reason: str


class ClaimContradiction(BaseModel):
    contradiction_id: str
    atomic_claim_id: str
    conflicting_values: list[dict[str, Any]]
    likely_root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = True


class SufficiencyAssessment(BaseModel):
    atomic_claim_id: str
    coverage_score: float = Field(ge=0.0, le=1.0)
    authority_score: float = Field(ge=0.0, le=1.0)
    consistency_score: float = Field(ge=0.0, le=1.0)
    independence_score: float = Field(ge=0.0, le=1.0)
    overall_sufficiency: float = Field(ge=0.0, le=1.0)
    sufficient: bool
    reason: str


class AtomicClaimDecision(BaseModel):
    atomic_claim_id: str
    attribute: str
    status: ClaimStatus
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)
    observed_values: list[str | int | float | bool] = Field(default_factory=list)
    explanation: str


class ClaimLineage(BaseModel):
    claim_id: str
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, str]] = Field(default_factory=list)


class ClaimDecision(BaseModel):
    claim_id: str
    requirement_id: str
    original_claim: str
    status: ClaimStatus
    confidence: float = Field(ge=0.0, le=1.0)
    atomic_decisions: list[AtomicClaimDecision]
    contradictions: list[ClaimContradiction] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    counter_evidence: list[str] = Field(default_factory=list)
    defensible_claim_text: str | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    claim_fragility_score: float = Field(ge=0.0, le=1.0)
    minimal_defensible_evidence_set: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    lineage: ClaimLineage


class ClaimValidationInput(BaseModel):
    workflow: WorkflowContext
    institutional_claims: list[str] = Field(default_factory=list)
    classified_evidence: list[ClassifiedEvidence]
    bundles: list[EvidenceBundle]
    integrity_findings: list[IntegrityFinding] = Field(default_factory=list)
    integrity_gaps: list[EvidenceGap] = Field(default_factory=list)


class ClaimAgentResult(BaseModel):
    run_id: str
    agent_run_id: str
    agent_name: str = "claim_intelligence"
    agent_version: str = "1.0.0"
    status: str
    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    claims: list[InstitutionalClaim] = Field(default_factory=list)
    support_links: list[EvidenceSupportLink] = Field(default_factory=list)
    sufficiency_assessments: list[SufficiencyAssessment] = Field(default_factory=list)
    decisions: list[ClaimDecision] = Field(default_factory=list)
    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[Any] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0

