"""Provenance, workload, permission, conflict, backup, and escalation tests."""

from __future__ import annotations

from proofchain.agents.ownership.assignment_validator import (
    AssignmentValidationSpecialist,
)
from proofchain.agents.ownership.escalation_planner import (
    EscalationPlanningSpecialist,
)
from proofchain.agents.ownership.provenance_resolver import (
    EvidenceProvenanceSpecialist,
)
from proofchain.agents.ownership.responsibility_matcher import (
    ResponsibilityMatchingSpecialist,
)
from proofchain.agents.ownership.workload_balancer import (
    WorkloadBalancingSpecialist,
)
from proofchain.schemas.gaps import (
    GapResolutionPlan,
    PrioritizedGap,
    ResolutionGap,
    ResolutionPortfolio,
    ResolutionStrategy,
)
from proofchain.schemas.ownership import OrganisationMember


def portfolio():
    gap = ResolutionGap(
        gap_id="RGAP-0001",
        source_type="integrity_gap",
        source_ids=["GAP-1"],
        affected_claims=["CLM-1"],
        affected_requirements=["C3.2.1"],
        department="CSE",
        gap_type="missing_required_document",
        severity="high",
        blocking=True,
        description="Signed approval is missing.",
        root_cause="Signed version was not uploaded.",
        readiness_impact=12,
    )
    plan = GapResolutionPlan(
        plan_id="RPLAN-1",
        gap_id=gap.gap_id,
        strategies=[
            ResolutionStrategy(
                strategy_id="STR-1",
                title="Upload signed approval",
                actions=["Locate", "Verify", "Upload"],
                estimated_effort="medium",
                expected_resolution_confidence=0.95,
                requires_new_evidence=True,
            )
        ],
        recommended_strategy_id="STR-1",
        required_completion_evidence=["Signed approval", "Passing revalidation"],
        expected_readiness_delta=12,
    )
    return ResolutionPortfolio(
        portfolio_id="PORT-1",
        run_id="RUN-1",
        current_readiness=72,
        projected_readiness=84,
        evidence_debt_score=68,
        gaps=[gap],
        plans=[plan],
        priorities=[
            PrioritizedGap(
                gap_id=gap.gap_id,
                priority_score=90,
                priority="critical",
                reason="Blocking approval gap.",
            )
        ],
        minimal_resolution_set=[gap.gap_id],
        dependency_graph={gap.gap_id: []},
    )


def members():
    return [
        OrganisationMember(
            user_id="USR-COORD",
            display_name="CSE Accreditation Coordinator",
            role="Department Accreditation Coordinator",
            department="CSE",
            permissions=["upload_evidence", "manage_department_tasks"],
            active_tasks=2,
        ),
        OrganisationMember(
            user_id="USR-EVENT",
            display_name="CSE Event Coordinator",
            role="Event Coordinator",
            department="CSE",
            permissions=["upload_evidence", "correct_attendance"],
            active_tasks=9,
        ),
        OrganisationMember(
            user_id="USR-HOD",
            display_name="Head of CSE",
            role="Head of Department",
            department="CSE",
            permissions=["approve_evidence"],
            active_tasks=3,
        ),
    ]


def test_owner_selection_balances_workload_and_preserves_independent_approval():
    value = portfolio()
    people = members()
    provenance = EvidenceProvenanceSpecialist().run(value, people, "CSE")
    responsibility = ResponsibilityMatchingSpecialist().run(value)
    balanced = WorkloadBalancingSpecialist().run(
        provenance, responsibility, people
    )
    escalation = EscalationPlanningSpecialist().run(value)
    assignments = AssignmentValidationSpecialist().run(
        value, provenance, responsibility, balanced, escalation
    )
    assignment = assignments[0]
    assert assignment.status == "recommended"
    assert assignment.primary_owner.user_id == "USR-COORD"
    assert assignment.approver.user_id == "USR-HOD"
    assert assignment.primary_owner.user_id != assignment.approver.user_id
    assert assignment.backup_owner is not None
    assert len(assignment.escalation_plan) == 3
    assert assignment.human_approval_required
    assert not assignment.conflict_checks["conflict_of_interest"]


def test_unauthorized_candidate_is_formally_unresolved():
    value = portfolio()
    people = [
        OrganisationMember(
            user_id="USR-NOAUTH",
            display_name="Unauthorized User",
            role="Department Accreditation Coordinator",
            department="CSE",
            permissions=[],
            active_tasks=0,
        )
    ]
    provenance = EvidenceProvenanceSpecialist().run(value, people, "CSE")
    responsibility = ResponsibilityMatchingSpecialist().run(value)
    balanced = WorkloadBalancingSpecialist().run(
        provenance, responsibility, people
    )
    assignments = AssignmentValidationSpecialist().run(
        value,
        provenance,
        responsibility,
        balanced,
        EscalationPlanningSpecialist().run(value),
    )
    assert assignments[0].status == "unresolved"
    assert assignments[0].primary_owner is None
