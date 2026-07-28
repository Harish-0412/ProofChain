"""Typed contracts for Phase 2 institutional governance agents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from proofchain.schemas.production import ProductionAgentResult
from proofchain.schemas.workflow import WorkflowContext


class SchemaArtifact(BaseModel):
    artifact_id: str
    schema_version: str
    payload: dict[str, Any]


class SchemaEvolutionInput(BaseModel):
    workflow: WorkflowContext
    schema_name: str
    current_version: str
    target_version: str
    current_schema: dict[str, Any]
    target_schema: dict[str, Any]
    artifacts: list[SchemaArtifact] = Field(default_factory=list)
    field_mappings: dict[str, str] = Field(default_factory=dict)
    default_values: dict[str, Any] = Field(default_factory=dict)
    deployment_requested: bool = False
    human_approval_id: str | None = None


class ConvertedArtifact(BaseModel):
    artifact_id: str
    original_schema_version: str
    converted_schema_version: str
    original_hash: str
    converted_hash: str
    converted_payload: dict[str, Any]


class SchemaEvolutionResult(ProductionAgentResult):
    schema_name: str
    compatibility: Literal["backward_compatible", "migration_required", "incompatible"]
    breaking_changes: list[str] = Field(default_factory=list)
    migration_steps: list[str] = Field(default_factory=list)
    converted_artifacts: list[ConvertedArtifact] = Field(default_factory=list)
    historical_artifacts_preserved: bool = True
    deployment_decision: Literal["PASS", "BLOCK", "NEEDS_HUMAN_APPROVAL"]


class PolicyChange(BaseModel):
    policy_id: str
    base_version: str
    proposed_version: str
    document: dict[str, Any]
    reason: str


class HistoricalPolicyCase(BaseModel):
    case_id: str
    facts: dict[str, Any]
    previous_decision: str


class PolicyLifecycleInput(BaseModel):
    workflow: WorkflowContext
    active_policies: dict[str, dict[str, Any]]
    proposed_change: PolicyChange | None = None
    historical_cases: list[HistoricalPolicyCase] = Field(default_factory=list)
    activation_requested: bool = False
    human_approval_id: str | None = None


class PolicySimulationOutcome(BaseModel):
    case_id: str
    previous_decision: str
    simulated_decision: str
    changed: bool


class PolicyLifecycleResult(ProductionAgentResult):
    policy_id: str | None = None
    syntax_valid: bool = True
    conflicts: list[str] = Field(default_factory=list)
    affected_open_run_ids: list[str] = Field(default_factory=list)
    simulations: list[PolicySimulationOutcome] = Field(default_factory=list)
    historical_decisions_preserved: bool = True
    activation_decision: Literal[
        "NO_CHANGE", "ACTIVATE", "BLOCK", "NEEDS_HUMAN_APPROVAL"
    ] = "NO_CHANGE"


class TenantGrant(BaseModel):
    subject_id: str
    tenant_id: str
    departments: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class ResourceShare(BaseModel):
    share_id: str
    resource_id: str
    source_tenant_id: str
    target_tenant_id: str
    departments: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    approved: bool = False
    expires_at: datetime | None = None


class TenantGovernanceInput(BaseModel):
    workflow: WorkflowContext
    subject_id: str
    requested_tenant_id: str
    requested_department_id: str | None = None
    action: str
    resource_id: str
    resource_tenant_id: str
    resource_department_id: str | None = None
    grants: list[TenantGrant] = Field(default_factory=list)
    shares: list[ResourceShare] = Field(default_factory=list)


class TenantGovernanceResult(ProductionAgentResult):
    tenant_id: str
    department_id: str | None = None
    access_decision: Literal["ALLOW", "DENY", "NEEDS_SHARING_APPROVAL"]
    effective_permissions: list[str] = Field(default_factory=list)
    applied_share_id: str | None = None
    cross_tenant_request: bool = False
    policy_reasons: list[str] = Field(default_factory=list)


class SubmissionApproval(BaseModel):
    approval_id: str
    approver_id: str
    package_hash: str
    decision: Literal["approved", "rejected"]
    independent: bool = True
    approved_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class SubmissionInput(BaseModel):
    workflow: WorkflowContext
    package_id: str
    package_path: str
    expected_package_hash: str
    quality_status: str
    approvals: list[SubmissionApproval] = Field(default_factory=list)
    final_confirmation: bool = False
    portal_type: Literal["recording", "https"] = "recording"
    portal_destination: str = "local-submission-outbox"
    idempotency_key: str
    submission_deadline: datetime | None = None


class SubmissionReceipt(BaseModel):
    receipt_id: str
    package_id: str
    package_hash: str
    portal_type: str
    destination: str
    submitted_at: datetime
    provider_reference: str


class SubmissionResult(ProductionAgentResult):
    package_id: str
    frozen_package_hash: str | None = None
    eligibility_decision: Literal["ELIGIBLE", "NOT_ELIGIBLE", "NEEDS_FINAL_CONFIRMATION"]
    submission_status: Literal[
        "not_submitted", "submitted", "duplicate_suppressed", "rejected", "failed"
    ]
    receipt: SubmissionReceipt | None = None
    idempotency_key: str
    policy_reasons: list[str] = Field(default_factory=list)


class EvaluationScenario(BaseModel):
    scenario_id: str
    category: str
    expected_decision: str
    observed_decision: str
    expected_confidence: float | None = Field(default=None, ge=0, le=1)
    observed_confidence: float | None = Field(default=None, ge=0, le=1)
    component_under_test: str | None = None
    rationale: str | None = None
    fixture_hash: str | None = None


class EvaluationThresholds(BaseModel):
    minimum_accuracy: float = Field(default=0.95, ge=0, le=1)
    maximum_false_approval_rate: float = Field(default=0.0, ge=0, le=1)
    maximum_false_closure_rate: float = Field(default=0.0, ge=0, le=1)
    maximum_accuracy_regression: float = Field(default=0.02, ge=0, le=1)


class EvaluationInput(BaseModel):
    workflow: WorkflowContext
    release_id: str
    baseline_release_id: str | None = None
    scenarios: list[EvaluationScenario]
    baseline_metrics: dict[str, float] = Field(default_factory=dict)
    thresholds: EvaluationThresholds = Field(default_factory=EvaluationThresholds)


class EvaluationResult(ProductionAgentResult):
    release_id: str
    scenario_count: int
    accuracy: float
    false_approval_rate: float
    false_closure_rate: float
    calibration_error: float
    regression_findings: list[str] = Field(default_factory=list)
    release_decision: Literal["PASS", "BLOCK", "NEEDS_HUMAN_REVIEW"]
    scenarios: list[EvaluationScenario] = Field(default_factory=list)
    failed_scenario_ids: list[str] = Field(default_factory=list)
    category_accuracy: dict[str, float] = Field(default_factory=dict)


class KnowledgeSource(BaseModel):
    source_id: str
    title: str
    uri: str
    authority: Literal[
        "official_framework",
        "institutional_policy",
        "approved_procedure",
        "historical_package",
        "advisory_example",
    ]
    content: str
    approved: bool = True
    published_at: datetime | None = None
    valid_until: datetime | None = None
    checksum: str | None = None


class RetrievalInput(BaseModel):
    workflow: WorkflowContext
    query: str
    sources: list[KnowledgeSource]
    maximum_results: int = Field(default=5, ge=1, le=20)
    require_current_sources: bool = True


class KnowledgeCitation(BaseModel):
    source_id: str
    title: str
    uri: str
    authority: str
    source_checksum: str
    relevance_score: float = Field(ge=0, le=1)
    freshness_status: Literal["current", "expired", "undated"]
    supporting_excerpt: str


class RetrievalResult(ProductionAgentResult):
    query: str
    answer: str
    citations: list[KnowledgeCitation] = Field(default_factory=list)
    conflicting_source_ids: list[str] = Field(default_factory=list)
    advisory_only: bool = True
    human_interpretation_required: bool = False


class PhaseTwoRequest(BaseModel):
    run_id: str
    tenant_id: str = "default-institution"
    department_id: str | None = None
    backend: Literal["sqlite", "postgres"] = "sqlite"
    database_url: str | None = None
    schema_input: SchemaEvolutionInput | None = None
    policy_input: PolicyLifecycleInput | None = None
    tenant_input: TenantGovernanceInput | None = None
    submission_input: SubmissionInput | None = None
    evaluation_input: EvaluationInput | None = None
    retrieval_input: RetrievalInput | None = None
    retrieval_query: str = "What governance rules apply to accreditation evidence?"


class PhaseTwoResult(BaseModel):
    run_id: str
    status: Literal["completed", "completed_with_warnings", "blocked", "failed"]
    agent_statuses: dict[str, str]
    completion_decisions: dict[str, str]
    artifact_references: list[str]
    persistence_synchronized: bool
    started_at: datetime
    completed_at: datetime
    warnings: list[str] = Field(default_factory=list)
