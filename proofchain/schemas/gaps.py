"""Adaptive gap resolution and readiness planning contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from proofchain.schemas.claims import ClaimDecision
from proofchain.schemas.integrity import EvidenceGap as IntegrityEvidenceGap
from proofchain.schemas.integrity import IntegrityFinding, IntegritySummary
from proofchain.schemas.workflow import WorkflowContext


class ResolutionGap(BaseModel):
    gap_id: str
    issue_id: str | None = None
    source_type: Literal["integrity_finding", "integrity_gap", "claim_decision"]
    source_ids: list[str]
    affected_claims: list[str] = Field(default_factory=list)
    affected_requirements: list[str] = Field(default_factory=list)
    department: str | None = None
    gap_type: str
    severity: Literal["critical", "high", "medium", "low"]
    blocking: bool
    description: str
    root_cause: str | None = None
    root_cause_hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    readiness_impact: float = Field(default=0.0, ge=0.0, le=100.0)
    status: Literal["open", "planned", "needs_human_review", "resolved"] = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ResolutionStrategy(BaseModel):
    strategy_id: str
    title: str
    actions: list[str]
    estimated_effort: Literal["low", "medium", "high"]
    expected_resolution_confidence: float = Field(ge=0.0, le=1.0)
    requires_new_evidence: bool = False
    requires_claim_revision: bool = False


class GapResolutionPlan(BaseModel):
    plan_id: str
    gap_id: str
    strategies: list[ResolutionStrategy]
    recommended_strategy_id: str
    dependencies: list[str] = Field(default_factory=list)
    required_completion_evidence: list[str] = Field(default_factory=list)
    expected_readiness_delta: float = Field(ge=0.0, le=100.0)
    human_approval_required: bool = True


class ReadinessScenario(BaseModel):
    gap_id: str
    strategy_id: str
    expected_readiness: float = Field(ge=0.0, le=100.0)
    readiness_delta: float = Field(ge=0.0, le=100.0)
    remaining_blockers: int = Field(ge=0)


class ReadinessSimulation(BaseModel):
    current_readiness: float = Field(ge=0.0, le=100.0)
    projected_readiness: float = Field(ge=0.0, le=100.0)
    projection_type: Literal["counterfactual"] = "counterfactual"
    projection_confidence: float = Field(default=0.78, ge=0.0, le=1.0)
    assumptions: list[str] = Field(
        default_factory=lambda: [
            "All recommended closure evidence is accepted.",
            "No new contradictions are introduced.",
            "All blocking gaps pass revalidation.",
        ]
    )
    unresolved_dependencies: list[str] = Field(default_factory=list)
    not_an_approval: bool = True
    scenario_bands: dict[str, float] = Field(default_factory=dict)
    scenarios: list[ReadinessScenario] = Field(default_factory=list)


class PrioritizedGap(BaseModel):
    gap_id: str
    priority_score: float = Field(ge=0.0, le=100.0)
    priority: Literal["critical", "high", "medium", "low"]
    reason: str


class ResolutionPortfolio(BaseModel):
    portfolio_id: str
    run_id: str
    current_readiness: float
    current_verified_readiness: float | None = None
    target_readiness: float = 90.0
    projected_readiness: float
    projection_type: Literal["counterfactual"] = "counterfactual"
    projection_confidence: float = Field(default=0.78, ge=0.0, le=1.0)
    projection_assumptions: list[str] = Field(default_factory=list)
    projection_unresolved_dependencies: list[str] = Field(default_factory=list)
    scenario_bands: dict[str, float] = Field(default_factory=dict)
    not_an_approval: bool = True
    evidence_debt_score: float
    gaps: list[ResolutionGap]
    plans: list[GapResolutionPlan]
    priorities: list[PrioritizedGap]
    minimal_resolution_set: list[str]
    dependency_graph: dict[str, list[str]]
    human_approval_required: bool = True


class GapResolutionInput(BaseModel):
    workflow: WorkflowContext
    claim_decisions: list[ClaimDecision]
    integrity_findings: list[IntegrityFinding]
    integrity_gaps: list[IntegrityEvidenceGap]
    integrity_summaries: list[IntegritySummary]


class GapAgentResult(BaseModel):
    run_id: str
    agent_run_id: str
    agent_name: str = "adaptive_gap_resolution"
    agent_version: str = "1.0.0"
    status: str
    input_count: int = 0
    success_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    portfolio: ResolutionPortfolio
    output_reference: str | None = None
    input_snapshot_hash: str | None = None
    output_snapshot_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[Any] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    duration_ms: int = 0
