"""Closure condition specialist module."""

from __future__ import annotations

from proofchain.schemas.claims import ClaimDecision
from proofchain.schemas.closure import ClosureCheck
from proofchain.schemas.issues import CanonicalIssue
from proofchain.schemas.tasks import ResolutionTask


class ClosureVerifierSpecialist:
    specialist_name = "closure_verifier"

    def run(
        self,
        *,
        issue: CanonicalIssue,
        task: ResolutionTask | None,
        submitted: bool,
        registered: bool,
        integrity_passed: bool,
        claim_decisions: list[ClaimDecision],
    ) -> ClosureCheck:
        affected_claims = [
            decision
            for decision in claim_decisions
            if decision.claim_id in issue.source_claim_ids
            or decision.claim_id in issue.canonical_key
        ]
        claims_revalidated = all(
            decision.status == "supported" for decision in affected_claims
        ) if affected_claims else not issue.source_claim_ids
        policy_ok = submitted and registered and integrity_passed and claims_revalidated
        if policy_ok:
            status = "resolved"
        elif submitted:
            status = "under_revalidation"
        else:
            status = "waiting_for_evidence"
        reasons = []
        if not submitted:
            reasons.append("Closure evidence has not been submitted.")
        if submitted and not registered:
            reasons.append("Submitted evidence is not yet registered.")
        if not integrity_passed:
            reasons.append("Targeted integrity checks still fail.")
        if not claims_revalidated:
            reasons.append("Affected claims are not fully supported.")
        return ClosureCheck(
            check_id=f"CHK-{issue.issue_id}",
            issue_id=issue.issue_id,
            task_id=task.task_id if task else None,
            evidence_submitted=submitted,
            evidence_registered=registered,
            classification_complete=registered,
            integrity_rules_passed=integrity_passed,
            affected_claims_revalidated=claims_revalidated,
            closure_policy_satisfied=policy_ok,
            status=status,
            reasons=reasons,
        )
