"""Bounded retry, replanning, tool permission, and trace behavior."""

from __future__ import annotations

import shutil
import uuid
from typing import ClassVar

from pydantic import BaseModel

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.core.paths import (
    get_agentic_agent_path,
    get_coordination_artifact_path,
    get_run_dir,
)
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.schemas.agentic import (
    AgentBudget,
    CompletionDecision,
    Goal,
    Observation,
)
from proofchain.schemas.workflow import WorkflowContext


class RuntimeInput(BaseModel):
    workflow: WorkflowContext


class RuntimeOutput(BaseModel):
    status: str = "completed"
    success_count: int = 1
    warning_count: int = 0
    failure_count: int = 0
    output_reference: str = "memory://test-output"
    output_snapshot_hash: str = "abc123"


class ReplanningAgent(BaseGoalAgent[RuntimeInput, RuntimeOutput]):
    agent_name = "replanning_test"
    agentic_tool_name = "unstable_test_tool"
    attempts: ClassVar[int] = 0

    def validate_input(self, input_data: RuntimeInput) -> None:
        return None

    def execute(self, input_data: RuntimeInput) -> RuntimeOutput:
        type(self).attempts += 1
        if type(self).attempts == 1:
            raise RuntimeError("planned recoverable failure")
        return RuntimeOutput()

    def validate_output(self, output_data: RuntimeOutput) -> None:
        return None

    def evaluate_goal_completion(
        self,
        goal: Goal,
        output: RuntimeOutput | None,
        observations: list[Observation],
    ) -> CompletionDecision:
        return CompletionDecision(
            decision_id="DEC-REPLAN",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=output is not None,
            success_conditions_met=goal.success_conditions if output else [],
            success_conditions_unmet=[] if output else goal.success_conditions,
            confidence=1.0 if output else 0.0,
            final_status="completed" if output else "failed",
            explanation="The replanned deterministic action produced a validated result.",
            supporting_artifacts=[output.output_reference] if output else [],
        )


def test_base_goal_agent_replans_after_retry_budget_and_replays_trace():
    run_id = f"RUN-REPLAN-{uuid.uuid4().hex[:10].upper()}"
    goal = Goal(
        goal_id=f"GOAL-{run_id}",
        run_id=run_id,
        assigned_agent=ReplanningAgent.agent_name,
        objective="Recover from one deterministic tool failure.",
        goal_type="runtime_test",
        success_conditions=["A validated result is produced after replanning."],
    )
    coordination = JsonCoordinationRepository()
    coordination.initialize(
        Goal(
            goal_id=f"GOAL-{run_id}-TOP",
            run_id=run_id,
            assigned_agent="supervisor",
            objective="Test runtime.",
            goal_type="test",
        ),
        [goal],
    )
    workflow = WorkflowContext(
        run_id=run_id,
        correlation_id=str(uuid.uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )
    ReplanningAgent.attempts = 0
    try:
        result = ReplanningAgent().run_goal(
            goal,
            RuntimeInput(workflow=workflow),
            coordination,
            AgentBudget(
                max_plan_revisions=2,
                max_action_rounds=8,
                max_tool_retries_per_step=0,
            ),
        )
        assert result.completion.final_status == "completed"
        assert result.plan.revision == 2
        assert ReplanningAgent.attempts == 2
        assert any(
            observation.observation_type == "tool_failure"
            for observation in result.observations
        )
        assert get_agentic_agent_path(
            run_id, ReplanningAgent.agent_name, "plans.json"
        ).exists()
        assert get_coordination_artifact_path(run_id, "tool_calls.jsonl").exists()
    finally:
        shutil.rmtree(get_run_dir(run_id), ignore_errors=True)
