"""Specialist that creates alternative strategies and closure evidence."""

from __future__ import annotations

from proofchain.schemas.gaps import (
    GapResolutionPlan,
    ResolutionGap,
    ResolutionStrategy,
)


class ResolutionPlanningSpecialist:
    specialist_name = "resolution_planning"
    goal = "Create actionable alternatives without changing claims or closing gaps."

    def run(self, gaps: list[ResolutionGap]) -> list[GapResolutionPlan]:
        return [self._plan(gap) for gap in gaps]

    def _plan(self, gap: ResolutionGap) -> GapResolutionPlan:
        if gap.gap_type in {"missing_required_document", "missing_signature"}:
            strategies = [
                ResolutionStrategy(
                    strategy_id=f"STR-{gap.gap_id}-A",
                    title="Locate and upload authoritative evidence",
                    actions=[
                        "Search approved department and institutional sources.",
                        "Verify document identity, date, and authorization.",
                        "Upload the authoritative signed document.",
                        "Rerun classification and integrity validation.",
                    ],
                    estimated_effort="medium",
                    expected_resolution_confidence=0.95,
                    requires_new_evidence=True,
                ),
                ResolutionStrategy(
                    strategy_id=f"STR-{gap.gap_id}-B",
                    title="Obtain governed replacement approval",
                    actions=[
                        "Confirm original evidence is unavailable.",
                        "Obtain approval under institutional policy.",
                        "Record the replacement provenance and human approval.",
                    ],
                    estimated_effort="high",
                    expected_resolution_confidence=0.80,
                    requires_new_evidence=True,
                ),
            ]
            completion = [
                "Authorized evidence document",
                "Approval identity and date",
                "Passing integrity revalidation",
            ]
            dependencies = ["acquire_evidence", "classify_evidence", "reverify_integrity"]
        elif gap.gap_type in {
            "participant_count_mismatch",
            "duplicate_student_row",
            "unsupported_claim_component",
        }:
            strategies = [
                ResolutionStrategy(
                    strategy_id=f"STR-{gap.gap_id}-A",
                    title="Correct the underlying attendance evidence",
                    actions=[
                        "Remove duplicate participant identifiers.",
                        "Verify participant categories and unique totals.",
                        "Obtain coordinator confirmation.",
                        "Upload and revalidate the corrected record.",
                    ],
                    estimated_effort="medium",
                    expected_resolution_confidence=0.93,
                    requires_new_evidence=True,
                ),
                ResolutionStrategy(
                    strategy_id=f"STR-{gap.gap_id}-B",
                    title="Revise the claim to the verified value",
                    actions=[
                        "Use the strongest authoritative observed value.",
                        "Obtain human approval for the revised claim.",
                        "Rerun claim defensibility validation.",
                    ],
                    estimated_effort="low",
                    expected_resolution_confidence=0.98,
                    requires_claim_revision=True,
                ),
            ]
            completion = [
                "Corrected attendance or approved revised claim",
                "Human approval record",
                "Passing claim revalidation",
            ]
            dependencies = ["human_approval", "revalidate_claim"]
        else:
            strategies = [
                ResolutionStrategy(
                    strategy_id=f"STR-{gap.gap_id}-A",
                    title="Correct and revalidate the affected evidence",
                    actions=[
                        "Identify the authoritative source.",
                        "Correct or replace the defective evidence.",
                        "Rerun the affected deterministic checks.",
                    ],
                    estimated_effort="medium",
                    expected_resolution_confidence=0.85,
                    requires_new_evidence=True,
                )
            ]
            completion = ["Corrected evidence", "Passing affected-rule result"]
            dependencies = ["reverify_integrity"]
        return GapResolutionPlan(
            plan_id=f"RPLAN-{gap.gap_id}",
            gap_id=gap.gap_id,
            strategies=strategies,
            recommended_strategy_id=max(
                strategies,
                key=lambda item: item.expected_resolution_confidence,
            ).strategy_id,
            dependencies=dependencies,
            required_completion_evidence=completion,
            expected_readiness_delta=0.0,
        )
