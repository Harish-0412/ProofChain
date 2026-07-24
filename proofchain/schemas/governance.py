"""Human approval records for high-impact institutional decisions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class HumanApprovalRecord(BaseModel):
    approval_id: str
    run_id: str
    approval_type: Literal[
        "claim_revision",
        "gap_resolution_strategy",
        "ownership_assignment",
        "escalation",
    ]
    target_id: str
    decision: Literal["approved", "rejected"]
    decided_by: str
    reason: str
    evidence_references: list[str] = Field(default_factory=list)
    approval_state: Literal[
        "REQUESTED",
        "APPROVED",
        "REJECTED",
        "EXPIRED",
        "SUPERSEDED",
        "REVOKED",
        "EXECUTED",
    ] = "REQUESTED"
    approver_role: str | None = None
    approver_scope: list[str] = Field(default_factory=list)
    authorization_checks: dict[str, bool] = Field(default_factory=dict)
    recommendation_hash: str | None = None
    permitted_transition: str | None = None
    transition_event_id: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = "1.0.0"
