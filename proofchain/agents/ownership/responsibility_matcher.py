"""Specialist that maps each gap to institutionally eligible roles."""

from __future__ import annotations

from proofchain.schemas.gaps import ResolutionPortfolio


class ResponsibilityMatchingSpecialist:
    specialist_name = "responsibility_matching"
    goal = "Match gap work to authorized roles without assigning blame."

    def run(self, portfolio: ResolutionPortfolio) -> dict[str, dict]:
        results = {}
        for gap in portfolio.gaps:
            if "approval" in gap.gap_type or "signature" in gap.gap_type:
                responsibility = "provide_signed_approval"
                roles = [
                    "Department Accreditation Coordinator",
                    "Head of Department",
                ]
                permission = "upload_evidence"
            elif "participant" in gap.gap_type or "student_row" in gap.gap_type:
                responsibility = "correct_participant_evidence"
                roles = [
                    "Event Coordinator",
                    "Department Accreditation Coordinator",
                ]
                permission = "correct_attendance"
            else:
                responsibility = "correct_or_supply_evidence"
                roles = [
                    "Department Accreditation Coordinator",
                    "Event Coordinator",
                    "Head of Department",
                ]
                permission = "upload_evidence"
            results[gap.gap_id] = {
                "required_responsibility": responsibility,
                "eligible_roles": roles,
                "required_permission": permission,
            }
        return results
