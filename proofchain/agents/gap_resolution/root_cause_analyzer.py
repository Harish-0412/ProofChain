"""Specialist that assigns explicit root-cause hypotheses."""

from __future__ import annotations

from proofchain.schemas.gaps import ResolutionGap


class RootCauseAnalysisSpecialist:
    specialist_name = "root_cause_analysis"
    goal = "Explain why each gap exists and identify the safest investigation."

    RULES = {
        "missing_required_document": (
            "The required document was not found in any approved source scope.",
            "Check departmental source folders and the approval register.",
        ),
        "participant_count_mismatch": (
            "The reported total was not calculated from unique participant identifiers.",
            "Compare total rows, duplicate identifiers, and participant categories.",
        ),
        "duplicate_student_row": (
            "Duplicate participant identifiers were entered in the attendance record.",
            "Deduplicate by institutional register number and verify the corrected total.",
        ),
        "missing_signature": (
            "The approval workflow is incomplete or the signed version was not uploaded.",
            "Locate the signed version or obtain authorized retrospective approval.",
        ),
        "duplicate_file": (
            "The same evidence content was registered from more than one path.",
            "Confirm the authoritative copy and disclose cross-claim reuse.",
        ),
        "unsupported_claim_component": (
            "The institutional claim was written using a value not established by evidence.",
            "Review the strongest observed value and the claim approval history.",
        ),
    }

    def run(self, gaps: list[ResolutionGap]) -> list[ResolutionGap]:
        results = []
        for gap in gaps:
            cause, investigation = self.RULES.get(
                gap.gap_type,
                (
                    "Evidence is incomplete, inconsistent, or not sufficiently authoritative.",
                    "Review source provenance, extraction quality, and requirement context.",
                ),
            )
            confidence = 0.9 if gap.gap_type in self.RULES else 0.65
            updated = gap.model_copy(
                update={
                    "root_cause": cause,
                    "root_cause_hypotheses": [
                        {
                            "cause": cause,
                            "confidence": confidence,
                            "recommended_investigation": investigation,
                        }
                    ],
                },
                deep=True,
            )
            results.append(updated)
        return results
