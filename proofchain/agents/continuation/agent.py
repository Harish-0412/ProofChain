"""Agent 12: fingerprint-based continuation and partial re-execution planning."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.services.continuation import calculate_impact, fingerprint_references
from proofchain.schemas.production import ContinuationInput, ContinuationResult


class WorkflowContinuationAgent(
    ProductionGoalAgent[ContinuationInput, ContinuationResult]
):
    agent_name = "workflow_continuation"
    agent_version = "1.0.0"
    expected_artifact = "continuation_reexecution_plan.json"
    tool_specs = (
        (
            "calculate_fingerprints",
            "Fingerprint current artifacts and identify changes.",
            "A deterministic change set is available.",
        ),
        (
            "analyze_dependency_impact",
            "Traverse dependencies and identify stale and reusable scope.",
            "Affected entities and agents are known.",
        ),
        (
            "resolve_resume_state",
            "Resume eligible waiting goals and suppress duplicate work.",
            "A bounded partial re-execution plan is available.",
        ),
        (
            "reconcile_continuation",
            "Persist the continuation decision.",
            "The supervisor can schedule only affected work.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._fingerprint(input_data)
        self._impact(input_data)
        self._resume(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "calculate_fingerprints": lambda: self._fingerprint(input_data),
            "analyze_dependency_impact": lambda: self._impact(input_data),
            "resolve_resume_state": lambda: self._resume(input_data),
            "reconcile_continuation": lambda: self._complete(input_data),
        }

    def _fingerprint(self, input_data):
        current = fingerprint_references(input_data.current_references)
        self._state["current"] = current
        return {"status": "completed", "fingerprints": len(current)}

    def _impact(self, input_data):
        changed, stale, reusable, agents = calculate_impact(
            input_data.previous_fingerprints,
            self._state["current"],
            input_data.dependency_graph,
        )
        self._state.update(
            changed=changed, stale=stale, reusable=reusable, agents=agents
        )
        return {"status": "completed", "changed": len(changed), "stale": len(stale)}

    def _resume(self, input_data):
        resumed = list(dict.fromkeys(input_data.waiting_goal_ids))
        duplicates = [
            goal_id
            for index, goal_id in enumerate(input_data.waiting_goal_ids)
            if goal_id in input_data.waiting_goal_ids[:index]
        ]
        self._state["resumed"] = resumed
        self._state["duplicates"] = sorted(set(duplicates))
        return {"status": "completed", "resumed": len(resumed)}

    def _complete(self, input_data):
        changed = self._state.get("changed", [])
        result = ContinuationResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed",
            input_count=len(input_data.current_references),
            success_count=len(self._state.get("agents", [])),
            change_set=changed,
            stale_entities=self._state.get("stale", []),
            reusable_entities=self._state.get("reusable", []),
            scheduled_agents=self._state.get("agents", []),
            resumed_goal_ids=self._state.get("resumed", []),
            duplicate_actions_suppressed=self._state.get("duplicates", []),
            fingerprints=self._state.get("current", []),
            reconciliation_required=bool(changed),
        )
        return self._persist(result)

