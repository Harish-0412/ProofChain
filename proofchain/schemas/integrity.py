"""
schemas/integrity.py
Integrity schemas — output contract of the Evidence Integrity Agent.

Separates:
- EvidenceBundle   (grouping of related evidence)
- IntegrityFinding (a detected problem)
- EvidenceGap      (an unmet requirement)
- IntegritySummary (score + counts per scope)
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from proofchain.core.enums import Severity, FindingStatus, FindingType, GapType


# ---------------------------------------------------------------------------
# Evidence Bundle
# ---------------------------------------------------------------------------

class EvidenceBundle(BaseModel):
    """
    Groups related evidence files under a common activity or event.
    Integrity cross-document rules only apply within a bundle.
    """
    bundle_id: str
    bundle_type: str = "event"
    event_id: str | None = None
    event_title: str | None = None
    department: str
    academic_year: str
    evidence_ids: list[str] = Field(default_factory=list)
    document_types_present: list[str] = Field(default_factory=list)
    grouping_method: str = "event_title"
    grouping_confidence: float = 1.0
    run_id: str | None = None


# ---------------------------------------------------------------------------
# Integrity Finding
# ---------------------------------------------------------------------------

class IntegrityFinding(BaseModel):
    """
    A detected integrity problem.
    Created by a specific rule, tied to evidence and optionally a bundle.
    """
    finding_id: str
    run_id: str
    rule_id: str
    rule_version: str = "1.0.0"
    finding_type: FindingType
    severity: Severity
    status: FindingStatus = FindingStatus.OPEN
    evidence_ids: list[str] = Field(default_factory=list)
    bundle_id: str | None = None
    requirement_id: str | None = None

    title: str
    description: str
    expected_value: str | int | float | None = None
    observed_value: str | int | float | None = None

    source_references: list["SourceReference"] = Field(default_factory=list)
    confidence: float = 1.0
    blocking: bool = False
    recommended_action: str = ""
    requires_human_review: bool = True

    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ---------------------------------------------------------------------------
# Evidence Gap
# ---------------------------------------------------------------------------

class EvidenceGap(BaseModel):
    """
    An unmet accreditation requirement.
    Distinct from a Finding: a Gap is about what is MISSING, not what is WRONG.
    """
    gap_id: str
    run_id: str
    requirement_id: str
    bundle_id: str | None = None
    department: str | None = None

    gap_type: GapType
    severity: Severity
    missing_evidence_type: str | None = None
    related_findings: list[str] = Field(default_factory=list, description="Finding IDs")

    description: str
    recommended_action: str
    status: FindingStatus = FindingStatus.OPEN
    blocking: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ---------------------------------------------------------------------------
# Integrity Summary (per scope)
# ---------------------------------------------------------------------------

class IntegritySummary(BaseModel):
    """Integrity score and finding breakdown for one department/requirement scope."""
    scope_type: str = "requirement"
    scope_id: str

    integrity_score: float = 100.0
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    blocking_findings: int = 0
    total_gaps: int = 0
    status: str = "verified_by_automated_checks"


# ---------------------------------------------------------------------------
# Integrity Agent Input / Output
# ---------------------------------------------------------------------------

class IntegrityInput(BaseModel):
    """Input to the Evidence Integrity Agent."""
    workflow: "WorkflowContext"
    classified_evidence: list["ClassifiedEvidence"]
    rule_set_ids: list[str] = Field(default_factory=lambda: ["common-v1", "event-evidence-v1"])
    requirement_definitions: list[dict] = Field(default_factory=list)


class IntegrityAgentResult(BaseModel):
    """Output contract of the Evidence Integrity Agent."""
    run_id: str
    agent_run_id: str
    agent_name: str = "evidence_integrity"
    agent_version: str = "1.0.0"
    status: str

    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0

    bundles: list[EvidenceBundle] = Field(default_factory=list)
    findings: list[IntegrityFinding] = Field(default_factory=list)
    gaps: list[EvidenceGap] = Field(default_factory=list)
    summaries: list[IntegritySummary] = Field(default_factory=list)

    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list["AgentError"] = Field(default_factory=list)

    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
    next_recommended_stage: str | None = "gap_analysis"


from proofchain.schemas.common import SourceReference, AgentError  # noqa: E402
from proofchain.schemas.workflow import WorkflowContext  # noqa: E402
from proofchain.schemas.classification import ClassifiedEvidence  # noqa: E402
IntegrityFinding.model_rebuild()
IntegrityInput.model_rebuild()
IntegrityAgentResult.model_rebuild()
