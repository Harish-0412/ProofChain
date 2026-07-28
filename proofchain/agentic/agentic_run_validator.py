"""Validate Phase 1 cognition artifacts and decision-ledger synchronization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from proofchain.agentic.cognition_profiles import ALL_AGENT_FEATURES
from proofchain.core.paths import get_goal_graph_path, get_run_dir
from proofchain.repositories.json_store import AtomicJsonStore


class AgenticRunValidator:
    ALWAYS_REQUIRED = {
        "cognition_profile.json",
        "interpreted_goal.json",
        "input_validation.json",
        "context_snapshot.json",
        "hypotheses.json",
        "state_transitions.jsonl",
        "completion_proof.json",
        "final_uncertainty.json",
        "decision_explanation.json",
        "core_precision_assessment.json",
        "agentic_scorecard.json",
        "experience_candidate.json",
    }
    VALID_INPUT_REQUIRED = {
        "action_selections.jsonl",
        "normalized_observations.jsonl",
        "structured_reflections.jsonl",
    }

    def __init__(self, store: AtomicJsonStore | None = None):
        self.store = store or AtomicJsonStore()

    def validate(self, run_id: str) -> dict[str, Any]:
        run_dir = get_run_dir(run_id)
        graph_path = get_goal_graph_path(run_id)
        errors: list[str] = []
        warnings: list[str] = []
        if not graph_path.exists():
            return {
                "run_id": run_id,
                "valid": False,
                "agents_validated": 0,
                "errors": ["goal_graph.json is missing."],
                "warnings": [],
            }
        graph = self.store.read(graph_path, default={})
        core_goals = [
            item
            for item in graph.get("goals", [])
            if item.get("assigned_agent") in ALL_AGENT_FEATURES
            and item.get("status") in {
                "completed",
                "blocked",
                "needs_human_review",
                "failed",
            }
        ]
        goals = [
            item
            for item in core_goals
            if not str(item.get("goal_type", "")).startswith("resolve_")
            or (
                run_dir
                / "agents"
                / item["assigned_agent"]
                / item["goal_id"]
            ).exists()
        ]
        undispatched = len(core_goals) - len(goals)
        if undispatched:
            warnings.append(
                f"{undispatched} generated resolution goals were terminally routed "
                "without agent execution and were excluded from cognition validation."
            )
        ledger = self._read_jsonl(run_dir / "agent_decisions.jsonl", errors)
        ledger_ids = {item.get("explanation_id") for item in ledger}

        validated = 0
        for goal in goals:
            agent_name = goal["assigned_agent"]
            goal_id = goal["goal_id"]
            root = run_dir / "agents" / agent_name / goal_id
            if not root.exists():
                errors.append(f"{agent_name}/{goal_id}: cognition directory is missing.")
                continue
            validated += 1
            for name in self.ALWAYS_REQUIRED:
                if not (root / name).exists():
                    errors.append(f"{agent_name}/{goal_id}: {name} is missing.")
            profile = self.store.read(root / "cognition_profile.json", default={})
            if profile.get("profile_name") != "advanced-cognition-platform":
                errors.append(f"{agent_name}/{goal_id}: advanced profile is not active.")
            if profile.get("profile_version") != "phase2-2.0.0":
                errors.append(
                    f"{agent_name}/{goal_id}: cognition profile version is not Phase 2."
                )
            for name in self.ALWAYS_REQUIRED - {"state_transitions.jsonl"}:
                payload = self.store.read(root / name, default={})
                versions = (
                    [item.get("schema_version") for item in payload]
                    if isinstance(payload, list)
                    else [payload.get("schema_version")]
                    if payload
                    else []
                )
                if versions and any(version != "1.0.0" for version in versions):
                    errors.append(
                        f"{agent_name}/{goal_id}: {name} has an unsupported schema version."
                    )
            inputs = self.store.read(root / "input_validation.json", default={})
            if inputs.get("valid"):
                for name in self.VALID_INPUT_REQUIRED:
                    if not (root / name).exists():
                        errors.append(f"{agent_name}/{goal_id}: {name} is missing.")
                plan_files = list((root / "plans").glob("plan_revision_*.json"))
                critique_files = list(
                    (root / "critiques").glob("critique_revision_*.json")
                )
                if not plan_files:
                    errors.append(f"{agent_name}/{goal_id}: no advanced plan exists.")
                if not critique_files:
                    errors.append(f"{agent_name}/{goal_id}: no plan critique exists.")
                elif not any(
                    self.store.read(path, default={}).get("approved")
                    for path in critique_files
                ):
                    errors.append(f"{agent_name}/{goal_id}: no approved critique exists.")
            proof = self.store.read(root / "completion_proof.json", default={})
            explanation = self.store.read(
                root / "decision_explanation.json", default={}
            )
            if explanation.get("completion_proof_id") != proof.get("proof_id"):
                errors.append(
                    f"{agent_name}/{goal_id}: decision is not linked to its completion proof."
                )
            if not proof.get("proof_valid"):
                errors.append(
                    f"{agent_name}/{goal_id}: canonical completion proof is invalid."
                )
            if explanation.get("explanation_id") not in ledger_ids:
                errors.append(
                    f"{agent_name}/{goal_id}: decision ledger entry is missing."
                )
            transitions = self._read_jsonl(root / "state_transitions.jsonl", errors)
            for previous, current in zip(transitions, transitions[1:]):
                if current.get("from_state") != previous.get("to_state"):
                    errors.append(
                        f"{agent_name}/{goal_id}: state transition chain is discontinuous."
                    )
                    break
            if transitions and transitions[-1].get("to_state") not in {
                "COMPLETED",
                "COMPLETED_WITH_WARNINGS",
                "WAITING_FOR_HUMAN",
                "BLOCKED",
                "FAILED",
                "CANCELLED",
            }:
                errors.append(
                    f"{agent_name}/{goal_id}: state machine has no terminal transition."
                )
            peer_requests = self._read_jsonl(
                root / "peer_requests.jsonl", []
            ) if (root / "peer_requests.jsonl").exists() else []
            latest_peers = {}
            for request in peer_requests:
                latest_peers[request.get("request_id")] = request
            for request in latest_peers.values():
                if request.get("status") == "RESOLVED" and not set(
                    request.get("acceptance_conditions", [])
                ) <= set(request.get("satisfied_acceptance_conditions", [])):
                    errors.append(
                        f"{agent_name}/{goal_id}: peer request was falsely resolved."
                    )
            uncertainty = self.store.read(
                root / "final_uncertainty.json", default={}
            )
            if (
                uncertainty.get("deterministic_block")
                and explanation.get("decision")
                in {"completed", "completed_with_warnings"}
            ):
                errors.append(
                    f"{agent_name}/{goal_id}: positive decision bypassed uncertainty block."
                )
        if not goals:
            warnings.append("No terminal core-agent goals were found.")
        return {
            "run_id": run_id,
            "valid": not errors,
            "agents_validated": validated,
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
        if not path.exists():
            errors.append(f"{path.name} is missing.")
            return []
        values = []
        with path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    values.append(json.loads(line))
                except json.JSONDecodeError:
                    errors.append(f"{path.name}:{number} is invalid JSON.")
        return values
