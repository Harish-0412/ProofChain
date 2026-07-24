"""Evidence selection specialist module."""

from __future__ import annotations

from proofchain.schemas.evidence import EvidenceRecord
from proofchain.schemas.packages import PackageEvidenceItem


class EvidenceSelectionSpecialist:
    specialist_name = "evidence_selection"

    def run(self, evidence_records: list[EvidenceRecord]) -> tuple[list[PackageEvidenceItem], list[PackageEvidenceItem]]:
        eligible = []
        excluded = []
        seen_hashes = set()
        for record in evidence_records:
            item = PackageEvidenceItem(
                evidence_id=record.evidence_id,
                source_path=record.absolute_path,
                sha256=record.sha256_checksum,
                included=record.sha256_checksum not in seen_hashes,
                reason="current registered evidence" if record.sha256_checksum not in seen_hashes else "duplicate content excluded",
            )
            if item.included:
                eligible.append(item)
                seen_hashes.add(record.sha256_checksum)
            else:
                excluded.append(item)
        return eligible, excluded
