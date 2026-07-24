"""Package integrity specialist module."""

from __future__ import annotations

from pathlib import Path

from proofchain.repositories.json_store import file_sha256
from proofchain.schemas.packages import AuditPackageManifest


class PackageIntegritySpecialist:
    specialist_name = "package_integrity"

    def run(self, manifest: AuditPackageManifest) -> list[str]:
        errors = []
        for item in manifest.eligible_evidence:
            if not Path(item.source_path).exists():
                errors.append(f"Missing package evidence: {item.evidence_id}")
        for claim_id, evidence_ids in manifest.package_lineage.items():
            if not evidence_ids:
                errors.append(f"Claim {claim_id} has no package evidence references.")
        if not manifest.bundle_path:
            errors.append("Internal audit package bundle was not generated.")
        else:
            bundle_path = Path(manifest.bundle_path)
            if not bundle_path.exists():
                errors.append("Internal audit package bundle is missing.")
            elif manifest.bundle_sha256 != file_sha256(bundle_path):
                errors.append("Internal audit package bundle checksum does not match.")
        if manifest.external_submission_approved:
            errors.append("Draft package cannot self-authorize external submission.")
        return errors
