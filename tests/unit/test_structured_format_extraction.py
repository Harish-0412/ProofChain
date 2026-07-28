from __future__ import annotations

import json
from pathlib import Path

from proofchain.core.enums import ExtractionStatus
from proofchain.schemas.evidence import EvidenceRecord
from proofchain.services.document_extractor import DocumentExtractionService
from proofchain.services.field_extractor import FieldExtractor


def evidence(path: Path) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id="EVD-AIML-2025-2026-00001",
        version_id="VER-00001-01",
        department="AIML",
        academic_year="2025-2026",
        original_filename=path.name,
        relative_path=path.name,
        absolute_path=str(path),
        file_extension=path.suffix,
        mime_type="application/octet-stream",
        file_size_bytes=path.stat().st_size,
        sha256_checksum="0" * 64,
    )


def test_json_fields_remain_extractable(tmp_path: Path) -> None:
    path = tmp_path / "EVT-AIML-001_C3.2.1_event_report.json"
    path.write_text(
        json.dumps(
            {
                "Event ID": "EVT-AIML-001",
                "Department": "AIML",
                "Academic Year": "2025-2026",
                "Event Title": "Industry Workshop",
                "Reported Participant Count": 30,
            }
        ),
        encoding="utf-8",
    )

    extraction = DocumentExtractionService().extract(path, "EVD-JSON")
    fields = FieldExtractor().extract(evidence(path), extraction)

    assert extraction.extraction_status == ExtractionStatus.SUCCESS
    assert fields["event_id"].normalized_value == "EVT-AIML-001"
    assert fields["department"].normalized_value == "AIML"
    assert fields["reported_participant_count"].normalized_value == 30


def test_xml_fields_use_display_labels(tmp_path: Path) -> None:
    path = tmp_path / "EVT-AIDS-001_C3.2.1_event_report.xml"
    path.write_text(
        """
        <proofchain_evidence>
          <event_id>EVT-AIDS-001</event_id>
          <department>AIDS</department>
          <academic_year>2025-2026</academic_year>
          <event_title>Data Engineering Workshop</event_title>
          <reported_participant_count>30</reported_participant_count>
        </proofchain_evidence>
        """,
        encoding="utf-8",
    )

    extraction = DocumentExtractionService().extract(path, "EVD-XML")
    fields = FieldExtractor().extract(evidence(path), extraction)

    assert fields["event_id"].normalized_value == "EVT-AIDS-001"
    assert fields["event_title"].normalized_value == "Data Engineering Workshop"
    assert fields["reported_participant_count"].normalized_value == 30


def test_tsv_attendance_fields_are_counted(tmp_path: Path) -> None:
    path = tmp_path / "EVT-CSE-001_C3.2.1_attendance.tsv"
    path.write_text(
        "\t".join(
            [
                "Event ID",
                "Event Title",
                "Department",
                "Academic Year",
                "Event Date",
                "Roll Number",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "EVT-CSE-001",
                "Cloud Workshop",
                "CSE",
                "2025-2026",
                "2025-08-22",
                "25CSE001",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    extraction = DocumentExtractionService().extract(path, "EVD-TSV")
    fields = FieldExtractor().extract(evidence(path), extraction)

    assert fields["unique_student_count"].normalized_value == 1
    assert fields["event_id"].normalized_value == "EVT-CSE-001"
