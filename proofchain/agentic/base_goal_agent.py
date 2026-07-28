"""Reusable bounded observe-plan-act-reflect loop for ProofChain agents."""

from __future__ import annotations

import time
from abc import abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import uuid4

from proofchain.agents.base import BaseAgent
from proofchain.agentic.advanced_cognition_runtime import AdvancedCognitionRuntime
from proofchain.agentic.cognition_profiles import cognition_profile_for
from proofchain.agentic.planner import make_plan
from proofchain.agentic.memory import AgentMemory
from proofchain.agentic.tool_router import ToolRouter
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.core.ids import generate_agent_run_id
from proofchain.schemas.agentic import (
    ActionProposal,
    AgentBudget,
    AgentPlan,
    CompletionDecision,
    CoordinationMessage,
    DecisionRationale,
    Goal,
    Observation,
    ReflectionDecision,
)

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


@dataclass
class GoalRunResult(Generic[OutputType]):
    output: OutputType | None
    plan: AgentPlan
    completion: CompletionDecision
    observations: list[Observation]
    reflections: list[ReflectionDecision]


class BaseGoalAgent(
    BaseAgent[InputType, OutputType],
    Generic[InputType, OutputType],
):
    """Adds governed autonomy while preserving BaseAgent's deterministic lifecycle."""

    agentic_tool_name = "execute_deterministic_stage"
    preparation_objective = "Inspect goal scope, dependencies, and constraints."
    execution_objective = "Execute the approved deterministic evidence tools."
    review_objective = "Evaluate results, uncertainty, blockers, and completion policy."
    expected_tool_output = "A validated, persisted stage artifact."

    def run_goal(
        self,
        goal: Goal,
        input_data: InputType,
        coordination: JsonCoordinationRepository,
        budget: AgentBudget | None = None,
    ) -> GoalRunResult[OutputType]:
        budget = budget or AgentBudget()
        started = time.perf_counter()
        observations: list[Observation] = []
        reflections: list[ReflectionDecision] = []
        retries: dict[str, int] = {}
        action_rounds = 0
        output: OutputType | None = None
        cognition: AdvancedCognitionRuntime | None = None
        tools = self.agentic_tools(input_data)

        profile = cognition_profile_for(self.agent_name)
        if profile.profile_name == "advanced-cognition-platform":
            cognition = AdvancedCognitionRuntime(goal, coordination)
            validation_error: Exception | None = None
            try:
                self.validate_input(input_data)
            except Exception as exc:
                validation_error = exc
            input_validation = cognition.initialize(
                input_data,
                deterministic_error=validation_error,
            )
            if not input_validation.valid:
                plan = AgentPlan(
                    plan_id=f"PLAN-{uuid4().hex[:12].upper()}",
                    run_id=goal.run_id,
                    goal_id=goal.goal_id,
                    agent_name=self.agent_name,
                    revision=1,
                    rationale="Execution was prohibited by the pre-plan input gate.",
                    steps=[],
                    status="abandoned",
                )
                completion = self._input_gate_completion(
                    goal,
                    input_validation.missing_inputs,
                    validation_error,
                )
                completion = cognition.finalize(
                    plan,
                    output,
                    completion,
                    output_schema_valid=False,
                )
                return self._finish(
                    goal,
                    plan,
                    completion,
                    output,
                    observations,
                    reflections,
                    coordination,
                )
        else:
            self.validate_input(input_data)
        self._agent_run_id = generate_agent_run_id(self.agent_name, goal.run_id)
        goal.status = "planning"
        coordination.save_goal(goal)
        plan = self.create_goal_plan(goal, input_data, revision=1)
        coordination.save_plan(plan)
        router = ToolRouter(coordination)
        memory = AgentMemory(coordination)
        for tool_name, function in tools.items():
            router.register(
                name=tool_name,
                agent_name=self.agent_name,
                function=function,
                version=self.agent_version,
            )
        if cognition:
            _, critique = cognition.record_plan(
                plan, allowed_tools=set(tools)
            )
            while (
                not critique.approved
                and plan.revision < budget.max_plan_revisions
            ):
                plan.status = "abandoned"
                coordination.save_plan(plan)
                plan = self.create_goal_plan(
                    goal, input_data, revision=plan.revision + 1
                )
                coordination.save_plan(plan)
                _, critique = cognition.record_plan(
                    plan, allowed_tools=set(tools)
                )
            if not critique.approved:
                completion = CompletionDecision(
                    decision_id=f"DEC-{uuid4().hex[:12].upper()}",
                    run_id=goal.run_id,
                    goal_id=goal.goal_id,
                    agent_name=self.agent_name,
                    goal_satisfied=False,
                    success_conditions_unmet=goal.success_conditions,
                    blockers=[
                        "The plan critic rejected every bounded plan revision.",
                        *critique.required_revisions,
                    ],
                    confidence=0.0,
                    final_status="needs_human_review",
                    explanation=(
                        "Execution was prohibited because the plan did not pass "
                        "coverage, permission, risk, and policy criticism."
                    ),
                )
                completion = cognition.finalize(
                    plan,
                    output,
                    completion,
                    output_schema_valid=False,
                )
                return self._finish(
                    goal,
                    plan,
                    completion,
                    output,
                    observations,
                    reflections,
                    coordination,
                )
        goal.status = "executing"
        plan.status = "executing"
        coordination.save_goal(goal)

        while action_rounds < budget.max_action_rounds:
            if time.perf_counter() - started > budget.max_runtime_seconds:
                completion = self._budget_completion(
                    goal, plan, observations, "Maximum runtime was exhausted."
                )
                if cognition:
                    completion = cognition.finalize(
                        plan,
                        output,
                        completion,
                        output_schema_valid=output is not None,
                    )
                return self._finish(
                    goal, plan, completion, output, observations, reflections, coordination
                )
            step = next(
                (item for item in plan.steps if item.status in {"pending", "failed"}),
                None,
            )
            if step is None:
                break
            action_rounds += 1
            step.status = "running"

            if step.proposed_tool is None:
                if cognition:
                    cognition.record_control_action(step.step_id, step.objective)
                observation = self.observe_control_step(goal, plan, step, output)
            else:
                action = (
                    cognition.select_action(
                        step.step_id, allowed_tools=set(tools)
                    )
                    if cognition
                    else ActionProposal(
                        action_id=f"ACT-{uuid4().hex[:12].upper()}",
                        run_id=goal.run_id,
                        goal_id=goal.goal_id,
                        agent_name=self.agent_name,
                        action_type="execute_tool",
                        selected_tool=step.proposed_tool,
                        reason=step.objective,
                        expected_effect=step.expected_observation,
                        risk_level="low",
                    )
                )
                coordination.append_action(action)
                try:
                    execution = router.execute(action)
                    output = execution.output
                    observation = self.observe_tool_result(
                        goal, step.step_id, output, execution.audit.status
                    )
                except Exception as exc:
                    observation = Observation(
                        observation_id=f"OBS-{uuid4().hex[:12].upper()}",
                        run_id=goal.run_id,
                        goal_id=goal.goal_id,
                        agent_name=self.agent_name,
                        plan_step_id=step.step_id,
                        observation_type="tool_failure",
                        summary=f"Deterministic tool failed: {exc}",
                        confidence=1.0,
                        uncertainty_reasons=["No valid tool result was produced."],
                    )

            observations.append(observation)
            coordination.append_observation(observation)
            normalized = (
                cognition.record_observation(
                    observation,
                    source_tool=step.proposed_tool
                    or "internal_control_assessment",
                    source_version=self.agent_version,
                )
                if cognition
                else None
            )
            reflection = self.reflect(goal, plan, step.step_id, observation, output)
            reflections.append(reflection)
            coordination.append_reflection(reflection)
            if cognition and normalized:
                cognition.record_reflection(reflection, normalized)
            memory.record_rationale(
                DecisionRationale(
                    run_id=goal.run_id,
                    goal_id=goal.goal_id,
                    agent_name=self.agent_name,
                    decision=reflection.decision,
                    evidence_considered=observation.source_references,
                    rules_applied=["AGENT-BUDGET-001", "COMPLETION-POLICY-001"],
                    alternatives_considered=[
                        "continue",
                        "retry",
                        "replan",
                        "request peer or human review",
                    ],
                    uncertainty=observation.uncertainty_reasons,
                    justification=reflection.reason,
                )
            )
            memory.checkpoint(
                goal=goal,
                plan=plan,
                recent_observations=observations,
                extra={"action_rounds": action_rounds},
            )

            if reflection.decision in {"continue", "complete", "request_peer"}:
                step.status = "completed"
            elif reflection.decision == "retry":
                step.status = "failed"
                retries[step.step_id] = retries.get(step.step_id, 0) + 1
                if retries[step.step_id] > budget.max_tool_retries_per_step:
                    reflection.decision = "replan"
            if reflection.decision == "replan":
                if plan.revision >= budget.max_plan_revisions:
                    completion = self._budget_completion(
                        goal, plan, observations, "Plan revision budget was exhausted."
                    )
                    if cognition:
                        completion = cognition.finalize(
                            plan,
                            output,
                            completion,
                            output_schema_valid=output is not None,
                        )
                    return self._finish(
                        goal,
                        plan,
                        completion,
                        output,
                        observations,
                        reflections,
                        coordination,
                    )
                plan.status = "abandoned"
                coordination.save_plan(plan)
                plan = self.create_goal_plan(
                    goal, input_data, revision=plan.revision + 1
                )
                plan.status = "replanning"
                coordination.save_plan(plan)
                if cognition:
                    _, critique = cognition.record_plan(
                        plan, allowed_tools=set(tools)
                    )
                    if not critique.approved:
                        completion = CompletionDecision(
                            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
                            run_id=goal.run_id,
                            goal_id=goal.goal_id,
                            agent_name=self.agent_name,
                            goal_satisfied=False,
                            success_conditions_unmet=goal.success_conditions,
                            blockers=critique.required_revisions,
                            confidence=0.0,
                            final_status="needs_human_review",
                            explanation="The replanned action sequence failed plan criticism.",
                        )
                        completion = cognition.finalize(
                            plan,
                            output,
                            completion,
                            output_schema_valid=output is not None,
                        )
                        return self._finish(
                            goal,
                            plan,
                            completion,
                            output,
                            observations,
                            reflections,
                            coordination,
                        )
                continue
            if reflection.decision == "request_human":
                completion = self._human_review_completion(goal, observations)
                if cognition:
                    completion = cognition.finalize(
                        plan,
                        output,
                        completion,
                        output_schema_valid=output is not None,
                    )
                return self._finish(
                    goal, plan, completion, output, observations, reflections, coordination
                )
            if reflection.decision == "block":
                break

        if any(step.status not in {"completed", "skipped"} for step in plan.steps):
            completion = self._budget_completion(
                goal, plan, observations, "Action round budget was exhausted."
            )
        else:
            peer_requests = self.create_peer_requests(goal, output)
            for message in peer_requests[: budget.max_peer_requests]:
                coordination.append_message(message)
            if cognition:
                cognition.record_peer_requests(
                    peer_requests[: budget.max_peer_requests]
                )
            completion = self.evaluate_goal_completion(goal, output, observations)
        if cognition:
            completion = cognition.finalize(
                plan,
                output,
                completion,
                output_schema_valid=output is not None,
            )
        return self._finish(
            goal, plan, completion, output, observations, reflections, coordination
        )

    def create_goal_plan(
        self, goal: Goal, input_data: InputType, revision: int
    ) -> AgentPlan:
        return make_plan(
            goal=goal,
            agent_name=self.agent_name,
            tool_name=self.agentic_tool_name,
            preparation_objective=self.preparation_objective,
            execution_objective=self.execution_objective,
            review_objective=self.review_objective,
            expected_output=self.expected_tool_output,
            revision=revision,
        )

    def agentic_tools(self, input_data: InputType) -> dict[str, object]:
        return {
            self.agentic_tool_name: lambda: super(BaseGoalAgent, self).run(input_data)
        }

    def observe_control_step(
        self,
        goal: Goal,
        plan: AgentPlan,
        step,
        output: OutputType | None,
    ) -> Observation:
        is_review = output is not None
        return Observation(
            observation_id=f"OBS-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            plan_step_id=step.step_id,
            observation_type="completion_assessment" if is_review else "goal_context",
            summary=(
                "Deterministic result is available for policy-based completion assessment."
                if is_review
                else f"Goal has {len(goal.success_conditions)} success conditions and "
                f"{len(goal.dependencies)} dependencies."
            ),
            structured_data={
                "success_conditions": goal.success_conditions,
                "dependencies": goal.dependencies,
                "result_status": getattr(output, "status", None),
            },
            confidence=1.0,
        )

    def observe_tool_result(
        self,
        goal: Goal,
        plan_step_id: str,
        output: OutputType,
        tool_status: str,
    ) -> Observation:
        status = getattr(output, "status", tool_status)
        failures = getattr(output, "failure_count", 0)
        warnings = getattr(output, "warning_count", 0)
        confidence = 1.0 if status == "completed" else 0.85
        if status == "failed":
            confidence = 0.0
        return Observation(
            observation_id=f"OBS-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            plan_step_id=plan_step_id,
            observation_type="deterministic_tool_result",
            summary=(
                f"Tool completed with status={status}, "
                f"warnings={warnings}, failures={failures}."
            ),
            structured_data={
                "status": status,
                "success_count": getattr(output, "success_count", 0),
                "warning_count": warnings,
                "failure_count": failures,
                "output_snapshot_hash": getattr(output, "output_snapshot_hash", None),
            },
            source_references=[
                item
                for item in [getattr(output, "output_reference", None)]
                if item
            ],
            confidence=confidence,
            uncertainty_reasons=list(getattr(output, "warnings", []))[:10],
        )

    def reflect(
        self,
        goal: Goal,
        plan: AgentPlan,
        plan_step_id: str,
        observation: Observation,
        output: OutputType | None,
    ) -> ReflectionDecision:
        result_status = getattr(output, "status", None)
        decision = "continue"
        reason = "The latest observation satisfies the current plan step."
        if observation.observation_type == "tool_failure" or result_status == "failed":
            decision = "retry"
            reason = "The deterministic action did not produce an eligible result."
        elif output is not None and plan_step_id == plan.steps[-1].step_id:
            decision = "complete"
            reason = "All planned actions ran and completion policy can now be evaluated."
        return ReflectionDecision(
            reflection_id=f"REF-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            plan_revision=plan.revision,
            observations_considered=[observation.observation_id],
            progress_assessment=observation.summary,
            confidence=observation.confidence,
            decision=decision,
            reason=reason,
            next_action="Select the next pending plan step"
            if decision == "continue"
            else None,
        )

    def create_peer_requests(
        self, goal: Goal, output: OutputType | None
    ) -> list[CoordinationMessage]:
        return []

    @abstractmethod
    def evaluate_goal_completion(
        self,
        goal: Goal,
        output: OutputType | None,
        observations: list[Observation],
    ) -> CompletionDecision:
        ...

    def _finish(
        self,
        goal: Goal,
        plan: AgentPlan,
        completion: CompletionDecision,
        output: OutputType | None,
        observations: list[Observation],
        reflections: list[ReflectionDecision],
        coordination: JsonCoordinationRepository,
    ) -> GoalRunResult[OutputType]:
        plan.status = "completed" if completion.final_status != "failed" else "abandoned"
        coordination.save_plan(plan)
        goal.status = {
            "completed": "completed",
            "completed_with_warnings": "completed",
            "needs_human_review": "needs_human_review",
            "blocked": "blocked",
            "failed": "failed",
        }[completion.final_status]
        coordination.save_goal(goal)
        coordination.save_completion(completion)
        return GoalRunResult(
            output=output,
            plan=plan,
            completion=completion,
            observations=observations,
            reflections=reflections,
        )

    def _budget_completion(
        self,
        goal: Goal,
        plan: AgentPlan,
        observations: list[Observation],
        reason: str,
    ) -> CompletionDecision:
        completed = [step.objective for step in plan.steps if step.status == "completed"]
        remaining = [
            step.objective for step in plan.steps if step.status != "completed"
        ]
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=False,
            success_conditions_unmet=goal.success_conditions,
            blockers=[reason],
            unresolved_questions=remaining,
            confidence=0.0,
            final_status="needs_human_review",
            explanation=(
                f"{reason} Completed work: {completed or ['none']}. "
                f"Remaining work: {remaining or ['none']}."
            ),
            supporting_artifacts=[
                reference
                for observation in observations
                for reference in observation.source_references
            ],
        )

    def _human_review_completion(
        self, goal: Goal, observations: list[Observation]
    ) -> CompletionDecision:
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=False,
            success_conditions_unmet=goal.success_conditions,
            blockers=["A governed human decision is required."],
            confidence=0.0,
            final_status="needs_human_review",
            explanation="The agent cannot safely complete this goal without human review.",
            supporting_artifacts=[
                reference
                for observation in observations
                for reference in observation.source_references
            ],
        )

    def _input_gate_completion(
        self,
        goal: Goal,
        missing_inputs: list[str],
        validation_error: Exception | None,
    ) -> CompletionDecision:
        blockers = list(missing_inputs)
        if validation_error:
            blockers.append(str(validation_error))
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=False,
            success_conditions_unmet=goal.success_conditions,
            blockers=blockers or ["The pre-plan input gate rejected the request."],
            confidence=0.0,
            final_status="blocked",
            explanation=(
                "The agent did not plan or execute tools because mandatory input "
                "validation failed."
            ),
        )
