"""Detect instruction-like content without treating document text as instructions."""

from __future__ import annotations

from hashlib import sha256
from typing import Iterable

from proofchain.schemas.classification import ClassifiedEvidence


class UntrustedContentScanner:
    def __init__(self, patterns: Iterable[dict]):
        self.patterns = [dict(item) for item in patterns]

    def scan(self, records: list[ClassifiedEvidence]) -> list[dict]:
        findings: list[dict] = []
        for record in records:
            text_parts = [record.extraction.text or ""]
            for table in record.extraction.tables:
                for row in table.get("rows", []):
                    text_parts.extend(str(value) for value in row if value is not None)
            content = "\n".join(text_parts)
            normalized = content.casefold()
            for pattern in self.patterns:
                expression = str(pattern.get("expression", "")).casefold()
                if expression and expression in normalized:
                    findings.append(
                        {
                            "finding_id": (
                                f"PIF-{record.evidence_id}-"
                                f"{str(pattern['pattern_id']).upper()}"
                            ),
                            "evidence_id": record.evidence_id,
                            "pattern_id": pattern["pattern_id"],
                            "severity": pattern.get("severity", "high"),
                            "content_sha256": sha256(content.encode("utf-8")).hexdigest(),
                            "action": "quarantine_instruction_and_record_finding",
                            "content_executed": False,
                        }
                    )
        return findings
