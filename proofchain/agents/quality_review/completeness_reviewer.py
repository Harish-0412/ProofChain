"""Package completeness specialist module."""

from __future__ import annotations

from proofchain.schemas.packages import AuditPackageManifest


class PackageCompletenessReviewer:
    specialist_name = "package_completeness"

    def run(self, manifest: AuditPackageManifest) -> list[str]:
        missing = []
        if not manifest.eligible_evidence:
            missing.append("No eligible evidence is included.")
        if not manifest.claim_ids:
            missing.append("No claim references are included.")
        if not manifest.package_hash:
            missing.append("Package hash is missing.")
        return missing
