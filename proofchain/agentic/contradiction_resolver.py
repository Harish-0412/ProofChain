"""Bounded contradiction classification and escalation."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.cognition import NormalizedToolObservation
from proofchain.schemas.contradiction_resolution import ContradictionResolution


class ContradictionResolver:
    def evaluate(
        self, observations: list[NormalizedToolObservation]
    ) -> ContradictionResolution | None:
        conflicting = [
            item
            for item in observations
            if item.contradictions
        ]
        if not conflicting:
            return None
        latest = conflicting[-1]
        source_rank = sorted(
            {
                reference
                for item in conflicting
                for reference in item.source_references
            }
        )
        return ContradictionResolution(
            contradiction_id=f"CON-{uuid4().hex[:12].upper()}",
            run_id=latest.run_id,
            goal_id=latest.goal_id,
            conflicting_observation_ids=[
                item.observation_id for item in conflicting
            ],
            likely_explanation=None,
            resolution_status="escalated",
            confidence=0.5,
            authority_ranking=source_rank,
            required_followup=[
                "Compare source version, time, scope, and authority.",
                "Run targeted deterministic validation.",
            ],
            human_review_required=True,
        )
