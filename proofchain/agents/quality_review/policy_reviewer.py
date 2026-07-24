"""Package policy compliance specialist module."""

from __future__ import annotations

from proofchain.schemas.packages import AuditPackageManifest


class PolicyComplianceReviewer:
    specialist_name = "policy_compliance"

    def run(self, manifest: AuditPackageManifest) -> list[str]:
        findings = []
        if manifest.unresolved_warning_issue_ids:
            findings.append("Unresolved issues are disclosed and require reviewer attention.")
        if any(item.included is False for item in manifest.eligible_evidence):
            findings.append("Ineligible evidence appears in eligible list.")
        return findings
