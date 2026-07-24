"""Duplicate and reuse audit specialist module."""

from __future__ import annotations

from proofchain.schemas.packages import AuditPackageManifest


class ReuseAuditSpecialist:
    specialist_name = "reuse_audit"

    def run(self, manifest: AuditPackageManifest) -> int:
        hashes = [item.sha256 for item in manifest.eligible_evidence]
        return len(hashes) - len(set(hashes))
