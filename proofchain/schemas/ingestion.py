"""Explicit ingestion capability contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


IngestionCapability = Literal[
    "native_extraction",
    "metadata_only",
    "unsupported",
    "rejected",
]


class IngestionCapabilityDecision(BaseModel):
    extension: str
    capability: IngestionCapability
    extractor: str | None = None
    reason: str
    downstream_action: Literal[
        "process",
        "process_with_warning",
        "human_conversion_required",
        "block",
    ]
    security_inspection_required: bool = False


class IngestionCapabilityReport(BaseModel):
    schema_version: str = "1.0.0"
    native_extensions: list[str] = Field(default_factory=list)
    metadata_only_extensions: list[str] = Field(default_factory=list)
    rejected_extensions: list[str] = Field(default_factory=list)
    unknown_file_policy: str
    decisions: list[IngestionCapabilityDecision] = Field(default_factory=list)
