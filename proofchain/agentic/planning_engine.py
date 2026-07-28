"""Convert executable plans into richer risk-aware planning records."""

from __future__ import annotations

from proofchain.schemas.advanced_plans import AdvancedAgentPlan, AdvancedPlanStep
from proofchain.schemas.agentic import AgentPlan, Goal


class AdvancedPlanningEngine:
    def enrich(
        self,
        goal: Goal,
        plan: AgentPlan,
        *,
        validated_case_ids: list[str] | None = None,
    ) -> AdvancedAgentPlan:
        last_step = plan.steps[-1].step_id if plan.steps else None
        coverage = {
            condition: [last_step] if last_step else []
            for condition in goal.success_conditions
        }
        return AdvancedAgentPlan(
            plan_id=plan.plan_id,
            run_id=plan.run_id,
            goal_id=plan.goal_id,
            agent_name=plan.agent_name,
            revision=plan.revision,
            rationale=plan.rationale,
            assumptions=[
                *plan.assumptions,
                *(
                    [
                        "Validated experience may inform ordering but cannot override "
                        f"current evidence or policy: {', '.join(validated_case_ids)}"
                    ]
                    if validated_case_ids
                    else []
                ),
            ],
            dependencies=plan.dependencies,
            success_condition_coverage=coverage,
            steps=[
                AdvancedPlanStep(
                    step_id=step.step_id,
                    sequence=step.sequence,
                    objective=step.objective,
                    preferred_tool=step.proposed_tool,
                    fallback_tools=[],
                    required_inputs=step.required_inputs,
                    expected_observations=[step.expected_observation],
                    success_condition=step.completion_condition,
                    failure_condition=f"{step.completion_condition} is not demonstrated.",
                    risk_level="medium" if step.proposed_tool else "low",
                    reversible=True,
                    on_success="continue",
                    on_failure="retry_or_replan",
                    on_uncertainty="retrieve_context_or_request_review",
                    expected_information_gain=0.9
                    if step.proposed_tool
                    else 0.5,
                    status=step.status,
                )
                for step in plan.steps
            ],
            expected_outputs=plan.expected_outputs,
            status="draft",
        )
