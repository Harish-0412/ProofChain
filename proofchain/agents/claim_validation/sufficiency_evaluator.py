"""Specialist that scores coverage, authority, consistency, and independence."""

from __future__ import annotations

from collections import defaultdict

from proofchain.schemas.claims import (
    ClaimContradiction,
    EvidenceSupportLink,
    InstitutionalClaim,
    SufficiencyAssessment,
)


class SufficiencyEvaluationSpecialist:
    specialist_name = "claim_sufficiency_evaluation"
    goal = "Determine whether every atomic assertion has enough independent evidence."

    def run(
        self,
        claims: list[InstitutionalClaim],
        links: list[EvidenceSupportLink],
        contradictions: list[ClaimContradiction],
    ) -> list[SufficiencyAssessment]:
        by_atomic: dict[str, list[EvidenceSupportLink]] = defaultdict(list)
        for link in links:
            by_atomic[link.atomic_claim_id].append(link)
        contradicted = {item.atomic_claim_id for item in contradictions}
        results = []
        for claim in claims:
            for atomic in claim.atomic_claims:
                items = by_atomic.get(atomic.atomic_claim_id, [])
                evidence_ids = {item.evidence_id for item in items}
                authorities = {item.authority for item in items}
                coverage = min(1.0, len(items) / 2) if items else 0.0
                authority = max((item.strength for item in items), default=0.0)
                consistency = 0.45 if atomic.atomic_claim_id in contradicted else 1.0
                independence = min(1.0, len(authorities) / 2) if authorities else 0.0
                overall = round(
                    0.30 * coverage
                    + 0.30 * authority
                    + 0.25 * consistency
                    + 0.15 * independence,
                    4,
                )
                results.append(
                    SufficiencyAssessment(
                        atomic_claim_id=atomic.atomic_claim_id,
                        coverage_score=coverage,
                        authority_score=authority,
                        consistency_score=consistency,
                        independence_score=independence,
                        overall_sufficiency=overall,
                        sufficient=overall >= 0.75 and bool(evidence_ids),
                        reason=(
                            "Evidence is sufficiently authoritative and consistent."
                            if overall >= 0.75
                            else "Coverage, independence, or consistency is below policy."
                        ),
                    )
                )
        return results
