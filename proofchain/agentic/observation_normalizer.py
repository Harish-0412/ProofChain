"""Normalize heterogeneous tool and control observations."""

from __future__ import annotations

from proofchain.schemas.agentic import Observation
from proofchain.schemas.cognition import NormalizedToolObservation


class ObservationNormalizer:
    def normalize(
        self, observation: Observation, *, source_tool: str, source_version: str
    ) -> NormalizedToolObservation:
        contradictions = [
            item
            for item in observation.uncertainty_reasons
            if "contradict" in item.lower() or "mismatch" in item.lower()
        ]
        missing = [
            item
            for item in observation.uncertainty_reasons
            if "missing" in item.lower() or "not " in item.lower()
        ]
        quality = (
            "invalid"
            if observation.observation_type == "tool_failure"
            else "high"
            if observation.confidence >= 0.9
            else "medium"
            if observation.confidence >= 0.75
            else "low"
        )
        return NormalizedToolObservation(
            observation_id=observation.observation_id,
            run_id=observation.run_id,
            goal_id=observation.goal_id,
            agent_name=observation.agent_name,
            plan_step_id=observation.plan_step_id,
            source_tool=source_tool,
            source_version=source_version,
            summary=observation.summary,
            structured_data=observation.structured_data,
            source_references=observation.source_references,
            data_quality=quality,
            confidence=observation.confidence,
            contradictions=contradictions,
            missing_information=missing,
            sufficient_for_step=quality != "invalid" and observation.confidence >= 0.75,
        )
