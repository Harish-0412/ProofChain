"""Pre-plan input validation with explicit recovery routing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from proofchain.schemas.agentic import Goal
from proofchain.schemas.input_validation import InputCheck, InputValidationResult


class PrePlanInputValidator:
    def validate(
        self,
        goal: Goal,
        input_data: Any,
        *,
        deterministic_error: Exception | None = None,
    ) -> InputValidationResult:
        checks: list[InputCheck] = []
        missing: list[str] = []
        stale: list[str] = []
        conflicts: list[str] = []
        unauthorized: list[str] = []

        checks.append(
            InputCheck(
                check_name="deterministic_input_contract",
                status="failed" if deterministic_error else "passed",
                explanation=str(deterministic_error)
                if deterministic_error
                else "The agent-specific input contract accepted the payload.",
            )
        )
        for reference in goal.input_references:
            if self._is_path_reference(reference):
                exists = Path(reference).expanduser().exists()
                checks.append(
                    InputCheck(
                        check_name="artifact_exists",
                        status="passed" if exists else "failed",
                        reference=reference,
                        explanation="Referenced artifact is available."
                        if exists
                        else "Referenced artifact is missing.",
                    )
                )
                if not exists:
                    missing.append(reference)

        schema_version = getattr(input_data, "schema_version", None)
        checks.append(
            InputCheck(
                check_name="schema_version_supported",
                status="passed" if schema_version in {None, "1.0.0"} else "failed",
                reference=str(schema_version) if schema_version else None,
                explanation="Input schema version is supported."
                if schema_version in {None, "1.0.0"}
                else f"Unsupported input schema version: {schema_version}.",
            )
        )
        workflow_run = getattr(getattr(input_data, "workflow", None), "run_id", None)
        run_matches = workflow_run in {None, goal.run_id}
        checks.append(
            InputCheck(
                check_name="run_scope_matches",
                status="passed" if run_matches else "failed",
                reference=workflow_run,
                explanation="Input belongs to the current run."
                if run_matches
                else "Input belongs to another run.",
            )
        )
        if not run_matches:
            unauthorized.append(str(workflow_run))

        valid = deterministic_error is None and not missing and not conflicts
        authorized = not unauthorized
        complete = not missing
        recoverable = bool(missing) and deterministic_error is None
        recommended = (
            "continue"
            if valid and authorized
            else "request_human"
            if not authorized
            else "request_peer"
            if recoverable
            else "block"
        )
        return InputValidationResult(
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            valid=valid and authorized,
            complete=complete,
            authorized=authorized,
            current=not stale,
            checks=checks,
            missing_inputs=missing,
            stale_inputs=stale,
            conflicting_inputs=conflicts,
            unauthorized_inputs=unauthorized,
            recoverable=recoverable,
            recommended_action=recommended,
        )

    @staticmethod
    def _is_path_reference(reference: str) -> bool:
        return (
            Path(reference).is_absolute()
            or "/" in reference
            or "\\" in reference
        )
