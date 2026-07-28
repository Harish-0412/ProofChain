"""Platform-wide supervisor assurance, replanning, and release contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class CompletionProofAudit(BaseModel):
    run_id: str
    proofs_expected: int
    proofs_found: int
    valid_proof_ids: list[str] = Field(default_factory=list)
    invalid_proof_ids: list[str] = Field(default_factory=list)
    missing_goal_ids: list[str] = Field(default_factory=list)
    decision_mismatches: list[str] = Field(default_factory=list)
    audit_passed: bool
    schema_version: str = SCHEMA_VERSION


class GlobalReplanRecord(BaseModel):
    replan_id: str
    run_id: str
    trigger: Literal[
        "critical_goal_failure",
        "policy_version_change",
        "quality_review_failure",
        "security_incident",
        "tenant_boundary_change",
        "submission_deadline_change",
        "schema_migration_block",
        "new_contradictory_evidence",
    ]
    reason: str
    affected_goal_ids: list[str] = Field(default_factory=list)
    changed_assumptions: list[str] = Field(default_factory=list)
    invalidated_step_ids: list[str] = Field(default_factory=list)
    new_scope: list[str] = Field(default_factory=list)
    decision: Literal[
        "targeted_revalidation",
        "pause_for_human",
        "block_downstream",
        "recalculate_critical_path",
    ]
    original_artifacts_unchanged: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION


class CrossAgentContradictionReport(BaseModel):
    run_id: str
    contradiction_ids: list[str] = Field(default_factory=list)
    source_agents: list[str] = Field(default_factory=list)
    unresolved_count: int = 0
    escalated_count: int = 0
    report_status: Literal["clear", "resolved", "escalated"]
    schema_version: str = SCHEMA_VERSION


class CriticalPathSchedule(BaseModel):
    run_id: str
    critical_path_goal_ids: list[str] = Field(default_factory=list)
    ordered_goal_ids: list[str] = Field(default_factory=list)
    priority_scores: dict[str, float] = Field(default_factory=dict)
    agent_allocation_counts: dict[str, int] = Field(default_factory=dict)
    fairness_strategy: str = "priority_then_depth_then_least_served"
    schema_version: str = SCHEMA_VERSION


class HumanReviewQueueItem(BaseModel):
    goal_id: str
    agent_name: str
    reason: str
    priority: str
    proof_id: str | None = None


class AgenticReleaseDecision(BaseModel):
    run_id: str
    decision: Literal["PASS", "BLOCK", "NEEDS_HUMAN_REVIEW"]
    scorecards_expected: int
    scorecards_found: int
    gates: dict[str, bool]
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION


class SupervisorAssuranceReport(BaseModel):
    run_id: str
    stage: Literal["core", "phase_one", "phase_two"]
    completion_proof_audit: CompletionProofAudit
    contradiction_report: CrossAgentContradictionReport
    critical_path_schedule: CriticalPathSchedule
    replan_records: list[GlobalReplanRecord] = Field(default_factory=list)
    human_review_queue: list[HumanReviewQueueItem] = Field(default_factory=list)
    release_decision: AgenticReleaseDecision
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    schema_version: str = SCHEMA_VERSION
