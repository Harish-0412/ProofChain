"""Specialist that explains material cross-evidence contradictions."""

from __future__ import annotations

from collections import defaultdict

from proofchain.schemas.claims import ClaimContradiction, EvidenceSupportLink


class ContradictionInvestigationSpecialist:
    specialist_name = "contradiction_investigation"
    goal = "Identify and explain conflicting values without suppressing counter-evidence."

    def run(self, links: list[EvidenceSupportLink]) -> list[ClaimContradiction]:
        grouped: dict[str, list[EvidenceSupportLink]] = defaultdict(list)
        for link in links:
            grouped[link.atomic_claim_id].append(link)
        contradictions = []
        for index, (atomic_id, items) in enumerate(sorted(grouped.items()), 1):
            values = {
                str(item.observed_value)
                for item in items
                if item.observed_value is not None
            }
            if len(values) <= 1 and not any(
                item.relation == "contradicts" for item in items
            ):
                continue
            authorities = {item.authority for item in items}
            likely_cause = (
                "The report total differs from unique attendance identifiers."
                if {"event_report", "attendance_sheet"}.issubset(authorities)
                else "Independent evidence sources contain inconsistent extracted values."
            )
            contradictions.append(
                ClaimContradiction(
                    contradiction_id=f"CON-{index:04d}",
                    atomic_claim_id=atomic_id,
                    conflicting_values=[
                        {
                            "evidence_id": item.evidence_id,
                            "value": item.observed_value,
                            "authority": item.authority,
                        }
                        for item in items
                    ],
                    likely_root_cause=likely_cause,
                    confidence=max(item.strength for item in items),
                )
            )
        return contradictions
