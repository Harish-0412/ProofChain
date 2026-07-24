"""Specialist that normalizes integrity and claim failures into unique gaps."""

from __future__ import annotations

from proofchain.schemas.gaps import GapResolutionInput, ResolutionGap


class GapDetectionSpecialist:
    specialist_name = "gap_detection"
    goal = "Normalize every unresolved finding and unsupported claim into a gap."

    def run(self, input_data: GapResolutionInput) -> list[ResolutionGap]:
        gaps: list[ResolutionGap] = []
        consumed_findings: set[str] = set()
        for source in input_data.integrity_gaps:
            consumed_findings.update(source.related_findings)
            affected_claims = [
                item.claim_id
                for item in input_data.claim_decisions
                if item.requirement_id == source.requirement_id
            ]
            gaps.append(
                ResolutionGap(
                    gap_id=f"RGAP-{len(gaps) + 1:04d}",
                    source_type="integrity_gap",
                    source_ids=[source.gap_id, *source.related_findings],
                    affected_claims=affected_claims,
                    affected_requirements=[source.requirement_id],
                    department=source.department,
                    gap_type=source.gap_type.value,
                    severity=source.severity.value,
                    blocking=source.blocking,
                    description=source.description,
                )
            )
        for finding in input_data.integrity_findings:
            if finding.finding_id in consumed_findings:
                continue
            affected_claims = [
                item.claim_id
                for item in input_data.claim_decisions
                if finding.requirement_id is None
                or item.requirement_id == finding.requirement_id
            ]
            gaps.append(
                ResolutionGap(
                    gap_id=f"RGAP-{len(gaps) + 1:04d}",
                    source_type="integrity_finding",
                    source_ids=[finding.finding_id],
                    affected_claims=affected_claims,
                    affected_requirements=[finding.requirement_id]
                    if finding.requirement_id
                    else [],
                    gap_type=finding.finding_type.value,
                    severity=finding.severity.value,
                    blocking=finding.blocking,
                    description=finding.description,
                )
            )
        existing_claim_ids = {
            claim_id for gap in gaps for claim_id in gap.affected_claims
        }
        for decision in input_data.claim_decisions:
            if decision.status == "supported" or decision.claim_id in existing_claim_ids:
                continue
            gaps.append(
                ResolutionGap(
                    gap_id=f"RGAP-{len(gaps) + 1:04d}",
                    source_type="claim_decision",
                    source_ids=[decision.claim_id],
                    affected_claims=[decision.claim_id],
                    affected_requirements=[decision.requirement_id],
                    gap_type="unsupported_claim_component",
                    severity="high",
                    blocking=True,
                    description=(
                        f"Claim {decision.claim_id} is {decision.status} and cannot be "
                        "approved without correction or additional evidence."
                    ),
                )
            )
        return self._merge_duplicates(gaps)

    @staticmethod
    def _merge_duplicates(gaps: list[ResolutionGap]) -> list[ResolutionGap]:
        merged: dict[tuple, ResolutionGap] = {}
        for gap in gaps:
            key = (
                gap.gap_type,
                tuple(sorted(gap.affected_requirements)),
                gap.description.casefold(),
            )
            if key not in merged:
                merged[key] = gap
                continue
            current = merged[key]
            current.source_ids = list(dict.fromkeys([*current.source_ids, *gap.source_ids]))
            current.affected_claims = list(
                dict.fromkeys([*current.affected_claims, *gap.affected_claims])
            )
            current.blocking = current.blocking or gap.blocking
        return list(merged.values())
