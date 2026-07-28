"""Agent 18: policy versioning, conflict detection, simulation, and activation."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.institutional import (
    PolicyLifecycleInput,
    PolicyLifecycleResult,
)
from proofchain.services.policy_lifecycle import (
    detect_policy_conflicts,
    simulate_policy,
    validate_policy_change,
)


class PolicyLifecycleAgent(
    ProductionGoalAgent[PolicyLifecycleInput, PolicyLifecycleResult]
):
    agent_name = "policy_lifecycle"
    agent_version = "1.0.0"
    expected_artifact = "policy_lifecycle_report.json"
    tool_specs = (
        (
            "parse_policy_change",
            "Parse and validate the proposed policy version.",
            "Policy syntax and identity are valid.",
        ),
        (
            "detect_governance_conflicts",
            "Detect deny-by-default and human-governance conflicts.",
            "Unsafe policy semantics are disclosed.",
        ),
        (
            "simulate_historical_impact",
            "Replay representative historical cases.",
            "Decision impact is measured without rewriting history.",
        ),
        (
            "identify_affected_runs",
            "Identify open runs named by the policy change.",
            "Operational impact is explicit.",
        ),
        (
            "gate_policy_activation",
            "Require conflict resolution and human approval before activation.",
            "An explainable activation decision is persisted.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._parse(input_data)
        self._conflicts(input_data)
        self._simulate(input_data)
        self._affected(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "parse_policy_change": lambda: self._parse(input_data),
            "detect_governance_conflicts": lambda: self._conflicts(input_data),
            "simulate_historical_impact": lambda: self._simulate(input_data),
            "identify_affected_runs": lambda: self._affected(input_data),
            "gate_policy_activation": lambda: self._complete(input_data),
        }

    def _parse(self, input_data):
        errors = (
            validate_policy_change(input_data.proposed_change)
            if input_data.proposed_change
            else []
        )
        self._state["syntax_errors"] = errors
        return {"status": "completed_with_warnings" if errors else "completed", "errors": errors}

    def _conflicts(self, input_data):
        conflicts = (
            detect_policy_conflicts(input_data.active_policies, input_data.proposed_change)
            if input_data.proposed_change
            else []
        )
        self._state["conflicts"] = conflicts
        return {
            "status": "completed_with_warnings" if conflicts else "completed",
            "conflicts": conflicts,
        }

    def _simulate(self, input_data):
        simulations = (
            simulate_policy(input_data.historical_cases, input_data.proposed_change)
            if input_data.proposed_change
            else []
        )
        self._state["simulations"] = simulations
        return {
            "status": "completed",
            "changed_decisions": sum(item.changed for item in simulations),
        }

    def _affected(self, input_data):
        affected = []
        if input_data.proposed_change:
            affected = [
                str(item)
                for item in input_data.proposed_change.document.get(
                    "affected_open_run_ids", []
                )
            ]
        self._state["affected"] = affected
        return {"status": "completed", "affected_runs": len(affected)}

    def _complete(self, input_data):
        syntax_errors = self._state["syntax_errors"]
        conflicts = self._state["conflicts"]
        if input_data.proposed_change is None:
            decision = "NO_CHANGE"
        elif syntax_errors or conflicts:
            decision = "BLOCK"
        elif input_data.activation_requested and not input_data.human_approval_id:
            decision = "NEEDS_HUMAN_APPROVAL"
        elif input_data.activation_requested:
            decision = "ACTIVATE"
        else:
            decision = "NEEDS_HUMAN_APPROVAL"
        warnings = [*syntax_errors, *conflicts]
        if decision == "NEEDS_HUMAN_APPROVAL":
            warnings.append("Policy activation requires explicit human approval.")
        result = PolicyLifecycleResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if warnings else "completed",
            input_count=len(input_data.active_policies),
            success_count=1 if not syntax_errors and not conflicts else 0,
            warning_count=len(warnings),
            warnings=warnings,
            policy_id=input_data.proposed_change.policy_id
            if input_data.proposed_change
            else None,
            syntax_valid=not syntax_errors,
            conflicts=conflicts,
            affected_open_run_ids=self._state["affected"],
            simulations=self._state["simulations"],
            historical_decisions_preserved=True,
            activation_decision=decision,
        )
        result = self._persist(result)
        JsonEventRepository().append(
            run_id=result.run_id,
            event_type="PolicyLifecycleEvaluated",
            aggregate_type="policy",
            aggregate_id=result.policy_id or "active-policy-set",
            actor=self.agent_name,
            payload={
                "activation_decision": decision,
                "conflict_count": len(conflicts),
                "historical_decisions_preserved": True,
            },
        )
        return result

