"""Package index and cross-reference specialist module."""

from __future__ import annotations

from proofchain.schemas.claims import ClaimDecision


class IndexBuilderSpecialist:
    specialist_name = "index_builder"

    def run(self, claim_decisions: list[ClaimDecision]) -> dict[str, list[str]]:
        return {
            decision.claim_id: list(dict.fromkeys(decision.supporting_evidence))
            for decision in claim_decisions
        }
