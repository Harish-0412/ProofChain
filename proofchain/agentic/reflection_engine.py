"""Translate runtime reflection into the shared precision contract."""

from __future__ import annotations

from proofchain.schemas.agentic import Goal, ReflectionDecision
from proofchain.schemas.cognition import NormalizedToolObservation, StructuredReflection


class StructuredReflectionEngine:
    _DECISIONS = {
        "request_peer": "ask_peer",
        "request_human": "ask_human",
    }

    def reflect(
        self,
        goal: Goal,
        reflection: ReflectionDecision,
        observation: NormalizedToolObservation,
    ) -> StructuredReflection:
        decision = self._DECISIONS.get(reflection.decision, reflection.decision)
        condition_met = (
            goal.success_conditions
            if reflection.decision == "complete" and observation.sufficient_for_step
            else []
        )
        return StructuredReflection(
            reflection_id=reflection.reflection_id,
            run_id=reflection.run_id,
            goal_id=reflection.goal_id,
            agent_name=reflection.agent_name,
            plan_revision=reflection.plan_revision,
            new_facts=[observation.summary],
            hypotheses_supported=[]
            if not observation.sufficient_for_step
            else ["available_inputs_are_sufficient"],
            hypotheses_rejected=[]
            if observation.sufficient_for_step
            else ["available_inputs_are_sufficient"],
            success_conditions_met=condition_met,
            success_conditions_remaining=[
                item for item in goal.success_conditions if item not in condition_met
            ],
            blockers=[
                *observation.contradictions,
                *observation.missing_information,
            ],
            decision=decision,
            reason_summary=reflection.reason,
            confidence=reflection.confidence,
        )
