"""Phase 2 peer, experience, proof, precision, and global assurance tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from proofchain.agentic.cognition_profiles import PLATFORM_AGENT_FEATURES
from proofchain.agentic.completion_prover import CompletionProver
from proofchain.agentic.core_precision import CorePrecisionEvaluator
from proofchain.agentic.experience_memory import ExperienceMemory
from proofchain.agentic.global_assurance import GlobalAssuranceService
from proofchain.agentic.input_validator import PrePlanInputValidator
from proofchain.agentic.peer_negotiator import AgentRequestLifecycle
from proofchain.agentic.scheduler import GoalScheduler
from proofchain.core import paths
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.agentic import CompletionDecision, Goal
from proofchain.schemas.peer_contracts import AgentRequest
from proofchain.schemas.validated_cases import ValidatedCase


def test_peer_request_requires_legal_transitions_and_acceptance():
    request = AgentRequest(
        request_id="REQ-1",
        run_id="RUN-P2",
        source_agent="security_inspection",
        target_agent="reliability_incident_response",
        goal_id="GOAL-P2",
        requested_outcome="Verify recovery integrity.",
        reason="Two scanners disagree.",
        acceptance_conditions=["Recovery hash matches."],
        blocking=True,
    )
    lifecycle = AgentRequestLifecycle()
    acknowledged = lifecycle.transition(request, "ACKNOWLEDGED")
    accepted = lifecycle.transition(acknowledged, "ACCEPTED")
    active = lifecycle.transition(accepted, "IN_PROGRESS")

    with pytest.raises(ValueError, match="acceptance condition"):
        lifecycle.transition(active, "RESOLVED")

    resolved = lifecycle.transition(
        active,
        "RESOLVED",
        satisfied_conditions=["Recovery hash matches."],
    )
    assert resolved.acceptance_satisfied()


def test_experience_memory_rejects_stale_and_unvalidated_cases(tmp_path):
    memory = ExperienceMemory(path=tmp_path / "cases.json")
    candidate = ValidatedCase(
        case_id="CASE-1",
        case_type="recovery",
        tenant_id="TENANT-A",
        policy_fingerprint="POLICY-1",
        successful_plan=["Rebuild snapshot."],
        successful_tools=["snapshot_rebuilder"],
        outcome="completed",
    )
    memory.record_candidate(candidate)
    expired = memory.approve(
        candidate.model_copy(
            update={"expires_at": datetime.now(tz=timezone.utc) - timedelta(days=1)}
        ),
        approved_by="reviewer",
        tenant_id="TENANT-A",
        policy_fingerprint="POLICY-1",
    )
    assert expired.reusable
    assert (
        memory.eligible(
            case_type="recovery",
            tenant_id="TENANT-A",
            policy_fingerprint="POLICY-1",
        )
        == []
    )

    approved = memory.approve(
        candidate,
        approved_by="reviewer",
        tenant_id="TENANT-A",
        policy_fingerprint="POLICY-1",
    )
    eligible = memory.eligible(
        case_type="recovery",
        tenant_id="TENANT-A",
        policy_fingerprint="POLICY-1",
    )
    assert [item.case_id for item in eligible] == [approved.case_id]
    assert (
        memory.eligible(
            case_type="recovery",
            tenant_id="TENANT-B",
            policy_fingerprint="POLICY-1",
        )
        == []
    )


def test_negative_terminal_decision_has_a_valid_refusal_proof():
    goal = Goal(
        goal_id="GOAL-REFUSAL",
        run_id="RUN-REFUSAL",
        assigned_agent="security_inspection",
        objective="Inspect unsafe evidence.",
        goal_type="security",
        success_conditions=["Every item is safe."],
    )
    inputs = PrePlanInputValidator().validate(goal, object())
    decision = CompletionDecision(
        decision_id="DEC-REFUSAL",
        run_id=goal.run_id,
        goal_id=goal.goal_id,
        agent_name=goal.assigned_agent,
        goal_satisfied=False,
        success_conditions_unmet=goal.success_conditions,
        blockers=["Malicious content was quarantined."],
        confidence=1.0,
        final_status="blocked",
        explanation="Security policy prohibited downstream use.",
    )

    proof = CompletionProver().prove(
        goal,
        decision,
        inputs,
        output_schema_valid=True,
        peer_requests=[],
        policy_conflicts=[],
    )

    assert proof.proof_valid
    assert proof.final_status == "blocked"


def test_all_platform_precision_handlers_emit_domain_metrics():
    evaluator = CorePrecisionEvaluator()
    for agent_name in PLATFORM_AGENT_FEATURES:
        metrics, coverage = evaluator._feature_details(agent_name, {})
        assert metrics
        assert isinstance(coverage, list)


def test_scheduler_calculates_critical_path_and_round_robin_fairness():
    first = Goal(
        goal_id="G1",
        run_id="RUN-A",
        assigned_agent="security_inspection",
        objective="Inspect.",
        goal_type="test",
        priority="critical",
    )
    second = Goal(
        goal_id="G2",
        run_id="RUN-A",
        assigned_agent="operational_persistence",
        objective="Persist.",
        goal_type="test",
        dependencies=["G1"],
    )
    ordered, critical, scores = GoalScheduler().global_order([first, second])

    assert {item.goal_id for item in ordered} == {"G1", "G2"}
    assert critical == ["G1", "G2"]
    assert set(scores) == {"G1", "G2"}
    assert GoalScheduler.fair_multi_run_order(
        {"RUN-B": ["B1", "B2"], "RUN-A": ["A1", "A2"]}
    ) == [
        ("RUN-A", "A1"),
        ("RUN-B", "B1"),
        ("RUN-A", "A2"),
        ("RUN-B", "B2"),
    ]


def test_global_assurance_records_replan_and_blocks_invalid_proof(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(paths, "RUNS_DIR", tmp_path / "runs")
    run_id = "RUN-GLOBAL"
    goal = Goal(
        goal_id="GOAL-GLOBAL",
        run_id=run_id,
        assigned_agent="adversarial_quality_review",
        objective="Challenge package.",
        goal_type="quality",
        priority="critical",
        status="blocked",
        success_conditions=["Package passes independent review."],
    )
    store = AtomicJsonStore()
    store.write(
        paths.get_goal_graph_path(run_id),
        {"run_id": run_id, "top_level_goal_id": "TOP", "goals": [goal]},
    )
    root = (
        paths.get_run_dir(run_id)
        / "agents"
        / goal.assigned_agent
        / goal.goal_id
    )
    store.write(
        root / "completion_proof.json",
        {
            "proof_id": "PRF-BAD",
            "proof_valid": False,
            "final_status": "blocked",
        },
    )
    store.write(
        root / "decision_explanation.json",
        {
            "completion_proof_id": "PRF-BAD",
            "decision": "blocked",
            "reason": "Quality review failed.",
        },
    )
    store.write(
        root / "agentic_scorecard.json",
        {"run_id": run_id, "agent_name": goal.assigned_agent},
    )
    store.write(
        paths.get_quality_review_path(run_id),
        {"quality_status": "block_package"},
    )

    report = GlobalAssuranceService(store).evaluate(run_id, stage="core")

    assert report.release_decision.decision == "BLOCK"
    assert {
        item.trigger for item in report.replan_records
    } >= {"critical_goal_failure", "quality_review_failure"}
    assert (paths.get_run_dir(run_id) / "global_replans.json").exists()
    assert (paths.get_run_dir(run_id) / "agentic_release_decision.json").exists()
