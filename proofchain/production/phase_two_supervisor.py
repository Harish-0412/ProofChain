"""Orchestrates institutional governance Agents 17-22."""

from __future__ import annotations

from datetime import datetime, timezone
from proofchain.agents.evaluation import ContinuousEvaluationAgent
from proofchain.agents.knowledge_retrieval import KnowledgeRetrievalAgent
from proofchain.agents.persistence import OperationalPersistenceAgent
from proofchain.agents.policy_lifecycle import PolicyLifecycleAgent
from proofchain.agents.schema_evolution import SchemaEvolutionAgent
from proofchain.agents.submission import ExternalSubmissionAgent
from proofchain.agents.tenant_governance import TenantGovernanceAgent
from proofchain.agentic.global_assurance import GlobalAssuranceService
from proofchain.core.enums import WorkflowStage
from proofchain.core.paths import (
    POLICIES_DIR,
    get_audit_package_bundle_path,
    get_pipeline_result_path,
    get_quality_review_path,
    get_run_dir,
)
from proofchain.production.governance_registry import register_governed_agents
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.agentic import AgentBudget, Goal
from proofchain.schemas.institutional import (
    EvaluationInput,
    KnowledgeSource,
    PhaseTwoRequest,
    PhaseTwoResult,
    PolicyLifecycleInput,
    RetrievalInput,
    SchemaArtifact,
    SchemaEvolutionInput,
    SubmissionInput,
    TenantGovernanceInput,
    TenantGrant,
)
from proofchain.schemas.production import PersistenceInput
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.policy_loader import GovernancePolicyCatalog
from proofchain.services.golden_scenario_suite import GoldenScenarioSuite
from proofchain.services.submission_governance import file_sha256


PHASE_TWO_AGENTS = {
    "schema_evolution": [
        "schema_registry_reader",
        "compatibility_analyzer",
        "schema_migration_planner",
        "artifact_converter",
        "schema_regression_validator",
        "schema_deployment_gate",
    ],
    "policy_lifecycle": [
        "policy_parser",
        "policy_conflict_detector",
        "policy_impact_analyzer",
        "historical_replay_simulator",
        "policy_version_manager",
        "policy_activation_gate",
    ],
    "tenant_governance": [
        "tenant_resolver",
        "scope_boundary_evaluator",
        "cross_tenant_access_detector",
        "tenant_policy_resolver",
        "resource_sharing_planner",
        "isolation_completion_evaluator",
    ],
    "external_submission": [
        "submission_eligibility_evaluator",
        "portal_adapter_selector",
        "submission_payload_validator",
        "final_confirmation_gate",
        "submission_executor",
        "submission_receipt_verifier",
        "submission_rejection_handler",
        "submission_completion_evaluator",
    ],
    "continuous_evaluation": [
        "evaluation_dataset_resolver",
        "evaluation_planner",
        "evaluation_scenario_runner",
        "evaluation_metric_calculator",
        "evaluation_regression_detector",
        "calibration_evaluator",
        "release_decision_evaluator",
    ],
    "knowledge_retrieval": [
        "retrieval_query_planner",
        "source_authority_evaluator",
        "semantic_retriever",
        "contradiction_retriever",
        "citation_builder",
        "freshness_evaluator",
        "retrieval_completion_evaluator",
    ],
}


