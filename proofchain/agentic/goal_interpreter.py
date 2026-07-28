"""Deterministic, auditable goal interpretation."""

from __future__ import annotations

import re

from proofchain.schemas.agentic import Goal
from proofchain.schemas.interpreted_goal import InterpretedGoal


class GoalInterpreter:
    def interpret(self, goal: Goal, *, policy_version_known: bool) -> InterpretedGoal:
        ambiguity: list[str] = []
        if not goal.objective.strip():
            ambiguity.append("objective_missing")
        if not goal.success_conditions:
            ambiguity.append("success_conditions_missing")
        if not goal.goal_type.strip():
            ambiguity.append("goal_type_missing")

        entities = re.findall(
            r"\b(?:C\d+(?:\.\d+)+|RUN-[A-Z0-9-]+|\d{4}-\d{4})\b",
            goal.objective,
        )
        prohibited = [
            item
            for item in goal.constraints
            if any(token in item.lower() for token in ("do not", "must not", "prohibit"))
        ]
        scope_complete = bool(goal.objective.strip() and goal.success_conditions)
        if not policy_version_known:
            ambiguity.append("policy_version_unknown")
        confidence = max(0.0, 1.0 - (0.2 * len(ambiguity)))
        return InterpretedGoal(
            goal_id=goal.goal_id,
            run_id=goal.run_id,
            normalized_objective=" ".join(goal.objective.split()),
            subject_entities=list(dict.fromkeys([*entities, *goal.input_references])),
            required_inputs=list(goal.input_references),
            constraints=list(goal.constraints),
            prohibited_actions=prohibited,
            success_conditions=list(goal.success_conditions),
            failure_conditions=list(goal.failure_conditions),
            ambiguity_flags=ambiguity,
            clarification_required=not scope_complete or not policy_version_known,
            interpretation_confidence=confidence,
            policy_version_known=policy_version_known,
            scope_complete=scope_complete,
        )
