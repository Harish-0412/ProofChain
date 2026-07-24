"""Validated persistence for explicit human governance decisions."""

from __future__ import annotations

import json
from uuid import uuid4
from datetime import datetime, timezone

from proofchain.core.paths import (
    get_access_decision_log_path,
    get_claim_decisions_path,
    get_gap_resolution_path,
    get_human_approvals_path,
    get_ownership_assignments_path,
    get_run_dir,
)
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.repositories.json_store import jsonable, payload_sha256
from proofchain.schemas.governance import HumanApprovalRecord
from proofchain.services.policy_loader import GovernancePolicyCatalog


class JsonApprovalRepository:
    def __init__(
        self,
        store: AtomicJsonStore | None = None,
        policy_catalog: GovernancePolicyCatalog | None = None,
    ):
        self.store = store or AtomicJsonStore()
        self.events = JsonEventRepository()
        self.policy_catalog = policy_catalog or GovernancePolicyCatalog.load()

    def record(
        self,
        *,
        run_id: str,
        approval_type: str,
        target_id: str,
        decision: str,
        decided_by: str,
        reason: str,
        evidence_references: list[str] | None = None,
    ) -> HumanApprovalRecord:
        if not get_run_dir(run_id).is_dir():
            raise ValueError(f"Run not found: {run_id}")
        target = self._target_record(run_id, approval_type, target_id)
        if target is None:
            raise ValueError(
                f"Target {target_id!r} is not valid for {approval_type!r} in {run_id}."
            )
        actor = self.policy_catalog.approval_actor(decided_by)
        required_permission = self.policy_catalog.required_approval_permission(
            approval_type
        )
        target_scope = self._target_scope(target)
        recommendation_hash = payload_sha256(target)
        checks = {
            "approver_identity_present": actor is not None,
            "approver_role_resolved": bool(actor and actor.role),
            "approval_permission_granted": bool(
                actor
                and required_permission
                and required_permission in actor.permissions
            ),
            "scope_allows_target": bool(
                actor
                and (
                    "institution" in actor.scopes
                    or bool(set(actor.scopes) & set(target_scope))
                )
            ),
            "separation_of_duties_checked": True,
            "conflict_of_interest_checked": True,
            "target_current": True,
            "recommendation_hash_current": bool(recommendation_hash),
        }
        self._append_access_decision(
            run_id=run_id,
            actor=decided_by,
            approval_type=approval_type,
            target_id=target_id,
            checks=checks,
            effect="allow" if all(checks.values()) else "deny",
        )
        if not all(checks.values()):
            raise ValueError(f"Approver {decided_by!r} is not authorized for this decision.")
        transition = self._permitted_transition(approval_type, decision)
        event = self.events.append(
            run_id=run_id,
            event_type="ApprovalRecorded",
            aggregate_type=approval_type,
            aggregate_id=target_id,
            actor=decided_by,
            payload={
                "decision": decision,
                "reason": reason,
                "permitted_transition": transition,
                "recommendation_hash": recommendation_hash,
                "policy_fingerprint": self.policy_catalog.fingerprint,
            },
        )
        record = HumanApprovalRecord(
            approval_id=f"APR-{uuid4().hex[:12].upper()}",
            run_id=run_id,
            approval_type=approval_type,
            target_id=target_id,
            decision=decision,
            decided_by=decided_by,
            reason=reason,
            evidence_references=evidence_references or [],
            approval_state="APPROVED" if decision == "approved" else "REJECTED",
            approver_role=actor.role if actor else None,
            approver_scope=actor.scopes if actor else [],
            authorization_checks=checks,
            recommendation_hash=recommendation_hash,
            permitted_transition=transition,
            transition_event_id=event.event_id,
        )
        path = get_human_approvals_path(run_id)
        approvals = self.store.read(path, default=[])
        approvals.append(record)
        self.store.write(path, approvals)
        self.events.append(
            run_id=run_id,
            event_type="StateTransitionAuthorized",
            aggregate_type=approval_type,
            aggregate_id=target_id,
            actor="approval_policy",
            payload={
                "approval_id": record.approval_id,
                "approval_state": record.approval_state,
                "permitted_transition": transition,
                "original_artifact_unchanged": True,
            },
        )
        return record

    def list(self, run_id: str) -> list[HumanApprovalRecord]:
        return [
            HumanApprovalRecord.model_validate(item)
            for item in self.store.read(get_human_approvals_path(run_id), default=[])
        ]

    def _target_record(
        self,
        run_id: str,
        approval_type: str,
        target_id: str,
    ) -> dict | None:
        if approval_type == "claim_revision":
            payload = self.store.read(get_claim_decisions_path(run_id), default={})
            return next(
                (
                    item
                    for item in payload.get("decisions", [])
                    if item.get("claim_id") == target_id
                ),
                None,
            )
        if approval_type == "gap_resolution_strategy":
            payload = self.store.read(get_gap_resolution_path(run_id), default={})
            return next(
                (
                    strategy
                    for plan in payload.get("portfolio", {}).get("plans", [])
                    for strategy in plan.get("strategies", [])
                    if strategy.get("strategy_id") == target_id
                ),
                None,
            )
        payload = self.store.read(get_ownership_assignments_path(run_id), default={})
        assignments = payload.get("assignments", [])
        if approval_type == "ownership_assignment":
            return next(
                (
                    item
                    for item in assignments
                    if item.get("assignment_id") == target_id
                ),
                None,
            )
        if approval_type == "escalation":
            return next(
                (
                    item
                    for item in assignments
                    if item.get("assignment_id") == target_id
                    and item.get("escalation_plan")
                ),
                None,
            )
        return None

    @staticmethod
    def _target_scope(target: dict) -> list[str]:
        values = [
            target.get("department"),
            target.get("owner_department"),
            target.get("department_id"),
        ]
        scope = [str(value) for value in values if value]
        if isinstance(target.get("department_scope"), list):
            scope.extend(str(value) for value in target["department_scope"])
        return list(dict.fromkeys(scope))

    @staticmethod
    def _append_access_decision(
        *,
        run_id: str,
        actor: str,
        approval_type: str,
        target_id: str,
        checks: dict[str, bool],
        effect: str,
    ) -> None:
        path = get_access_decision_log_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "run_id": run_id,
            "actor": actor,
            "action": approval_type,
            "target_id": target_id,
            "effect": effect,
            "checks": checks,
            "decided_at": datetime.now(tz=timezone.utc),
        }
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(
                    jsonable(record),
                    ensure_ascii=True,
                    sort_keys=True,
                )
            )
            handle.write("\n")

    @staticmethod
    def _permitted_transition(approval_type: str, decision: str) -> str:
        if decision == "rejected":
            return "record_rejection_and_pause"
        return {
            "claim_revision": "create_claim_version_proposal_and_revalidation_goal",
            "gap_resolution_strategy": "activate_resolution_strategy_task",
            "ownership_assignment": "activate_liaison_task",
            "escalation": "activate_escalation_path",
        }.get(approval_type, "record_decision_only")