class PhaseTwoSupervisor:
    """Runs Phase 2 after Phase 1 has established operational controls."""

    def __init__(self, *, coordination=None, store=None):
        self.store = store or AtomicJsonStore()
        self.coordination = coordination or JsonCoordinationRepository(self.store)

    def run(self, request: PhaseTwoRequest) -> PhaseTwoResult:
        started_at = datetime.now(tz=timezone.utc)
        workflow = self._workflow(request.run_id)
        budget = AgentBudget(
            max_plan_revisions=3,
            max_action_rounds=12,
            max_tool_retries_per_step=2,
            max_peer_requests=6,
            max_runtime_seconds=600,
        )
        pipeline = self.store.read(get_pipeline_result_path(request.run_id), default={})
        runs = {}

        schema_input = request.schema_input or self._default_schema_input(
            workflow, pipeline
        )
        runs["schema_evolution"] = SchemaEvolutionAgent().run_goal(
            self._goal(
                workflow,
                "SCHEMA",
                "schema_evolution",
                "Validate schema compatibility and protect historical artifacts.",
                [
                    "Compatibility is measured.",
                    "Historical artifacts remain readable and immutable.",
                    "Unsafe deployment is blocked.",
                ],
            ),
            schema_input,
            self.coordination,
            budget,
        )

        policy_input = request.policy_input or PolicyLifecycleInput(
            workflow=workflow,
            active_policies=GovernancePolicyCatalog.load().policies,
        )
        runs["policy_lifecycle"] = PolicyLifecycleAgent().run_goal(
            self._goal(
                workflow,
                "POLICY",
                "policy_lifecycle",
                "Evaluate policy consistency, impact, and activation governance.",
                [
                    "Policy syntax and conflicts are evaluated.",
                    "Historical decisions remain immutable.",
                    "Activation remains human-controlled.",
                ],
            ),
            policy_input,
            self.coordination,
            budget,
        )

        tenant_input = request.tenant_input or TenantGovernanceInput(
            workflow=workflow,
            subject_id="phase-two-supervisor",
            requested_tenant_id=request.tenant_id,
            requested_department_id=request.department_id,
            action="govern_run",
            resource_id=request.run_id,
            resource_tenant_id=request.tenant_id,
            resource_department_id=request.department_id,
            grants=[
                TenantGrant(
                    subject_id="phase-two-supervisor",
                    tenant_id=request.tenant_id,
                    departments=[request.department_id]
                    if request.department_id
                    else [],
                    permissions=["govern_run"],
                )
            ],
        )
        runs["tenant_governance"] = TenantGovernanceAgent().run_goal(
            self._goal(
                workflow,
                "TENANT",
                "tenant_governance",
                "Enforce tenant and department isolation for the run.",
                [
                    "Tenant and department are resolved.",
                    "Cross-tenant access is denied without an approved share.",
                ],
            ),
            tenant_input,
            self.coordination,
            budget,
        )

        submission_input = request.submission_input or self._default_submission_input(
            workflow
        )
        runs["external_submission"] = ExternalSubmissionAgent().run_goal(
            self._goal(
                workflow,
                "SUBMISSION",
                "external_submission",
                "Evaluate and, only when approved, submit the frozen audit package.",
                [
                    "Package eligibility is evaluated.",
                    "Submission cannot bypass final human confirmation.",
                    "A receipt or safe refusal is persisted.",
                ],
            ),
            submission_input,
            self.coordination,
            budget,
        )

        evaluation_input = request.evaluation_input or self._default_evaluation_input(
            workflow, pipeline
        )
        runs["continuous_evaluation"] = ContinuousEvaluationAgent().run_goal(
            self._goal(
                workflow,
                "EVALUATION",
                "continuous_evaluation",
                "Evaluate release quality and block unsafe regressions.",
                [
                    "Golden scenarios execute.",
                    "False approvals and false closures are measured.",
                    "Release thresholds are enforced.",
                ],
            ),
            evaluation_input,
            self.coordination,
            budget,
        )

        retrieval_input = request.retrieval_input or RetrievalInput(
            workflow=workflow,
            query=request.retrieval_query,
            sources=self._policy_sources(),
        )
        runs["knowledge_retrieval"] = KnowledgeRetrievalAgent().run_goal(
            self._goal(
                workflow,
                "RETRIEVAL",
                "knowledge_retrieval",
                "Retrieve authoritative, cited, advisory governance guidance.",
                [
                    "Only approved sources are used.",
                    "Every material answer has citations.",
                    "Retrieval cannot override decisions.",
                ],
            ),
            retrieval_input,
            self.coordination,
            budget,
        )

        persistence = OperationalPersistenceAgent().run_goal(
            self._goal(
                workflow,
                "PERSISTENCE-PHASE2",
                "operational_persistence",
                "Synchronize Phase 2 events into the operational store.",
                [
                    "Every Phase 2 event is durable.",
                    "State reconstruction and event hashes validate.",
                ],
            ),
            PersistenceInput(
                workflow=workflow,
                backend=request.backend,
                database_url=request.database_url,
            ),
            self.coordination,
            budget,
        )

        register_governed_agents(
            run_id=request.run_id,
            agents=PHASE_TWO_AGENTS,
            description="Phase 2 institutional governance goal agent.",
            store=self.store,
        )
        statuses = {
            name: item.output.status if item.output else "failed"
            for name, item in runs.items()
        }
        completions = {
            name: item.completion.final_status for name, item in runs.items()
        }
        warnings = [
            warning
            for item in runs.values()
            if item.output
            for warning in item.output.warnings
        ]
        blocked = any(
            status in {"blocked", "failed", "needs_human_review"}
            for status in completions.values()
        )
        result = PhaseTwoResult(
            run_id=request.run_id,
            status=(
                "blocked"
                if blocked
                else "completed_with_warnings"
                if warnings
                else "completed"
            ),
            agent_statuses=statuses,
            completion_decisions=completions,
            artifact_references=[
                item.output.output_reference
                for item in runs.values()
                if item.output and item.output.output_reference
            ],
            persistence_synchronized=bool(
                persistence.output and persistence.output.recovery_verified
            ),
            started_at=started_at,
            completed_at=datetime.now(tz=timezone.utc),
            warnings=warnings,
        )
        self.store.write(get_run_dir(request.run_id) / "phase_two_result.json", result)
        GlobalAssuranceService(self.store).evaluate(
            request.run_id, stage="phase_two"
        )
        return result

    def _workflow(self, run_id: str) -> WorkflowContext:
        phase_one = self.store.read(get_run_dir(run_id) / "phase_one_result.json")
        if phase_one is None:
            raise FileNotFoundError(
                f"Phase 1 result not found for {run_id}; run run-phase-one first."
            )
        if phase_one.get("status") in {"failed", "blocked"}:
            raise ValueError("Phase 1 controls must complete before Phase 2.")
        pipeline = self.store.read(get_pipeline_result_path(run_id))
        if pipeline is None:
            raise FileNotFoundError(f"Pipeline result not found for {run_id}.")
        return WorkflowContext(
            run_id=run_id,
            correlation_id=f"PHASE2-{run_id}",
            requested_by="phase-two-supervisor",
            department_scope=pipeline.get("department_scope", []),
            academic_year=pipeline.get("academic_year", "unknown"),
            requirement_scope=pipeline.get("requirement_scope", []),
            current_stage=WorkflowStage.COMPLETED,
        )

    @staticmethod
    def _goal(workflow, suffix, agent_name, objective, conditions):
        return Goal(
            goal_id=f"GOAL-{workflow.run_id}-{suffix}",
            run_id=workflow.run_id,
            parent_goal_id=f"GOAL-{workflow.run_id}-TOP",
            assigned_agent=agent_name,
            objective=objective,
            goal_type="phase_two_institutional_governance",
            priority="high",
            constraints=[
                "Use only allowlisted tools.",
                "Preserve original artifacts and historical decisions.",
                "Do not bypass tenant, policy, or human-approval boundaries.",
            ],
            success_conditions=conditions,
        )

    @staticmethod
    def _default_schema_input(workflow, pipeline):
        schema = {
            "type": "object",
            "required": ["run_id", "status"],
            "properties": {
                "run_id": {"type": "string"},
                "status": {"type": "string"},
            },
        }
        return SchemaEvolutionInput(
            workflow=workflow,
            schema_name="PipelineResult",
            current_version="1.0.0",
            target_version="1.0.0",
            current_schema=schema,
            target_schema=schema,
            artifacts=[
                SchemaArtifact(
                    artifact_id=f"PIPELINE-{workflow.run_id}",
                    schema_version="1.0.0",
                    payload={
                        "run_id": pipeline.get("run_id", workflow.run_id),
                        "status": pipeline.get("status", "unknown"),
                    },
                )
            ],
        )

    def _default_submission_input(self, workflow):
        quality = self.store.read(get_quality_review_path(workflow.run_id), default={})
        bundle = get_audit_package_bundle_path(workflow.run_id)
        package_hash = file_sha256(bundle) if bundle.is_file() else "missing"
        return SubmissionInput(
            workflow=workflow,
            package_id=quality.get("package_id", f"PKG-{workflow.run_id}"),
            package_path=str(bundle.resolve()),
            expected_package_hash=package_hash,
            quality_status=quality.get("quality_status", "unknown"),
            approvals=[],
            final_confirmation=False,
            idempotency_key=f"SUBMIT-{workflow.run_id}-{package_hash[:12]}",
        )

    def _default_evaluation_input(self, workflow, pipeline):
        scenarios = GoldenScenarioSuite().run(
            workflow=workflow,
            package_path=get_audit_package_bundle_path(workflow.run_id),
        )
        return EvaluationInput(
            workflow=workflow,
            release_id="proofchain-0.2.0",
            scenarios=scenarios,
        )

    @staticmethod
    def _policy_sources():
        sources = []
        for index, path in enumerate(sorted(POLICIES_DIR.glob("*.yaml")), 1):
            sources.append(
                KnowledgeSource(
                    source_id=f"POLICY-{index:02d}",
                    title=path.stem.replace("_", " ").title(),
                    uri=str(path.resolve()),
                    authority="institutional_policy",
                    content=path.read_text(encoding="utf-8"),
                    approved=True,
                )
            )
        return sources
