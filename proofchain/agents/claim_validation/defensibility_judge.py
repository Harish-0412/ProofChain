"""Specialist that produces atomic and claim-level defensibility decisions."""

from __future__ import annotations

from collections import defaultdict

from proofchain.schemas.claims import (
    AtomicClaimDecision,
    ClaimContradiction,
    ClaimDecision,
    ClaimLineage,
    EvidenceSupportLink,
    InstitutionalClaim,
    SufficiencyAssessment,
)


class DefensibilityDecisionSpecialist:
    specialist_name = "defensibility_decision"
    goal = "Produce a traceable claim decision and a non-destructive repair proposal."

    def run(
        self,
        claims: list[InstitutionalClaim],
        links: list[EvidenceSupportLink],
        contradictions: list[ClaimContradiction],
        sufficiency: list[SufficiencyAssessment],
    ) -> list[ClaimDecision]:
        links_by_atomic: dict[str, list[EvidenceSupportLink]] = defaultdict(list)
        contradictions_by_atomic: dict[str, list[ClaimContradiction]] = defaultdict(list)
        sufficiency_by_atomic = {item.atomic_claim_id: item for item in sufficiency}
        for link in links:
            links_by_atomic[link.atomic_claim_id].append(link)
        for item in contradictions:
            contradictions_by_atomic[item.atomic_claim_id].append(item)

        decisions = []
        for claim in claims:
            atomic_decisions = []
            supporting: set[str] = set()
            counter: set[str] = set()
            recommended_actions = []
            defensible_parts = []
            for atomic in claim.atomic_claims:
                atomic_links = links_by_atomic.get(atomic.atomic_claim_id, [])
                support = [item for item in atomic_links if item.relation in {"supports", "partially_supports"}]
                conflicts = [item for item in atomic_links if item.relation == "contradicts"]
                assessment = sufficiency_by_atomic.get(atomic.atomic_claim_id)
                if support and conflicts:
                    status = "partially_supported"
                elif support and assessment and assessment.sufficient:
                    status = "supported"
                elif conflicts:
                    status = "contradicted"
                elif support:
                    status = "partially_supported"
                else:
                    status = "insufficient_evidence"
                evidence_ids = list(
                    dict.fromkeys(item.evidence_id for item in atomic_links)
                )
                supporting.update(item.evidence_id for item in support)
                counter.update(item.evidence_id for item in conflicts)
                strongest = max(
                    atomic_links,
                    key=lambda item: item.strength,
                    default=None,
                )
                if status != "supported":
                    if strongest and strongest.observed_value is not None:
                        recommended_actions.append(
                            f"Revise {atomic.attribute} to {strongest.observed_value!r} "
                            "or provide authoritative counter-evidence."
                        )
                        defensible_parts.append(
                            f"{atomic.attribute}={strongest.observed_value}"
                        )
                    else:
                        recommended_actions.append(
                            f"Provide evidence for {atomic.attribute}={atomic.expected_value!r}."
                        )
                else:
                    defensible_parts.append(
                        f"{atomic.attribute}={atomic.expected_value}"
                    )
                confidence = (
                    assessment.overall_sufficiency if assessment else 0.0
                )
                atomic_decisions.append(
                    AtomicClaimDecision(
                        atomic_claim_id=atomic.atomic_claim_id,
                        attribute=atomic.attribute,
                        status=status,
                        confidence=confidence,
                        evidence_ids=evidence_ids,
                        observed_values=[
                            item.observed_value
                            for item in atomic_links
                            if item.observed_value is not None
                        ],
                        explanation=(
                            f"{len(support)} supporting and {len(conflicts)} "
                            "contradictory evidence links were evaluated."
                        ),
                    )
                )
            statuses = {item.status for item in atomic_decisions}
            if statuses == {"supported"}:
                overall_status = "supported"
            elif "supported" in statuses or "partially_supported" in statuses:
                overall_status = "partially_supported"
            elif "contradicted" in statuses:
                overall_status = "contradicted"
            else:
                overall_status = "insufficient_evidence"
            all_evidence = supporting | counter
            minimal_set = self._minimal_set(claim, atomic_decisions, links_by_atomic)
            fragility = round(1 / max(1, len(minimal_set)), 4)
            claim_contradictions = [
                item
                for atomic in claim.atomic_claims
                for item in contradictions_by_atomic.get(atomic.atomic_claim_id, [])
            ]
            confidence = round(
                sum(item.confidence for item in atomic_decisions)
                / max(1, len(atomic_decisions)),
                4,
            )
            decisions.append(
                ClaimDecision(
                    claim_id=claim.claim_id,
                    requirement_id=claim.requirement_id,
                    original_claim=claim.original_claim,
                    status=overall_status,
                    confidence=confidence,
                    atomic_decisions=atomic_decisions,
                    contradictions=claim_contradictions,
                    supporting_evidence=sorted(supporting),
                    counter_evidence=sorted(counter),
                    defensible_claim_text=(
                        "Evidence currently supports: " + "; ".join(defensible_parts) + "."
                        if defensible_parts
                        else None
                    ),
                    recommended_actions=list(dict.fromkeys(recommended_actions)),
                    claim_fragility_score=fragility,
                    minimal_defensible_evidence_set=minimal_set,
                    requires_human_review=overall_status != "supported",
                    lineage=self._lineage(claim, atomic_decisions, all_evidence),
                )
            )
        return decisions

    @staticmethod
    def _minimal_set(claim, atomic_decisions, links_by_atomic) -> list[str]:
        selected = []
        for atomic, decision in zip(claim.atomic_claims, atomic_decisions, strict=True):
            if decision.status == "insufficient_evidence":
                continue
            strongest = max(
                links_by_atomic.get(atomic.atomic_claim_id, []),
                key=lambda item: item.strength,
                default=None,
            )
            if strongest and strongest.evidence_id not in selected:
                selected.append(strongest.evidence_id)
        return selected

    @staticmethod
    def _lineage(claim, atomic_decisions, evidence_ids) -> ClaimLineage:
        nodes = [
            {"id": claim.claim_id, "type": "institutional_claim"},
            *[
                {"id": item.atomic_claim_id, "type": "atomic_claim", "status": item.status}
                for item in atomic_decisions
            ],
            *[{"id": item, "type": "evidence"} for item in sorted(evidence_ids)],
        ]
        edges = [
            {
                "from": claim.claim_id,
                "to": item.atomic_claim_id,
                "relation": "DECOMPOSES_TO",
            }
            for item in atomic_decisions
        ]
        for decision in atomic_decisions:
            edges.extend(
                {
                    "from": decision.atomic_claim_id,
                    "to": evidence_id,
                    "relation": "VALIDATED_BY",
                }
                for evidence_id in decision.evidence_ids
            )
        return ClaimLineage(claim_id=claim.claim_id, nodes=nodes, edges=edges)
