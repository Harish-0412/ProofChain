"""Checksum-based exact duplicate grouping."""

from __future__ import annotations

from collections import defaultdict

from proofchain.schemas.classification import ClassifiedEvidence


class DuplicateDetector:
    def exact_groups(
        self, records: list[ClassifiedEvidence]
    ) -> list[list[ClassifiedEvidence]]:
        grouped: dict[str, list[ClassifiedEvidence]] = defaultdict(list)
        for record in records:
            grouped[record.sha256_checksum].append(record)
        return [
            sorted(items, key=lambda item: item.evidence_id)
            for _, items in sorted(grouped.items())
            if len(items) > 1
        ]
