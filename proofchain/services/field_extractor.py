"""Source-backed deterministic field extraction."""

from __future__ import annotations

import re
from typing import Any

from proofchain.schemas.classification import ExtractedField, ExtractionResult
from proofchain.schemas.evidence import EvidenceRecord


class FieldExtractor:
    LABELS = {
        "Event ID": "event_id",
        "Accreditation Requirement": "requirement_id",
        "Mapped Requirement": "mapped_requirement_id",
        "Department": "department",
        "Academic Year": "academic_year",
        "Event Title": "event_title",
        "Event Date": "event_date",
        "Coordinator": "coordinator",
        "Reported Participant Count": "reported_participant_count",
        "Signature Present": "signature_present",
        "Approval Status": "approval_status",
        "Approval Number": "approval_number",
        "Reference Number": "reference_number",
    }

    def extract(
        self,
        evidence: EvidenceRecord,
        extraction: ExtractionResult,
    ) -> dict[str, ExtractedField]:
        fields = self._from_text(evidence, extraction)
        if extraction.tables and evidence.file_extension in {".xlsx", ".csv"}:
            fields.update(self._from_spreadsheet(evidence, extraction))

        event_match = re.search(r"EVT-[A-Z]+-\d+", evidence.original_filename, re.IGNORECASE)
        if event_match and "event_id" not in fields:
            fields["event_id"] = ExtractedField(
                field_name="event_id",
                raw_value=event_match.group(0),
                normalized_value=event_match.group(0).upper(),
                confidence=0.95,
                extraction_method="filename_regex",
            )
        if "department" not in fields:
            fields["department"] = ExtractedField(
                field_name="department",
                raw_value=evidence.department,
                normalized_value=evidence.department,
                confidence=0.9,
                extraction_method="collector_metadata",
            )
        return fields

    def _from_text(
        self,
        evidence: EvidenceRecord,
        extraction: ExtractionResult,
    ) -> dict[str, ExtractedField]:
        text = extraction.text or ""
        fields: dict[str, ExtractedField] = {}
        for label, field_name in self.LABELS.items():
            pattern = re.compile(
                rf"(?im)^\s*{re.escape(label)}\s+(?:\|\s*)?(.+?)\s*$"
            )
            match = pattern.search(text)
            if not match:
                continue
            raw = match.group(1).strip().strip("|").strip()
            normalized: str | int | float | bool | None = raw
            if field_name == "reported_participant_count":
                number = re.search(r"\d+", raw)
                normalized = int(number.group(0)) if number else raw
            fields[field_name] = ExtractedField(
                field_name=field_name,
                raw_value=raw,
                normalized_value=normalized,
                confidence=0.96,
                page_number=1,
                extraction_method="label_regex",
            )
        return fields

    def _from_spreadsheet(
        self,
        evidence: EvidenceRecord,
        extraction: ExtractionResult,
    ) -> dict[str, ExtractedField]:
        fields: dict[str, ExtractedField] = {}
        table = extraction.tables[0]
        rows: list[list[Any]] = table.get("rows", [])
        if not rows:
            return fields

        header_index = next(
            (
                index
                for index, row in enumerate(rows)
                if any(str(cell).casefold() == "roll number" for cell in row if cell is not None)
            ),
            None,
        )
        if header_index is None:
            return fields
        headers = [str(value).strip() if value is not None else "" for value in rows[header_index]]
        records = [
            {headers[index]: value for index, value in enumerate(row) if index < len(headers)}
            for row in rows[header_index + 1 :]
            if any(value is not None and str(value).strip() for value in row)
        ]
        roll_key = next((header for header in headers if header.casefold() == "roll number"), None)
        roll_numbers = [
            str(record.get(roll_key)).strip()
            for record in records
            if roll_key and record.get(roll_key) not in (None, "")
        ]
        duplicates = sorted({value for value in roll_numbers if roll_numbers.count(value) > 1})
        first = records[0] if records else {}
        mapping = {
            "Event ID": "event_id",
            "Event Title": "event_title",
            "Department": "department",
            "Academic Year": "academic_year",
            "Event Date": "event_date",
        }
        for source_name, field_name in mapping.items():
            value = first.get(source_name)
            if value is not None:
                fields[field_name] = ExtractedField(
                    field_name=field_name,
                    raw_value=str(value),
                    normalized_value=str(value),
                    confidence=0.98,
                    sheet_name=table.get("sheet_name"),
                    cell_range=f"{source_name}:{source_name}",
                    extraction_method="spreadsheet_column",
                )
        fields["attendance_rows"] = ExtractedField(
            field_name="attendance_rows",
            normalized_value=len(roll_numbers),
            raw_value=str(len(roll_numbers)),
            confidence=0.99,
            sheet_name=table.get("sheet_name"),
            extraction_method="row_count",
        )
        fields["unique_student_count"] = ExtractedField(
            field_name="unique_student_count",
            normalized_value=len(set(roll_numbers)),
            raw_value=str(len(set(roll_numbers))),
            confidence=0.99,
            sheet_name=table.get("sheet_name"),
            extraction_method="distinct_count",
        )
        fields["duplicate_roll_numbers"] = ExtractedField(
            field_name="duplicate_roll_numbers",
            normalized_value=",".join(duplicates),
            raw_value=",".join(duplicates),
            confidence=0.99,
            sheet_name=table.get("sheet_name"),
            extraction_method="duplicate_scan",
        )
        return fields
