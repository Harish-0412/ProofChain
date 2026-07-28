"""Agent 13: identity, scope, delegation, and approval authorization."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.production import AuthorizationInput, AuthorizationResult
from proofchain.services.authorization import evaluate_authorization


class IdentityAuthorizationAgent(
    ProductionGoalAgent[AuthorizationInput, AuthorizationResult]
):
    agent_name = "identity_authorization"
    agent_version = "1.0.0"
    expected_artifact = "authorization_decision.json"
    tool_specs = (
        (
            "resolve_verified_identity",
            "Resolve the externally verified institutional identity.",
            "Identity assurance is explicit.",
        ),
        (
            "evaluate_role_and_scope",
            "Resolve roles, department scope, and delegated authority.",
            "Effective permissions are known.",
        ),
        (
            "evaluate_separation_of_duties",
            "Check conflict of interest and independent approvals.",
            "Self-approval and insufficient approval are blocked.",
        ),
        (
            "persist_authorization_decision",
            "Persist the explainable authorization decision.",
            "The protected action has a governed decision.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._identity(input_data)
        self._scope(input_data)
        self._separation(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "resolve_verified_identity": lambda: self._identity(input_data),
            "evaluate_role_and_scope": lambda: self._scope(input_data),
            "evaluate_separation_of_duties": lambda: self._separation(input_data),
            "persist_authorization_decision": lambda: self._complete(input_data),
        }

    def _identity(self, input_data):
        self._state["identity_verified"] = input_data.identity_verified
        return {
            "status": "completed" if input_data.identity_verified else "completed_with_warnings",
            "identity_verified": input_data.identity_verified,
        }

    def _scope(self, input_data):
        evaluated = evaluate_authorization(input_data)
        self._state["evaluation"] = evaluated
        return {"status": "completed", "effective_permissions": evaluated[1]}

    def _separation(self, input_data):
        evaluated = self._state["evaluation"]
        return {
            "status": "completed" if evaluated[5] else "completed_with_warnings",
            "separation_of_duties_passed": evaluated[5],
        }

    def _complete(self, input_data):
        decision, permissions, reasons, required, valid, separation = self._state["evaluation"]
        denied = decision == "DENIED"
        warning = decision == "NEEDS_ADDITIONAL_APPROVAL"
        result = AuthorizationResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if denied or warning else "completed",
            input_count=1,
            success_count=0 if denied else 1,
            warning_count=1 if denied or warning else 0,
            subject_id=input_data.subject_id,
            resource_id=input_data.resource_id,
            authorization_decision=decision,
            effective_permissions=permissions,
            required_approval_count=required,
            valid_approval_count=valid,
            separation_of_duties_passed=separation,
            policy_reasons=reasons,
            warnings=reasons if denied or warning else [],
        )
        result = self._persist(result)
        JsonEventRepository().append(
            run_id=result.run_id,
            event_type="AuthorizationDecisionRecorded",
            aggregate_type="authorization",
            aggregate_id=input_data.resource_id,
            actor=self.agent_name,
            payload={
                "subject_id": input_data.subject_id,
                "action": input_data.action,
                "decision": decision,
                "reasons": reasons,
            },
        )
        return result

