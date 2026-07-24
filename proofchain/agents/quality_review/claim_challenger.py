"""Adversarial claim challenge specialist module."""

from __future__ import annotations

from proofchain.schemas.claims import ClaimDecision
from proofchain.schemas.quality import ClaimChallenge


class ClaimChallengerSpecialist:
    specialist_name = "claim_challenger"

    def run(self, claim_decisions: list[ClaimDecision]) -> list[ClaimChallenge]:
        challenges = []
        for decision in claim_decisions:
            if decision.status == "supported":
                result = "passed"
                reason = "The claim is supported by the current defensibility decision."
            elif decision.requires_human_review:
                result = "failed"
                reason = "The claim requires human review and cannot pass package quality."
            else:
                result = "warning"
                reason = f"The claim status is {decision.status}."
            challenges.append(
                ClaimChallenge(claim_id=decision.claim_id, result=result, reason=reason)
            )
        return challenges
