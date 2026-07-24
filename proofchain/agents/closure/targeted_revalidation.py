"""Targeted revalidation specialist module."""

from __future__ import annotations

from proofchain.schemas.integrity import IntegrityFinding
from proofchain.schemas.issues import CanonicalIssue


class TargetedRevalidationSpecialist:
    specialist_name = "targeted_revalidation"

    def run(
        self, issues: list[CanonicalIssue], findings: list[IntegrityFinding]
    ) -> dict[str, bool]:
        finding_ids = {finding.finding_id for finding in findings if finding.blocking}
        return {
            issue.issue_id: not bool(set(issue.source_finding_ids) & finding_ids)
            for issue in issues
        }
