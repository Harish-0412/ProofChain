"""
schemas/common.py
Shared primitive schemas used across all agents and services.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Source Reference
# ---------------------------------------------------------------------------

class SourceReference(BaseModel):
    """Tracks exactly where an extracted value came from in a document."""
    document: str = Field(description="Relative path or evidence ID of the source file")
    page_number: int | None = Field(default=None, description="Page number (1-indexed) for PDFs")
    sheet_name: str | None = Field(default=None, description="Sheet name for spreadsheets")
    cell_range: str | None = Field(default=None, description="Cell range, e.g. 'B4:B112'")
    text_snippet: str | None = Field(default=None, description="Short text snippet from which value was extracted")


# ---------------------------------------------------------------------------
# Structured Agent Error
# ---------------------------------------------------------------------------

class AgentError(BaseModel):
    """Structured error record for a single agent failure event."""
    error_code: str
    agent_name: str
    evidence_id: str | None = None
    stage: str
    severity: str
    recoverable: bool = True
    message: str
    technical_details: str | None = None
    recommended_action: str | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ---------------------------------------------------------------------------
# Stage Summary
# ---------------------------------------------------------------------------

class StageSummary(BaseModel):
    """Compact summary of a single pipeline stage execution."""
    stage_name: str
    status: str
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    skipped_count: int = 0
    duration_ms: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Persisted artifact synchronization
# ---------------------------------------------------------------------------

class ArtifactReference(BaseModel):
    """Immutable identity of a JSON artifact committed by one pipeline stage."""
    stage_name: str
    path: str
    sha256: str
    record_count: int = 0
    schema_version: str = "1.0.0"
    agent_run_id: str | None = None
    committed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class StageCheckpoint(BaseModel):
    """Synchronization record linking one stage input snapshot to its committed output."""
    run_id: str
    stage_name: str
    status: str
    input_sha256: str
    output: ArtifactReference
    upstream_sha256: str | None = None
    started_at: datetime
    completed_at: datetime
