"""Reference resolution specialist module."""

from __future__ import annotations

from pathlib import Path

from proofchain.schemas.packages import AuditPackageManifest


class ReferenceResolutionReviewer:
    specialist_name = "reference_resolution"

    def run(self, manifest: AuditPackageManifest) -> int:
        return sum(
            1 for item in manifest.eligible_evidence if not Path(item.source_path).exists()
        )
