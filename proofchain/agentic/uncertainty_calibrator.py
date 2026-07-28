"""Decompose confidence and apply deterministic uncertainty policy."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.cognition import NormalizedToolObservation
from proofchain.schemas.input_validation import InputValidationResult
from proofchain.schemas.interpreted_goal import InterpretedGoal
from proofchain.schemas.uncertainty import UncertaintyAssessment


class UncertaintyCalibrator:
    def assess(
        self,
        interpreted: InterpretedGoal,
        inputs: InputValidationResult,
        observation: NormalizedToolObservation | None = None,
        *,
        agent_name: str = "",
        completion_confidence: float = 0.0,
    ) -> UncertaintyAssessment:
        input_confidence = (
            1.0
            if inputs.valid and inputs.complete and inputs.authorized and inputs.current
            else 0.0
        )
        tool_confidence = observation.confidence if observation else 1.0
        decision_confidence = min(
            input_confidence,
            tool_confidence,
            interpreted.interpretation_confidence,
        )
        values = [
            input_confidence,
            tool_confidence,
            interpreted.interpretation_confidence,
            decision_confidence,
            completion_confidence,
        ]
        aggregate = sum(values) / len(values)
        deterministic_block = not inputs.valid or (
            observation is not None and observation.data_quality == "invalid"
        )
        recommended = (
            "prohibit_positive_decision"
            if deterministic_block or aggregate < 0.30
            else "request_human"
            if aggregate < 0.50
            else "retrieve_or_ask_peer"
            if aggregate < 0.75
            else "continue_with_warning"
            if aggregate < 0.90
            else "continue"
        )
        uncertainty_types = []
        if input_confidence < 1.0:
            uncertainty_types.append("input")
        if tool_confidence < 0.9:
            uncertainty_types.append("extraction")
        if interpreted.interpretation_confidence < 0.9:
            uncertainty_types.append("policy")
        if completion_confidence < 0.9:
            uncertainty_types.append("completion")
        return UncertaintyAssessment(
            assessment_id=f"UNC-{uuid4().hex[:12].upper()}",
            run_id=interpreted.run_id,
            goal_id=interpreted.goal_id,
            agent_name=observation.agent_name if observation else agent_name,
            plan_step_id=observation.plan_step_id if observation else None,
            input_confidence=input_confidence,
            tool_confidence=tool_confidence,
            interpretation_confidence=interpreted.interpretation_confidence,
            decision_confidence=decision_confidence,
            completion_confidence=completion_confidence,
            uncertainty_types=uncertainty_types,
            reasons=[
                *inputs.missing_inputs,
                *(observation.missing_information if observation else []),
                *(observation.contradictions if observation else []),
            ],
            recommended_action=recommended,
            deterministic_block=deterministic_block,
        )
