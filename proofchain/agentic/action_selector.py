"""Information-gain-aware action proposal construction."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.advanced_plans import AdvancedPlanStep
from proofchain.schemas.agentic import ActionProposal, Goal


class InformationGainActionSelector:
    def select(
        self,
        goal: Goal,
        agent_name: str,
        step: AdvancedPlanStep,
        *,
        available_tools: set[str],
    ) -> ActionProposal:
        candidates = [
            tool
            for tool in [step.preferred_tool, *step.fallback_tools]
            if tool and tool in available_tools
        ]
        if not candidates:
            raise PermissionError(f"No authorized tool is available for {step.step_id}.")
        selected = candidates[0]
        return ActionProposal(
            action_id=f"ACT-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=agent_name,
            action_type="execute_tool",
            selected_tool=selected,
            step_id=step.step_id,
            alternatives=candidates[1:],
            reason=(
                f"Selected {selected} for plan order, policy eligibility, and "
                f"expected information gain {step.expected_information_gain:.2f}."
            ),
            expected_effect="; ".join(step.expected_observations),
            expected_information_gain=step.expected_information_gain,
            risk_level="high"
            if step.risk_level in {"high", "critical"}
            else step.risk_level,
            reversible=step.reversible,
            requires_approval=step.requires_approval,
        )
