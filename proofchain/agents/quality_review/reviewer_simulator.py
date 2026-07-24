"""Reviewer journey simulation specialist module."""

from __future__ import annotations

from proofchain.schemas.packages import AuditPackageManifest


class ReviewerSimulationSpecialist:
    specialist_name = "reviewer_simulation"

    def run(self, manifest: AuditPackageManifest, broken_references: int) -> float:
        base = 20.0
        base += broken_references * 20.0
        base += len(manifest.unresolved_warning_issue_ids) * 3.0
        base += max(0, len(manifest.claim_ids) - len(manifest.package_lineage)) * 10.0
        return min(100.0, round(base, 2))
