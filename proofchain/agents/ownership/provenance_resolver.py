"""Specialist that resolves evidence provenance through a bounded role graph."""

from __future__ import annotations

import yaml

from proofchain.core.paths import ORGANISATION_ROLES_FILE
from proofchain.schemas.gaps import ResolutionPortfolio
from proofchain.schemas.ownership import (
    OrganisationMember,
    ProvenanceCandidate,
)


class EvidenceProvenanceSpecialist:
    specialist_name = "evidence_provenance"
    goal = "Trace department and role relationships relevant to each gap."

    def load_members(
        self,
        departments: list[str],
        supplied: list[OrganisationMember],
    ) -> list[OrganisationMember]:
        if supplied:
            return supplied
        payload = yaml.safe_load(ORGANISATION_ROLES_FILE.read_text(encoding="utf-8"))
        members = []
        for department in departments:
            department_payload = payload["departments"].get(
                department, payload["departments"]["DEFAULT"]
            )
            for item in department_payload["members"]:
                members.append(OrganisationMember(department=department, **item))
        members.extend(
            OrganisationMember(**item)
            for item in payload.get("institution", {}).get("members", [])
        )
        return members

    def run(
        self,
        portfolio: ResolutionPortfolio,
        members: list[OrganisationMember],
        default_department: str,
    ) -> dict[str, list[ProvenanceCandidate]]:
        results = {}
        for gap in portfolio.gaps:
            department = gap.department or default_department
            candidates = []
            for member in members:
                if member.department not in {department, "INSTITUTION"}:
                    continue
                relationship = self._relationship(member.role, gap.gap_type)
                confidence = {
                    "responsible_department_coordinator": 0.92,
                    "event_coordinator": 0.88,
                    "approval_authority": 0.86,
                    "institutional_escalation": 0.65,
                }.get(relationship, 0.55)
                candidates.append(
                    ProvenanceCandidate(
                        user_id=member.user_id,
                        relationship=relationship,
                        confidence=confidence,
                    )
                )
            results[gap.gap_id] = sorted(
                candidates, key=lambda item: (-item.confidence, item.user_id)
            )
        return results

    @staticmethod
    def _relationship(role: str, gap_type: str) -> str:
        if role == "IQAC Coordinator":
            return "institutional_escalation"
        if "approval" in gap_type or "signature" in gap_type:
            return (
                "approval_authority"
                if role == "Head of Department"
                else "responsible_department_coordinator"
            )
        if "participant" in gap_type or "attendance" in gap_type:
            return (
                "event_coordinator"
                if role == "Event Coordinator"
                else "responsible_department_coordinator"
            )
        return "responsible_department_coordinator"
