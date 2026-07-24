"""
schemas/evidence.py
Evidence record schemas — output contract of the Evidence Collector Agent.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from proofchain.core.enums import IngestionStatus, DuplicateStatus, SourceType


# ---------------------------------------------------------------------------
# Evidence Record
# ---------------------------------------------------------------------------

class EvidenceRecord(BaseModel):
    """
    Represents one registered piece of institutional evidence.
    This is the atomic output unit of the Evidence Collector Agent.
    """
    evidence_id: str = Field(description="Stable human-readable ID: EVD-CSE-2025-2026-00017")
    version_id: str = Field(description="Version ID: VER-00017-01")
    version_number: int = 1

    department: str
    academic_year: str

    original_filename: str
    relative_path: str = Field(description="Path relative to the project root")
    absolute_path: str

    file_extension: str
    mime_type: str
    file_size_bytes: int

    sha256_checksum: str
    created_at: datetime | None = None
    modified_at: datetime | None = None

    ingestion_status: IngestionStatus = IngestionStatus.REGISTERED
    duplicate_status: DuplicateStatus = DuplicateStatus.UNIQUE
    duplicate_of_evidence_id: str | None = None

    source_type: SourceType = SourceType.DEPARTMENT_FOLDER
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    # Agent trace fields
    run_id: str | None = None
    agent_run_id: str | None = None


# ---------------------------------------------------------------------------
# Collector Input / Output
# ---------------------------------------------------------------------------

class CollectorInput(BaseModel):
    """Input to the Evidence Collector Agent."""
    workflow: "WorkflowContext"
    source_directories: list[str]
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [".pdf", ".xlsx", ".csv", ".docx", ".png", ".jpg", ".jpeg"]
    )
    recursive: bool = True
    rescan_existing: bool = False


class CollectorAgentResult(BaseModel):
    """Output contract of the Evidence Collector Agent."""
    run_id: str
    agent_run_id: str
    agent_name: str = "evidence_collector"
    agent_version: str = "1.0.0"
    status: str

    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    duplicate_count: int = 0
    unsupported_count: int = 0

    records: list[EvidenceRecord] = Field(default_factory=list)

    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list["AgentError"] = Field(default_factory=list)

    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
    next_recommended_stage: str | None = "evidence_classification"


# Deferred imports
from proofchain.schemas.workflow import WorkflowContext  # noqa: E402
from proofchain.schemas.common import AgentError  # noqa: E402
CollectorInput.model_rebuild()
CollectorAgentResult.model_rebuild()
