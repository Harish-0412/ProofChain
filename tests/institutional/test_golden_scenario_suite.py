from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from proofchain.agents.closure.issue_state_decider import (
    IssueStateDecisionSpecialist,
)
from proofchain.schemas.closure import ClosureCheck
from proofchain.schemas.issues import CanonicalIssue
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.golden_scenario_suite import GoldenScenarioSuite


def _workflow() -> WorkflowContext:
    return WorkflowContext(
        run_id="RUN-GOLDEN-SUITE",
        correlation_id=str(uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )


def test_all_mandatory_golden_scenarios_pass_production_policies(tmp_path: Path):
    package = tmp_path / "package.zip"
    package.write_bytes(b"deterministic package")

    scenarios = GoldenScenarioSuite().run(
        workflow=_workflow(),
        package_path=package,
    )

    assert len(scenarios) == 10
    assert {item.category for item in scenarios} == {
        "fully_supported_claim",
        "partially_supported_claim",
        "contradicted_claim",
        "missing_evidence",
        "corrected_evidence",
        "reopened_issue",
        "failed_package_review",
        "successful_package_review",
        "authorized_submission",
        "rejected_submission",
    }
    assert all(
        item.expected_decision == item.observed_decision for item in scenarios
    )
    assert all(item.fixture_hash for item in scenarios)


def test_failed_revalidation_reopens_a_resolved_issue():
    issue = CanonicalIssue(
        issue_id="ISS-REOPEN",
        run_id="RUN-GOLDEN-SUITE",
        issue_type="contradiction",
        root_entity_type="integrity_gap",
        root_entity_id="GAP-REOPEN",
        severity="critical",
        blocking=True,
        status="RESOLVED",
        canonical_key="golden|reopen",
    )
    check = ClosureCheck(
        check_id="CHK-REOPEN",
        issue_id=issue.issue_id,
        evidence_submitted=True,
        evidence_registered=True,
        classification_complete=True,
        integrity_rules_passed=False,
        affected_claims_revalidated=True,
        closure_policy_satisfied=False,
        status="under_revalidation",
        reasons=["Targeted integrity checks still fail."],
    )

    updated, transitions = IssueStateDecisionSpecialist().run([issue], [check])

    assert updated[0].status == "REOPENED"
    assert transitions[0].from_status == "RESOLVED"
    assert transitions[0].to_status == "REOPENED"
