"""Agent 14: approved, idempotent notification delivery and correlation."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.integrations.notifications import adapter_for, idempotency_ledger_path
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.production import NotificationInput, NotificationResult


class IntegrationNotificationAgent(
    ProductionGoalAgent[NotificationInput, NotificationResult]
):
    agent_name = "integration_notification"
    agent_version = "1.0.0"
    expected_artifact = "notification_delivery_report.json"
    tool_specs = (
        (
            "verify_communication_approval",
            "Verify that the communication is approved.",
            "Unapproved communication is suppressed.",
        ),
        (
            "select_healthy_channel",
            "Select the highest-priority configured channel.",
            "A permitted provider route is selected.",
        ),
        (
            "dispatch_idempotently",
            "Deliver once with correlation and fallback.",
            "Delivery or safe failure is recorded.",
        ),
        (
            "persist_delivery_state",
            "Persist receipt and response-correlation state.",
            "The task has an auditable delivery state.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._approval(input_data)
        self._select(input_data)
        self._dispatch(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "verify_communication_approval": lambda: self._approval(input_data),
            "select_healthy_channel": lambda: self._select(input_data),
            "dispatch_idempotently": lambda: self._dispatch(input_data),
            "persist_delivery_state": lambda: self._complete(input_data),
        }

    def _approval(self, input_data):
        self._state["approved"] = input_data.approved
        return {
            "status": "completed" if input_data.approved else "completed_with_warnings",
            "approved": input_data.approved,
        }

    def _select(self, input_data):
        channels = sorted(input_data.channels, key=lambda item: item.priority)
        self._state["channels"] = channels
        return {"status": "completed", "channel_count": len(channels)}

    def _dispatch(self, input_data):
        store = AtomicJsonStore()
        ledger_path = idempotency_ledger_path(input_data.workflow.run_id)
        ledger = store.read(ledger_path, default={})
        if input_data.idempotency_key in ledger:
            self._state.update(
                attempts=[],
                duplicate=True,
                delivery_status="suppressed",
                selected_channel=ledger[input_data.idempotency_key].get("channel"),
            )
            return {"status": "completed", "duplicate_suppressed": True}
        if not input_data.approved:
            self._state.update(
                attempts=[],
                duplicate=False,
                delivery_status="suppressed",
                selected_channel=None,
            )
            return {"status": "completed_with_warnings", "reason": "approval_required"}

        attempts = []
        selected = None
        for channel in self._state["channels"]:
            try:
                attempt = adapter_for(channel.channel_type).deliver(input_data, channel)
            except Exception as exc:
                from proofchain.schemas.production import DeliveryAttempt

                attempt = DeliveryAttempt(
                    channel_type=channel.channel_type,
                    destination=channel.destination,
                    status="failed",
                    error=str(exc),
                )
            attempts.append(attempt)
            if attempt.status == "delivered":
                selected = channel.channel_type
                break
        status = "delivered" if selected else "failed"
        if selected:
            ledger[input_data.idempotency_key] = {
                "task_id": input_data.task_id,
                "channel": selected,
                "correlation_token": input_data.correlation_token,
            }
            store.write(ledger_path, ledger)
        self._state.update(
            attempts=attempts,
            duplicate=False,
            delivery_status=status,
            selected_channel=selected,
        )
        return {"status": "completed" if selected else "failed", "attempts": len(attempts)}

    def _complete(self, input_data):
        status = self._state.get("delivery_status", "failed")
        duplicate = self._state.get("duplicate", False)
        attempts = self._state.get("attempts", [])
        failed = status == "failed"
        warnings = (
            ["Duplicate delivery was suppressed."]
            if duplicate
            else ["Communication approval is required."]
            if not input_data.approved
            else []
        )
        result = NotificationResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="failed" if failed else "completed_with_warnings" if warnings else "completed",
            input_count=1,
            success_count=1 if status in {"delivered", "suppressed"} else 0,
            warning_count=len(warnings),
            failure_count=1 if failed else 0,
            errors=["All configured notification providers failed."] if failed else [],
            warnings=warnings,
            task_id=input_data.task_id,
            delivery_status=status,
            selected_channel=self._state.get("selected_channel"),
            correlation_token=input_data.correlation_token,
            idempotency_key=input_data.idempotency_key,
            attempts=attempts,
            duplicate_suppressed=duplicate,
        )
        result = self._persist(result)
        JsonEventRepository().append(
            run_id=result.run_id,
            event_type="NotificationDeliveryRecorded",
            aggregate_type="task",
            aggregate_id=input_data.task_id,
            actor=self.agent_name,
            payload={
                "status": status,
                "channel": result.selected_channel,
                "correlation_token": result.correlation_token,
                "duplicate_suppressed": duplicate,
            },
        )
        return result

