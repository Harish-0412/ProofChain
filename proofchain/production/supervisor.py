"""Orchestrates Phase 1 agents around an existing ten-agent ProofChain run."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from proofchain.agents.continuation import WorkflowContinuationAgent
from proofchain.agents.identity import IdentityAuthorizationAgent
from proofchain.agents.integration import IntegrationNotificationAgent
from proofchain.agents.persistence import OperationalPersistenceAgent
from proofchain.agents.reliability import ReliabilityIncidentAgent
from proofchain.agents.security import SecurityInspectionAgent
from proofchain.agentic.global_assurance import GlobalAssuranceService
from proofchain.core.enums import WorkflowStage
from proofchain.core.paths import (
    ROOT,
    get_component_registry_path,
    get_evidence_registry_path,
    get_model_governance_manifest_path,
    get_observability_metrics_path,
    get_pipeline_result_path,
    get_policy_manifest_path,
    get_run_dir,
)
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.agentic import AgentBudget, Goal
from proofchain.schemas.components import ComponentDeclaration, ComponentRegistry
from proofchain.schemas.production import (
    AuthorizationInput,
    ContinuationInput,
    DeliveryChannel,
    NotificationInput,
    PersistenceInput,
    PhaseOneRequest,
    PhaseOneResult,
    ReliabilityInput,
    RoleGrant,
    SecurityInput,
)
from proofchain.schemas.runtime_governance import (
    AgentExecutionProfile,
    ModelGovernanceManifest,
)
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.policy_loader import GovernancePolicyCatalog


class PhaseOneSupervisor:
    """Runs operational controls without replacing the accreditation supervisor."""

    def __init__(self, *, coordination=None, store=None):
        self.store = store or AtomicJsonStore()
        self.coordination = coordination or JsonCoordinationRepository(self.store)

    def run(self, request: PhaseOneRequest) -> PhaseOneResult:
        started_at = datetime.now(tz=timezone.utc)
        workflow = self._workflow(request.run_id)
        security_paths = request.security_paths or self._evidence_paths(request.run_id)
        allowed_roots = request.security_allowed_roots or sorted(
            {
                str(Path(reference).resolve().parent)
                for reference in security_paths
            }
        )
        previous_fingerprints = self._previous_fingerprints(request.run_id)
        current_references = list(
            dict.fromkeys([*security_paths, *request.changed_references])
        )
        dependency_graph = {
            reference: [
                f"classification:{Path(reference).name}",
                f"integrity:{Path(reference).name}",
                f"package:{Path(reference).name}",
            ]
            for reference in current_references
        }
        budget = AgentBudget(
            max_plan_revisions=3,
            max_action_rounds=12,
            max_tool_retries_per_step=2,
            max_peer_requests=6,
            max_runtime_seconds=600,
        )
        runs = {}

        security_goal = self._goal(
            workflow,
            "SECURITY",
            "security_inspection",
            "Inspect all in-scope evidence and quarantine unsafe material.",
            [
                "Every evidence item has a security decision.",
                "Unsafe content cannot enter normal downstream processing.",
            ],
        )
        runs["security_inspection"] = SecurityInspectionAgent().run_goal(
            security_goal,
            SecurityInput(
                workflow=workflow,
                evidence_paths=security_paths,
                allowed_roots=allowed_roots or [str(ROOT.resolve())],
            ),
            self.coordination,
            budget,
        )

        authorization_input = request.authorization or AuthorizationInput(
            workflow=workflow,
            subject_id=workflow.requested_by,
            identity_verified=True,
            action="operate_phase_one",
            resource_id=request.run_id,
            tenant_id="default-institution",
            role_grants=[
                RoleGrant(
                    role="proofchain_operator",
                    tenant_id="default-institution",
                    departments=workflow.department_scope,
                    permissions=["operate_phase_one"],
                )
            ],
        )
        identity_goal = self._goal(
            workflow,
            "IDENTITY",
            "identity_authorization",
            "Authorize the Phase 1 operation under identity and scope policy.",
            [
                "Identity and scope are resolved.",
                "Separation-of-duties policy is evaluated.",
            ],
        )
        runs["identity_authorization"] = IdentityAuthorizationAgent().run_goal(
            identity_goal, authorization_input, self.coordination, budget
        )

        notifications = request.notifications or [
            NotificationInput(
                workflow=workflow,
                task_id=f"PHASE1-{request.run_id}",
                recipient_id="local-audit-outbox",
                approved=True,
                subject="ProofChain Phase 1 controls initialized",
                message=(
                    f"Production controls were evaluated for {request.run_id}. "
                    "This local recording is not an external notification."
                ),
                channels=[
                    DeliveryChannel(
                        channel_type="recording",
                        destination="local-audit-outbox",
                    )
                ],
                correlation_token=workflow.correlation_id,
                idempotency_key=f"PHASE1-INIT-{request.run_id}",
                disclosure_fields=["run_id", "control_status"],
            )
        ]
        notification_runs = []
        for index, notification in enumerate(notifications, 1):
            integration_goal = self._goal(
                workflow,
                f"INTEGRATION-{index:02d}",
                "integration_notification",
                f"Deliver approved task {notification.task_id} idempotently.",
                [
                    "Approval is verified.",
                    "Delivery is recorded exactly once or safely fails.",
                ],
            )
            notification_runs.append(
                IntegrationNotificationAgent().run_goal(
                    integration_goal, notification, self.coordination, budget
                )
            )
        runs["integration_notification"] = notification_runs[-1]

        continuation_goal = self._goal(
            workflow,
            "CONTINUATION",
            "workflow_continuation",
            "Calculate affected scope and a duplicate-safe partial re-execution plan.",
            [
                "Changed and reusable scope are explicit.",
                "Only affected agents are scheduled.",
            ],
        )
        runs["workflow_continuation"] = WorkflowContinuationAgent().run_goal(
            continuation_goal,
            ContinuationInput(
                workflow=workflow,
                previous_fingerprints=previous_fingerprints,
                current_references=current_references,
                dependency_graph=dependency_graph,
            ),
            self.coordination,
            budget,
        )

        reliability_goal = self._goal(
            workflow,
            "RELIABILITY",
            "reliability_incident_response",
            "Correlate operational telemetry and coordinate bounded recovery.",
            [
                "Incidents are classified.",
                "Recovery or human escalation is explicit.",
                "Evidence integrity is preserved.",
            ],
        )
        runs["reliability_incident_response"] = ReliabilityIncidentAgent().run_goal(
            reliability_goal,
            ReliabilityInput(workflow=workflow, telemetry=request.telemetry),
            self.coordination,
            budget,
        )

        persistence_goal = self._goal(
            workflow,
            "PERSISTENCE",
            "operational_persistence",
            "Persist and reconstruct all workflow state emitted by Phase 1.",
            [
                "Every workflow event is durable.",
                "Event order and hash links validate.",
                "State reconstruction succeeds.",
            ],
        )
        runs["operational_persistence"] = OperationalPersistenceAgent().run_goal(
            persistence_goal,
            PersistenceInput(
                workflow=workflow,
                backend=request.backend,
                database_url=request.database_url,
            ),
            self.coordination,
            budget,
        )

        statuses = {
            name: item.output.status if item.output else "failed"
            for name, item in runs.items()
        }
        completions = {
            name: item.completion.final_status for name, item in runs.items()
        }
        artifacts = [
            item.output.output_reference
            for item in runs.values()
            if item.output and item.output.output_reference
        ]
        blocked = any(
            status in {"blocked", "needs_human_review", "failed"}
            for status in completions.values()
        )
        warning_messages = [
            warning
            for item in runs.values()
            if item.output
            for warning in item.output.warnings
        ]
        result = PhaseOneResult(
            run_id=request.run_id,
            status=(
                "blocked"
                if blocked
                else "completed_with_warnings"
                if warning_messages
                else "completed"
            ),
            agent_statuses=statuses,
            completion_decisions=completions,
            artifact_references=artifacts,
            started_at=started_at,
            completed_at=datetime.now(tz=timezone.utc),
            warnings=warning_messages,
        )
        self._register_phase_one_governance(request.run_id)
        self.store.write(get_run_dir(request.run_id) / "phase_one_result.json", result)
        GlobalAssuranceService(self.store).evaluate(
            request.run_id, stage="phase_one"
        )
        return result

    def _workflow(self, run_id: str) -> WorkflowContext:
        payload = self.store.read(get_pipeline_result_path(run_id))
        if payload is None:
            raise FileNotFoundError(
                f"Pipeline result not found for {run_id}; run the core pipeline first."
            )
        return WorkflowContext(
            run_id=run_id,
            correlation_id=f"PHASE1-{run_id}",
            requested_by="phase-one-supervisor",
            department_scope=payload.get("department_scope", []),
            academic_year=payload.get("academic_year", "unknown"),
            requirement_scope=payload.get("requirement_scope", []),
            current_stage=WorkflowStage.COMPLETED,
        )

    def _evidence_paths(self, run_id: str) -> list[str]:
        payload = self.store.read(get_evidence_registry_path(run_id), default=[])
        return [
            item["absolute_path"]
            for item in payload
            if item.get("absolute_path")
        ]

    def _previous_fingerprints(self, run_id: str):
        payload = self.store.read(
            get_run_dir(run_id) / "continuation_reexecution_plan.json",
            default={},
        )
        from proofchain.schemas.production import FingerprintRecord

        return [
            FingerprintRecord.model_validate(item)
            for item in payload.get("fingerprints", [])
        ]

    @staticmethod
    def _goal(
        workflow: WorkflowContext,
        suffix: str,
        agent_name: str,
        objective: str,
        success_conditions: list[str],
    ) -> Goal:
        return Goal(
            goal_id=f"GOAL-{workflow.run_id}-{suffix}",
            run_id=workflow.run_id,
            parent_goal_id=f"GOAL-{workflow.run_id}-TOP",
            assigned_agent=agent_name,
            objective=objective,
            goal_type="phase_one_production_control",
            priority="high",
            constraints=[
                "Use only allowlisted tools.",
                "Do not rewrite historical events or approvals.",
                "Escalate when a governed completion condition cannot be met.",
            ],
            success_conditions=success_conditions,
        )

    def _register_phase_one_governance(self, run_id: str) -> None:
        phase_agents = {
            "operational_persistence": [
                "database_health_checker",
                "migration_planner",
                "event_importer",
                "snapshot_rebuilder",
                "persistence_integrity_validator",
                "recovery_executor",
                "materialized_view_builder",
                "persistence_completion_evaluator",
            ],
            "workflow_continuation": [
                "change_detector",
                "fingerprint_calculator",
                "dependency_impact_analyzer",
                "cache_eligibility_evaluator",
                "reexecution_planner",
                "resume_state_resolver",
                "duplicate_action_detector",
                "continuation_completion_reconciler",
            ],
            "identity_authorization": [
                "identity_resolver",
                "role_scope_evaluator",
                "permission_matcher",
                "conflict_of_interest_detector",
                "separation_of_duties_evaluator",
                "delegation_validator",
                "dual_approval_planner",
                "authorization_decision_evaluator",
            ],
            "integration_notification": [
                "channel_policy_resolver",
                "provider_selector",
                "notification_payload_builder",
                "delivery_executor",
                "receipt_verifier",
                "notification_retry_planner",
                "response_correlator",
                "integration_health_monitor",
            ],
            "security_inspection": [
                "mime_file_safety_inspector",
                "malware_scanner_adapter",
                "archive_safety_evaluator",
                "spreadsheet_formula_inspector",
                "prompt_injection_detector",
                "pii_detector",
                "access_boundary_evaluator",
                "redaction_planner",
                "security_decision_evaluator",
            ],
            "reliability_incident_response": [
                "metrics_analyzer",
                "trace_analyzer",
                "anomaly_detector",
                "failure_correlator",
                "incident_classifier",
                "recovery_planner",
                "sla_monitor",
                "incident_completion_evaluator",
            ],
        }
        registry_payload = self.store.read(
            get_component_registry_path(run_id), default={"run_id": run_id, "components": []}
        )
        registry = ComponentRegistry.model_validate(registry_payload)
        existing = {item.component_id for item in registry.components}
        for agent_name, specialists in phase_agents.items():
            if agent_name not in existing:
                registry.components.append(
                    ComponentDeclaration(
                        component_id=agent_name,
                        component_type="goal_agent",
                        has_independent_goal=True,
                        has_plan=True,
                        has_memory=True,
                        can_replan=True,
                        description="Phase 1 production and governance goal agent.",
                    )
                )
            for specialist in specialists:
                if specialist not in existing:
                    registry.components.append(
                        ComponentDeclaration(
                            component_id=specialist,
                            component_type="deterministic_specialist_module",
                            parent_agent=agent_name,
                            description=(
                                "Deterministic specialist executed inside its Phase 1 "
                                "parent goal agent."
                            ),
                        )
                    )
        self.store.write(get_component_registry_path(run_id), registry)

        catalog = GovernancePolicyCatalog.load()
        self.store.write(get_policy_manifest_path(run_id), catalog.manifest(run_id))
        model_payload = self.store.read(
            get_model_governance_manifest_path(run_id), default=None
        )
        existing_profiles = (
            ModelGovernanceManifest.model_validate(model_payload).profiles
            if model_payload
            else []
        )
        profile_names = {profile.agent_name for profile in existing_profiles}
        existing_profiles.extend(
            AgentExecutionProfile(
                agent_name=agent_name,
                execution_mode="deterministic",
                external_model_calls=0,
                high_impact_actions_require_approval=True,
                fallback_behavior="deterministic_only",
            )
            for agent_name in phase_agents
            if agent_name not in profile_names
        )
        self.store.write(
            get_model_governance_manifest_path(run_id),
            ModelGovernanceManifest(
                run_id=run_id,
                policy_fingerprint=catalog.fingerprint,
                profiles=existing_profiles,
                total_external_model_calls=sum(
                    profile.external_model_calls for profile in existing_profiles
                ),
            ),
        )
        observability = self.store.read(get_observability_metrics_path(run_id), default={})
        if observability:
            observability["primary_agent_count"] = sum(
                item.component_type == "goal_agent" for item in registry.components
            )
            observability["specialist_module_count"] = sum(
                item.component_type == "deterministic_specialist_module"
                for item in registry.components
            )
            self.store.write(get_observability_metrics_path(run_id), observability)
