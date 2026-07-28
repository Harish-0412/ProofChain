"""Production-policy golden scenarios for Agent 21 release assurance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from proofchain.agents.claim_validation.defensibility_judge import (
    DefensibilityDecisionSpecialist,
)
from proofchain.agents.closure.closure_verifier import ClosureVerifierSpecialist
from proofchain.agents.closure.issue_state_decider import IssueStateDecisionSpecialist
from proofchain.agents.quality_review.claim_challenger import ClaimChallengerSpecialist
from proofchain.schemas.claims import (
    AtomicClaim,
    EvidenceSupportLink,
    InstitutionalClaim,
    SufficiencyAssessment,
)
from proofchain.schemas.institutional import (
    EvaluationScenario,
    SubmissionApproval,
    SubmissionInput,
)
from proofchain.schemas.issues import CanonicalIssue
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.submission_governance import evaluate_submission, file_sha256


class GoldenScenarioSuite:
    """Run the mandatory governance scenarios against production decision code."""

    def run(
        self,
        *,
        workflow: WorkflowContext,
        package_path: Path,
    ) -> list[EvaluationScenario]:
        supported = self._claim_decision("supports", sufficient=True)
        partial = self._claim_decision("supports", sufficient=False)
        contradicted = self._claim_decision("contradicts", sufficient=False)
        missing = self._claim_decision(None, sufficient=False)

        issue = self._issue(workflow.run_id, status="EVIDENCE_SUBMITTED")
        corrected = ClosureVerifierSpecialist().run(
            issue=issue,
            task=None,
            submitted=True,
            registered=True,
            integrity_passed=True,
            claim_decisions=[],
        )
        resolved_issue = self._issue(workflow.run_id, status="RESOLVED")
        failed_revalidation = ClosureVerifierSpecialist().run(
            issue=resolved_issue,
            task=None,
            submitted=True,
            registered=True,
            integrity_passed=False,
            claim_decisions=[],
        )
        _, reopen_transitions = IssueStateDecisionSpecialist().run(
            [resolved_issue], [failed_revalidation]
        )

        failed_challenge = ClaimChallengerSpecialist().run([contradicted])[0]
        successful_challenge = ClaimChallengerSpecialist().run([supported])[0]
        authorized, rejected = self._submission_decisions(workflow, package_path)

        rows = [
            (
                "GOLDEN-CLAIM-SUPPORTED",
                "fully_supported_claim",
                "supported",
                supported.status,
                "defensibility_decision",
                "Authoritative support and sufficient coverage produce a supported claim.",
                1.0,
            ),
            (
                "GOLDEN-CLAIM-PARTIAL",
                "partially_supported_claim",
                "partially_supported",
                partial.status,
                "defensibility_decision",
                "Relevant evidence without sufficient coverage remains partial.",
                partial.confidence,
            ),
            (
                "GOLDEN-CLAIM-CONTRADICTED",
                "contradicted_claim",
                "contradicted",
                contradicted.status,
                "defensibility_decision",
                "Counter-evidence prevents a positive claim decision.",
                contradicted.confidence,
            ),
            (
                "GOLDEN-CLAIM-MISSING",
                "missing_evidence",
                "insufficient_evidence",
                missing.status,
                "defensibility_decision",
                "A claim without linked evidence remains insufficient.",
                missing.confidence,
            ),
            (
                "GOLDEN-CLOSURE-CORRECTED",
                "corrected_evidence",
                "resolved",
                corrected.status,
                "closure_verifier",
                "Submitted, registered, integrity-passing evidence closes the issue.",
                1.0,
            ),
            (
                "GOLDEN-CLOSURE-REOPENED",
                "reopened_issue",
                "REOPENED",
                reopen_transitions[0].to_status,
                "issue_state_decider",
                "A resolved issue is reopened when targeted revalidation later fails.",
                1.0,
            ),
            (
                "GOLDEN-PACKAGE-FAILED",
                "failed_package_review",
                "failed",
                failed_challenge.result,
                "claim_challenger",
                "A contradicted claim fails adversarial package review.",
                1.0,
            ),
            (
                "GOLDEN-PACKAGE-SUCCESS",
                "successful_package_review",
                "passed",
                successful_challenge.result,
                "claim_challenger",
                "A fully supported claim passes its adversarial challenge.",
                1.0,
            ),
            (
                "GOLDEN-SUBMISSION-AUTHORIZED",
                "authorized_submission",
                "ELIGIBLE",
                authorized,
                "submission_governance",
                "Matching package hash, independent approval, and confirmation authorize handoff.",
                1.0,
            ),
            (
                "GOLDEN-SUBMISSION-REJECTED",
                "rejected_submission",
                "NOT_ELIGIBLE",
                rejected,
                "submission_governance",
                "A rejection blocks handoff even when the package hash is valid.",
                1.0,
            ),
        ]
        return [
            EvaluationScenario(
                scenario_id=scenario_id,
                category=category,
                expected_decision=expected,
                observed_decision=observed,
                observed_confidence=confidence,
                component_under_test=component,
                rationale=rationale,
                fixture_hash=self._fixture_hash(
                    {
                        "scenario_id": scenario_id,
                        "category": category,
                        "expected": expected,
                        "component": component,
                    }
                ),
            )
            for (
                scenario_id,
                category,
                expected,
                observed,
                component,
                rationale,
                confidence,
            ) in rows
        ]

    @staticmethod
    def _claim_decision(relation: str | None, *, sufficient: bool):
        claim = InstitutionalClaim(
            claim_id="CLM-GOLDEN",
            requirement_id="C3.2.1",
            original_claim="The governed activity occurred.",
            department="CSE",
            academic_year="2025-2026",
            atomic_claims=[
                AtomicClaim(
                    atomic_claim_id="ATM-GOLDEN",
                    claim_id="CLM-GOLDEN",
                    attribute="activity_occurred",
                    expected_value=True,
                )
            ],
        )
        links = (
            [
                EvidenceSupportLink(
                    atomic_claim_id="ATM-GOLDEN",
                    evidence_id="EVD-GOLDEN",
                    relation=relation,
                    strength=0.99,
                    observed_value=relation != "contradicts",
                    authority="golden_fixture",
                    reason="Controlled release-assurance fixture.",
                )
            ]
            if relation
            else []
        )
        assessments = [
            SufficiencyAssessment(
                atomic_claim_id="ATM-GOLDEN",
                coverage_score=1.0 if sufficient else 0.5,
                authority_score=1.0,
                consistency_score=1.0 if relation != "contradicts" else 0.0,
                independence_score=1.0,
                overall_sufficiency=1.0 if sufficient else 0.5,
                sufficient=sufficient,
                reason="Controlled release-assurance fixture.",
            )
        ]
        return DefensibilityDecisionSpecialist().run(
            [claim], links, [], assessments
        )[0]

    @staticmethod
    def _issue(run_id: str, *, status: str) -> CanonicalIssue:
        return CanonicalIssue(
            issue_id="ISS-GOLDEN",
            run_id=run_id,
            issue_type="missing_required_document",
            root_entity_type="integrity_gap",
            root_entity_id="GAP-GOLDEN",
            severity="high",
            blocking=True,
            status=status,
            canonical_key="golden|missing_required_document",
        )

    @staticmethod
    def _submission_decisions(
        workflow: WorkflowContext,
        package_path: Path,
    ) -> tuple[str, str]:
        package_hash = file_sha256(package_path)
        approved = SubmissionApproval(
            approval_id="APR-GOLDEN-APPROVED",
            approver_id="independent-reviewer",
            package_hash=package_hash,
            decision="approved",
            independent=True,
        )
        rejected = SubmissionApproval(
            approval_id="APR-GOLDEN-REJECTED",
            approver_id="independent-reviewer",
            package_hash=package_hash,
            decision="rejected",
            independent=True,
        )
        common = {
            "workflow": workflow,
            "package_id": "PKG-GOLDEN",
            "package_path": str(package_path.resolve()),
            "expected_package_hash": package_hash,
            "quality_status": "pass_for_human_approval",
            "final_confirmation": True,
            "idempotency_key": "GOLDEN-SUBMISSION",
        }
        authorized, _, _ = evaluate_submission(
            SubmissionInput(**common, approvals=[approved])
        )
        denied, _, _ = evaluate_submission(
            SubmissionInput(**common, approvals=[rejected])
        )
        return authorized, denied

    @staticmethod
    def _fixture_hash(payload: dict[str, str]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()
