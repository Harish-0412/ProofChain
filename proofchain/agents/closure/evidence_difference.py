"""Evidence difference specialist module."""

from __future__ import annotations

from proofchain.schemas.classification import ClassifiedEvidence


class EvidenceDifferenceSpecialist:
    specialist_name = "evidence_difference"

    def run(self, evidence: list[ClassifiedEvidence]) -> dict[str, bool]:
        return {
            item.evidence_id: not item.requires_human_review
            for item in evidence
        }
