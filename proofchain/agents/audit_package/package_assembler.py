"""Package assembly specialist module."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

from proofchain.core.paths import get_audit_package_bundle_path
from proofchain.repositories.json_store import jsonable
from proofchain.repositories.json_store import file_sha256
from proofchain.schemas.packages import AuditPackageManifest


class PackageAssemblySpecialist:
    specialist_name = "package_assembly"

    def run(self, manifest: AuditPackageManifest) -> AuditPackageManifest:
        logical_payload = jsonable(
            manifest.model_dump(
                exclude={
                    "package_hash",
                    "bundle_path",
                    "bundle_sha256",
                    "bundle_format",
                    "bundle_contains_original_evidence",
                    "external_submission_approved",
                    "generated_at",
                }
            )
        )
        payload = json.dumps(
            logical_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        package_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        bundle_path = get_audit_package_bundle_path(manifest.run_id)
        self._write_bundle(
            manifest=manifest,
            logical_payload=logical_payload,
            package_hash=package_hash,
            destination=bundle_path,
        )
        return manifest.model_copy(
            update={
                "package_hash": package_hash,
                "bundle_path": str(bundle_path.resolve()),
                "bundle_sha256": file_sha256(bundle_path),
                "bundle_format": "zip",
                "bundle_contains_original_evidence": True,
                "external_submission_approved": False,
            }
        )

    def _write_bundle(
        self,
        *,
        manifest: AuditPackageManifest,
        logical_payload: dict,
        package_hash: str,
        destination: Path,
    ) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
        )
        os.close(descriptor)
        try:
            with zipfile.ZipFile(
                temporary_name,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            ) as archive:
                bundle_manifest = {
                    **logical_payload,
                    "package_hash": package_hash,
                    "bundle_classification": "INTERNAL_DRAFT",
                    "external_submission_approved": False,
                    "generated_narrative_is_evidence": False,
                }
                self._write_entry(
                    archive,
                    "package_manifest.json",
                    json.dumps(
                        bundle_manifest,
                        ensure_ascii=True,
                        indent=2,
                        sort_keys=True,
                    ).encode("utf-8"),
                )
                self._write_entry(
                    archive,
                    "claim_evidence_index.json",
                    json.dumps(
                        manifest.package_lineage,
                        ensure_ascii=True,
                        indent=2,
                        sort_keys=True,
                    ).encode("utf-8"),
                )
                self._write_entry(
                    archive,
                    "unresolved_issues.json",
                    json.dumps(
                        manifest.unresolved_warning_issue_ids,
                        ensure_ascii=True,
                        indent=2,
                        sort_keys=True,
                    ).encode("utf-8"),
                )
                self._write_entry(
                    archive,
                    "evidence_index.csv",
                    self._csv_index(manifest).encode("utf-8"),
                )
                for item in sorted(
                    manifest.eligible_evidence, key=lambda value: value.evidence_id
                ):
                    source = Path(item.source_path)
                    if not source.is_file():
                        continue
                    safe_name = "".join(
                        character
                        if character.isalnum() or character in {".", "_", "-"}
                        else "_"
                        for character in source.name
                    )
                    self._write_entry(
                        archive,
                        f"evidence/{item.evidence_id}/{safe_name}",
                        source.read_bytes(),
                    )
            os.replace(temporary_name, destination)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    @staticmethod
    def _write_entry(
        archive: zipfile.ZipFile,
        archive_name: str,
        content: bytes,
    ) -> None:
        entry = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.create_system = 3
        entry.external_attr = 0o600 << 16
        archive.writestr(entry, content, compresslevel=9)

    @staticmethod
    def _csv_index(manifest: AuditPackageManifest) -> str:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(
            ["evidence_id", "sha256", "included", "reason", "source_filename"]
        )
        for item in sorted(
            [*manifest.eligible_evidence, *manifest.excluded_evidence],
            key=lambda value: value.evidence_id,
        ):
            writer.writerow(
                [
                    item.evidence_id,
                    item.sha256,
                    str(item.included).lower(),
                    item.reason,
                    Path(item.source_path).name,
                ]
            )
        return buffer.getvalue()
