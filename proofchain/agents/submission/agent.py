"""Agent 20: human-controlled, immutable, idempotent package handoff."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.core.paths import get_run_dir
from proofchain.integrations.submission_portals import portal_for
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.institutional import SubmissionInput, SubmissionResult
from proofchain.services.submission_governance import evaluate_submission


class ExternalSubmissionAgent(
    ProductionGoalAgent[SubmissionInput, SubmissionResult]
):
    agent_name = "external_submission"
    agent_version = "1.0.0"
    expected_artifact = "external_submission_report.json"
    tool_specs = (
        (
            "verify_submission_eligibility",
            "Verify quality status, package version, deadline, and approvals.",
            "Ineligible or stale packages are blocked.",
        ),
        (
            "freeze_approved_package_hash",
            "Freeze the exact approved package hash.",
            "The submission payload cannot alter the package.",
        ),
        (
            "verify_final_confirmation",
            "Require final human confirmation for the frozen hash.",
            "No external handoff occurs autonomously.",
        ),
        (
            "submit_package_idempotently",
            "Submit once through the approved portal adapter.",
            "Duplicate irreversible actions are suppressed.",
        ),
        (
            "verify_submission_receipt",
            "Verify and persist the provider receipt or safe refusal.",
            "Submission status is complete and explainable.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._eligibility(input_data)
        self._freeze(input_data)
        self._confirm(input_data)
        self._submit(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "verify_submission_eligibility": lambda: self._eligibility(input_data),
            "freeze_approved_package_hash": lambda: self._freeze(input_data),
            "verify_final_confirmation": lambda: self._confirm(input_data),
            "submit_package_idempotently": lambda: self._submit(input_data),
            "verify_submission_receipt": lambda: self._complete(input_data),
        }

    def _eligibility(self, input_data):
        eligibility, package_hash, reasons = evaluate_submission(input_data)
        self._state.update(
            eligibility=eligibility, package_hash=package_hash, reasons=reasons
        )
        return {
            "status": "completed" if eligibility == "ELIGIBLE" else "completed_with_warnings",
            "eligibility": eligibility,
        }

    def _freeze(self, input_data):
        return {
            "status": "completed" if self._state["package_hash"] else "completed_with_warnings",
            "package_hash": self._state["package_hash"],
        }

    def _confirm(self, input_data):
        return {
            "status": "completed" if input_data.final_confirmation else "completed_with_warnings",
            "confirmed": input_data.final_confirmation,
        }

    def _submit(self, input_data):
        ledger_path = get_run_dir(input_data.workflow.run_id) / "submission_idempotency.json"
        store = AtomicJsonStore()
        ledger = store.read(ledger_path, default={})
        if input_data.idempotency_key in ledger:
            self._state.update(
                submission_status="duplicate_suppressed",
                receipt=ledger[input_data.idempotency_key],
            )
            return {"status": "completed", "duplicate_suppressed": True}
        if self._state["eligibility"] != "ELIGIBLE":
            self._state.update(submission_status="not_submitted", receipt=None)
            return {"status": "completed_with_warnings", "submitted": False}
        try:
            receipt = portal_for(input_data.portal_type).submit(
                input_data, self._state["package_hash"]
            )
        except Exception as exc:
            self._state.update(
                submission_status="failed", receipt=None, portal_error=str(exc)
            )
            return {"status": "failed", "error": str(exc)}
        ledger[input_data.idempotency_key] = receipt.model_dump(mode="json")
        store.write(ledger_path, ledger)
        self._state.update(submission_status="submitted", receipt=receipt)
        return {"status": "completed", "receipt_id": receipt.receipt_id}

    def _complete(self, input_data):
        from proofchain.schemas.institutional import SubmissionReceipt

        raw_receipt = self._state.get("receipt")
        receipt = (
            SubmissionReceipt.model_validate(raw_receipt)
            if isinstance(raw_receipt, dict)
            else raw_receipt
        )
        status = self._state.get("submission_status", "failed")
        warnings = (
            self._state["reasons"]
            if self._state["eligibility"] != "ELIGIBLE"
            else ["Duplicate submission was suppressed."]
            if status == "duplicate_suppressed"
            else []
        )
        errors = [self._state["portal_error"]] if self._state.get("portal_error") else []
        result = SubmissionResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="failed" if errors else "completed_with_warnings" if warnings else "completed",
            input_count=1,
            success_count=1 if status in {"submitted", "duplicate_suppressed", "not_submitted"} else 0,
            warning_count=len(warnings),
            failure_count=len(errors),
            warnings=warnings,
            errors=errors,
            package_id=input_data.package_id,
            frozen_package_hash=self._state["package_hash"],
            eligibility_decision=self._state["eligibility"],
            submission_status=status,
            receipt=receipt,
            idempotency_key=input_data.idempotency_key,
            policy_reasons=self._state["reasons"],
        )
        result = self._persist(result)
        JsonEventRepository().append(
            run_id=result.run_id,
            event_type="PackageSubmitted"
            if status == "submitted"
            else "SubmissionDecisionRecorded",
            aggregate_type="audit_package",
            aggregate_id=input_data.package_id,
            actor=self.agent_name,
            payload={
                "eligibility": result.eligibility_decision,
                "submission_status": status,
                "package_hash": result.frozen_package_hash,
                "receipt_id": receipt.receipt_id if receipt else None,
            },
        )
        return result

