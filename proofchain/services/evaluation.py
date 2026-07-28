"""Golden-scenario metrics and release regression gates."""

from __future__ import annotations

from proofchain.schemas.institutional import EvaluationInput


def calculate_evaluation_metrics(
    request: EvaluationInput,
) -> tuple[float, float, float, float, list[str]]:
    total = len(request.scenarios)
    if total == 0:
        return 0.0, 0.0, 0.0, 1.0, ["No evaluation scenarios were supplied."]
    correct = sum(
        item.expected_decision == item.observed_decision
        for item in request.scenarios
    )
    false_approvals = sum(
        item.observed_decision in {"approved", "pass", "closed"}
        and item.expected_decision in {"blocked", "rejected", "open"}
        for item in request.scenarios
    )
    false_closures = sum(
        item.observed_decision == "closed"
        and item.expected_decision != "closed"
        for item in request.scenarios
    )
    calibration_values = [
        abs(
            (1.0 if item.expected_decision == item.observed_decision else 0.0)
            - item.observed_confidence
        )
        for item in request.scenarios
        if item.observed_confidence is not None
    ]
    accuracy = correct / total
    false_approval_rate = false_approvals / total
    false_closure_rate = false_closures / total
    calibration_error = (
        sum(calibration_values) / len(calibration_values)
        if calibration_values
        else 0.0
    )
    findings: list[str] = []
    if accuracy < request.thresholds.minimum_accuracy:
        findings.append("Accuracy is below the release threshold.")
    if false_approval_rate > request.thresholds.maximum_false_approval_rate:
        findings.append("False approval rate exceeds the release threshold.")
    if false_closure_rate > request.thresholds.maximum_false_closure_rate:
        findings.append("False closure rate exceeds the release threshold.")
    baseline_accuracy = request.baseline_metrics.get("accuracy")
    if (
        baseline_accuracy is not None
        and baseline_accuracy - accuracy
        > request.thresholds.maximum_accuracy_regression
    ):
        findings.append("Accuracy regression exceeds the permitted release delta.")
    return (
        accuracy,
        false_approval_rate,
        false_closure_rate,
        calibration_error,
        findings,
    )


def calculate_category_accuracy(request: EvaluationInput) -> dict[str, float]:
    grouped: dict[str, list[bool]] = {}
    for item in request.scenarios:
        grouped.setdefault(item.category, []).append(
            item.expected_decision == item.observed_decision
        )
    return {
        category: round(sum(results) / len(results), 4)
        for category, results in sorted(grouped.items())
    }
