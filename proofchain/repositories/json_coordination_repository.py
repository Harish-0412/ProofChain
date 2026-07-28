"""Persistent, versioned blackboard for governed multi-agent coordination."""

from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from proofchain.core.paths import (
    get_agentic_agent_path,
    get_coordination_artifact_path,
    get_coordination_state_path,
    get_final_decision_path,
    get_goal_graph_path,
    get_top_level_goal_path,
)
from proofchain.repositories.json_store import AtomicJsonStore, jsonable
from proofchain.schemas.agentic import (
    ActionProposal,
    AgentPlan,
    CompletionDecision,
    CoordinationMessage,
    CoordinationPatch,
    CoordinationState,
    DecisionRationale,
    Goal,
    GoalGraph,
    Observation,
    ReflectionDecision,
    ToolResult,
)
from proofchain.schemas.peer_contracts import AgentRequest


class CoordinationVersionConflict(RuntimeError):
    """Raised when optimistic-lock state has changed since the caller read it."""


_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


def _path_lock(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.RLock())


class JsonCoordinationRepository:
    def __init__(self, store: AtomicJsonStore | None = None):
        self.store = store or AtomicJsonStore()

    def initialize(self, top_level_goal: Goal, subgoals: list[Goal]) -> CoordinationState:
        run_id = top_level_goal.run_id
        state = CoordinationState(
            run_id=run_id,
            top_level_goal_id=top_level_goal.goal_id,
            active_goals=[
                goal.goal_id for goal in subgoals if not goal.dependencies
            ],
        )
        self.store.write(get_top_level_goal_path(run_id), top_level_goal)
        self.store.write(
            get_goal_graph_path(run_id),
            GoalGraph(
                run_id=run_id,
                top_level_goal_id=top_level_goal.goal_id,
                goals=[top_level_goal, *subgoals],
            ),
        )
        self.store.write(get_coordination_artifact_path(run_id, "goals.json"), subgoals)
        self.store.write(get_coordination_artifact_path(run_id, "plans.json"), [])
        self.store.write(get_coordination_artifact_path(run_id, "blockers.json"), [])
        self.store.write(
            get_coordination_artifact_path(run_id, "completion_claims.json"), []
        )
        self.store.write(
            get_coordination_artifact_path(run_id, "resolution_tasks.json"), []
        )
        self.store.write(get_coordination_state_path(run_id), state)
        return state

    def load_state(self, run_id: str) -> CoordinationState:
        payload = self.store.read(get_coordination_state_path(run_id))
        if payload is None:
            raise FileNotFoundError(f"Coordination state not found for {run_id}.")
        return CoordinationState.model_validate(payload)

    def get_goals(self, run_id: str) -> list[Goal]:
        payload = self.store.read(
            get_coordination_artifact_path(run_id, "goals.json"),
            default=[],
        )
        return [Goal.model_validate(item) for item in payload]

    def update_state(
        self,
        run_id: str,
        expected_version: int,
        patch: CoordinationPatch,
    ) -> CoordinationState:
        path = get_coordination_state_path(run_id)
        with _path_lock(path):
            state = self.load_state(run_id)
            if state.state_version != expected_version:
                raise CoordinationVersionConflict(
                    f"Expected coordination version {expected_version}, "
                    f"found {state.state_version}."
                )
            self._apply_patch(state, patch)
            state.state_version += 1
            state.updated_at = datetime.now(tz=timezone.utc)
            self.store.write(path, state)
            return state

    def save_goal(self, goal: Goal) -> None:
        self.store.write(
            get_agentic_agent_path(goal.run_id, goal.assigned_agent, "goal.json"),
            goal,
        )
        goals_path = get_coordination_artifact_path(goal.run_id, "goals.json")
        goals = self.store.read(goals_path, default=[])
        existing = next(
            (index for index, item in enumerate(goals) if item["goal_id"] == goal.goal_id),
            None,
        )
        if existing is None:
            goals.append(jsonable(goal))
        else:
            goals[existing] = jsonable(goal)
        self.store.write(goals_path, goals)
        graph_path = get_goal_graph_path(goal.run_id)
        graph = self.store.read(graph_path, default={})
        graph_goals = graph.get("goals", [])
        graph_existing = next(
            (
                index
                for index, item in enumerate(graph_goals)
                if item["goal_id"] == goal.goal_id
            ),
            None,
        )
        if graph_existing is None:
            graph_goals.append(jsonable(goal))
        else:
            graph_goals[graph_existing] = jsonable(goal)
        graph["goals"] = graph_goals
        self.store.write(graph_path, graph)

    def save_plan(self, plan: AgentPlan) -> None:
        agent_path = get_agentic_agent_path(
            plan.run_id, plan.agent_name, "plans.json"
        )
        self._append_json_array(agent_path, plan)
        self._append_json_array(
            get_coordination_artifact_path(plan.run_id, "plans.json"), plan
        )
        self.patch_retrying(
            plan.run_id,
            CoordinationPatch(current_plans={plan.goal_id: plan.plan_id}),
        )

    def append_observation(self, observation: Observation) -> None:
        self._append_jsonl(
            get_agentic_agent_path(
                observation.run_id, observation.agent_name, "observations.jsonl"
            ),
            observation,
        )
        self._append_jsonl(
            get_coordination_artifact_path(observation.run_id, "observations.jsonl"),
            observation,
        )

    def append_reflection(self, reflection: ReflectionDecision) -> None:
        self._append_jsonl(
            get_agentic_agent_path(
                reflection.run_id, reflection.agent_name, "reflections.jsonl"
            ),
            reflection,
        )
        self._append_jsonl(
            get_coordination_artifact_path(reflection.run_id, "reflections.jsonl"),
            reflection,
        )

    def append_action(self, action: ActionProposal) -> None:
        self._append_jsonl(
            get_coordination_artifact_path(action.run_id, "actions.jsonl"), action
        )

    def append_tool_result(self, run_id: str, tool_result: ToolResult) -> None:
        self._append_jsonl(
            get_coordination_artifact_path(run_id, "tool_calls.jsonl"), tool_result
        )

    def append_rationale(self, rationale: DecisionRationale) -> None:
        self._append_jsonl(
            get_coordination_artifact_path(
                rationale.run_id, "decision_rationales.jsonl"
            ),
            rationale,
        )

    def save_working_memory(
        self, *, run_id: str, agent_name: str, payload: dict[str, Any]
    ) -> None:
        self.store.write(
            get_agentic_agent_path(run_id, agent_name, "working_memory.json"),
            payload,
        )

    def append_message(self, message: CoordinationMessage) -> None:
        self._append_jsonl(
            get_coordination_artifact_path(message.run_id, "messages.jsonl"),
            message,
        )
        self.patch_retrying(
            message.run_id,
            CoordinationPatch(add_open_messages=[message.message_id]),
        )

    def append_agent_request(self, request: AgentRequest) -> None:
        self._append_jsonl(
            get_coordination_artifact_path(
                request.run_id, "peer_requests.jsonl"
            ),
            request,
        )

    def get_agent_requests(self, run_id: str) -> list[AgentRequest]:
        path = get_coordination_artifact_path(run_id, "peer_requests.jsonl")
        if not path.exists():
            return []
        latest: dict[str, AgentRequest] = {}
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    item = AgentRequest.model_validate_json(line)
                    latest[item.request_id] = item
        return list(latest.values())

    def get_messages(self, run_id: str) -> list[CoordinationMessage]:
        path = get_coordination_artifact_path(run_id, "messages.jsonl")
        if not path.exists():
            return []
        latest: dict[str, CoordinationMessage] = {}
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    item = CoordinationMessage.model_validate_json(line)
                    latest[item.message_id] = item
        return list(latest.values())

    def get_open_messages(self, run_id: str) -> list[CoordinationMessage]:
        open_ids = set(self.load_state(run_id).open_messages)
        return [
            item
            for item in self.get_messages(run_id)
            if item.message_id in open_ids and item.status == "open"
        ]

    def resolve_message(
        self,
        message: CoordinationMessage,
        *,
        status: str,
        resolution: str,
    ) -> CoordinationMessage:
        resolved = message.model_copy(
            update={
                "status": status,
                "resolution": resolution,
                "resolved_at": datetime.now(tz=timezone.utc),
            }
        )
        self._append_jsonl(
            get_coordination_artifact_path(message.run_id, "messages.jsonl"),
            resolved,
        )
        self.patch_retrying(
            message.run_id,
            CoordinationPatch(resolve_messages=[message.message_id]),
        )
        return resolved

    def save_completion(self, decision: CompletionDecision) -> None:
        agent_dir_path = get_agentic_agent_path(
            decision.run_id, decision.agent_name, "completion_decision.json"
        )
        if not agent_dir_path.exists() or decision.goal_id.endswith("-TOP"):
            self.store.write(agent_dir_path, decision)
        self.store.write(
            get_agentic_agent_path(
                decision.run_id,
                decision.agent_name,
                f"completion_decisions/{decision.goal_id}.json",
            ),
            decision,
        )
        self._append_json_array(
            get_coordination_artifact_path(
                decision.run_id, "completion_claims.json"
            ),
            decision,
        )
        patch = CoordinationPatch(add_completion_claims=[decision.decision_id])
        if decision.final_status in {"completed", "completed_with_warnings"}:
            patch.complete_goals.append(decision.goal_id)
        elif decision.final_status == "needs_human_review":
            patch.human_review_goals.append(decision.goal_id)
        else:
            patch.block_goals.append(decision.goal_id)
        self.patch_retrying(decision.run_id, patch)

    def save_final_decision(self, decision: CompletionDecision) -> Path:
        path = get_final_decision_path(decision.run_id)
        self.store.write(path, decision)
        return path

    def add_resolution_task(self, run_id: str, task: dict[str, Any]) -> None:
        self._append_json_array(
            get_coordination_artifact_path(run_id, "resolution_tasks.json"), task
        )

    def patch_retrying(
        self, run_id: str, patch: CoordinationPatch, attempts: int = 3
    ) -> CoordinationState:
        for attempt in range(attempts):
            state = self.load_state(run_id)
            try:
                return self.update_state(run_id, state.state_version, patch)
            except CoordinationVersionConflict:
                if attempt == attempts - 1:
                    raise
        raise CoordinationVersionConflict("Coordination update retry budget exhausted.")

    @staticmethod
    def _apply_patch(state: CoordinationState, patch: CoordinationPatch) -> None:
        for goal_id in patch.activate_goals:
            if goal_id not in state.active_goals:
                state.active_goals.append(goal_id)
        for goal_id in [
            *patch.complete_goals,
            *patch.block_goals,
            *patch.human_review_goals,
        ]:
            if goal_id in state.active_goals:
                state.active_goals.remove(goal_id)
        for goal_id in patch.complete_goals:
            if goal_id not in state.completed_goals:
                state.completed_goals.append(goal_id)
        for goal_id in patch.block_goals:
            if goal_id not in state.blocked_goals:
                state.blocked_goals.append(goal_id)
        for goal_id in patch.human_review_goals:
            if goal_id not in state.human_review_goals:
                state.human_review_goals.append(goal_id)
        state.current_plans.update(patch.current_plans)
        JsonCoordinationRepository._extend_unique(
            state.open_messages, patch.add_open_messages
        )
        JsonCoordinationRepository._remove_all(
            state.open_messages, patch.resolve_messages
        )
        JsonCoordinationRepository._extend_unique(
            state.unresolved_questions, patch.add_questions
        )
        JsonCoordinationRepository._remove_all(
            state.unresolved_questions, patch.resolve_questions
        )
        JsonCoordinationRepository._extend_unique(state.blockers, patch.add_blockers)
        JsonCoordinationRepository._remove_all(
            state.blockers, patch.resolve_blockers
        )
        JsonCoordinationRepository._extend_unique(
            state.completion_claims, patch.add_completion_claims
        )
        state.supervisor_round += patch.supervisor_round_increment

    @staticmethod
    def _extend_unique(target: list[str], values: list[str]) -> None:
        for value in values:
            if value not in target:
                target.append(value)

    @staticmethod
    def _remove_all(target: list[str], values: list[str]) -> None:
        for value in values:
            if value in target:
                target.remove(value)

    def _append_json_array(self, path: Path, value: Any) -> None:
        with _path_lock(path):
            payload = self.store.read(path, default=[])
            payload.append(jsonable(value))
            self.store.write(path, payload)

    @staticmethod
    def _append_jsonl(path: Path, value: Any) -> None:
        import json

        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(jsonable(value), ensure_ascii=True, sort_keys=True) + "\n"
        with _path_lock(path):
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
