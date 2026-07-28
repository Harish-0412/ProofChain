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

    def global_order(
        self, goals: list[Goal]
    ) -> tuple[list[Goal], list[str], dict[str, float]]:
        """Order goals by priority, dependency depth, and least-served agent."""
        by_id = {goal.goal_id: goal for goal in goals}
        depth_cache: dict[str, int] = {}

        def depth(goal_id: str, visiting: set[str] | None = None) -> int:
            if goal_id in depth_cache:
                return depth_cache[goal_id]
            visiting = set(visiting or set())
            if goal_id in visiting:
                return 0
            visiting.add(goal_id)
            goal = by_id[goal_id]
            value = (
                0
                if not goal.dependencies
                else 1
                + max(
                    (
                        depth(item, visiting)
                        for item in goal.dependencies
                        if item in by_id
                    ),
                    default=0,
                )
            )
            depth_cache[goal_id] = value
            return value

        priority_weight = {
            "critical": 100.0,
            "high": 75.0,
            "medium": 50.0,
            "low": 25.0,
        }
        served: Counter = Counter()
        remaining = list(goals)
        ordered: list[Goal] = []
        scores: dict[str, float] = {}
        while remaining:
            for goal in remaining:
                scores[goal.goal_id] = (
                    priority_weight[goal.priority]
                    + 10.0 * depth(goal.goal_id)
                    - 2.0 * served[goal.assigned_agent]
                )
            selected = max(
                remaining,
                key=lambda goal: (
                    scores[goal.goal_id],
                    -served[goal.assigned_agent],
                    goal.created_at.timestamp(),
                ),
            )
            ordered.append(selected)
            served[selected.assigned_agent] += 1
            remaining.remove(selected)

        terminal_candidates = [
            goal for goal in goals if not any(
                goal.goal_id in item.dependencies for item in goals
            )
        ]
        terminal = max(
            terminal_candidates or goals,
            key=lambda goal: depth(goal.goal_id),
            default=None,
        )
        critical_path = []
        current = terminal
        while current:
            critical_path.append(current.goal_id)
            dependencies = [
                by_id[item]
                for item in current.dependencies
                if item in by_id
            ]
            current = (
                max(dependencies, key=lambda goal: depth(goal.goal_id))
                if dependencies
                else None
            )
        critical_path.reverse()
        return ordered, critical_path, scores

    @staticmethod
    def fair_multi_run_order(
        run_queues: dict[str, list[str]]
    ) -> list[tuple[str, str]]:
        """Round-robin runnable work so one run cannot starve another."""
        queues = {run_id: list(items) for run_id, items in run_queues.items()}
        ordered: list[tuple[str, str]] = []
        while any(queues.values()):
            for run_id in sorted(queues):
                if queues[run_id]:
                    ordered.append((run_id, queues[run_id].pop(0)))
        return ordered
