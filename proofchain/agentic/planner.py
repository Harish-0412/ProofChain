"""Policy-based planning utilities used by all domain agents."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from proofchain.schemas.agentic import AgentPlan, Goal, PlanStep


def make_plan(
    *,
    goal: Goal,
    agent_name: str,
    tool_name: str,
    preparation_objective: str,
    execution_objective: str,
    review_objective: str,
    expected_output: str,
    revision: int = 1,
) -> AgentPlan:
    token = uuid4().hex[:10].upper()
    steps: Sequence[PlanStep] = [
        PlanStep(
            step_id=f"STEP-{token}-01",
            sequence=1,
            objective=preparation_objective,
            required_inputs=goal.input_references,
            expected_observation="Scope, constraints, and dependencies are explicit.",
            completion_condition="The agent has enough bounded context to execute.",
        ),
        PlanStep(
            step_id=f"STEP-{token}-02",
            sequence=2,
            objective=execution_objective,
            proposed_tool=tool_name,
            required_inputs=goal.input_references,
            expected_observation=expected_output,
            completion_condition="The deterministic tool returns a validated artifact.",
        ),
        PlanStep(
            step_id=f"STEP-{token}-03",
            sequence=3,
            objective=review_objective,
            expected_observation="Success conditions, uncertainty, and blockers are evaluated.",
            completion_condition="A policy-based completion claim can be produced.",
        ),
    ]
    return AgentPlan(
        plan_id=f"PLAN-{agent_name.upper()}-{token}-R{revision}",
        run_id=goal.run_id,
        goal_id=goal.goal_id,
        agent_name=agent_name,
        revision=revision,
        rationale=(
            "Use an auditable prepare-execute-reflect plan while delegating evidence "
            "processing to deterministic services."
        ),
        steps=list(steps),
        assumptions=[
            "Original evidence remains immutable.",
            "Committed upstream hashes identify the exact input snapshot.",
        ],
        dependencies=goal.dependencies,
        expected_outputs=[expected_output, "completion_decision.json"],
        status="approved",
    )
