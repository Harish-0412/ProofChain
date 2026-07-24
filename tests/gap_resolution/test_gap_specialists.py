"""Gap normalization, strategy, readiness, dependency, and priority tests."""

from __future__ import annotations

import uuid

from proofchain.agents.gap_resolution.gap_detector import GapDetectionSpecialist
from proofchain.agents.gap_resolution.gap_prioritizer import (
    GapPrioritizationSpecialist,
)
from proofchain.agents.gap_resolution.readiness_simulator import (
    ReadinessSimulationSpecialist,
)
from proofchain.agents.gap_resolution.resolution_planner import (
    ResolutionPlanningSpecialist,
)
from proofchain.agents.gap_resolution.root_cause_analyzer import (
    RootCauseAnalysisSpecialist,
)
from proofchain.core.enums import FindingType, GapType, Severity
from proofchain.schemas.claims import ClaimDecision, ClaimLineage
from proofchain.schemas.gaps import GapResolutionInput
from proofchain.schemas.integrity import EvidenceGap, IntegrityFinding, IntegritySummary
from proofchain.schemas.workflow import WorkflowContext


def test_findings_become_unique_prioritized_resolution_portfolio():
    workflow = WorkflowContext(
        run_id=f"RUN-GAP-{uuid.uuid4().hex[:8].upper()}",
        correlation_id=str(uuid.uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )
    claim = ClaimDecision(
        claim_id="CLM-001",
        requirement_id="C3.2.1",
        original_claim="120 students participated.",
        status="partially_supported",
        confidence=0.72,
        atomic_decisions=[],
        defensible_claim_text="108 students participated.",
        recommended_actions=["Revise count to 108."],
        claim_fragility_score=0.5,
        requires_human_review=True,
        lineage=ClaimLineage(claim_id="CLM-001"),
    )
    missing_finding = IntegrityFinding(
        finding_id="FND-MISSING",
        run_id=workflow.run_id,
        rule_id="DOC-001",
        finding_type=FindingType.MISSING_REQUIRED_FIELD,
        severity=Severity.HIGH,
        requirement_id="C3.2.1",
        title="Approval missing",
        description="Approval evidence is missing.",
        blocking=True,
    )
    count_finding = IntegrityFinding(
        finding_id="FND-COUNT",
        run_id=workflow.run_id,
        rule_id="EVT-COUNT-001",
        finding_type=FindingType.PARTICIPANT_COUNT_MISMATCH,
        severity=Severity.HIGH,
        title="Count mismatch",
        description="Report says 120 but attendance supports 108.",
        blocking=True,
    )
    source_gap = EvidenceGap(
        gap_id="GAP-MISSING",
        run_id=workflow.run_id,
        requirement_id="C3.2.1",
        department="CSE",
        gap_type=GapType.MISSING_REQUIRED_DOCUMENT,
        severity=Severity.HIGH,
        missing_evidence_type="approval_document",
        related_findings=["FND-MISSING"],
        description="Signed approval is unavailable.",
        recommended_action="Upload approval.",
        blocking=True,
    )
    input_data = GapResolutionInput(
        workflow=workflow,
        claim_decisions=[claim],
        integrity_findings=[missing_finding, count_finding],
        integrity_gaps=[source_gap],
        integrity_summaries=[
            IntegritySummary(scope_id="CSE:C3.2.1", integrity_score=72)
        ],
    )
    gaps = GapDetectionSpecialist().run(input_data)
    assert len(gaps) == 2
    assert all(gap.affected_claims == ["CLM-001"] for gap in gaps)

    gaps = RootCauseAnalysisSpecialist().run(gaps)
    assert all(gap.root_cause and gap.root_cause_hypotheses for gap in gaps)
    plans = ResolutionPlanningSpecialist().run(gaps)
    assert all(len(plan.strategies) >= 2 for plan in plans)
    assert all(plan.required_completion_evidence for plan in plans)
    gaps, plans, simulation = ReadinessSimulationSpecialist().run(
        gaps, plans, 72
    )
    priorities = GapPrioritizationSpecialist().run(gaps, plans)
    assert simulation.projected_readiness > simulation.current_readiness
    assert all(plan.expected_readiness_delta > 0 for plan in plans)
    assert priorities[0].priority in {"critical", "high"}
    assert any("revalidate_claim" in plan.dependencies for plan in plans)
