"""Auditable supervisor scheduling decisions over the persisted goal graph."""

from __future__ import annotations

from collections import Counter

from proofchain.agentic.dependency_manager import DependencyManager
from proofchain.schemas.agentic import CoordinationState, Goal
from proofchain.schemas.runtime_governance import SupervisorRoundRecord


class GoalScheduler:
    def __init__(self, dependency_manager: DependencyManager | None = None):
        self.dependencies = dependency_manager or DependencyManager()

    def evaluate(
        self,
        *,
        run_id: str,
        goals: list[Goal],
        state: CoordinationState,
        round_number: int,
        phase: str,
        maximum_rounds: int,
        messages_processed: int = 0,
    ) -> SupervisorRoundRecord:
        runnable = self.dependencies.runnable(goals)
        blocked_by_dependency = self.dependencies.blocked_by_terminal_dependencies(goals)
        deadlock = self.dependencies.detect_deadlock(goals, state)
        terminal = self.dependencies.terminal_statuses
        waiting = [
            goal
            for goal in goals
            if goal.status not in terminal
            and goal.goal_id not in state.active_goals
            and goal not in runnable
        ]
        budget_exhausted = (
            round_number >= maximum_rounds
            and bool(state.open_messages or waiting or state.active_goals)
        )
        if deadlock.detected:
            decision = "block_circular_dependency"
        elif blocked_by_dependency:
            decision = "hold_for_failed_dependency"
        elif budget_exhausted:
            decision = "block_round_budget_exhausted"
        elif state.open_messages:
            decision = "process_coordination_messages"
        elif runnable:
            decision = "activate_runnable_goals"
        elif waiting:
            decision = "wait_for_external_or_upstream_state"
        else:
            decision = "terminal_or_no_pending_work"
        return SupervisorRoundRecord(
            run_id=run_id,
            round_number=round_number,
            phase=phase,
            goal_status_counts=dict(Counter(goal.status for goal in goals)),
            runnable_goal_ids=[goal.goal_id for goal in runnable],
            waiting_goal_ids=[goal.goal_id for goal in waiting],
            blocked_dependency_goal_ids=[
                goal.goal_id for goal in blocked_by_dependency
            ],
            open_message_ids=list(state.open_messages),
            messages_processed=messages_processed,
            decision=decision,
            deadlock_detected=deadlock.detected,
            circular_goal_ids=deadlock.circular_goal_ids,
            budget_exhausted=budget_exhausted,
        )
