"""End-to-end test for canonical cognition artifacts and validation."""

from __future__ import annotations

import shutil
import uuid

from pydantic import BaseModel

from proofchain.agentic.agentic_run_validator import AgenticRunValidator
from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.core.paths import get_run_dir
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.schemas.agentic import CompletionDecision, Goal, Observation
from proofchain.schemas.workflow import WorkflowContext


class CognitionInput(BaseModel):
    workflow: WorkflowContext


class CognitionOutput(BaseModel):
    status: str = "completed"
    success_count: int = 1
    warning_count: int = 0
    failure_count: int = 0
    output_reference: str = "memory://cognition-output"
    output_snapshot_hash: str = "cognition-hash"


class AdvancedCollectorFixture(
    BaseGoalAgent[CognitionInput, CognitionOutput]
):
    agent_name = "evidence_collector"
    agentic_tool_name = "fixture_collection_tool"

    def validate_input(self, input_data: CognitionInput) -> None:
        if input_data.workflow.run_id == "INVALID":
            raise ValueError("Invalid fixture input.")

    def execute(self, input_data: CognitionInput) -> CognitionOutput:
        return CognitionOutput()

    def validate_output(self, output_data: CognitionOutput) -> None:
        return None

    def evaluate_goal_completion(
        self,
        goal: Goal,
        output: CognitionOutput | None,
        observations: list[Observation],
    ) -> CompletionDecision:
        return CompletionDecision(
            decision_id="DEC-ADVANCED-FIXTURE",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=output is not None,
            success_conditions_met=goal.success_conditions if output else [],
            success_conditions_unmet=[] if output else goal.success_conditions,
            confidence=1.0 if output else 0.0,
            final_status="completed" if output else "failed",
            explanation="The fixture produced and validated its governed artifact.",
            supporting_artifacts=[output.output_reference] if output else [],
        )


def test_advanced_agent_emits_complete_cognition_and_valid_ledger():
    run_id = f"RUN-COG-{uuid.uuid4().hex[:10].upper()}"
    goal = Goal(
        goal_id=f"GOAL-{run_id}-COLLECT",
        run_id=run_id,
        assigned_agent="evidence_collector",
        objective="Collect all authorized evidence for C3.2.1 in 2025-2026.",
        goal_type="acquire_evidence",
        success_conditions=["Collection is complete and traceable."],
    )
    top = Goal(
        goal_id=f"GOAL-{run_id}-TOP",
        run_id=run_id,
        assigned_agent="supervisor",
        objective="Validate evidence.",
        goal_type="test",
    )
    coordination = JsonCoordinationRepository()
    coordination.initialize(top, [goal])
    workflow = WorkflowContext(
        run_id=run_id,
        correlation_id=str(uuid.uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )
    try:
        result = AdvancedCollectorFixture().run_goal(
            goal, CognitionInput(workflow=workflow), coordination
        )
        report = AgenticRunValidator().validate(run_id)
        root = get_run_dir(run_id) / "agents" / "evidence_collector" / goal.goal_id

        assert result.completion.final_status == "completed"
        assert report["valid"], report["errors"]
        assert report["agents_validated"] == 1
        assert (root / "completion_proof.json").exists()
        assert (root / "core_precision_assessment.json").exists()
        assert (get_run_dir(run_id) / "agent_decisions.jsonl").exists()
    finally:
        shutil.rmtree(get_run_dir(run_id), ignore_errors=True)


def test_invalid_advanced_input_stops_before_tool_execution():
    run_id = f"RUN-COG-{uuid.uuid4().hex[:10].upper()}"
    goal = Goal(
        goal_id=f"GOAL-{run_id}-COLLECT",
        run_id=run_id,
        assigned_agent="evidence_collector",
        objective="Collect evidence.",
        goal_type="acquire_evidence",
        success_conditions=["Collection is complete."],
    )
    top = goal.model_copy(
        update={
            "goal_id": f"GOAL-{run_id}-TOP",
            "assigned_agent": "supervisor",
        }
    )
    coordination = JsonCoordinationRepository()
    coordination.initialize(top, [goal])
    workflow = WorkflowContext(
        run_id="INVALID",
        correlation_id=str(uuid.uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )
    try:
        result = AdvancedCollectorFixture().run_goal(
            goal, CognitionInput(workflow=workflow), coordination
        )
        root = get_run_dir(run_id) / "agents" / "evidence_collector" / goal.goal_id

        assert result.output is None
        assert result.completion.final_status == "blocked"
        assert result.plan.steps == []
        assert not (root / "action_selections.jsonl").exists()
        assert (root / "input_validation.json").exists()
        assert (root / "completion_proof.json").exists()
    finally:
        shutil.rmtree(get_run_dir(run_id), ignore_errors=True)
