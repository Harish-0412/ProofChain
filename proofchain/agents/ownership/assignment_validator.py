"""Specialist that validates authorization, independence, and workload."""

from __future__ import annotations

from datetime import date, timedelta

from proofchain.schemas.gaps import ResolutionPortfolio
from proofchain.schemas.ownership import (
    OwnerReference,
    OwnershipAssignment,
    ProvenanceCandidate,
)


class AssignmentValidationSpecialist:
    specialist_name = "assignment_validation"
    goal = "Validate role, department, permission, workload, and conflict boundaries."

    def run(
        self,
        portfolio: ResolutionPortfolio,
        provenance: dict[str, list[ProvenanceCandidate]],
        responsibility: dict[str, dict],
        balanced: dict[str, dict],
        escalation: dict,
    ) -> list[OwnershipAssignment]:
        assignments = []
        priority_by_gap = {item.gap_id: item.priority for item in portfolio.priorities}
        for gap in portfolio.gaps:
            selection = balanced[gap.gap_id]
            primary = selection["primary"]
            backup = selection["backup"]
            approver = selection["approver"]
            rule = responsibility[gap.gap_id]
            confidence_by_user = {
                item.user_id: item.confidence for item in provenance[gap.gap_id]
            }
            checks = {
                "role_eligible": bool(primary and primary.role in rule["eligible_roles"]),
                "department_match": bool(
                    primary and primary.department == (gap.department or primary.department)
                ),
                "permission_valid": bool(
                    primary
                    and (
                        rule["required_permission"] in primary.permissions
                        or "manage_department_tasks" in primary.permissions
                    )
                ),
                "conflict_of_interest": bool(
                    primary and approver and primary.user_id == approver.user_id
                ),
                "workload_acceptable": bool(primary and primary.active_tasks <= 8),
                "independent_approver": bool(
                    primary and approver and primary.user_id != approver.user_id
                ),
            }
            valid = (
                all(
                    checks[item]
                    for item in (
                        "role_eligible",
                        "department_match",
                        "permission_valid",
                        "workload_acceptable",
                        "independent_approver",
                    )
                )
                and not checks["conflict_of_interest"]
            )
            assignment_confidence = (
                confidence_by_user.get(primary.user_id, 0.0) if primary else 0.0
            )
            days = 3 if priority_by_gap.get(gap.gap_id) == "critical" else 7
            assignments.append(
                OwnershipAssignment(
                    assignment_id=f"ASN-{gap.gap_id}",
                    gap_id=gap.gap_id,
                    primary_owner=self._reference(
                        primary, assignment_confidence, gap
                    ),
                    backup_owner=self._reference(
                        backup,
                        confidence_by_user.get(backup.user_id, 0.0) if backup else 0.0,
                        gap,
                    ),
                    approver=self._reference(
                        approver,
                        confidence_by_user.get(approver.user_id, 0.8)
                        if approver
                        else 0.0,
                        gap,
                    ),
                    assignment_confidence=assignment_confidence,
                    workload_assessment={
                        "candidates": selection["candidate_workloads"],
                        "threshold": 0.8,
                    },
                    conflict_checks=checks,
                    escalation_plan=escalation[gap.gap_id],
                    due_date_recommendation=date.today() + timedelta(days=days),
                    communication_data_scope=[
                        "gap title",
                        "required evidence type",
                        "deadline",
                        "submission instructions",
                    ],
                    status="recommended" if valid else "unresolved",
                )
            )
        return assignments

    @staticmethod
    def _reference(member, confidence, gap):
        if member is None:
            return None
        return OwnerReference(
            user_id=member.user_id,
            display_name=member.display_name,
            role=member.role,
            confidence=confidence,
            selection_reasons=[
                f"Role is relevant to {gap.gap_type}.",
                "Member belongs to the responsible department or approval hierarchy.",
                "Configured permissions and workload were checked.",
            ],
        )
