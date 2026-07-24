"""Append-only workflow events for replayable operational state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class WorkflowEvent(BaseModel):
    event_id: str
    run_id: str
    sequence: int | None = Field(default=None, ge=1)
    event_type: str
    aggregate_type: str
    aggregate_id: str
    actor: str = "system"
    payload: dict[str, Any] = Field(default_factory=dict)
    previous_event_id: str | None = None
    previous_event_hash: str | None = None
    event_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = "1.0.0"
