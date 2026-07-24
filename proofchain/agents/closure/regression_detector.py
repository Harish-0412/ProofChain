"""Regression detection specialist module."""

from __future__ import annotations

from proofchain.schemas.closure import ClosureCheck


class RegressionDetectorSpecialist:
    specialist_name = "regression_detector"

    def run(self, checks: list[ClosureCheck]) -> list[str]:
        return [
            check.issue_id
            for check in checks
            if check.evidence_submitted and not check.integrity_rules_passed
        ]
