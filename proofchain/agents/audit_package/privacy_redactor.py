"""Privacy and redaction policy specialist module."""

from __future__ import annotations

from proofchain.schemas.packages import PackageEvidenceItem


class PrivacyRedactionSpecialist:
    specialist_name = "privacy_redaction"

    def run(self, items: list[PackageEvidenceItem]) -> list[PackageEvidenceItem]:
        return items
