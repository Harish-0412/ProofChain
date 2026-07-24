"""Schema invariants and optimistic coordination-state tests."""

from __future__ import annotations

import shutil
import uuid

import pytest
from pydantic import ValidationError

from proofchain.core.paths import get_run_dir
from proofchain.agentic.dependency_manager import DependencyManager
from proofchain.agentic.policies import ConfidencePolicy
from proofchain.repositories.json_coordination_repository import (
    CoordinationVersionConflict,
    JsonCoordinationRepository,
)
from proofchain.schemas.agentic import (
    AgentPlan,
    CompletionDecision,
    CoordinationPatch,
    CoordinationState,
    Goal,
    PlanStep,
)


def make_goal(run_id: str, goal_id: str, agent: str = "supervisor") -> Goal:
    return Goal(
        goal_id=goal_id,
        run_id=run_id,
        assigned_agent=agent,
        objective="Validate a bounded test goal.",
        goal_type="test",
        success_conditions=["A replayable result exists."],
    )


def test_agentic_schema_invariants_reject_invalid_claims():
    with pytest.raises(ValidationError):
        CompletionDecision(
            decision_id="DEC-1",
            run_id="RUN-1",
            goal_id="GOAL-1",
            agent_name="test",
            goal_satisfied=True,
            confidence=1.1,
            final_status="blocked",
            explanation="Contradictory claim.",
        )

    with pytest.raises(ValidationError):
        AgentPlan(
            plan_id="PLAN-1",
            run_id="RUN-1",
            goal_id="GOAL-1",
            agent_name="test",
            revision=1,
            rationale="Invalid duplicate sequence.",
            steps=[
                PlanStep(
                    step_id="STEP-1",
                    sequence=1,
                    objective="One",
                    expected_observation="One",
                    completion_condition="One",
                ),
                PlanStep(
                    step_id="STEP-2",
                    sequence=1,
                    objective="Two",
                    expected_observation="Two",
                    completion_condition="Two",
                ),
            ],
        )


def test_coordination_repository_rejects_stale_version_and_persists_transition():
    run_id = f"RUN-COORD-{uuid.uuid4().hex[:10].upper()}"
    repository = JsonCoordinationRepository()
    top = make_goal(run_id, f"GOAL-{run_id}-TOP")
    child = make_goal(run_id, f"GOAL-{run_id}-CHILD", "evidence_collector")
    try:
        initial = repository.initialize(top, [child])
        updated = repository.update_state(
            run_id,
            initial.state_version,
            CoordinationPatch(complete_goals=[child.goal_id]),
        )
        assert child.goal_id in updated.completed_goals
        assert child.goal_id not in updated.active_goals
        assert updated.state_version == initial.state_version + 1

        with pytest.raises(CoordinationVersionConflict):
            repository.update_state(
                run_id,
                initial.state_version,
                CoordinationPatch(add_blockers=["stale write"]),
            )

        reloaded = JsonCoordinationRepository().load_state(run_id)
        assert reloaded == updated
    finally:
        shutil.rmtree(get_run_dir(run_id), ignore_errors=True)


def test_confidence_policy_never_overrides_blocker_and_deadlock_is_detected():
    assert ConfidencePolicy.action_for(0.99, deterministic_blocker=True) == (
        "block_positive_decision"
    )
    assert ConfidencePolicy.action_for(0.72) == "retry_or_ask_peer"
    assert ConfidencePolicy.action_for(0.45) == "request_human"

    run_id = "RUN-DEADLOCK"
    goal_a = make_goal(run_id, "GOAL-A", "evidence_collector").model_copy(
        update={"dependencies": ["GOAL-B"]}
    )
    goal_b = make_goal(run_id, "GOAL-B", "evidence_classification").model_copy(
        update={"dependencies": ["GOAL-A"]}
    )
    report = DependencyManager().detect_deadlock(
        [goal_a, goal_b],
        CoordinationState(
            run_id=run_id,
            top_level_goal_id="GOAL-TOP",
            active_goals=[],
        ),
    )
    assert report.detected
    assert set(report.circular_goal_ids) == {"GOAL-A", "GOAL-B"}
