"""Goal-oriented Supervisor for the governed three-agent ProofChain workflow."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.goal_manager import GoalManager
from proofchain.agentic.scheduler import GoalScheduler
from proofchain.agents.evidence_classification import EvidenceClassificationAgent
from proofchain.agents.evidence_collector import EvidenceCollectorAgent
from proofchain.agents.evidence_integrity import EvidenceIntegrityAgent
from proofchain.agents.claim_validation.agent import ClaimIntelligenceAgent
from proofchain.agents.gap_resolution.agent import AdaptiveGapResolutionAgent
from proofchain.agents.ownership.agent import AccountabilityOwnershipAgent
from proofchain.agents.liaison.agent import DepartmentLiaisonAgent
from proofchain.agents.closure.agent import ClosureRevalidationAgent
from proofchain.agents.audit_package.agent import AuditPackageComposerAgent
from proofchain.agents.quality_review.agent import AdversarialQualityReviewAgent
from proofchain.core.config import get_settings
from proofchain.core.enums import RunMode, WorkflowStage
from proofchain.core.exceptions import ProofChainError, StageGateError
from proofchain.core.ids import generate_correlation_id, generate_run_id
from proofchain.core.logging import TraceLogger, get_logger
from proofchain.core.paths import (
    get_classified_evidence_path,
    get_evidence_registry_path,
    get_errors_path,
    get_pipeline_trace_path,
    get_run_manifest_path,
    get_goal_graph_path,
    get_coordination_state_path,
    get_canonical_issues_path,
    get_communications_path,
    get_workflow_events_path,
    get_component_registry_path,
    get_policy_manifest_path,
    get_model_governance_manifest_path,
    get_supervisor_rounds_path,
    get_observability_metrics_path,
)
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.repositories.json_artifact_repository import JsonArtifactRepository
from proofchain.repositories.json_run_repository import JsonRunRepository
from proofchain.repositories.json_decision_repository import JsonDecisionRepository
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_lifecycle_repository import JsonLifecycleRepository
from proofchain.repositories.json_store import AtomicJsonStore, file_sha256
from proofchain.services.issue_builder import build_issue_ledger
from proofchain.services.policy_loader import GovernancePolicyCatalog
from proofchain.services.untrusted_content_scanner import UntrustedContentScanner
from proofchain.schemas.classification import (
    ClassificationAgentResult,
    ClassificationInput,
    ClassifiedEvidence,
)
from proofchain.schemas.common import AgentError, ArtifactReference, StageSummary
from proofchain.schemas.agentic import (
    AgentPlan,
    AgentBudget,
    CompletionDecision,
    CoordinationPatch,
    CoordinationState,
    Goal,
    PlanStep,
)
from proofchain.schemas.evidence import CollectorAgentResult, CollectorInput, EvidenceRecord
from proofchain.schemas.integrity import IntegrityAgentResult, IntegrityInput
from proofchain.schemas.claims import ClaimAgentResult, ClaimValidationInput
from proofchain.schemas.gaps import GapAgentResult, GapResolutionInput
from proofchain.schemas.ownership import OwnershipAgentResult, OwnershipInput
from proofchain.schemas.readiness import ExtendedAgentPipelineReport
from proofchain.schemas.closure import ClosureAgentResult, ClosureInput
from proofchain.schemas.components import ComponentDeclaration, ComponentRegistry
from proofchain.schemas.issues import IssueLedger
from proofchain.schemas.packages import AuditPackageAgentResult, AuditPackageInput
from proofchain.schemas.quality import QualityReviewAgentResult, QualityReviewInput
from proofchain.schemas.tasks import LiaisonAgentResult, LiaisonInput
from proofchain.schemas.runtime_governance import (
    AgentExecutionProfile,
    ModelGovernanceManifest,
    RunObservabilitySnapshot,
)
from proofchain.schemas.workflow import PipelineResult, SupervisorRequest, WorkflowContext


class Supervisor:
    """Decomposes an institutional goal and governs synchronized agent execution."""

    def __init__(
        self,
        run_repository: JsonRunRepository | None = None,
        coordination_repository: JsonCoordinationRepository | None = None,
    ):
        self.run_repository = run_repository or JsonRunRepository()
        self.store = AtomicJsonStore()
        self.artifacts = JsonArtifactRepository(self.store)
        self.coordination = coordination_repository or JsonCoordinationRepository(
            self.store
        )
        self.goal_manager = GoalManager()
        self.decisions = JsonDecisionRepository(self.store)
        self.lifecycle = JsonLifecycleRepository(self.store)
        self.events = JsonEventRepository()
        self.policy_catalog = GovernancePolicyCatalog.load()
        self.scheduler = GoalScheduler()
        security_policy = self.policy_catalog.security_policy()
        self.untrusted_content_scanner = UntrustedContentScanner(
            security_policy.get("prompt_injection_patterns", [])
        )
        self.logger = get_logger("proofchain.supervisor")

    def run(self, request: SupervisorRequest) -> PipelineResult:
        settings = get_settings()
        run_id = generate_run_id()
        started_at = datetime.now(tz=timezone.utc)
        started_clock = time.perf_counter()
        workflow = WorkflowContext(
            run_id=run_id,
            correlation_id=generate_correlation_id(),
            requested_by=request.requested_by,
            department_scope=request.department_scope,
            academic_year=request.academic_year,
            requirement_scope=request.requirement_scope,
            configuration_version="1.0.0",
            rule_version=settings.rule_version,
            extractor_version=settings.extractor_version,
            classifier_version=settings.classifier_version,
        )
        self.run_repository.create(workflow, request.run_mode.value)
        top_goal = self.goal_manager.create_top_level_goal(workflow, request)
        goals = self.goal_manager.decompose(top_goal, request)
        initial_state = self.coordination.initialize(top_goal, goals)
        component_registry = self._build_component_registry(workflow.run_id)
        self.lifecycle.save_component_registry(component_registry)
        policy_manifest = self.policy_catalog.manifest(workflow.run_id)
        self.lifecycle.save_policy_manifest(policy_manifest)
        self.lifecycle.save_model_governance(
            self._build_model_governance(
                workflow.run_id,
                policy_manifest.policy_fingerprint,
            )
        )
        preflight = self.scheduler.evaluate(
            run_id=workflow.run_id,
            goals=goals,
            state=initial_state,
            round_number=0,
            phase="preflight",
            maximum_rounds=request.maximum_agent_rounds,
        )
        self.lifecycle.save_scheduler_round(preflight)
        self.lifecycle.save_security_exports(workflow.run_id)
        self.events.append(
            run_id=workflow.run_id,
            event_type="RunStarted",
            aggregate_type="run",
            aggregate_id=workflow.run_id,
            actor=request.requested_by,
            payload={"run_mode": request.run_mode.value, "objective": request.objective},
        )
        goal_by_agent = {goal.assigned_agent: goal for goal in goals}
        budget = AgentBudget(max_plan_revisions=request.maximum_replans_per_agent)
        goal_completions: list[CompletionDecision] = []
        tracer = TraceLogger(run_id, get_pipeline_trace_path(run_id))
        tracer.log(
            agent="supervisor",
            event="pipeline_started",
            status="running",
            run_mode=request.run_mode.value,
            correlation_id=workflow.correlation_id,
            top_level_goal_id=top_goal.goal_id,
            objective=top_goal.objective,
        )

        collector_result: CollectorAgentResult | None = None
        classification_result: ClassificationAgentResult | None = None
        integrity_result: IntegrityAgentResult | None = None
        claim_result: ClaimAgentResult | None = None
        gap_result: GapAgentResult | None = None
        ownership_result: OwnershipAgentResult | None = None
        issue_ledger: IssueLedger | None = None
        liaison_result: LiaisonAgentResult | None = None
        closure_result: ClosureAgentResult | None = None
        audit_package_result: AuditPackageAgentResult | None = None
        quality_result: QualityReviewAgentResult | None = None
        collection_summary = None
        classification_summary = None
        integrity_summary = None
        claim_summary = None
        gap_resolution_summary = None
        ownership_summary = None
        liaison_summary = None
        closure_summary = None
        audit_package_summary = None
        quality_review_summary = None
        extended_report_reference = None
        pipeline_errors: list[AgentError] = []
        pipeline_warnings: list[str] = []

        try:
            evidence_records: list[EvidenceRecord] = []
            classified_records: list[ClassifiedEvidence] = []

            if request.run_mode in {RunMode.FULL, RunMode.COLLECT_ONLY, RunMode.RERUN}:
                workflow.current_stage = WorkflowStage.COLLECTING
                collector = EvidenceCollectorAgent(tracer=tracer)
                collector_execution = collector.run_goal(
                    goal_by_agent["evidence_collector"],
                    CollectorInput(
                        workflow=workflow,
                        source_directories=request.source_directories,
                        allowed_extensions=settings.allowed_extensions,
                    ),
                    self.coordination,
                    budget,
                )
                collector_result = collector_execution.output
                goal_completions.append(collector_execution.completion)
                if collector_result is None:
                    raise StageGateError("Collector goal produced no deterministic output.")
                evidence_records = collector_result.records
                self._gate_collection(collector_result)
                workflow.current_stage = (
                    WorkflowStage.COLLECTION_COMPLETED
                    if collector_result.status == "completed"
                    else WorkflowStage.COLLECTION_PARTIAL
                )
                collection_summary = self._summary("collection", collector_result)
                collector_artifact = self._artifact_from_result(
                    "collection",
                    collector_result,
                    len(evidence_records),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="collection",
                    status=collector_result.status,
                    input_sha256=collector_result.input_snapshot_hash or "",
                    output=collector_artifact,
                    upstream_sha256=None,
                    started_at=collector_result.started_at,
                    completed_at=collector_result.completed_at,
                )
                workflow.upstream_artifact_hash = collector_result.output_snapshot_hash
                pipeline_errors.extend(collector_result.errors)
                pipeline_warnings.extend(collector_result.warnings)

            if request.run_mode == RunMode.CLASSIFY_ONLY:
                evidence_records, upstream_hash = self._load_evidence(request.resume_run_id)
                workflow.upstream_artifact_hash = upstream_hash

            if request.run_mode in {
                RunMode.FULL,
                RunMode.CLASSIFY_ONLY,
                RunMode.RERUN,
            }:
                workflow.current_stage = WorkflowStage.CLASSIFYING
                upstream_hash = workflow.upstream_artifact_hash
                classifier = EvidenceClassificationAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["evidence_classification"])
                classification_execution = classifier.run_goal(
                    goal_by_agent["evidence_classification"],
                    ClassificationInput(
                        workflow=workflow,
                        evidence_records=evidence_records,
                    ),
                    self.coordination,
                    budget,
                )
                classification_result = classification_execution.output
                goal_completions.append(classification_execution.completion)
                if classification_result is None:
                    raise StageGateError(
                        "Classification goal produced no deterministic output."
                    )
                classified_records = classification_result.records
                prompt_injection_findings = self.untrusted_content_scanner.scan(
                    classified_records
                )
                self.lifecycle.save_prompt_injection_findings(
                    workflow.run_id,
                    prompt_injection_findings,
                )
                if prompt_injection_findings:
                    pipeline_warnings.append(
                        f"Quarantined {len(prompt_injection_findings)} "
                        "instruction-like content findings."
                    )
                    self.events.append(
                        run_id=workflow.run_id,
                        event_type="PromptInjectionFindingRecorded",
                        aggregate_type="run",
                        aggregate_id=workflow.run_id,
                        actor="untrusted_content_scanner",
                        payload={
                            "finding_count": len(prompt_injection_findings),
                            "content_executed": False,
                        },
                    )
                self._gate_classification(classification_result)
                workflow.current_stage = (
                    WorkflowStage.CLASSIFICATION_COMPLETED
                    if classification_result.status == "completed"
                    else WorkflowStage.CLASSIFICATION_PARTIAL
                )
                classification_summary = self._summary(
                    "classification", classification_result
                )
                classification_artifact = self._artifact_from_result(
                    "classification",
                    classification_result,
                    len(classified_records),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="classification",
                    status=classification_result.status,
                    input_sha256=classification_result.input_snapshot_hash or "",
                    output=classification_artifact,
                    upstream_sha256=upstream_hash,
                    started_at=classification_result.started_at,
                    completed_at=classification_result.completed_at,
                )
                workflow.upstream_artifact_hash = classification_result.output_snapshot_hash
                pipeline_errors.extend(classification_result.errors)
                pipeline_warnings.extend(classification_result.warnings)

            if request.run_mode == RunMode.INTEGRITY_ONLY:
                classified_records, upstream_hash = self._load_classification(
                    request.resume_run_id
                )
                workflow.upstream_artifact_hash = upstream_hash

            if request.run_mode in {
                RunMode.FULL,
                RunMode.INTEGRITY_ONLY,
                RunMode.RERUN,
            }:
                workflow.current_stage = WorkflowStage.VALIDATING_INTEGRITY
                upstream_hash = workflow.upstream_artifact_hash
                integrity = EvidenceIntegrityAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["evidence_integrity"])
                integrity_execution = integrity.run_goal(
                    goal_by_agent["evidence_integrity"],
                    IntegrityInput(
                        workflow=workflow,
                        classified_evidence=classified_records,
                    ),
                    self.coordination,
                    budget,
                )
                integrity_result = integrity_execution.output
                goal_completions.append(integrity_execution.completion)
                if integrity_result is None:
                    raise StageGateError("Integrity goal produced no deterministic output.")
                self._gate_integrity(integrity_result)
                workflow.current_stage = (
                    WorkflowStage.INTEGRITY_COMPLETED
                    if integrity_result.status == "completed"
                    else WorkflowStage.INTEGRITY_PARTIAL
                )
                integrity_summary = self._summary("integrity", integrity_result)
                integrity_artifact = self._artifact_from_result(
                    "integrity",
                    integrity_result,
                    len(integrity_result.findings) + len(integrity_result.gaps),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="integrity",
                    status=integrity_result.status,
                    input_sha256=integrity_result.input_snapshot_hash or "",
                    output=integrity_artifact,
                    upstream_sha256=upstream_hash,
                    started_at=integrity_result.started_at,
                    completed_at=integrity_result.completed_at,
                )
                workflow.upstream_artifact_hash = integrity_result.output_snapshot_hash
                pipeline_errors.extend(integrity_result.errors)
                pipeline_warnings.extend(integrity_result.warnings)

                claim_agent = ClaimIntelligenceAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["claim_intelligence"])
                claim_execution = claim_agent.run_goal(
                    goal_by_agent["claim_intelligence"],
                    ClaimValidationInput(
                        workflow=workflow,
                        institutional_claims=request.institutional_claims,
                        classified_evidence=classified_records,
                        bundles=integrity_result.bundles,
                        integrity_findings=integrity_result.findings,
                        integrity_gaps=integrity_result.gaps,
                    ),
                    self.coordination,
                    budget,
                )
                claim_result = claim_execution.output
                goal_completions.append(claim_execution.completion)
                if claim_result is None:
                    raise StageGateError("Claim intelligence produced no output.")
                claim_summary = self._summary("claim_intelligence", claim_result)
                claim_artifact = self._artifact_from_result(
                    "claim_intelligence", claim_result, len(claim_result.decisions)
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="claim_intelligence",
                    status=claim_result.status,
                    input_sha256=claim_result.input_snapshot_hash or "",
                    output=claim_artifact,
                    upstream_sha256=workflow.upstream_artifact_hash,
                    started_at=claim_result.started_at,
                    completed_at=claim_result.completed_at,
                )
                workflow.upstream_artifact_hash = claim_result.output_snapshot_hash
                pipeline_warnings.extend(claim_result.warnings)

                gap_agent = AdaptiveGapResolutionAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["adaptive_gap_resolution"])
                gap_execution = gap_agent.run_goal(
                    goal_by_agent["adaptive_gap_resolution"],
                    GapResolutionInput(
                        workflow=workflow,
                        claim_decisions=claim_result.decisions,
                        integrity_findings=integrity_result.findings,
                        integrity_gaps=integrity_result.gaps,
                        integrity_summaries=integrity_result.summaries,
                    ),
                    self.coordination,
                    budget,
                )
                gap_result = gap_execution.output
                goal_completions.append(gap_execution.completion)
                if gap_result is None:
                    raise StageGateError("Gap resolution produced no output.")
                gap_resolution_summary = self._summary(
                    "adaptive_gap_resolution", gap_result
                )
                gap_artifact = self._artifact_from_result(
                    "adaptive_gap_resolution",
                    gap_result,
                    len(gap_result.portfolio.gaps),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="adaptive_gap_resolution",
                    status=gap_result.status,
                    input_sha256=gap_result.input_snapshot_hash or "",
                    output=gap_artifact,
                    upstream_sha256=workflow.upstream_artifact_hash,
                    started_at=gap_result.started_at,
                    completed_at=gap_result.completed_at,
                )
                workflow.upstream_artifact_hash = gap_result.output_snapshot_hash
                pipeline_warnings.extend(gap_result.warnings)

                ownership_agent = AccountabilityOwnershipAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["accountability_ownership"])
                ownership_execution = ownership_agent.run_goal(
                    goal_by_agent["accountability_ownership"],
                    OwnershipInput(
                        workflow=workflow,
                        portfolio=gap_result.portfolio,
                    ),
                    self.coordination,
                    budget,
                )
                ownership_result = ownership_execution.output
                goal_completions.append(ownership_execution.completion)
                if ownership_result is None:
                    raise StageGateError("Ownership agent produced no output.")
                ownership_summary = self._summary(
                    "accountability_ownership", ownership_result
                )
                ownership_artifact = self._artifact_from_result(
                    "accountability_ownership",
                    ownership_result,
                    len(ownership_result.assignments),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="accountability_ownership",
                    status=ownership_result.status,
                    input_sha256=ownership_result.input_snapshot_hash or "",
                    output=ownership_artifact,
                    upstream_sha256=workflow.upstream_artifact_hash,
                    started_at=ownership_result.started_at,
                    completed_at=ownership_result.completed_at,
                )
                workflow.upstream_artifact_hash = ownership_result.output_snapshot_hash
                pipeline_warnings.extend(ownership_result.warnings)

                issue_ledger = build_issue_ledger(
                    run_id=workflow.run_id,
                    findings=integrity_result.findings,
                    evidence_gaps=integrity_result.gaps,
                    claim_decisions=claim_result.decisions,
                    portfolio=gap_result.portfolio,
                )
                self.lifecycle.save_issues(issue_ledger)
                workflow.upstream_artifact_hash = ownership_result.output_snapshot_hash

                liaison_agent = DepartmentLiaisonAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["department_liaison"])
                liaison_execution = liaison_agent.run_goal(
                    goal_by_agent["department_liaison"],
                    LiaisonInput(
                        workflow=workflow,
                        portfolio=gap_result.portfolio,
                        ownership=ownership_result,
                        canonical_issues=issue_ledger.issues,
                    ),
                    self.coordination,
                    budget,
                )
                liaison_result = liaison_execution.output
                goal_completions.append(liaison_execution.completion)
                if liaison_result is None:
                    raise StageGateError("Department liaison produced no output.")
                liaison_summary = self._summary("department_liaison", liaison_result)
                liaison_artifact = self._artifact_from_result(
                    "department_liaison", liaison_result, len(liaison_result.tasks)
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="department_liaison",
                    status=liaison_result.status,
                    input_sha256=liaison_result.input_snapshot_hash or "",
                    output=liaison_artifact,
                    upstream_sha256=workflow.upstream_artifact_hash,
                    started_at=liaison_result.started_at,
                    completed_at=liaison_result.completed_at,
                )
                workflow.upstream_artifact_hash = liaison_result.output_snapshot_hash
                issue_ledger.resolution_tasks = len(liaison_result.tasks)
                for issue in issue_ledger.issues:
                    issue.resolution_task_ids = [
                        task.task_id for task in liaison_result.tasks if task.issue_id == issue.issue_id
                    ]
                self.lifecycle.save_issues(issue_ledger)
                pipeline_warnings.extend(liaison_result.warnings)

                closure_agent = ClosureRevalidationAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["closure_revalidation"])
                closure_execution = closure_agent.run_goal(
                    goal_by_agent["closure_revalidation"],
                    ClosureInput(
                        workflow=workflow,
                        canonical_issues=issue_ledger.issues,
                        tasks=liaison_result.tasks,
                        classified_evidence=classified_records,
                        integrity_findings=integrity_result.findings,
                        claim_decisions=claim_result.decisions,
                        portfolio=gap_result.portfolio,
                    ),
                    self.coordination,
                    budget,
                )
                closure_result = closure_execution.output
                goal_completions.append(closure_execution.completion)
                if closure_result is None:
                    raise StageGateError("Closure revalidation produced no output.")
                closure_summary = self._summary("closure_revalidation", closure_result)
                closure_artifact = self._artifact_from_result(
                    "closure_revalidation",
                    closure_result,
                    len(closure_result.closure_checks),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="closure_revalidation",
                    status=closure_result.status,
                    input_sha256=closure_result.input_snapshot_hash or "",
                    output=closure_artifact,
                    upstream_sha256=workflow.upstream_artifact_hash,
                    started_at=closure_result.started_at,
                    completed_at=closure_result.completed_at,
                )
                workflow.upstream_artifact_hash = closure_result.output_snapshot_hash
                pipeline_warnings.extend(closure_result.warnings)

                package_agent = AuditPackageComposerAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["audit_package_composer"])
                package_execution = package_agent.run_goal(
                    goal_by_agent["audit_package_composer"],
                    AuditPackageInput(
                        workflow=workflow,
                        evidence_records=evidence_records,
                        claim_decisions=claim_result.decisions,
                        canonical_issues=closure_result.updated_issues,
                        closure_result=closure_result,
                    ),
                    self.coordination,
                    budget,
                )
                audit_package_result = package_execution.output
                goal_completions.append(package_execution.completion)
                if audit_package_result is None:
                    raise StageGateError("Audit package composer produced no output.")
                audit_package_summary = self._summary(
                    "audit_package_composer", audit_package_result
                )
                package_artifact = self._artifact_from_result(
                    "audit_package_composer",
                    audit_package_result,
                    len(audit_package_result.manifest.eligible_evidence),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="audit_package_composer",
                    status=audit_package_result.status,
                    input_sha256=audit_package_result.input_snapshot_hash or "",
                    output=package_artifact,
                    upstream_sha256=workflow.upstream_artifact_hash,
                    started_at=audit_package_result.started_at,
                    completed_at=audit_package_result.completed_at,
                )
                workflow.upstream_artifact_hash = audit_package_result.output_snapshot_hash
                pipeline_warnings.extend(audit_package_result.warnings)

                quality_agent = AdversarialQualityReviewAgent(tracer=tracer)
                self._activate_goal(goal_by_agent["adversarial_quality_review"])
                quality_execution = quality_agent.run_goal(
                    goal_by_agent["adversarial_quality_review"],
                    QualityReviewInput(
                        workflow=workflow,
                        package_manifest=audit_package_result.manifest,
                        claim_decisions=claim_result.decisions,
                    ),
                    self.coordination,
                    budget,
                )
                quality_result = quality_execution.output
                goal_completions.append(quality_execution.completion)
                if quality_result is None:
                    raise StageGateError("Quality review produced no output.")
                quality_review_summary = self._summary(
                    "adversarial_quality_review", quality_result
                )
                quality_artifact = self._artifact_from_result(
                    "adversarial_quality_review",
                    quality_result,
                    len(quality_result.claim_challenges),
                )
                self.run_repository.register_checkpoint(
                    workflow,
                    stage_name="adversarial_quality_review",
                    status=quality_result.status,
                    input_sha256=quality_result.input_snapshot_hash or "",
                    output=quality_artifact,
                    upstream_sha256=workflow.upstream_artifact_hash,
                    started_at=quality_result.started_at,
                    completed_at=quality_result.completed_at,
                )
                workflow.upstream_artifact_hash = quality_result.output_snapshot_hash
                pipeline_warnings.extend(quality_result.warnings)

                extended_report_reference = self.decisions.save_report(
                    self._build_extended_report(
                        request=request,
                        claim_result=claim_result,
                        gap_result=gap_result,
                        ownership_result=ownership_result,
                        integrity_result=integrity_result,
                        issue_ledger=issue_ledger,
                        liaison_result=liaison_result,
                        closure_result=closure_result,
                        audit_package_result=audit_package_result,
                        quality_result=quality_result,
                    )
                )

            self._process_coordination_requests(
                request=request,
                goals=goals,
                collector_result=collector_result,
                classification_result=classification_result,
                tracer=tracer,
            )
            status = self._final_status_agentic(
                collector_result,
                classification_result,
                integrity_result,
                goal_completions,
                request.human_approval_for_final_decision,
            )
            workflow.current_stage = self._workflow_status(status)
        except ProofChainError as exc:
            status = "failed"
            workflow.current_stage = WorkflowStage.FAILED
            pipeline_errors.append(
                AgentError(
                    error_code=exc.error_code,
                    agent_name="supervisor",
                    stage=workflow.current_stage.value,
                    severity="critical",
                    recoverable=exc.recoverable,
                    message=exc.message,
                    technical_details=str(exc.context) if exc.context else None,
                )
            )
            tracer.log_error(
                agent="supervisor",
                error_code=exc.error_code,
                message=exc.message,
            )

        completed_at = datetime.now(tz=timezone.utc)
        coordination_state = self.coordination.load_state(run_id)
        final_decision = self._top_level_completion(
            top_goal=top_goal,
            status=status,
            goal_completions=goal_completions,
            coordination_state=coordination_state,
        )
        top_goal.status = {
            "completed": "completed",
            "completed_with_warnings": "completed",
            "needs_human_review": "needs_human_review",
            "blocked": "blocked",
            "failed": "failed",
        }[final_decision.final_status]
        self.coordination.save_goal(top_goal)
        self.coordination.save_completion(final_decision)
        final_decision_path = self.coordination.save_final_decision(final_decision)
        coordination_state = self.coordination.load_state(run_id)
        terminal_schedule = self.scheduler.evaluate(
            run_id=run_id,
            goals=self.coordination.get_goals(run_id),
            state=coordination_state,
            round_number=coordination_state.supervisor_round,
            phase="terminal",
            maximum_rounds=request.maximum_agent_rounds,
        )
        self.lifecycle.save_scheduler_round(terminal_schedule)
        result = PipelineResult(
            run_id=run_id,
            status=status,
            academic_year=request.academic_year,
            department_scope=request.department_scope,
            requirement_scope=request.requirement_scope,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=int((time.perf_counter() - started_clock) * 1000),
            collection_summary=collection_summary,
            classification_summary=classification_summary,
            integrity_summary=integrity_summary,
            claim_summary=claim_summary,
            gap_resolution_summary=gap_resolution_summary,
            ownership_summary=ownership_summary,
            liaison_summary=liaison_summary,
            closure_summary=closure_summary,
            audit_package_summary=audit_package_summary,
            quality_review_summary=quality_review_summary,
            total_files_discovered=collector_result.input_count if collector_result else 0,
            total_evidence_registered=len(collector_result.records)
            if collector_result
            else 0,
            total_documents_classified=len(classification_result.records)
            if classification_result
            else 0,
            total_documents_unresolved=classification_result.unresolved_count
            if classification_result
            else 0,
            total_findings=len(integrity_result.findings) if integrity_result else 0,
            total_gaps=len(integrity_result.gaps) if integrity_result else 0,
            blocking_findings=(
                sum(finding.blocking for finding in integrity_result.findings)
                + sum(gap.blocking for gap in integrity_result.gaps)
                if integrity_result
                else 0
            ),
            total_claims=len(claim_result.decisions) if claim_result else 0,
            claims_requiring_review=sum(
                item.requires_human_review for item in claim_result.decisions
            )
            if claim_result
            else 0,
            total_resolution_gaps=len(gap_result.portfolio.gaps)
            if gap_result
            else 0,
            total_ownership_assignments=len(ownership_result.assignments)
            if ownership_result
            else 0,
            unresolved_ownership=len(ownership_result.unresolved_ownership)
            if ownership_result
            else 0,
            total_canonical_issues=issue_ledger.canonical_issues
            if issue_ledger
            else 0,
            blocking_canonical_issues=issue_ledger.blocking_canonical_issues
            if issue_ledger
            else 0,
            total_resolution_tasks=len(liaison_result.tasks)
            if liaison_result
            else 0,
            total_closure_checks=len(closure_result.closure_checks)
            if closure_result
            else 0,
            resolved_issues=sum(
                issue.status == "RESOLVED" for issue in closure_result.updated_issues
            )
            if closure_result
            else 0,
            package_eligible_evidence=len(
                audit_package_result.manifest.eligible_evidence
            )
            if audit_package_result
            else 0,
            quality_required_corrections=len(quality_result.required_corrections)
            if quality_result
            else 0,
            evidence_output_path=collector_result.output_reference
            if collector_result
            else None,
            classification_output_path=classification_result.output_reference
            if classification_result
            else None,
            integrity_output_path=integrity_result.output_reference
            if integrity_result
            else None,
            trace_output_path=str(get_pipeline_trace_path(run_id).resolve()),
            run_manifest_path=str(get_run_manifest_path(run_id).resolve()),
            top_level_goal_id=top_goal.goal_id,
            goal_graph_path=str(get_goal_graph_path(run_id).resolve()),
            coordination_state_path=str(get_coordination_state_path(run_id).resolve()),
            final_decision_path=str(final_decision_path.resolve()),
            claim_output_path=claim_result.output_reference if claim_result else None,
            gap_resolution_output_path=gap_result.output_reference if gap_result else None,
            ownership_output_path=ownership_result.output_reference
            if ownership_result
            else None,
            extended_report_path=extended_report_reference.path
            if extended_report_reference
            else None,
            canonical_issues_path=str(get_canonical_issues_path(run_id).resolve())
            if issue_ledger
            else None,
            liaison_tasks_path=liaison_result.output_reference
            if liaison_result
            else None,
            communications_path=str(get_communications_path(run_id).resolve())
            if liaison_result
            else None,
            closure_output_path=closure_result.output_reference
            if closure_result
            else None,
            audit_package_output_path=audit_package_result.output_reference
            if audit_package_result
            else None,
            quality_review_output_path=quality_result.output_reference
            if quality_result
            else None,
            workflow_events_path=str(get_workflow_events_path(run_id).resolve()),
            component_registry_path=str(get_component_registry_path(run_id).resolve()),
            policy_manifest_path=str(get_policy_manifest_path(run_id).resolve()),
            model_governance_manifest_path=str(
                get_model_governance_manifest_path(run_id).resolve()
            ),
            supervisor_rounds_path=str(get_supervisor_rounds_path(run_id).resolve()),
            observability_metrics_path=str(
                get_observability_metrics_path(run_id).resolve()
            ),
            audit_package_bundle_path=(
                audit_package_result.manifest.bundle_path
                if audit_package_result
                else None
            ),
            supervisor_rounds=coordination_state.supervisor_round,
            warnings=pipeline_warnings,
            errors=pipeline_errors,
        )
        self.store.write(get_errors_path(run_id), pipeline_errors)
        self.events.append(
            run_id=run_id,
            event_type="RunCompleted",
            aggregate_type="run",
            aggregate_id=run_id,
            actor="supervisor",
            payload={
                "status": status,
                "final_decision_id": final_decision.decision_id,
                "policy_fingerprint": policy_manifest.policy_fingerprint,
            },
        )
        self.lifecycle.save_observability(
            self._build_observability(
                result=result,
                component_registry=component_registry,
                coordination_state=coordination_state,
                issue_ledger=issue_ledger,
                policy_fingerprint=policy_manifest.policy_fingerprint,
            )
        )
        self.run_repository.complete(result)
        tracer.log(
            agent="supervisor",
            event="pipeline_completed",
            status=status,
            findings=result.total_findings,
            gaps=result.total_gaps,
            top_level_goal_id=top_goal.goal_id,
            supervisor_rounds=coordination_state.supervisor_round,
        )
        self.logger.info(
            "Pipeline %s finished with status=%s evidence=%s findings=%s gaps=%s",
            run_id,
            status,
            result.total_evidence_registered,
            result.total_findings,
            result.total_gaps,
        )
        return result

    @staticmethod
    def _build_extended_report(
        *,
        request: SupervisorRequest,
        claim_result: ClaimAgentResult,
        gap_result: GapAgentResult,
        ownership_result: OwnershipAgentResult,
        integrity_result: IntegrityAgentResult,
        issue_ledger: IssueLedger | None = None,
        liaison_result: LiaisonAgentResult | None = None,
        closure_result: ClosureAgentResult | None = None,
        audit_package_result: AuditPackageAgentResult | None = None,
        quality_result: QualityReviewAgentResult | None = None,
    ) -> ExtendedAgentPipelineReport:
        status_counts: dict[str, int] = {}
        for decision in claim_result.decisions:
            status_counts[decision.status] = status_counts.get(decision.status, 0) + 1
        priority_by_gap = {
            item.gap_id: item for item in gap_result.portfolio.priorities
        }
        plan_by_gap = {
            item.gap_id: item for item in gap_result.portfolio.plans
        }
        resolution_items = []
        next_actions = []
        for gap in gap_result.portfolio.gaps:
            plan = plan_by_gap[gap.gap_id]
            strategy = next(
                item
                for item in plan.strategies
                if item.strategy_id == plan.recommended_strategy_id
            )
            resolution_items.append(
                {
                    "gap_id": gap.gap_id,
                    "priority": priority_by_gap[gap.gap_id].priority,
                    "recommended_action": strategy.title,
                    "readiness_delta": plan.expected_readiness_delta,
                    "blocking": gap.blocking,
                }
            )
            next_actions.append(strategy.title)
        blocking = any(item.blocking for item in integrity_result.findings) or any(
            item.blocking for item in integrity_result.gaps
        )
        return ExtendedAgentPipelineReport(
            run_id=claim_result.run_id,
            criterion_ids=request.requirement_scope,
            academic_year=request.academic_year,
            departments=request.department_scope,
            claim_assessment={
                "total_claims": len(claim_result.decisions),
                **status_counts,
                "overall_claim_confidence": round(
                    sum(item.confidence for item in claim_result.decisions)
                    / max(1, len(claim_result.decisions)),
                    4,
                ),
            },
            claim_details=[
                {
                    "claim_id": item.claim_id,
                    "status": item.status,
                    "confidence": item.confidence,
                    "defensible_version": item.defensible_claim_text,
                    "blocking_reasons": [
                        contradiction.likely_root_cause
                        for contradiction in item.contradictions
                    ],
                }
                for item in claim_result.decisions
            ],
            gap_assessment={
                "total_gaps": len(gap_result.portfolio.gaps),
                "blocking_gaps": sum(
                    item.blocking for item in gap_result.portfolio.gaps
                ),
                "evidence_debt_score": gap_result.portfolio.evidence_debt_score,
                "current_verified_readiness": (
                    gap_result.portfolio.current_verified_readiness
                    or gap_result.portfolio.current_readiness
                ),
                "projected_readiness": gap_result.portfolio.projected_readiness,
                "projection_type": gap_result.portfolio.projection_type,
                "projection_confidence": gap_result.portfolio.projection_confidence,
                "projection_assumptions": gap_result.portfolio.projection_assumptions,
                "projection_unresolved_dependencies": gap_result.portfolio.projection_unresolved_dependencies,
                "scenario_bands": gap_result.portfolio.scenario_bands,
                "not_an_approval": gap_result.portfolio.not_an_approval,
                "raw_findings": issue_ledger.raw_findings if issue_ledger else len(integrity_result.findings),
                "claim_failures": issue_ledger.claim_failures if issue_ledger else 0,
                "raw_gaps": issue_ledger.raw_gaps if issue_ledger else len(integrity_result.gaps),
                "canonical_issues": issue_ledger.canonical_issues if issue_ledger else len(gap_result.portfolio.gaps),
                "blocking_canonical_issues": issue_ledger.blocking_canonical_issues if issue_ledger else 0,
                "resolution_tasks": issue_ledger.resolution_tasks if issue_ledger else 0,
            },
            resolution_portfolio=resolution_items,
            ownership_summary={
                "assigned_tasks": ownership_result.success_count,
                "unresolved_ownership": len(
                    ownership_result.unresolved_ownership
                ),
                "conflicts_detected": sum(
                    assignment.conflict_checks.get("conflict_of_interest", False)
                    for assignment in ownership_result.assignments
                ),
                "conflicts_resolved": 0,
            },
            assignments=[
                {
                    "gap_id": item.gap_id,
                    "primary_owner": item.primary_owner.display_name
                    if item.primary_owner
                    else None,
                    "backup_owner": item.backup_owner.display_name
                    if item.backup_owner
                    else None,
                    "approver": item.approver.display_name
                    if item.approver
                    else None,
                    "assignment_confidence": item.assignment_confidence,
                    "status": item.status,
                }
                for item in ownership_result.assignments
            ],
            lifecycle_summary={
                "resolution_tasks": len(liaison_result.tasks) if liaison_result else 0,
                "active_tasks": sum(task.status == "active" for task in liaison_result.tasks)
                if liaison_result
                else 0,
                "closure_checks": len(closure_result.closure_checks) if closure_result else 0,
                "resolved_issues": sum(
                    issue.status == "RESOLVED" for issue in closure_result.updated_issues
                )
                if closure_result
                else 0,
                "audit_package_status": audit_package_result.manifest.status
                if audit_package_result
                else None,
                "quality_status": quality_result.quality_status if quality_result else None,
                "quality_required_corrections": len(quality_result.required_corrections)
                if quality_result
                else 0,
            },
            overall_status=(
                "not_yet_defensible"
                if blocking
                else "defensible_pending_human_approval"
            ),
            next_required_actions=list(dict.fromkeys(next_actions)),
        )

    def _activate_goal(self, goal: Goal) -> None:
        state = self.coordination.load_state(goal.run_id)
        if goal.goal_id not in state.active_goals:
            self.coordination.update_state(
                goal.run_id,
                state.state_version,
                CoordinationPatch(activate_goals=[goal.goal_id]),
            )

    def _process_coordination_requests(
        self,
        *,
        request: SupervisorRequest,
        goals: list[Goal],
        collector_result: CollectorAgentResult | None,
        classification_result: ClassificationAgentResult | None,
        tracer: TraceLogger,
    ) -> None:
        """Route peer requests into explicit resolution tasks with bounded probing."""
        run_id = goals[0].run_id if goals else collector_result.run_id
        for round_number in range(1, request.maximum_agent_rounds + 1):
            messages = self.coordination.get_open_messages(run_id)
            if not messages:
                state = self.coordination.load_state(run_id)
                self.lifecycle.save_scheduler_round(
                    self.scheduler.evaluate(
                        run_id=run_id,
                        goals=self.coordination.get_goals(run_id),
                        state=state,
                        round_number=state.supervisor_round,
                        phase="coordination",
                        maximum_rounds=request.maximum_agent_rounds,
                    )
                )
                break
            self.coordination.patch_retrying(
                messages[0].run_id,
                CoordinationPatch(supervisor_round_increment=1),
            )
            progressed = False
            for message in messages:
                resolution = self._probe_message(
                    message,
                    collector_result=collector_result,
                    classification_result=classification_result,
                )
                self.coordination.add_resolution_task(
                    message.run_id,
                    {
                        "task_id": f"TASK-{uuid4().hex[:12].upper()}",
                        "source_message_id": message.message_id,
                        "title": message.reason,
                        "responsible_agent": message.target_agent,
                        "blocking": message.priority in {"critical", "high"},
                        "status": resolution["status"],
                        "resolution": resolution["explanation"],
                        "round": round_number,
                    },
                )
                self._record_resolution_goal(message, resolution)
                self.coordination.resolve_message(
                    message,
                    status=resolution["message_status"],
                    resolution=resolution["explanation"],
                )
                tracer.log(
                    agent="supervisor",
                    event="coordination_message_resolved",
                    status=resolution["status"],
                    message_id=message.message_id,
                    target_agent=message.target_agent,
                )
                progressed = True
            state = self.coordination.load_state(run_id)
            self.lifecycle.save_scheduler_round(
                self.scheduler.evaluate(
                    run_id=run_id,
                    goals=self.coordination.get_goals(run_id),
                    state=state,
                    round_number=state.supervisor_round,
                    phase="coordination",
                    maximum_rounds=request.maximum_agent_rounds,
                    messages_processed=len(messages),
                )
            )
            if not progressed:
                break

    def _record_resolution_goal(self, message, resolution: dict[str, str]) -> None:
        """Turn each peer request into a terminal, replayable dynamic subgoal."""
        goal = Goal(
            goal_id=f"GOAL-{message.run_id}-RES-{message.message_id}",
            run_id=message.run_id,
            parent_goal_id=message.goal_id,
            assigned_agent=message.target_agent,
            objective=message.reason,
            goal_type=f"resolve_{message.message_type}",
            priority=message.priority,
            input_references=message.related_evidence_ids,
            success_conditions=[
                "The peer request is assessed against current committed evidence.",
                "The resolution or remaining blocker is recorded.",
            ],
            dependencies=[message.goal_id],
            status="executing",
        )
        self.coordination.save_goal(goal)
        plan = AgentPlan(
            plan_id=f"PLAN-RES-{uuid4().hex[:10].upper()}",
            run_id=message.run_id,
            goal_id=goal.goal_id,
            agent_name=message.target_agent,
            revision=1,
            rationale=(
                "Reopen the requested responsibility using current committed state "
                "without modifying original evidence."
            ),
            steps=[
                PlanStep(
                    step_id=f"STEP-RES-{uuid4().hex[:10].upper()}",
                    sequence=1,
                    objective="Assess the peer request and record the bounded resolution.",
                    expected_observation=resolution["explanation"],
                    completion_condition="The request has a terminal documented outcome.",
                    status="completed",
                )
            ],
            dependencies=[message.goal_id],
            expected_outputs=["resolution_tasks.json"],
            status="completed",
        )
        self.coordination.save_plan(plan)
        final_status = (
            "completed"
            if resolution["status"] == "resolved"
            else "needs_human_review"
            if resolution["status"] == "needs_human_review"
            else "blocked"
        )
        satisfied = final_status == "completed"
        goal.status = (
            "completed"
            if satisfied
            else "needs_human_review"
            if final_status == "needs_human_review"
            else "blocked"
        )
        self.coordination.save_goal(goal)
        self.coordination.save_completion(
            CompletionDecision(
                decision_id=f"DEC-{uuid4().hex[:12].upper()}",
                run_id=message.run_id,
                goal_id=goal.goal_id,
                agent_name=message.target_agent,
                goal_satisfied=satisfied,
                success_conditions_met=goal.success_conditions if satisfied else [],
                success_conditions_unmet=[] if satisfied else goal.success_conditions,
                blockers=[resolution["explanation"]] if not satisfied else [],
                confidence=1.0,
                final_status=final_status,
                explanation=resolution["explanation"],
                supporting_artifacts=message.related_evidence_ids,
            )
        )

    @staticmethod
    def _probe_message(
        message,
        *,
        collector_result: CollectorAgentResult | None,
        classification_result: ClassificationAgentResult | None,
    ) -> dict[str, str]:
        """Use current committed state to determine whether a peer can act again."""
        if message.target_agent == "evidence_collector":
            known_ids = {
                record.evidence_id for record in collector_result.records
            } if collector_result else set()
            related = set(message.related_evidence_ids)
            if related and related - known_ids:
                return {
                    "status": "needs_human_review",
                    "message_status": "resolved",
                    "explanation": (
                        "The requested evidence is outside the committed registry; "
                        "an owner must add it to an approved source before resume."
                    ),
                }
            return {
                "status": "blocked",
                "message_status": "resolved",
                "explanation": (
                    "Collector source scope was reopened for assessment, but all "
                    "currently approved files were already registered. The missing "
                    "evidence remains a disclosed blocker."
                ),
            }
        if message.target_agent == "evidence_classification":
            records = {
                record.evidence_id: record
                for record in (classification_result.records if classification_result else [])
            }
            unresolved = [
                evidence_id
                for evidence_id in message.related_evidence_ids
                if evidence_id not in records
                or records[evidence_id].requires_human_review
            ]
            return {
                "status": "needs_human_review" if unresolved else "resolved",
                "message_status": "resolved",
                "explanation": (
                    f"Reclassification assessment found {len(unresolved)} unresolved "
                    "items; deterministic source data was preserved."
                    if unresolved
                    else "The committed classification already resolves the requested items."
                ),
            }
        return {
            "status": "resolved",
            "message_status": "resolved",
            "explanation": "Supervisor recorded the informational request in the audit trace.",
        }

    @staticmethod
    def _top_level_completion(
        *,
        top_goal: Goal,
        status: str,
        goal_completions: list[CompletionDecision],
        coordination_state,
    ) -> CompletionDecision:
        positive = status in {"completed", "completed_with_warnings"}
        blockers = [
            blocker
            for decision in goal_completions
            for blocker in decision.blockers
        ]
        questions = [
            question
            for decision in goal_completions
            for question in decision.unresolved_questions
        ]
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=top_goal.run_id,
            goal_id=top_goal.goal_id,
            agent_name="supervisor",
            goal_satisfied=positive,
            success_conditions_met=top_goal.success_conditions if positive else [],
            success_conditions_unmet=[] if positive else top_goal.success_conditions,
            blockers=blockers,
            unresolved_questions=questions,
            confidence=min(
                (decision.confidence for decision in goal_completions),
                default=0.0,
            ),
            final_status=status,
            explanation=(
                f"Supervisor evaluated {len(goal_completions)} agent completion claims, "
                f"{len(coordination_state.blocked_goals)} blocked goals, and "
                f"{len(coordination_state.open_messages)} open peer requests."
            ),
            supporting_artifacts=[
                artifact
                for decision in goal_completions
                for artifact in decision.supporting_artifacts
            ],
        )

    @staticmethod
    def _artifact_from_result(stage, result, record_count) -> ArtifactReference:
        return ArtifactReference(
            stage_name=stage,
            path=result.output_reference or "",
            sha256=result.output_snapshot_hash or "",
            record_count=record_count,
            agent_run_id=result.agent_run_id,
            committed_at=result.completed_at,
        )

    @staticmethod
    def _summary(stage_name: str, result) -> StageSummary:
        return StageSummary(
            stage_name=stage_name,
            status=result.status,
            success_count=result.success_count,
            warning_count=result.warning_count,
            failure_count=result.failure_count,
            duration_ms=result.duration_ms,
            started_at=result.started_at,
            completed_at=result.completed_at,
            notes=result.warnings[:10],
        )

    @staticmethod
    def _build_component_registry(run_id: str) -> ComponentRegistry:
        primary_agents = [
            "evidence_collector",
            "evidence_classification",
            "evidence_integrity",
            "claim_intelligence",
            "adaptive_gap_resolution",
            "accountability_ownership",
            "department_liaison",
            "closure_revalidation",
            "audit_package_composer",
            "adversarial_quality_review",
        ]
        specialist_modules = {
            "claim_intelligence": [
                "claim_decomposer",
                "evidence_retriever",
                "contradiction_investigator",
                "sufficiency_evaluator",
                "defensibility_judge",
            ],
            "adaptive_gap_resolution": [
                "gap_detector",
                "root_cause_analyzer",
                "resolution_planner",
                "readiness_simulator",
                "gap_prioritizer",
            ],
            "accountability_ownership": [
                "provenance_resolver",
                "responsibility_matcher",
                "workload_balancer",
                "escalation_planner",
                "assignment_validator",
            ],
            "department_liaison": [
                "communication_scope",
                "task_composer",
                "message_drafter",
                "approval_gate",
                "dispatcher",
                "response_intake",
                "sla_escalation",
            ],
            "closure_revalidation": [
                "submission_intake",
                "evidence_difference",
                "targeted_revalidation",
                "closure_verifier",
                "regression_detector",
                "issue_state_decider",
            ],
            "audit_package_composer": [
                "scope_resolver",
                "evidence_selector",
                "evidence_orderer",
                "narrative_composer",
                "index_builder",
                "privacy_redactor",
                "package_assembler",
                "package_integrity",
            ],
            "adversarial_quality_review": [
                "completeness_reviewer",
                "reference_reviewer",
                "claim_challenger",
                "reuse_auditor",
                "policy_reviewer",
                "reviewer_simulator",
                "risk_scorer",
            ],
        }
        components = [
            ComponentDeclaration(
                component_id=agent,
                component_type="goal_agent",
                has_independent_goal=True,
                has_plan=True,
                has_memory=True,
                can_replan=True,
                description="Primary ProofChain governed goal agent.",
            )
            for agent in primary_agents
        ]
        for parent, children in specialist_modules.items():
            components.extend(
                ComponentDeclaration(
                    component_id=child,
                    component_type="deterministic_specialist_module",
                    parent_agent=parent,
                    has_independent_goal=False,
                    has_plan=False,
                    has_memory=False,
                    can_replan=False,
                    description="Deterministic specialist module executed inside its parent goal agent.",
                )
                for child in children
            )
        return ComponentRegistry(run_id=run_id, components=components)

    @staticmethod
    def _build_model_governance(
        run_id: str,
        policy_fingerprint: str,
    ) -> ModelGovernanceManifest:
        agents = [
            "evidence_collector",
            "evidence_classification",
            "evidence_integrity",
            "claim_intelligence",
            "adaptive_gap_resolution",
            "accountability_ownership",
            "department_liaison",
            "closure_revalidation",
            "audit_package_composer",
            "adversarial_quality_review",
        ]
        return ModelGovernanceManifest(
            run_id=run_id,
            policy_fingerprint=policy_fingerprint,
            profiles=[
                AgentExecutionProfile(
                    agent_name=agent_name,
                    execution_mode="deterministic",
                    external_model_calls=0,
                    high_impact_actions_require_approval=True,
                    fallback_behavior="deterministic_only",
                )
                for agent_name in agents
            ],
            total_external_model_calls=0,
        )

    def _build_observability(
        self,
        *,
        result: PipelineResult,
        component_registry: ComponentRegistry,
        coordination_state: CoordinationState,
        issue_ledger: IssueLedger | None,
        policy_fingerprint: str,
    ) -> RunObservabilitySnapshot:
        goals = self.coordination.get_goals(result.run_id)
        primary_agents = sum(
            item.component_type == "goal_agent"
            for item in component_registry.components
        )
        specialist_modules = sum(
            item.component_type == "deterministic_specialist_module"
            for item in component_registry.components
        )
        manifest = self.run_repository.load_manifest(result.run_id)
        unresolved_issues = (
            sum(
                issue.status not in {"RESOLVED", "WAIVED_WITH_APPROVAL", "CANCELLED"}
                for issue in issue_ledger.issues
            )
            if issue_ledger
            else 0
        )
        return RunObservabilitySnapshot(
            run_id=result.run_id,
            status=result.status,
            duration_ms=result.duration_ms,
            primary_agent_count=primary_agents,
            specialist_module_count=specialist_modules,
            checkpoint_count=len(manifest.get("checkpoints", [])),
            workflow_event_count=len(self.events.list(result.run_id)),
            supervisor_rounds=coordination_state.supervisor_round,
            goals_total=len(goals),
            goals_completed=sum(goal.status == "completed" for goal in goals),
            goals_blocked=sum(goal.status == "blocked" for goal in goals),
            goals_needing_human_review=sum(
                goal.status == "needs_human_review" for goal in goals
            ),
            open_coordination_messages=len(coordination_state.open_messages),
            canonical_issue_count=issue_ledger.canonical_issues
            if issue_ledger
            else 0,
            unresolved_issue_count=unresolved_issues,
            quality_required_corrections=result.quality_required_corrections,
            policy_fingerprint=policy_fingerprint,
        )

    @staticmethod
    def _gate_collection(result: CollectorAgentResult) -> None:
        if not result.records:
            raise StageGateError("Collection produced no readable evidence records.")
        if any(not record.sha256_checksum for record in result.records):
            raise StageGateError("Collection produced evidence without checksums.")

    @staticmethod
    def _gate_classification(result: ClassificationAgentResult) -> None:
        if result.success_count == 0:
            raise StageGateError("Classification produced no eligible records.")
        if len(result.records) != result.input_count:
            raise StageGateError("Classification did not account for every input record.")

    @staticmethod
    def _gate_integrity(result: IntegrityAgentResult) -> None:
        bundled_count = sum(len(bundle.evidence_ids) for bundle in result.bundles)
        if bundled_count != result.input_count:
            raise StageGateError("Integrity did not evaluate every classified record.")
        if len({finding.finding_id for finding in result.findings}) != len(result.findings):
            raise StageGateError("Integrity emitted duplicate finding IDs.")

    def _load_evidence(self, source_run_id: str | None):
        if not source_run_id:
            raise StageGateError("classify-only requires --from-run.")
        path = get_evidence_registry_path(source_run_id)
        if not path.exists():
            raise StageGateError(f"Evidence registry not found for {source_run_id}.")
        return self.artifacts.load_models(path, EvidenceRecord), file_sha256(path)

    def _load_classification(self, source_run_id: str | None):
        if not source_run_id:
            raise StageGateError("integrity-only requires --from-run.")
        path = get_classified_evidence_path(source_run_id)
        if not path.exists():
            raise StageGateError(f"Classification artifact not found for {source_run_id}.")
        return self.artifacts.load_models(path, ClassifiedEvidence), file_sha256(path)

    @staticmethod
    def _final_status(collector, classification, integrity) -> str:
        if integrity:
            if any(finding.blocking for finding in integrity.findings) or any(
                gap.blocking for gap in integrity.gaps
            ):
                return "blocked"
            if integrity.findings or integrity.gaps:
                return "requires_correction"
        results = [item for item in (collector, classification, integrity) if item]
        if any(item.status == "failed" for item in results):
            return "failed"
        if any(item.status == "completed_with_warnings" for item in results):
            return "completed_with_warnings"
        return "completed"

    @staticmethod
    def _final_status_agentic(
        collector,
        classification,
        integrity,
        completions: list[CompletionDecision],
        human_approval_required: bool,
    ) -> str:
        results = [item for item in (collector, classification, integrity) if item]
        if any(item.status == "failed" for item in results) or any(
            item.final_status == "failed" for item in completions
        ):
            return "failed"
        if integrity and (
            any(finding.blocking for finding in integrity.findings)
            or any(gap.blocking for gap in integrity.gaps)
        ):
            return "blocked"
        if any(item.final_status == "blocked" for item in completions):
            return "blocked"
        if human_approval_required or any(
            item.final_status == "needs_human_review" for item in completions
        ):
            return "needs_human_review"
        if any(
            item.final_status == "completed_with_warnings" for item in completions
        ):
            return "completed_with_warnings"
        return "completed"

    @staticmethod
    def _workflow_status(status: str) -> WorkflowStage:
        if status == "completed":
            return WorkflowStage.COMPLETED
        if status in {
            "completed_with_warnings",
            "requires_correction",
            "needs_human_review",
        }:
            return WorkflowStage.COMPLETED_WITH_WARNINGS
        if status == "blocked":
            return WorkflowStage.BLOCKED
        return WorkflowStage.FAILED
