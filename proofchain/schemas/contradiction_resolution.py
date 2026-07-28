"""Cross-observation contradiction resolution record."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class ContradictionResolution(BaseModel):
    contradiction_id: str
    run_id: str
    goal_id: str
    conflicting_observation_ids: list[str]
    likely_explanation: str | None = None
    resolution_status: Literal[
        "identified", "investigating", "resolved", "unresolved", "escalated"
    ]
    confidence: float = Field(ge=0, le=1)
    authority_ranking: list[str] = Field(default_factory=list)
    required_followup: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    schema_version: str = SCHEMA_VERSION

