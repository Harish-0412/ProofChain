"""Policy validation, conflict detection, and historical impact simulation."""

from __future__ import annotations

from proofchain.schemas.institutional import (
    HistoricalPolicyCase,
    PolicyChange,
    PolicySimulationOutcome,
)


def validate_policy_change(change: PolicyChange) -> list[str]:
    errors: list[str] = []
    if change.document.get("policy_id") != change.policy_id:
        errors.append("Policy document ID does not match the proposed policy ID.")
    if change.document.get("schema_version") is None:
        errors.append("Policy document requires schema_version.")
    if change.base_version == change.proposed_version:
        errors.append("Proposed policy version must differ from the base version.")
    return errors


def detect_policy_conflicts(
    active_policies: dict[str, dict], change: PolicyChange
) -> list[str]:
    conflicts: list[str] = []
    document = change.document
    if document.get("default_effect") == "allow":
        conflicts.append("Deny-by-default governance conflicts with default_effect=allow.")
    if document.get("bypass_human_approval") is True:
        conflicts.append("Policy attempts to bypass mandatory human approval.")
    if document.get("rewrite_historical_decisions") is True:
        conflicts.append("Policy attempts to rewrite historical decisions.")
    active = active_policies.get(change.policy_id)
    if active and active.get("immutable") and active != document:
        conflicts.append("An immutable active policy cannot be replaced.")
    return conflicts


def simulate_policy(
    cases: list[HistoricalPolicyCase], change: PolicyChange
) -> list[PolicySimulationOutcome]:
    effect = str(change.document.get("simulation_effect", "preserve"))
    outcomes: list[PolicySimulationOutcome] = []
    for case in cases:
        simulated = (
            str(change.document.get("simulated_decision", case.previous_decision))
            if effect == "override"
            else case.previous_decision
        )
        outcomes.append(
            PolicySimulationOutcome(
                case_id=case.case_id,
                previous_decision=case.previous_decision,
                simulated_decision=simulated,
                changed=simulated != case.previous_decision,
            )
        )
    return outcomes

