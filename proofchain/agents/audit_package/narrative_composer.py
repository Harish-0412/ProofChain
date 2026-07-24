"""Grounded package narrative specialist module."""

from __future__ import annotations

from proofchain.schemas.claims import ClaimDecision


class NarrativeComposerSpecialist:
    specialist_name = "narrative_composition"

    def run(self, claim_decisions: list[ClaimDecision]) -> list[str]:
        return [
            f"{decision.claim_id}: {decision.defensible_claim_text}"
            for decision in claim_decisions
        ]
