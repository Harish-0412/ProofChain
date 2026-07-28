"""Deterministic enterprise authorization and separation-of-duties evaluation."""

from __future__ import annotations

from datetime import datetime, timezone

from proofchain.schemas.production import AuthorizationInput


def evaluate_authorization(
    request: AuthorizationInput,
) -> tuple[str, list[str], list[str], int, int, bool]:
    now = datetime.now(tz=timezone.utc)
    reasons: list[str] = []
    permissions: set[str] = set()
    if not request.identity_verified:
        return "DENIED", [], ["Identity is not externally verified."], 2 if request.high_risk else 1, 0, False

    for grant in request.role_grants:
        in_time = (grant.valid_from is None or grant.valid_from <= now) and (
            grant.valid_until is None or grant.valid_until >= now
        )
        in_scope = grant.tenant_id == request.tenant_id and (
            not grant.departments
            or request.department_id is None
            or request.department_id in grant.departments
        )
        if in_time and in_scope:
            permissions.update(grant.permissions)

    for delegation in request.delegations:
        if (
            delegation.delegated_to == request.subject_id
            and delegation.tenant_id == request.tenant_id
            and delegation.valid_from <= now <= delegation.valid_until
            and (
                not delegation.departments
                or request.department_id is None
                or request.department_id in delegation.departments
            )
        ):
            permissions.update(delegation.permissions)
            reasons.append(f"Active delegation {delegation.delegation_id} applied.")

    self_approval = request.subject_id in {
        request.resource_creator_id,
        request.resource_owner_id,
    } and request.action.startswith(("approve", "waive", "submit"))
    if self_approval:
        reasons.append("Separation of duties prohibits self-approval.")
    if request.action not in permissions:
        reasons.append(f"Permission {request.action!r} is not present in the effective scope.")

    required = 2 if request.high_risk else 1
    valid_approvers = {
        approval.approver_id
        for approval in request.prior_approvals
        if approval.decision == "approved"
        and approval.independent
        and approval.approver_id != request.subject_id
    }
    valid_count = len(valid_approvers)
    separation_passed = not self_approval
    if self_approval or request.action not in permissions:
        decision = "DENIED"
    elif valid_count + 1 < required:
        decision = "NEEDS_ADDITIONAL_APPROVAL"
        reasons.append(f"{required} independent approvals are required.")
    else:
        decision = "AUTHORIZED"
        reasons.append("Identity, scope, permission, and approval policy passed.")
    return decision, sorted(permissions), reasons, required, valid_count, separation_passed

