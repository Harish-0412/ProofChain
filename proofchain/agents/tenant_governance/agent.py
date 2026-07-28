"""Agent 19: tenant isolation, department boundaries, and explicit sharing."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.institutional import (
    TenantGovernanceInput,
    TenantGovernanceResult,
)
from proofchain.services.tenant_governance import evaluate_tenant_access


class TenantGovernanceAgent(
    ProductionGoalAgent[TenantGovernanceInput, TenantGovernanceResult]
):
    agent_name = "tenant_governance"
    agent_version = "1.0.0"
    expected_artifact = "tenant_access_decision.json"
    tool_specs = (
        (
            "resolve_tenant_context",
            "Resolve subject, requested tenant, and resource tenant.",
            "Tenant identities are explicit.",
        ),
        (
            "evaluate_department_boundary",
            "Evaluate department scope and cross-department access.",
            "Department isolation is enforced.",
        ),
        (
            "evaluate_resource_sharing",
            "Validate approved, scoped, non-expired resource shares.",
            "Cross-tenant access requires an explicit share.",
        ),
        (
            "match_tenant_permission",
            "Match the requested action to effective tenant permissions.",
            "Access is denied by default.",
        ),
        (
            "persist_tenant_decision",
            "Persist the tenant access decision and policy source.",
            "Every resource operation has an auditable boundary decision.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._resolve(input_data)
        self._department(input_data)
        self._share(input_data)
        self._permission(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "resolve_tenant_context": lambda: self._resolve(input_data),
            "evaluate_department_boundary": lambda: self._department(input_data),
            "evaluate_resource_sharing": lambda: self._share(input_data),
            "match_tenant_permission": lambda: self._permission(input_data),
            "persist_tenant_decision": lambda: self._complete(input_data),
        }

    def _resolve(self, input_data):
        cross = input_data.requested_tenant_id != input_data.resource_tenant_id
        self._state["cross"] = cross
        return {"status": "completed", "cross_tenant": cross}

    def _department(self, input_data):
        mismatch = bool(
            input_data.requested_department_id
            and input_data.resource_department_id
            and input_data.requested_department_id
            != input_data.resource_department_id
        )
        self._state["department_mismatch"] = mismatch
        return {"status": "completed_with_warnings" if mismatch else "completed"}

    def _share(self, input_data):
        decision = evaluate_tenant_access(input_data)
        self._state["decision"] = decision
        return {
            "status": "completed" if decision[0] == "ALLOW" else "completed_with_warnings",
            "applied_share": decision[2],
        }

    def _permission(self, input_data):
        return {
            "status": "completed"
            if self._state["decision"][0] == "ALLOW"
            else "completed_with_warnings",
            "effective_permissions": self._state["decision"][1],
        }

    def _complete(self, input_data):
        decision, permissions, share_id, reasons = self._state["decision"]
        warnings = reasons if decision != "ALLOW" else []
        result = TenantGovernanceResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if warnings else "completed",
            input_count=1,
            success_count=1 if decision == "ALLOW" else 0,
            warning_count=len(warnings),
            warnings=warnings,
            tenant_id=input_data.requested_tenant_id,
            department_id=input_data.requested_department_id,
            access_decision=decision,
            effective_permissions=permissions,
            applied_share_id=share_id,
            cross_tenant_request=self._state["cross"],
            policy_reasons=reasons,
        )
        result = self._persist(result)
        JsonEventRepository().append(
            run_id=result.run_id,
            event_type="TenantAccessDecisionRecorded",
            aggregate_type="resource",
            aggregate_id=input_data.resource_id,
            actor=self.agent_name,
            payload={
                "subject_id": input_data.subject_id,
                "tenant_id": input_data.requested_tenant_id,
                "decision": decision,
                "share_id": share_id,
            },
        )
        return result

