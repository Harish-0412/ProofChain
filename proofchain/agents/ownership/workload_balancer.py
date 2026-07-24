"""Specialist that selects eligible candidates with bounded workload."""

from __future__ import annotations

from proofchain.schemas.ownership import OrganisationMember, ProvenanceCandidate


class WorkloadBalancingSpecialist:
    specialist_name = "workload_balancing"
    goal = "Recommend primary, backup, and approver candidates without overload."

    def run(
        self,
        provenance: dict[str, list[ProvenanceCandidate]],
        responsibility: dict[str, dict],
        members: list[OrganisationMember],
    ) -> dict[str, dict]:
        by_id = {member.user_id: member for member in members}
        results = {}
        for gap_id, candidates in provenance.items():
            rule = responsibility[gap_id]
            eligible = [
                by_id[item.user_id]
                for item in candidates
                if item.user_id in by_id
                and by_id[item.user_id].available
                and by_id[item.user_id].role in rule["eligible_roles"]
                and (
                    rule["required_permission"] in by_id[item.user_id].permissions
                    or "manage_department_tasks" in by_id[item.user_id].permissions
                )
            ]
            eligible.sort(key=lambda item: (item.active_tasks, item.user_id))
            primary = eligible[0] if eligible else None
            backup = eligible[1] if len(eligible) > 1 else None
            approvers = [
                item
                for item in members
                if item.available
                and item.department
                in {
                    primary.department if primary else "",
                    "INSTITUTION",
                }
                and (
                    "approve_evidence" in item.permissions
                    or "review_accreditation_decision" in item.permissions
                )
                and (primary is None or item.user_id != primary.user_id)
            ]
            approvers.sort(key=lambda item: (item.active_tasks, item.user_id))
            results[gap_id] = {
                "primary": primary,
                "backup": backup,
                "approver": approvers[0] if approvers else None,
                "candidate_workloads": [
                    {
                        "user_id": item.user_id,
                        "active_tasks": item.active_tasks,
                        "workload_score": min(1.0, item.active_tasks / 10),
                        "recommendation": (
                            "eligible" if item.active_tasks <= 8 else "avoid_new_assignment"
                        ),
                    }
                    for item in eligible
                ],
            }
        return results
