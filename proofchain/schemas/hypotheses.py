"""Explicit competing hypothesis contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class Hypothesis(BaseModel):
    hypothesis_id: str
    run_id: str
    goal_id: str
    statement: str
    supporting_observations: list[str] = Field(default_factory=list)
    contradicting_observations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    status: Literal[
        "proposed", "supported", "weakened", "rejected", "unresolved"
    ] = "proposed"
    discriminating_actions: list[str] = Field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

