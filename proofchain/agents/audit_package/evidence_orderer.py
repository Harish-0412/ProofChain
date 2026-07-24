"""Evidence ordering specialist module."""

from __future__ import annotations

from proofchain.schemas.packages import PackageEvidenceItem


class EvidenceOrderingSpecialist:
    specialist_name = "evidence_ordering"

    def run(self, items: list[PackageEvidenceItem]) -> list[PackageEvidenceItem]:
        return sorted(items, key=lambda item: item.evidence_id)
