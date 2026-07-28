"""Tenant, department, and explicit resource-sharing boundary evaluation."""

from __future__ import annotations

from datetime import datetime, timezone

from proofchain.schemas.institutional import TenantGovernanceInput


def evaluate_tenant_access(
    request: TenantGovernanceInput,
) -> tuple[str, list[str], str | None, list[str]]:
    reasons: list[str] = []
    permissions: set[str] = set()
    for grant in request.grants:
        if (
            grant.subject_id == request.subject_id
            and grant.tenant_id == request.requested_tenant_id
            and (
                not grant.departments
                or request.requested_department_id is None
                or request.requested_department_id in grant.departments
            )
        ):
            permissions.update(grant.permissions)

    cross_tenant = request.requested_tenant_id != request.resource_tenant_id
    applied_share = None
    if cross_tenant:
        now = datetime.now(tz=timezone.utc)
        share = next(
            (
                item
                for item in request.shares
                if item.resource_id == request.resource_id
                and item.source_tenant_id == request.resource_tenant_id
                and item.target_tenant_id == request.requested_tenant_id
                and item.approved
                and (item.expires_at is None or item.expires_at >= now)
                and (
                    not item.departments
                    or request.requested_department_id is None
                    or request.requested_department_id in item.departments
                )
            ),
            None,
        )
        if share is None:
            reasons.append("No active approved cross-tenant share covers this resource.")
            return "DENY", sorted(permissions), None, reasons
        permissions.update(share.permissions)
        applied_share = share.share_id
        reasons.append(f"Approved resource share {share.share_id} applied.")

    if request.resource_department_id and request.requested_department_id:
        same_department = (
            request.resource_department_id == request.requested_department_id
        )
        shared_department = applied_share is not None
        if not same_department and not shared_department:
            reasons.append("Department boundary does not permit this resource.")
            return "DENY", sorted(permissions), applied_share, reasons
    if request.action not in permissions:
        reasons.append(f"Permission {request.action!r} is not available in tenant scope.")
        return "DENY", sorted(permissions), applied_share, reasons
    reasons.append("Tenant, department, sharing, and permission checks passed.")
    return "ALLOW", sorted(permissions), applied_share, reasons

