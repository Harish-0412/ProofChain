"""Shared mechanics for independent production and institutional goal agents."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.repositories.production_artifact_repository import (
    ProductionArtifactRepository,
)
from proofchain.schemas.agentic import AgentPlan, CompletionDecision, PlanStep
from proofchain.schemas.production import ProductionAgentResult


InputT = TypeVar("InputT")
ResultT = TypeVar("ResultT", bound=ProductionAgentResult)


class ProductionGoalAgent(BaseGoalAgent[InputT, ResultT], Generic[InputT, ResultT]):
    """Base for operational agents; policy decisions remain in concrete agents."""

    tool_specs: tuple[tuple[str, str, str], ...] = ()
    expected_artifact = "production_agent_result.json"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or ProductionArtifactRepository()
        self._state: dict[str, Any] = {}

    def validate_input(self, input_data: InputT) -> None:
        if not getattr(input_data, "workflow", None):
            raise ValueError("A workflow context is required.")

    def validate_output(self, output_data: ResultT) -> None:
        if output_data.run_id == "":
            raise ValueError("A production agent result must reference a run.")

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        return AgentPlan(
            plan_id=f"PLAN-{self.agent_name.upper()}-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale=(
                "Observe operational state, execute only allowlisted deterministic "
                "tools, and evaluate governed completion conditions."
            ),
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=observation,
                    completion_condition=observation,
                )
                for index, (tool, objective, observation) in enumerate(self.tool_specs, 1)
            ],
            assumptions=["External side effects require configured adapters and policy gates."],
            dependencies=goal.dependencies,
            expected_outputs=[self.expected_artifact],
            status="approved",
        )

    def _persist(self, result: ResultT) -> ResultT:
        path, digest = self.repository.save(
            result.run_id, self.expected_artifact, result
        )
        result.output_reference = str(path.resolve())
        result.output_snapshot_hash = digest
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        available = output is not None and isinstance(output, ProductionAgentResult)
        failures = output.failure_count if available else 1
        complete = available and output.status != "failed" and failures == 0
        warnings = output.warning_count if available else 0
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=complete,
            success_conditions_met=goal.success_conditions if complete else [],
            success_conditions_unmet=[] if complete else goal.success_conditions,
            blockers=list(output.errors) if available else ["No result was produced."],
            confidence=0.95 if complete else 0.0,
            final_status=(
                "completed_with_warnings"
                if complete and warnings
                else "completed"
                if complete
                else "blocked"
            ),
            explanation=(
                f"{self.agent_name} completed its bounded plan with "
                f"{failures} failures and {warnings} warnings."
            ),
            supporting_artifacts=[
                output.output_reference
                for output in [output]
                if available and output.output_reference
            ],
        )
