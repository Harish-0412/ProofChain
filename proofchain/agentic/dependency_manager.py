"""Dependency scheduling and deadlock detection for supervisor goals."""

from __future__ import annotations

from dataclasses import dataclass

from proofchain.schemas.agentic import CoordinationState, Goal


@dataclass(frozen=True)
class DeadlockReport:
    detected: bool
    circular_goal_ids: list[str]
    explanation: str


class DependencyManager:
    successful_statuses = {"completed"}
    terminal_statuses = {
        "completed",
        "blocked",
        "needs_human_review",
        "failed",
        "cancelled",
    }

    def runnable(self, goals: list[Goal]) -> list[Goal]:
        successful = {
            goal.goal_id for goal in goals if goal.status in self.successful_statuses
        }
        return [
            goal
            for goal in goals
            if goal.status == "created"
            and set(goal.dependencies).issubset(successful)
        ]

    def blocked_by_terminal_dependencies(self, goals: list[Goal]) -> list[Goal]:
        by_id = {goal.goal_id: goal for goal in goals}
        failed_dependencies = {
            "blocked",
            "needs_human_review",
            "failed",
            "cancelled",
        }
        return [
            goal
            for goal in goals
            if goal.status == "created"
            and any(
                by_id.get(dependency)
                and by_id[dependency].status in failed_dependencies
                for dependency in goal.dependencies
            )
        ]

    def detect_deadlock(
        self, goals: list[Goal], state: CoordinationState
    ) -> DeadlockReport:
        pending = {
            goal.goal_id: goal
            for goal in goals
            if goal.status not in self.terminal_statuses
        }
        if not pending or state.active_goals:
            return DeadlockReport(False, [], "Runnable or active work still exists.")

        visiting: set[str] = set()
        visited: set[str] = set()
        cycle: list[str] = []

        def visit(goal_id: str, path: list[str]) -> bool:
            if goal_id in visiting:
                start = path.index(goal_id)
                cycle.extend(path[start:])
                return True
            if goal_id in visited or goal_id not in pending:
                return False
            visiting.add(goal_id)
            for dependency in pending[goal_id].dependencies:
                if visit(dependency, [*path, dependency]):
                    return True
            visiting.remove(goal_id)
            visited.add(goal_id)
            return False

        for goal_id in pending:
            if visit(goal_id, [goal_id]):
                return DeadlockReport(
                    True,
                    list(dict.fromkeys(cycle)),
                    "Pending goals form a circular dependency with no active execution.",
                )
        return DeadlockReport(
            False,
            [],
            "Pending goals are waiting on a non-circular external dependency.",
        )
