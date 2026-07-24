"""Consolidated decision report produced by agents 4 through 6."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ExtendedAgentPipelineReport(BaseModel):
    run_id: str
    criterion_ids: list[str]
    academic_year: str
    departments: list[str]
    claim_assessment: dict
    claim_details: list[dict]
    gap_assessment: dict
    resolution_portfolio: list[dict]
    ownership_summary: dict
    assignments: list[dict]
    lifecycle_summary: dict = Field(default_factory=dict)
    overall_status: str
    next_required_actions: list[str] = Field(default_factory=list)
    human_approval_required: bool = True
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
