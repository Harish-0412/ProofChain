"""Evidence Integrity Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agentic.completion_evaluator import evaluate_integrity
from proofchain.core.exceptions import SchemaValidationError
from proofchain.core.enums import FindingType
from proofchain.repositories.json_findings_repository import JsonFindingsRepository
from proofchain.schemas.integrity import IntegrityAgentResult, IntegrityInput
from proofchain.schemas.agentic import (
    CompletionDecision,
    CoordinationMessage,
    Goal,
    Observation,
)
from proofchain.services.evidence_bundler import EvidenceBundler
from proofchain.services.rule_engine import RuleEngine


class EvidenceIntegrityAgent(BaseGoalAgent[IntegrityInput, IntegrityAgentResult]):
    agent_name = "evidence_integrity"
    agent_version = "3.0.0"
    agentic_tool_name = "bundle_and_validate_evidence"
    preparation_objective = (
        "Inspect requirement scope and plan applicable deterministic verification rules."
    )
    execution_objective = (
        "Bundle related evidence, execute integrity rules, and calculate readiness results."
    )
    review_objective = (
        "Interpret findings, identify root blockers, and create upstream resolution requests."
    )
    expected_tool_output = "Evidence bundles, findings, gaps, and defensibility summaries."

    def __init__(
        self,
        *,
        bundler: EvidenceBundler | None = None,
        rule_engine: RuleEngine | None = None,
        repository: JsonFindingsRepository | None = None,
        tracer=None,
    ):
        super().__init__(tracer=tracer)
        self.bundler = bundler or EvidenceBundler()
        self.rule_engine = rule_engine or RuleEngine(tracer=tracer)
        self.repository = repository or JsonFindingsRepository()

    def validate_input(self, input_data: IntegrityInput) -> None:
        if not input_data.classified_evidence:
            raise SchemaValidationError("Integrity validation requires classified evidence.")
        if input_data.workflow.upstream_artifact_hash is None:
            raise SchemaValidationError("Integrity requires a committed classification snapshot hash.")

    def execute(self, input_data: IntegrityInput) -> IntegrityAgentResult:
        started_at = datetime.now(tz=timezone.utc)
        bundles, warnings = self.bundler.bundle(
            input_data.classified_evidence,
            input_data.workflow.run_id,
        )
        findings, gaps, summaries = self.rule_engine.evaluate(
            run_id=input_data.workflow.run_id,
            academic_year=input_data.workflow.academic_year,
            requirement_scope=input_data.workflow.requirement_scope,
            records=input_data.classified_evidence,
            bundles=bundles,
        )
        artifact = self.repository.save_all(
            input_data.workflow.run_id,
            bundles,
            findings,
            gaps,
            summaries,
            self.agent_run_id or "UNKNOWN",
        )
        blocking_count = sum(finding.blocking for finding in findings) + sum(
            gap.blocking for gap in gaps
        )
        status = "completed"
        if findings or gaps or warnings:
            status = "completed_with_warnings"

        return IntegrityAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            agent_version=self.agent_version,
            status=status,
            input_count=len(input_data.classified_evidence),
            success_count=len(input_data.classified_evidence),
            warning_count=len(warnings) + len(findings) + len(gaps),
            failure_count=blocking_count,
            bundles=bundles,
            findings=findings,
            gaps=gaps,
            summaries=summaries,
            output_reference=artifact.path,
            input_snapshot_hash=self.compute_input_hash(input_data),
            output_snapshot_hash=artifact.sha256,
            warnings=warnings,
            started_at=started_at,
        )

    def validate_output(self, output_data: IntegrityAgentResult) -> None:
        evidence_ids = {
            evidence_id
            for bundle in output_data.bundles
            for evidence_id in bundle.evidence_ids
        }
        if len(evidence_ids) != output_data.input_count:
            raise SchemaValidationError(
                "Integrity bundling must account for every classified evidence record exactly once."
            )
        finding_ids = [finding.finding_id for finding in output_data.findings]
        if len(finding_ids) != len(set(finding_ids)):
            raise SchemaValidationError("Integrity finding IDs are not unique.")

    def evaluate_goal_completion(
        self,
        goal: Goal,
        output: IntegrityAgentResult | None,
        observations: list[Observation],
    ) -> CompletionDecision:
        return evaluate_integrity(goal, output, observations)

    def create_peer_requests(
        self, goal: Goal, output: IntegrityAgentResult | None
    ) -> list[CoordinationMessage]:
        if output is None:
            return []
        requests: list[CoordinationMessage] = []
        for gap in output.gaps:
            if not gap.blocking:
                continue
            requests.append(
                CoordinationMessage(
                    message_id=f"MSG-{uuid4().hex[:12].upper()}",
                    run_id=goal.run_id,
                    goal_id=goal.goal_id,
                    source_agent=self.agent_name,
                    target_agent="evidence_collector",
                    message_type="additional_evidence_request",
                    reason=gap.description,
                    payload={
                        "requirement_id": gap.requirement_id,
                        "missing_evidence_type": gap.missing_evidence_type,
                        "bundle_id": gap.bundle_id,
                    },
                    priority="critical",
                )
            )
        reclassification_types = {
            FindingType.WEAK_MAPPING,
            FindingType.EXTRACTION_FAILED,
            FindingType.EMPTY_DOCUMENT,
        }
        for finding in output.findings:
            if (
                finding.finding_type not in reclassification_types
                and finding.confidence >= 0.75
            ):
                continue
            requests.append(
                CoordinationMessage(
                    message_id=f"MSG-{uuid4().hex[:12].upper()}",
                    run_id=goal.run_id,
                    goal_id=goal.goal_id,
                    source_agent=self.agent_name,
                    target_agent="evidence_classification",
                    message_type="reclassification_request",
                    reason=finding.description,
                    related_evidence_ids=finding.evidence_ids,
                    payload={
                        "rule_id": finding.rule_id,
                        "bundle_id": finding.bundle_id,
                    },
                    priority="high",
                )
            )
        return requests
