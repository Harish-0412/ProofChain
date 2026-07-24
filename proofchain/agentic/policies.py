"""Governance policies for confidence and bounded autonomous decisions."""

from __future__ import annotations

from typing import Literal


ConfidenceAction = Literal[
    "continue",
    "continue_with_warning",
    "retry_or_ask_peer",
    "request_human",
    "block_positive_decision",
]


class ConfidencePolicy:
    """Separates confidence guidance from deterministic blocking rules."""

    @staticmethod
    def action_for(confidence: float, *, deterministic_blocker: bool = False) -> ConfidenceAction:
        if deterministic_blocker:
            return "block_positive_decision"
        if confidence >= 0.90:
            return "continue"
        if confidence >= 0.75:
            return "continue_with_warning"
        if confidence >= 0.50:
            return "retry_or_ask_peer"
        if confidence >= 0.30:
            return "request_human"
        return "block_positive_decision"
