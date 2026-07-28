"""Stable evidence identity plus run-scoped evidence registry persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from proofchain.core.enums import DuplicateStatus, IngestionStatus, SourceType
from proofchain.core.ids import generate_evidence_id, generate_version_id
from proofchain.core.paths import get_evidence_registry_path, get_global_evidence_index_path
from proofchain.repositories.json_artifact_repository import JsonArtifactRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.common import ArtifactReference
from proofchain.schemas.evidence import EvidenceRecord


class JsonEvidenceRepository:
    """Assigns durable IDs by canonical source path and tracks content versions."""

    def __init__(
        self,
        index_path: Path | None = None,
        store: AtomicJsonStore | None = None,
    ):
        self.store = store or AtomicJsonStore()
        self.index_path = index_path or get_global_evidence_index_path()
        raw = self.store.read(
            self.index_path,
            default={"schema_version": "1.0.0", "records_by_path": {}},
        )
        self._records_by_path: dict[str, dict[str, Any]] = raw.get("records_by_path", {})

    @staticmethod
    def _path_key(path: Path) -> str:
        return str(path.resolve()).replace("\\", "/").casefold()

    def _next_sequence(self, department: str, academic_year: str) -> int:
        prefix = f"EVD-{department.upper()}-{academic_year}-"
        sequences = [
            int(record["evidence_id"].split("-")[-1])
            for record in self._records_by_path.values()
            if str(record.get("evidence_id", "")).startswith(prefix)
        ]
        return max(sequences, default=0) + 1

    def register(
        self,
        *,
        path: Path,
        project_root: Path,
        department: str,
        academic_year: str,
        sha256_checksum: str,
        mime_type: str,
        file_size_bytes: int,
        created_at: datetime | None,
        modified_at: datetime | None,
        run_id: str,
        agent_run_id: str,
        ingestion_status: IngestionStatus = IngestionStatus.REGISTERED,
        processing_capability: str = "native_extraction",
        capability_reason: str | None = None,
    ) -> EvidenceRecord:
        key = self._path_key(path)
        previous = self._records_by_path.get(key)

        if previous:
            evidence_id = previous["evidence_id"]
            if previous.get("sha256_checksum") == sha256_checksum:
                version_number = int(previous.get("version_number", 1))
            else:
                version_number = int(previous.get("version_number", 1)) + 1
        else:
            sequence = self._next_sequence(department, academic_year)
            evidence_id = generate_evidence_id(department, academic_year, sequence)
            version_number = 1

        duplicate_owner = None
        if previous and previous.get("sha256_checksum") == sha256_checksum:
            owner_id = previous.get("duplicate_of_evidence_id")
            if owner_id:
                duplicate_owner = next(
                    (
                        record
                        for record in self._records_by_path.values()
                        if record.get("evidence_id") == owner_id
                    ),
                    {"evidence_id": owner_id},
                )
        else:
            duplicate_owner = next(
                (
                    record
                    for record_key, record in sorted(self._records_by_path.items())
                    if record_key != key
                    and record.get("sha256_checksum") == sha256_checksum
                    and not record.get("duplicate_of_evidence_id")
                ),
                None,
            )
        duplicate_status = (
            DuplicateStatus.EXACT_DUPLICATE if duplicate_owner else DuplicateStatus.UNIQUE
        )
        try:
            relative_path = str(path.resolve().relative_to(project_root.resolve()))
        except ValueError:
            relative_path = path.name

        record = EvidenceRecord(
            evidence_id=evidence_id,
            version_id=generate_version_id(evidence_id, version_number),
            version_number=version_number,
            department=department,
            academic_year=academic_year,
            original_filename=path.name,
            relative_path=relative_path,
            absolute_path=str(path.resolve()),
            file_extension=path.suffix.lower(),
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            sha256_checksum=sha256_checksum,
            created_at=created_at,
            modified_at=modified_at,
            ingestion_status=(
                IngestionStatus.DUPLICATE_DETECTED
                if duplicate_owner and ingestion_status == IngestionStatus.REGISTERED
                else ingestion_status
            ),
            processing_capability=processing_capability,
            capability_reason=capability_reason,
            duplicate_status=duplicate_status,
            duplicate_of_evidence_id=duplicate_owner.get("evidence_id")
            if duplicate_owner
            else None,
            source_type=SourceType.DEPARTMENT_FOLDER,
            discovered_at=datetime.now(tz=timezone.utc),
            run_id=run_id,
            agent_run_id=agent_run_id,
        )
        self._records_by_path[key] = record.model_dump(mode="json")
        return record

    def commit_index(self) -> None:
        self.store.write(
            self.index_path,
            {
                "schema_version": "1.0.0",
                "records_by_path": self._records_by_path,
            },
        )

    def save_run_records(
        self,
        run_id: str,
        records: list[EvidenceRecord],
        agent_run_id: str,
    ) -> ArtifactReference:
        self.commit_index()
        return JsonArtifactRepository(self.store).save(
            get_evidence_registry_path(run_id),
            records,
            stage_name="collection",
            record_count=len(records),
            agent_run_id=agent_run_id,
        )
