"""Safe, auditable arbitration for conflicting agent claims."""

from __future__ import annotations

from proofchain.schemas.agentic import DecisionRationale


class ConflictResolver:
    def resolve_missing_evidence_conflict(
        self,
        *,
        run_id: str,
        goal_id: str,
        evidence_id: str,
        classification_confidence: float,
    ) -> DecisionRationale:
        if classification_confidence >= 0.75:
            decision = "create_reclassification_goal"
            justification = (
                "A plausible candidate exists, so classification should be rerun before "
                "the missing-evidence blocker is accepted."
            )
        elif classification_confidence >= 0.30:
            decision = "request_human_review"
            justification = (
                "The candidate is too ambiguous for autonomous acceptance or rejection."
            )
        else:
            decision = "retain_missing_evidence_blocker"
            justification = (
                "No sufficiently credible candidate contradicts the deterministic gap."
            )
        return DecisionRationale(
            run_id=run_id,
            goal_id=goal_id,
            agent_name="supervisor",
            decision=decision,
            evidence_considered=[evidence_id],
            rules_applied=["CONFIDENCE-POLICY-001", "NO-BLOCKER-OVERRIDE-001"],
            alternatives_considered=[
                "Accept current classification",
                "Retain missing-evidence blocker",
                "Request human review",
            ],
            uncertainty=[f"Candidate confidence is {classification_confidence:.2f}"],
            justification=justification,
        )
