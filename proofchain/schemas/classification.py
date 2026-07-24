"""
schemas/classification.py
Classification schemas — output contract of the Evidence Classification Agent.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from proofchain.core.enums import (
    DocumentType,
    ClassificationMethod,
    MappingType,
    ExtractionStatus,
    ProcessingStatus,
    ConfidenceLevel,
    classify_confidence,
)


# ---------------------------------------------------------------------------
# Source Reference (local use — also defined in common.py)
# ---------------------------------------------------------------------------

from proofchain.schemas.common import SourceReference  # noqa: E402


# ---------------------------------------------------------------------------
# Extracted Field
# ---------------------------------------------------------------------------

class ExtractedField(BaseModel):
    """
    A single structured value extracted from a document.
    Every value carries its source reference and confidence score.
    """
    field_name: str
    normalized_value: str | int | float | bool | None = None
    raw_value: str | None = None
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    page_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None
    extraction_method: str = "regex"

    def model_post_init(self, __context) -> None:
        self.confidence_level = classify_confidence(self.confidence)


# ---------------------------------------------------------------------------
# Extraction Result
# ---------------------------------------------------------------------------

class ExtractionResult(BaseModel):
    """Output of the Document Extraction Service for one evidence file."""
    extraction_status: ExtractionStatus
    extractor_used: str
    text: str | None = None
    tables: list[dict] = Field(default_factory=list)
    page_count: int | None = None
    sheet_names: list[str] = Field(default_factory=list)
    page_references: list[SourceReference] = Field(default_factory=list)
    extraction_confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Document Type Prediction
# ---------------------------------------------------------------------------

class ClassificationCandidate(BaseModel):
    """A secondary document type candidate with its confidence."""
    document_type: DocumentType
    confidence: float
    reason: str


class DocumentTypePrediction(BaseModel):
    """Result of document type classification for one evidence file."""
    primary_type: DocumentType
    confidence: float
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    secondary_types: list[ClassificationCandidate] = Field(default_factory=list)
    classification_method: ClassificationMethod = ClassificationMethod.FILENAME_RULE
    reasons: list[str] = Field(default_factory=list)
    requires_human_review: bool = False

    def model_post_init(self, __context) -> None:
        self.confidence_level = classify_confidence(self.confidence)
        self.requires_human_review = self.confidence < 0.75


# ---------------------------------------------------------------------------
# Requirement Mapping
# ---------------------------------------------------------------------------

class RequirementMapping(BaseModel):
    """Maps one evidence file to one accreditation requirement."""
    requirement_id: str
    mapping_type: MappingType = MappingType.FILENAME
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    reason: str = ""
    source_references: list[SourceReference] = Field(default_factory=list)
    requires_human_review: bool = False

    def model_post_init(self, __context) -> None:
        self.confidence_level = classify_confidence(self.confidence)
        self.requires_human_review = self.confidence < 0.75


# ---------------------------------------------------------------------------
# Classified Evidence
# ---------------------------------------------------------------------------

class ClassifiedEvidence(BaseModel):
    """
    Fully classified evidence record — output of the Classification Agent.
    Contains extraction results, document type, fields, and requirement mappings.
    """
    evidence_id: str
    version_id: str
    department: str
    academic_year: str
    original_filename: str
    relative_path: str
    absolute_path: str
    sha256_checksum: str
    duplicate_of_evidence_id: str | None = None
    run_id: str | None = None
    agent_run_id: str | None = None

    extraction: ExtractionResult
    document_type: DocumentTypePrediction
    extracted_fields: dict[str, ExtractedField] = Field(default_factory=dict)
    requirement_mappings: list[RequirementMapping] = Field(default_factory=list)

    overall_confidence: float = 0.0
    processing_status: ProcessingStatus = ProcessingStatus.COMPLETED
    requires_human_review: bool = False
    warnings: list[str] = Field(default_factory=list)

    classified_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ---------------------------------------------------------------------------
# Classification Agent Input / Output
# ---------------------------------------------------------------------------

class ClassificationInput(BaseModel):
    """Input to the Evidence Classification Agent."""
    workflow: "WorkflowContext"
    evidence_records: list["EvidenceRecord"]
    extraction_config: dict = Field(default_factory=dict)
    classification_config: dict = Field(default_factory=dict)
    mapping_config: dict = Field(default_factory=dict)


class ClassificationAgentResult(BaseModel):
    """Output contract of the Evidence Classification Agent."""
    run_id: str
    agent_run_id: str
    agent_name: str = "evidence_classification"
    agent_version: str = "1.0.0"
    status: str

    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    unresolved_count: int = 0

    records: list[ClassifiedEvidence] = Field(default_factory=list)

    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list["AgentError"] = Field(default_factory=list)

    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
    next_recommended_stage: str | None = "evidence_integrity"


from proofchain.schemas.workflow import WorkflowContext  # noqa: E402
from proofchain.schemas.evidence import EvidenceRecord  # noqa: E402
from proofchain.schemas.common import AgentError  # noqa: E402
ClassificationInput.model_rebuild()
ClassificationAgentResult.model_rebuild()
