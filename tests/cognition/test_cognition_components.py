"""Focused tests for Phase 1 cognition contracts and policy gates."""

from __future__ import annotations

from proofchain.agentic.cognition_profiles import (
    ALL_AGENT_FEATURES,
    CORE_AGENT_FEATURES,
    PLATFORM_AGENT_FEATURES,
    cognition_profile_for,
)
from proofchain.agentic.completion_prover import CompletionProver
from proofchain.agentic.goal_interpreter import GoalInterpreter
from proofchain.agentic.input_validator import PrePlanInputValidator
from proofchain.agentic.plan_critic import PlanCritic
from proofchain.agentic.uncertainty_calibrator import UncertaintyCalibrator
from proofchain.schemas.advanced_plans import AdvancedAgentPlan, AdvancedPlanStep
from proofchain.schemas.agentic import CompletionDecision, Goal
from proofchain.schemas.cognition import NormalizedToolObservation
from proofchain.schemas.peer_contracts import AgentRequest


def _goal() -> Goal:
    return Goal(
        goal_id="GOAL-COGNITION",
        run_id="RUN-COGNITION",
        assigned_agent="evidence_collector",
        objective="Validate C3.2.1 evidence for 2025-2026.",
        goal_type="cognition_test",
        constraints=["Do not modify original evidence."],
        success_conditions=["Evidence coverage is proven."],
    )


def test_goal_interpreter_detects_policy_ambiguity_and_prohibited_actions():
    interpreted = GoalInterpreter().interpret(_goal(), policy_version_known=False)

    assert interpreted.clarification_required
    assert "policy_version_unknown" in interpreted.ambiguity_flags
    assert interpreted.prohibited_actions == ["Do not modify original evidence."]
    assert {"C3.2.1", "2025-2026"} <= set(interpreted.subject_entities)


def test_input_validator_rejects_missing_path_and_cross_run_input(tmp_path):
    goal = _goal().model_copy(
        update={"input_references": [str(tmp_path / "missing.json")]}
    )

    class Workflow:
        run_id = "RUN-WRONG"

    class Input:
        workflow = Workflow()
        schema_version = "1.0.0"

    result = PrePlanInputValidator().validate(goal, Input())

    assert not result.valid
    assert result.missing_inputs
    assert result.unauthorized_inputs == ["RUN-WRONG"]
    assert result.recommended_action in {"request_human", "block"}


def test_plan_critic_rejects_unauthorized_tool_and_uncovered_condition():
    goal = _goal()
    plan = AdvancedAgentPlan(
        plan_id="PLAN-1",
        run_id=goal.run_id,
        goal_id=goal.goal_id,
        agent_name=goal.assigned_agent,
        revision=1,
        rationale="Test",
        success_condition_coverage={},
        steps=[
            AdvancedPlanStep(
                step_id="STEP-1",
                sequence=1,
                objective="Run unsafe tool.",
                preferred_tool="unsafe",
                success_condition="Result exists.",
                failure_condition="Result is missing.",
            )
        ],
    )

    critique = PlanCritic().critique(goal, plan, allowed_tools={"safe"})

    assert not critique.approved
    assert critique.missing_steps == goal.success_conditions
    assert critique.unsafe_steps


def test_uncertainty_policy_uses_decomposed_thresholds_and_block_override():
    goal = _goal()
    interpreted = GoalInterpreter().interpret(goal, policy_version_known=True)
    inputs = PrePlanInputValidator().validate(goal, object())
    high = NormalizedToolObservation(
        observation_id="OBS-HIGH",
        run_id=goal.run_id,
        goal_id=goal.goal_id,
        agent_name=goal.assigned_agent,
        plan_step_id="STEP-1",
        source_tool="safe",
        source_version="1.0.0",
        summary="Validated.",
        data_quality="high",
        confidence=1.0,
        sufficient_for_step=True,
    )
    low = high.model_copy(
        update={
            "observation_id": "OBS-LOW",
            "data_quality": "invalid",
            "confidence": 0.1,
            "sufficient_for_step": False,
        }
    )

    automatic = UncertaintyCalibrator().assess(
        interpreted, inputs, high, completion_confidence=1.0
    )
    blocked = UncertaintyCalibrator().assess(
        interpreted, inputs, low, completion_confidence=1.0
    )

    assert automatic.recommended_action == "continue"
    assert blocked.deterministic_block
    assert blocked.recommended_action == "prohibit_positive_decision"


def test_completion_proof_rejects_unresolved_blocking_peer_request():
    goal = _goal()
    inputs = PrePlanInputValidator().validate(goal, object())
    decision = CompletionDecision(
        decision_id="DEC-1",
        run_id=goal.run_id,
        goal_id=goal.goal_id,
        agent_name=goal.assigned_agent,
        goal_satisfied=True,
        success_conditions_met=goal.success_conditions,
        confidence=1.0,
        final_status="completed",
        explanation="All local checks passed.",
    )
    request = AgentRequest(
        request_id="REQ-1",
        run_id=goal.run_id,
        source_agent=goal.assigned_agent,
        target_agent="evidence_integrity",
        goal_id=goal.goal_id,
        requested_outcome="Independent verification",
        reason="A peer must reproduce the result.",
        acceptance_conditions=["Count reproduced."],
        blocking=True,
    )

    proof = CompletionProver().prove(
        goal,
        decision,
        inputs,
        output_schema_valid=True,
        peer_requests=[request],
        policy_conflicts=[],
    )

    assert not proof.proof_valid
    assert proof.final_status == "needs_human_review"
    assert proof.unresolved_peer_requests == ["REQ-1"]


def test_phase_two_profiles_cover_all_22_primary_agents():
    assert len(CORE_AGENT_FEATURES) == 10
    assert len(PLATFORM_AGENT_FEATURES) == 12
    assert len(ALL_AGENT_FEATURES) == 22
    for agent_name in ALL_AGENT_FEATURES:
        assert (
            cognition_profile_for(agent_name).profile_name
            == "advanced-cognition-platform"
        )
    assert cognition_profile_for("test_fixture").profile_name == "legacy-compatible"
