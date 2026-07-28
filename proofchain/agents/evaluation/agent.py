"""Agent 21: golden-scenario evaluation and release regression governance."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.institutional import EvaluationInput, EvaluationResult
from proofchain.services.evaluation import (
    calculate_category_accuracy,
    calculate_evaluation_metrics,
)


class ContinuousEvaluationAgent(
    ProductionGoalAgent[EvaluationInput, EvaluationResult]
):
    agent_name = "continuous_evaluation"
    agent_version = "1.0.0"
    expected_artifact = "continuous_evaluation_report.json"
    tool_specs = (
        (
            "resolve_evaluation_dataset",
            "Resolve the golden scenario set and release identity.",
            "Required scenarios are present.",
        ),
        (
            "plan_release_evaluation",
            "Bind metrics and thresholds to the release goal.",
            "Release gates are explicit before execution.",
        ),
        (
            "run_golden_scenarios",
            "Compare observed decisions with expected governed decisions.",
            "Every scenario has a reproducible outcome.",
        ),
        (
            "calculate_assurance_metrics",
            "Calculate accuracy, false approvals, false closures, and calibration.",
            "Quality and governance metrics are available.",
        ),
        (
            "detect_release_regression",
            "Compare metrics with baseline and thresholds.",
            "Unsafe regression is identified.",
        ),
        (
            "gate_release",
            "Pass, block, or route the release for human review.",
            "An explainable release decision is persisted.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._resolve(input_data)
        self._plan(input_data)
        self._run(input_data)
        self._metrics(input_data)
        self._regression(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "resolve_evaluation_dataset": lambda: self._resolve(input_data),
            "plan_release_evaluation": lambda: self._plan(input_data),
            "run_golden_scenarios": lambda: self._run(input_data),
            "calculate_assurance_metrics": lambda: self._metrics(input_data),
            "detect_release_regression": lambda: self._regression(input_data),
            "gate_release": lambda: self._complete(input_data),
        }

    def _resolve(self, input_data):
        return {"status": "completed", "scenario_count": len(input_data.scenarios)}

    def _plan(self, input_data):
        return {
            "status": "completed",
            "minimum_accuracy": input_data.thresholds.minimum_accuracy,
        }

    def _run(self, input_data):
        passed = sum(
            item.expected_decision == item.observed_decision
            for item in input_data.scenarios
        )
        self._state["passed"] = passed
        return {"status": "completed", "passed": passed}

    def _metrics(self, input_data):
        metrics = calculate_evaluation_metrics(input_data)
        self._state["metrics"] = metrics
        return {
            "status": "completed_with_warnings" if metrics[4] else "completed",
            "accuracy": metrics[0],
        }

    def _regression(self, input_data):
        return {
            "status": "completed_with_warnings" if self._state["metrics"][4] else "completed",
            "findings": self._state["metrics"][4],
        }

    def _complete(self, input_data):
        accuracy, false_approval, false_closure, calibration, findings = self._state[
            "metrics"
        ]
        decision = "BLOCK" if findings else "PASS"
        result = EvaluationResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if findings else "completed",
            input_count=len(input_data.scenarios),
            success_count=self._state["passed"],
            warning_count=len(findings),
            warnings=findings,
            release_id=input_data.release_id,
            scenario_count=len(input_data.scenarios),
            accuracy=accuracy,
            false_approval_rate=false_approval,
            false_closure_rate=false_closure,
            calibration_error=calibration,
            regression_findings=findings,
            release_decision=decision,
            scenarios=input_data.scenarios,
            failed_scenario_ids=[
                item.scenario_id
                for item in input_data.scenarios
                if item.expected_decision != item.observed_decision
            ],
            category_accuracy=calculate_category_accuracy(input_data),
        )
        result = self._persist(result)
        JsonEventRepository().append(
            run_id=result.run_id,
            event_type="ReleaseEvaluationCompleted",
            aggregate_type="release",
            aggregate_id=input_data.release_id,
            actor=self.agent_name,
            payload={
                "release_decision": decision,
                "accuracy": accuracy,
                "false_approval_rate": false_approval,
                "false_closure_rate": false_closure,
            },
        )
        return result
