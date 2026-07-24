"""Registry that distinguishes primary agents from deterministic specialist modules."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ComponentDeclaration(BaseModel):
    component_id: str
    component_type: str
    parent_agent: str | None = None
    has_independent_goal: bool = False
    has_plan: bool = False
    has_memory: bool = False
    can_replan: bool = False
    description: str


class ComponentRegistry(BaseModel):
    run_id: str
    components: list[ComponentDeclaration] = Field(default_factory=list)
