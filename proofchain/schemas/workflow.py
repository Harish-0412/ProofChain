"""
schemas/workflow.py
Workflow context and supervisor request/result schemas.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from proofchain.core.enums import WorkflowStage, RunMode


# ---------------------------------------------------------------------------
# Workflow Context
# ---------------------------------------------------------------------------

class WorkflowContext(BaseModel):
    """
    Shared context object passed across all agents in a pipeline run.
    Ensures all agents operate on the same run ID, scope, and configuration.
    """
    run_id: str
    correlation_id: str
    requested_by: str = "system"
    department_scope: list[str] = Field(description="Departments included in this run")
    academic_year: str
    requirement_scope: list[str] = Field(description="Requirement IDs targeted in this run")
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    current_stage: WorkflowStage = WorkflowStage.CREATED
    configuration_version: str = "1.0.0"
    rule_version: str = "1.0.0"
    extractor_version: str = "1.0.0"
    classifier_version: str = "1.0.0"
    upstream_artifact_hash: str | None = None


# ---------------------------------------------------------------------------
# Supervisor Request
# ---------------------------------------------------------------------------

class SupervisorRequest(BaseModel):
    """Input to the Supervisor Agent to start a pipeline run."""
    source_directories: list[str] = Field(
        default_factory=list,
        description="Absolute paths to folders containing evidence",
    )
    department_scope: list[str] = Field(description="Departments to include in this run")
    academic_year: str = "2025-2026"
    requirement_scope: list[str] = Field(
        default_factory=lambda: ["C3.2.1", "C5.1.3", "C6.3.2", "C7.1.1", "C1.2.1"]
    )
    requested_by: str = "system"
    run_mode: RunMode = RunMode.FULL
    objective: str | None = Field(
        default=None,
        description="Institutional objective that the supervisor decomposes into agent goals.",
    )
    success_conditions: list[str] = Field(default_factory=list)
    maximum_agent_rounds: int = Field(default=12, ge=1, le=100)
    maximum_replans_per_agent: int = Field(default=3, ge=1, le=20)
    human_approval_for_final_decision: bool = False
    institutional_claims: list[str] = Field(
        default_factory=list,
        description=(
            "Human-authored institutional claims. When empty, claims are derived "
            "from classified event evidence."
        ),
    )
    resume_run_id: str | None = Field(
        default=None,
        description="Existing run whose committed artifact is the input for a stage-only run",
    )


# ---------------------------------------------------------------------------
# Pipeline Result
# ---------------------------------------------------------------------------

class PipelineResult(BaseModel):
    """
    Consolidated output of a complete Supervisor-orchestrated pipeline run.
    Written to outputs/runs/{run_id}/pipeline_result.json
    """
    run_id: str
    status: str
    academic_year: str
    department_scope: list[str]
    requirement_scope: list[str]
    started_at: datetime
    completed_at: datetime
    duration_ms: int

    # Stage summaries
    collection_summary: "StageSummary | None" = None
    classification_summary: "StageSummary | None" = None
    integrity_summary: "StageSummary | None" = None
    claim_summary: "StageSummary | None" = None
    gap_resolution_summary: "StageSummary | None" = None
    ownership_summary: "StageSummary | None" = None
    liaison_summary: "StageSummary | None" = None
    closure_summary: "StageSummary | None" = None
    audit_package_summary: "StageSummary | None" = None
    quality_review_summary: "StageSummary | None" = None

    # Totals
    total_files_discovered: int = 0
    total_evidence_registered: int = 0
    total_documents_classified: int = 0
    total_documents_unresolved: int = 0
    total_findings: int = 0
    total_gaps: int = 0
    blocking_findings: int = 0
    total_claims: int = 0
    claims_requiring_review: int = 0
    total_resolution_gaps: int = 0
    total_ownership_assignments: int = 0
    unresolved_ownership: int = 0
    total_canonical_issues: int = 0
    blocking_canonical_issues: int = 0
    total_resolution_tasks: int = 0
    total_closure_checks: int = 0
    resolved_issues: int = 0
    package_eligible_evidence: int = 0
    quality_required_corrections: int = 0

    # Output paths
    evidence_output_path: str | None = None
    classification_output_path: str | None = None
    integrity_output_path: str | None = None
    trace_output_path: str | None = None
    run_manifest_path: str | None = None
    top_level_goal_id: str | None = None
    goal_graph_path: str | None = None
    coordination_state_path: str | None = None
    final_decision_path: str | None = None
    claim_output_path: str | None = None
    gap_resolution_output_path: str | None = None
    ownership_output_path: str | None = None
    extended_report_path: str | None = None
    canonical_issues_path: str | None = None
    liaison_tasks_path: str | None = None
    communications_path: str | None = None
    closure_output_path: str | None = None
    audit_package_output_path: str | None = None
    quality_review_output_path: str | None = None
    workflow_events_path: str | None = None
    component_registry_path: str | None = None
    policy_manifest_path: str | None = None
    model_governance_manifest_path: str | None = None
    supervisor_rounds_path: str | None = None
    observability_metrics_path: str | None = None
    audit_package_bundle_path: str | None = None
    supervisor_rounds: int = 0

    # Errors and warnings
    warnings: list[str] = Field(default_factory=list)
    errors: list["AgentError"] = Field(default_factory=list)


# Avoid circular import; import at bottom
from proofchain.schemas.common import StageSummary, AgentError  # noqa: E402
PipelineResult.model_rebuild()
