"""Goal-driven Adversarial Quality Review and Audit Simulation Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agents.quality_review.claim_challenger import ClaimChallengerSpecialist
from proofchain.agents.quality_review.completeness_reviewer import PackageCompletenessReviewer
from proofchain.agents.quality_review.policy_reviewer import PolicyComplianceReviewer
from proofchain.agents.quality_review.reference_reviewer import ReferenceResolutionReviewer
from proofchain.agents.quality_review.reuse_auditor import ReuseAuditSpecialist
from proofchain.agents.quality_review.reviewer_simulator import ReviewerSimulationSpecialist
from proofchain.agents.quality_review.risk_scorer import RiskScoringSpecialist
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_lifecycle_repository import JsonLifecycleRepository
from proofchain.schemas.agentic import AgentPlan, CompletionDecision, PlanStep
from proofchain.schemas.quality import QualityReviewAgentResult, QualityReviewInput


class AdversarialQualityReviewAgent(
    BaseGoalAgent[QualityReviewInput, QualityReviewAgentResult]
):
    agent_name = "adversarial_quality_review"
    agent_version = "1.0.0"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or JsonLifecycleRepository()
        self.events = JsonEventRepository()
        self.completeness = PackageCompletenessReviewer()
        self.references = ReferenceResolutionReviewer()
        self.challenger = ClaimChallengerSpecialist()
        self.reuse = ReuseAuditSpecialist()
        self.policy = PolicyComplianceReviewer()
        self.simulator = ReviewerSimulationSpecialist()
        self.risk = RiskScoringSpecialist()
        self._state: dict = {}

    def validate_input(self, input_data):
        return None

    def execute(self, input_data):
        self._state = {}
        self._check_completeness(input_data)
        self._check_references(input_data)
        self._challenge_claims(input_data)
        self._audit_reuse(input_data)
        self._review_policy(input_data)
        self._simulate(input_data)
        return self._score(input_data)

    def validate_output(self, output_data):
        return None

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        specs = [
            ("check_package_completeness", "Check required package components."),
            ("resolve_references", "Test evidence paths, checksums, and claim links."),
            ("challenge_claims", "Attempt to disprove every material claim."),
            ("audit_duplicate_reuse", "Detect duplicate or reused evidence risks."),
            ("review_package_policy", "Check disclosure and eligibility policy."),
            ("simulate_reviewer_journey", "Estimate reviewer friction."),
            ("score_quality_risk", "Produce final quality status and correction routing."),
        ]
        return AgentPlan(
            plan_id=f"PLAN-QUALITY-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale="Challenge the draft package independently before human approval.",
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=f"{tool} records adversarial review state.",
                    completion_condition="Every material claim and reference has been challenged.",
                )
                for index, (tool, objective) in enumerate(specs, 1)
            ],
            dependencies=goal.dependencies,
            expected_outputs=["quality_review_report.json"],
            status="approved",
        )

    def agentic_tools(self, input_data):
        return {
            "check_package_completeness": lambda: self._check_completeness(input_data),
            "resolve_references": lambda: self._check_references(input_data),
            "challenge_claims": lambda: self._challenge_claims(input_data),
            "audit_duplicate_reuse": lambda: self._audit_reuse(input_data),
            "review_package_policy": lambda: self._review_policy(input_data),
            "simulate_reviewer_journey": lambda: self._simulate(input_data),
            "score_quality_risk": lambda: self._score(input_data),
        }

    def _check_completeness(self, input_data):
        value = self.completeness.run(input_data.package_manifest)
        self._state["completeness"] = value
        return value

    def _check_references(self, input_data):
        value = self.references.run(input_data.package_manifest)
        self._state["broken_references"] = value
        return value

    def _challenge_claims(self, input_data):
        value = self.challenger.run(input_data.claim_decisions)
        self._state["claim_challenges"] = value
        return value

    def _audit_reuse(self, input_data):
        value = self.reuse.run(input_data.package_manifest)
        self._state["duplicate_evidence_risks"] = value
        return value

    def _review_policy(self, input_data):
        value = self.policy.run(input_data.package_manifest)
        self._state["policy_findings"] = value
        return value

    def _simulate(self, input_data):
        value = self.simulator.run(
            input_data.package_manifest, self._state["broken_references"]
        )
        self._state["reviewer_friction_score"] = value
        return value

    def _score(self, input_data):
        started = datetime.now(tz=timezone.utc)
        risk = self.risk.run(
            claim_challenges=self._state["claim_challenges"],
            broken_references=self._state["broken_references"],
            duplicate_evidence_risks=self._state["duplicate_evidence_risks"],
            privacy_findings=0,
            reviewer_friction_score=self._state["reviewer_friction_score"],
        )
        corrections = list(self._state["completeness"])
        corrections.extend(
            challenge.reason
            for challenge in self._state["claim_challenges"]
            if challenge.result == "failed"
        )
        if self._state["policy_findings"]:
            corrections.extend(self._state["policy_findings"])
        if risk >= 0.7:
            quality_status = "block_package"
        elif corrections:
            quality_status = "return_for_correction"
        elif risk >= 0.3:
            quality_status = "pass_with_warnings"
        else:
            quality_status = "pass_for_human_approval"
        result = QualityReviewAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if corrections else "completed",
            package_id=input_data.package_manifest.package_id,
            package_hash=input_data.package_manifest.package_hash,
            quality_status=quality_status,
            input_count=len(input_data.claim_decisions),
            success_count=sum(
                item.result == "passed" for item in self._state["claim_challenges"]
            ),
            warning_count=len(corrections),
            failure_count=sum(
                item.result == "failed" for item in self._state["claim_challenges"]
            ),
            claim_challenges=self._state["claim_challenges"],
            broken_references=self._state["broken_references"],
            omitted_material_findings=len(input_data.package_manifest.unresolved_warning_issue_ids),
            duplicate_evidence_risks=self._state["duplicate_evidence_risks"],
            privacy_findings=0,
            reviewer_friction_score=self._state["reviewer_friction_score"],
            audit_failure_risk=risk,
            required_corrections=corrections,
            input_snapshot_hash=self.compute_input_hash(input_data),
            warnings=corrections,
            started_at=started,
        )
        artifact = self.repository.save_quality(result)
        self.events.append(
            run_id=result.run_id,
            event_type="QualityReviewPassed"
            if quality_status.startswith("pass")
            else "QualityReviewFailed",
            aggregate_type="audit_package",
            aggregate_id=result.package_id,
            actor=self.agent_name,
            payload={"quality_status": quality_status, "risk": risk},
        )
        result.output_reference = artifact.path
        result.output_snapshot_hash = artifact.sha256
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        complete = output is not None
        blocked = output.quality_status == "block_package" if output else True
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=complete and not blocked,
            success_conditions_met=goal.success_conditions if complete and not blocked else [],
            success_conditions_unmet=[] if complete and not blocked else goal.success_conditions,
            blockers=output.required_corrections if output else ["No quality result was produced."],
            confidence=0.9 if complete else 0.0,
            final_status="blocked" if blocked else "completed_with_warnings" if output.warning_count else "completed",
            explanation=(
                f"Quality status is {output.quality_status if output else 'missing'}; "
                "the package was challenged and not externally approved."
            ),
            supporting_artifacts=[output.output_reference] if output and output.output_reference else [],
        )
