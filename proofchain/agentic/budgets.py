"""Mutable accounting for an immutable AgentBudget policy."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from proofchain.schemas.agentic import AgentBudget


@dataclass
class BudgetTracker:
    policy: AgentBudget
    started_at: float = field(default_factory=time.perf_counter)
    action_rounds: int = 0
    plan_revisions: int = 0
    peer_requests: int = 0
    retries_by_step: dict[str, int] = field(default_factory=dict)

    def consume_action(self) -> bool:
        self.action_rounds += 1
        return self.action_rounds <= self.policy.max_action_rounds

    def consume_retry(self, step_id: str) -> bool:
        self.retries_by_step[step_id] = self.retries_by_step.get(step_id, 0) + 1
        return self.retries_by_step[step_id] <= self.policy.max_tool_retries_per_step

    def consume_replan(self) -> bool:
        self.plan_revisions += 1
        return self.plan_revisions < self.policy.max_plan_revisions

    @property
    def runtime_exhausted(self) -> bool:
        return time.perf_counter() - self.started_at > self.policy.max_runtime_seconds
