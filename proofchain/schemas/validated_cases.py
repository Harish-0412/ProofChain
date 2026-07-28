"""Governed reusable experience record."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class ValidatedCase(BaseModel):
    case_id: str
    case_type: str
    tenant_id: str | None = None
    policy_fingerprint: str | None = None
    context_features: dict[str, Any] = Field(default_factory=dict)
    successful_plan: list[str]
    successful_tools: list[str]
    outcome: str
    validation_status: Literal[
        "pending", "validated", "rejected", "expired"
    ] = "pending"
    approved_by: str | None = None
    reusable: bool = False
    expires_at: datetime | None = None
    schema_version: str = SCHEMA_VERSION

