"""Agent 15: evidence safety inspection, restriction, and quarantine."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.production import SecurityInput, SecurityResult
from proofchain.services.security_inspection import inspect_evidence


DECISION_RANK = {
    "ALLOW": 0,
    "ALLOW_WITH_RESTRICTIONS": 1,
    "REDACT_DERIVATIVE_REQUIRED": 2,
    "NEEDS_SECURITY_REVIEW": 3,
    "QUARANTINE": 4,
    "REJECT": 5,
}


class SecurityInspectionAgent(ProductionGoalAgent[SecurityInput, SecurityResult]):
    agent_name = "security_inspection"
    agent_version = "1.0.0"
    expected_artifact = "phase_one_security_report.json"
    tool_specs = (
        (
            "verify_evidence_identity",
            "Resolve evidence paths, sizes, MIME indicators, and hashes.",
            "Every evidence reference has a stable identity.",
        ),
        (
            "inspect_evidence_safety",
            "Inspect malware signatures, archives, spreadsheets, injection, and PII.",
            "Every evidence item has a security decision.",
        ),
        (
            "apply_quarantine_policy",
            "Create non-destructive quarantine copies and downstream restrictions.",
            "Unsafe evidence is excluded from ordinary processing.",
        ),
        (
            "persist_security_decision",
            "Persist security decisions and downstream instructions.",
            "Downstream agents receive an explicit safety boundary.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._identity(input_data)
        self._inspect(input_data)
        self._quarantine(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "verify_evidence_identity": lambda: self._identity(input_data),
            "inspect_evidence_safety": lambda: self._inspect(input_data),
            "apply_quarantine_policy": lambda: self._quarantine(input_data),
            "persist_security_decision": lambda: self._complete(input_data),
        }

    def _identity(self, input_data):
        return {"status": "completed", "evidence_count": len(input_data.evidence_paths)}

    def _inspect(self, input_data):
        findings = inspect_evidence(input_data)
        self._state["findings"] = findings
        return {"status": "completed", "findings": len(findings)}

    def _quarantine(self, input_data):
        quarantined = [
            item.quarantine_reference
            for item in self._state["findings"]
            if item.quarantine_reference
        ]
        self._state["quarantined"] = quarantined
        return {"status": "completed", "quarantined": len(quarantined)}

    def _complete(self, input_data):
        findings = self._state["findings"]
        overall = max(
            (item.decision for item in findings),
            key=lambda item: DECISION_RANK[item],
            default="ALLOW",
        )
        allowed = [
            item.path
            for item in findings
            if item.decision in {
                "ALLOW",
                "ALLOW_WITH_RESTRICTIONS",
                "REDACT_DERIVATIVE_REQUIRED",
            }
        ]
        blocked = [
            item for item in findings if item.decision in {"QUARANTINE", "REJECT"}
        ]
        restricted = [
            item for item in findings if item.decision != "ALLOW"
        ]
        result = SecurityResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if restricted else "completed",
            input_count=len(findings),
            success_count=len(allowed),
            warning_count=len(restricted),
            failure_count=0,
            warnings=[
                f"{item.path}: {item.decision}" for item in restricted
            ],
            overall_decision=overall,
            evidence_findings=findings,
            allowed_paths=allowed,
            quarantined_paths=self._state["quarantined"],
        )
        result = self._persist(result)
        for item in blocked:
            JsonEventRepository().append(
                run_id=result.run_id,
                event_type="EvidenceQuarantined"
                if item.decision == "QUARANTINE"
                else "EvidenceRejected",
                aggregate_type="evidence",
                aggregate_id=item.sha256 or item.path,
                actor=self.agent_name,
                payload={"path": item.path, "findings": item.findings},
            )
        return result

