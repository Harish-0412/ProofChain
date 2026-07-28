"""Pre-planning input validation contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class InputCheck(BaseModel):
    check_name: str
    status: Literal["passed", "warning", "failed", "not_applicable"]
    reference: str | None = None
    explanation: str


class InputValidationResult(BaseModel):
    run_id: str
    goal_id: str
    valid: bool
    complete: bool
    authorized: bool
    current: bool
    checks: list[InputCheck] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    stale_inputs: list[str] = Field(default_factory=list)
    conflicting_inputs: list[str] = Field(default_factory=list)
    unauthorized_inputs: list[str] = Field(default_factory=list)
    recoverable: bool = False
    recommended_action: Literal[
        "continue", "recover", "request_peer", "request_human", "block"
    ] = "continue"
    schema_version: str = SCHEMA_VERSION

