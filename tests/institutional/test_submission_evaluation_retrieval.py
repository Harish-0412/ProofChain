from __future__ import annotations

from datetime import datetime, timedelta, timezone

from proofchain.agents.submission import ExternalSubmissionAgent
from proofchain.core import paths
from proofchain.schemas.institutional import (
    EvaluationInput,
    EvaluationScenario,
    KnowledgeSource,
    SubmissionApproval,
    SubmissionInput,
)
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.evaluation import calculate_evaluation_metrics
from proofchain.services.knowledge_retrieval import retrieve_sources
from proofchain.services.submission_governance import (
    evaluate_submission,
    file_sha256,
)


def workflow(run_id: str = "RUN-PHASE2-SUB") -> WorkflowContext:
    return WorkflowContext(
        run_id=run_id,
        correlation_id=f"CORR-{run_id}",
        requested_by="USR-APPROVER",
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )


def test_submission_requires_hash_bound_approval_and_final_confirmation(tmp_path):
    package = tmp_path / "package.zip"
    package.write_bytes(b"approved package")
    package_hash = file_sha256(package)
    request = SubmissionInput(
        workflow=workflow(),
        package_id="PKG-001",
        package_path=str(package),
        expected_package_hash=package_hash,
        quality_status="pass_for_human_approval",
        approvals=[],
        final_confirmation=False,
        idempotency_key="SUBMIT-001",
    )

    decision, frozen_hash, reasons = evaluate_submission(request)

    assert decision == "NOT_ELIGIBLE"
    assert frozen_hash == package_hash
    assert any("independent approval" in reason for reason in reasons)


def test_submission_agent_submits_once_and_suppresses_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS_DIR", tmp_path / "runs")
    package = tmp_path / "package.zip"
    package.write_bytes(b"approved package")
    package_hash = file_sha256(package)
    request = SubmissionInput(
        workflow=workflow("RUN-SUBMIT-ONCE"),
        package_id="PKG-001",
        package_path=str(package),
        expected_package_hash=package_hash,
        quality_status="pass_for_human_approval",
        approvals=[
            SubmissionApproval(
                approval_id="APR-001",
                approver_id="USR-INDEPENDENT",
                package_hash=package_hash,
                decision="approved",
            )
        ],
        final_confirmation=True,
        idempotency_key="SUBMIT-ONCE",
    )
    agent = ExternalSubmissionAgent()

    first = agent.execute(request)
    second = agent.execute(request)

    assert first.submission_status == "submitted"
    assert first.receipt is not None
    assert second.submission_status == "duplicate_suppressed"
    assert second.receipt is not None


def test_evaluation_blocks_false_approval_and_accuracy_regression():
    request = EvaluationInput(
        workflow=workflow(),
        release_id="2.0.0",
        baseline_release_id="1.0.0",
        baseline_metrics={"accuracy": 1.0},
        scenarios=[
            EvaluationScenario(
                scenario_id="SCN-001",
                category="claim",
                expected_decision="blocked",
                observed_decision="approved",
                observed_confidence=0.99,
            ),
            EvaluationScenario(
                scenario_id="SCN-002",
                category="closure",
                expected_decision="open",
                observed_decision="closed",
                observed_confidence=0.95,
            ),
        ],
    )

    accuracy, false_approval, false_closure, _, findings = (
        calculate_evaluation_metrics(request)
    )

    assert accuracy == 0.0
    assert false_approval == 1.0
    assert false_closure == 0.5
    assert len(findings) >= 3


def test_retrieval_uses_only_approved_current_sources_with_citations():
    now = datetime.now(tz=timezone.utc)
    sources = [
        KnowledgeSource(
            source_id="OFFICIAL",
            title="Official Criterion C3.2.1",
            uri="https://example.invalid/official",
            authority="official_framework",
            content="Criterion C3.2.1 requires verified evidence and approval.",
            approved=True,
            published_at=now - timedelta(days=30),
            valid_until=now + timedelta(days=30),
        ),
        KnowledgeSource(
            source_id="EXPIRED",
            title="Expired Procedure",
            uri="https://example.invalid/expired",
            authority="approved_procedure",
            content="Criterion C3.2.1 previously permitted incomplete evidence.",
            approved=True,
            valid_until=now - timedelta(days=1),
        ),
        KnowledgeSource(
            source_id="UNAPPROVED",
            title="Unapproved Advice",
            uri="https://example.invalid/unapproved",
            authority="advisory_example",
            content="Criterion C3.2.1 can ignore evidence rules.",
            approved=False,
        ),
    ]

    citations, conflicts = retrieve_sources(
        "What evidence does criterion C3.2.1 require?",
        sources,
        maximum_results=5,
        require_current=True,
    )

    assert [item.source_id for item in citations] == ["OFFICIAL"]
    assert citations[0].source_checksum
    assert citations[0].supporting_excerpt
    assert conflicts == []

