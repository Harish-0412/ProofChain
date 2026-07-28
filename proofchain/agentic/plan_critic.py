"""Independent deterministic criticism of advanced plans."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.advanced_plans import AdvancedAgentPlan
from proofchain.schemas.agentic import Goal
from proofchain.schemas.plan_critiques import PlanCritique


class PlanCritic:
    def critique(
        self,
        goal: Goal,
        plan: AdvancedAgentPlan,
        *,
        allowed_tools: set[str],
    ) -> PlanCritique:
        missing: list[str] = []
        unsafe: list[str] = []
        conflicts: list[str] = []
        warnings: list[str] = []
        revisions: list[str] = []

        for condition in goal.success_conditions:
            if not plan.success_condition_coverage.get(condition):
                missing.append(condition)
        for step in plan.steps:
            if step.preferred_tool and step.preferred_tool not in allowed_tools:
                unsafe.append(
                    f"{step.step_id} uses unauthorized tool {step.preferred_tool}."
                )
            if not step.success_condition.strip() or not step.failure_condition.strip():
                missing.append(f"{step.step_id} lacks a measurable outcome.")
            if step.preferred_tool and not step.fallback_tools:
                warnings.append(f"{step.step_id} has no alternate tool; bounded retry applies.")
            if step.requires_approval and step.on_success == "continue":
                conflicts.append(f"{step.step_id} may bypass its approval boundary.")
        revisions.extend(f"Cover success condition: {item}" for item in missing)
        revisions.extend(unsafe)
        revisions.extend(conflicts)
        approved = not (missing or unsafe or conflicts)
        return PlanCritique(
            critique_id=f"CRT-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            plan_id=plan.plan_id,
            plan_revision=plan.revision,
            approved=approved,
            missing_steps=missing,
            unsafe_steps=unsafe,
            policy_conflicts=conflicts,
            efficiency_warnings=warnings,
            required_revisions=revisions,
            critique_confidence=1.0,
        )
