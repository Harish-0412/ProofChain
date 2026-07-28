"""Acceptance-tested peer negotiation contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class AgentRequest(BaseModel):
    request_id: str
    run_id: str
    source_agent: str
    target_agent: str
    goal_id: str
    requested_outcome: str
    reason: str
    required_inputs: list[str] = Field(default_factory=list)
    related_entities: list[str] = Field(default_factory=list)
    acceptance_conditions: list[str] = Field(default_factory=list)
    satisfied_acceptance_conditions: list[str] = Field(default_factory=list)
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    deadline: datetime | None = None
    blocking: bool = False
    status: Literal[
        "OPEN",
        "ACKNOWLEDGED",
        "ACCEPTED",
        "DECLINED",
        "NEEDS_CLARIFICATION",
        "IN_PROGRESS",
        "RESOLVED",
        "EXPIRED",
        "CANCELLED",
    ] = "OPEN"
    schema_version: str = SCHEMA_VERSION

    def acceptance_satisfied(self) -> bool:
        return set(self.acceptance_conditions) <= set(
            self.satisfied_acceptance_conditions
        )

