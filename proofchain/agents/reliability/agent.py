"""Agent 16: telemetry correlation and bounded incident recovery decisions."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.production import ReliabilityInput, ReliabilityResult
from proofchain.services.reliability import analyze_telemetry


class ReliabilityIncidentAgent(
    ProductionGoalAgent[ReliabilityInput, ReliabilityResult]
):
    agent_name = "reliability_incident_response"
    agent_version = "1.0.0"
    expected_artifact = "incident_reliability_report.json"
    tool_specs = (
        (
            "observe_operational_signals",
            "Observe logs, metrics, traces, queues, and provider health.",
            "Abnormal signals are isolated from healthy signals.",
        ),
        (
            "correlate_and_classify_incidents",
            "Correlate failures and classify severity.",
            "Each incident has an evidence-based hypothesis.",
        ),
        (
            "plan_bounded_recovery",
            "Select retry, failover, pause, or escalation within budget.",
            "Recovery actions are bounded and duplicate-safe.",
        ),
        (
            "verify_and_report_reliability",
            "Verify integrity and persist incident outcomes.",
            "Operational reliability has an explainable state.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._observe(input_data)
        self._correlate(input_data)
        self._recover(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "observe_operational_signals": lambda: self._observe(input_data),
            "correlate_and_classify_incidents": lambda: self._correlate(input_data),
            "plan_bounded_recovery": lambda: self._recover(input_data),
            "verify_and_report_reliability": lambda: self._complete(input_data),
        }

    def _observe(self, input_data):
        unhealthy = [item for item in input_data.telemetry if item.status != "healthy"]
        self._state["unhealthy"] = unhealthy
        return {"status": "completed", "unhealthy_signals": len(unhealthy)}

    def _correlate(self, input_data):
        incidents, retries, failovers, paused = analyze_telemetry(
            input_data.telemetry, input_data.retry_budget
        )
        self._state.update(
            incidents=incidents, retries=retries, failovers=failovers, paused=paused
        )
        return {"status": "completed", "incidents": len(incidents)}

    def _recover(self, input_data):
        unresolved = [
            incident
            for incident in self._state["incidents"]
            if incident.recovery_action in {"pause", "human_escalation"}
        ]
        self._state["unresolved"] = unresolved
        return {
            "status": "completed_with_warnings" if unresolved else "completed",
            "unresolved": len(unresolved),
        }

    def _complete(self, input_data):
        incidents = self._state["incidents"]
        unresolved = self._state["unresolved"]
        integrity = all(item.integrity_verified for item in incidents)
        status = (
            "blocked"
            if any(item.severity == "critical" for item in unresolved)
            else "incident"
            if unresolved
            else "degraded"
            if incidents
            else "healthy"
        )
        result = ReliabilityResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if incidents else "completed",
            input_count=len(input_data.telemetry),
            success_count=len(input_data.telemetry) - len(self._state["unhealthy"]),
            warning_count=len(incidents),
            warnings=[incident.hypothesis for incident in unresolved],
            reliability_status=status,
            incidents=incidents,
            retries_authorized=self._state["retries"],
            failovers_authorized=self._state["failovers"],
            paused_sources=self._state["paused"],
            data_integrity_verified=integrity,
        )
        result = self._persist(result)
        for incident in incidents:
            JsonEventRepository().append(
                run_id=result.run_id,
                event_type="OperationalIncidentRecorded",
                aggregate_type="incident",
                aggregate_id=incident.incident_id,
                actor=self.agent_name,
                payload=incident.model_dump(mode="json"),
            )
        return result

