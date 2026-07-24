"""Audit package risk scoring specialist module."""

from __future__ import annotations

from proofchain.schemas.quality import ClaimChallenge


class RiskScoringSpecialist:
    specialist_name = "risk_scoring"

    def run(
        self,
        *,
        claim_challenges: list[ClaimChallenge],
        broken_references: int,
        duplicate_evidence_risks: int,
        privacy_findings: int,
        reviewer_friction_score: float,
    ) -> float:
        failed_claims = sum(item.result == "failed" for item in claim_challenges)
        risk = (
            failed_claims * 0.28
            + broken_references * 0.18
            + duplicate_evidence_risks * 0.08
            + privacy_findings * 0.12
            + reviewer_friction_score / 100.0 * 0.34
        )
        return min(1.0, round(risk, 2))
