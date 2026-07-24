"""Focused unit tests for the three-agent service boundaries."""

from __future__ import annotations

import json
import shutil
import uuid

import pytest

from proofchain.agents.evidence_collector import EvidenceCollectorAgent
from proofchain.core.enums import DocumentType, WorkflowStage
from proofchain.core.exceptions import DirectoryNotFoundError
from proofchain.core.paths import ROOT
from proofchain.repositories.json_evidence_repository import JsonEvidenceRepository
from proofchain.schemas.evidence import CollectorInput, EvidenceRecord
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.checksum_service import ChecksumService
from proofchain.services.document_classifier import DocumentClassifier
from proofchain.services.document_extractor import DocumentExtractionService
from proofchain.services.evidence_bundler import EvidenceBundler
from proofchain.services.field_extractor import FieldExtractor
from proofchain.services.requirement_mapper import RequirementMapper


def workflow(run_id: str, upstream: str | None = None) -> WorkflowContext:
    return WorkflowContext(
        run_id=run_id,
        correlation_id=str(uuid.uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1", "C5.1.3"],
        current_stage=WorkflowStage.CREATED,
        upstream_artifact_hash=upstream,
    )


@pytest.fixture
def local_workspace():
    path = ROOT / "outputs" / "test_tmp" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    yield path
    shutil.rmtree(path, ignore_errors=True)


def test_collector_reuses_identity_and_links_exact_duplicate(local_workspace):
    source = local_workspace / "CSE"
    source.mkdir()
    first = source / "first.pdf"
    duplicate = source / "duplicate.pdf"
    first.write_bytes(b"same evidence")
    duplicate.write_bytes(b"same evidence")
    repository = JsonEvidenceRepository(index_path=local_workspace / "index.json")
    agent = EvidenceCollectorAgent(repository=repository)

    first_result = agent.run(
        CollectorInput(
            workflow=workflow("RUN-TEST-COL1"),
            source_directories=[str(source)],
            allowed_extensions=[".pdf"],
        )
    )
    second_result = agent.run(
        CollectorInput(
            workflow=workflow("RUN-TEST-COL2"),
            source_directories=[str(source)],
            allowed_extensions=[".pdf"],
        )
    )

    first_by_name = {record.original_filename: record for record in first_result.records}
    second_by_name = {record.original_filename: record for record in second_result.records}
    assert first_by_name["first.pdf"].evidence_id == second_by_name["first.pdf"].evidence_id
    assert second_by_name["duplicate.pdf"].evidence_id != second_by_name["first.pdf"].evidence_id
    assert sum(record.duplicate_of_evidence_id is None for record in second_result.records) == 1
    assert {
        name: record.duplicate_of_evidence_id for name, record in first_by_name.items()
    } == {
        name: record.duplicate_of_evidence_id for name, record in second_by_name.items()
    }


def test_collector_versions_changed_content(local_workspace):
    source = local_workspace / "CSE"
    source.mkdir()
    document = source / "versioned.pdf"
    document.write_bytes(b"version one")
    repository = JsonEvidenceRepository(index_path=local_workspace / "index.json")
    agent = EvidenceCollectorAgent(repository=repository)
    first = agent.run(
        CollectorInput(
            workflow=workflow("RUN-TEST-VER1"),
            source_directories=[str(source)],
            allowed_extensions=[".pdf"],
        )
    ).records[0]
    document.write_bytes(b"version two")
    second = agent.run(
        CollectorInput(
            workflow=workflow("RUN-TEST-VER2"),
            source_directories=[str(source)],
            allowed_extensions=[".pdf"],
        )
    ).records[0]
    assert second.evidence_id == first.evidence_id
    assert second.version_number == first.version_number + 1
    assert second.version_id != first.version_id


def test_collector_rejects_when_every_source_is_missing(local_workspace):
    agent = EvidenceCollectorAgent(
        repository=JsonEvidenceRepository(index_path=local_workspace / "index.json")
    )
    with pytest.raises(DirectoryNotFoundError):
        agent.run(
            CollectorInput(
                workflow=workflow("RUN-TEST-MISSING"),
                source_directories=[str(local_workspace / "missing")],
            )
        )


def test_pdf_extraction_classification_fields_and_mapping():
    path = (
        ROOT
        / "sample_data"
        / "departments"
        / "CSE"
        / "event_reports"
        / "EVT-CSE-001_CSE_C3.2.1_event_report.pdf"
    )
    checksum = ChecksumService().sha256(path)
    evidence = EvidenceRecord(
        evidence_id="EVD-CSE-2025-2026-99991",
        version_id="VER-99991-01",
        department="CSE",
        academic_year="2025-2026",
        original_filename=path.name,
        relative_path=str(path.relative_to(ROOT)),
        absolute_path=str(path),
        file_extension=".pdf",
        mime_type="application/pdf",
        file_size_bytes=path.stat().st_size,
        sha256_checksum=checksum,
    )
    extraction = DocumentExtractionService().extract(path, evidence.evidence_id)
    prediction = DocumentClassifier().classify(evidence, extraction)
    fields = FieldExtractor().extract(evidence, extraction)
    mappings = RequirementMapper().map(
        evidence,
        extraction.text or "",
        fields,
        ["C3.2.1", "C5.1.3"],
    )
    assert prediction.primary_type == DocumentType.EVENT_REPORT
    assert fields["event_id"].normalized_value == "EVT-CSE-001"
    assert fields["reported_participant_count"].normalized_value == 120
    assert [mapping.requirement_id for mapping in mappings] == ["C3.2.1"]


def test_spreadsheet_extraction_counts_unique_students():
    path = (
        ROOT
        / "sample_data"
        / "departments"
        / "CSE"
        / "attendance_sheets"
        / "EVT-CSE-001_attendance.xlsx"
    )
    evidence = EvidenceRecord(
        evidence_id="EVD-CSE-2025-2026-99992",
        version_id="VER-99992-01",
        department="CSE",
        academic_year="2025-2026",
        original_filename=path.name,
        relative_path=str(path.relative_to(ROOT)),
        absolute_path=str(path),
        file_extension=".xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_size_bytes=path.stat().st_size,
        sha256_checksum=ChecksumService().sha256(path),
    )
    extraction = DocumentExtractionService().extract(path, evidence.evidence_id)
    fields = FieldExtractor().extract(evidence, extraction)
    manifest = json.loads(
        (ROOT / "sample_data" / "dataset_manifest.json").read_text(encoding="utf-8")
    )
    expected_count = next(
        event["attendance_unique_students"]
        for event in manifest["events"]
        if event["event_id"] == "EVT-CSE-001"
    )
    assert fields["unique_student_count"].normalized_value == expected_count
    assert fields["attendance_rows"].normalized_value > expected_count
    assert fields["duplicate_roll_numbers"].normalized_value


def test_bundler_separates_same_event_title_by_department():
    from proofchain.core.enums import ExtractionStatus
    from proofchain.schemas.classification import (
        ClassifiedEvidence,
        DocumentTypePrediction,
        ExtractionResult,
        ExtractedField,
    )

    records = []
    for index, department in enumerate(("CSE", "ECE"), start=1):
        records.append(
            ClassifiedEvidence(
                evidence_id=f"EVD-{department}-2025-2026-0000{index}",
                version_id=f"VER-0000{index}-01",
                department=department,
                academic_year="2025-2026",
                original_filename=f"EVT-{department}-001_report.pdf",
                relative_path=f"{department}/report.pdf",
                absolute_path=f"C:/{department}/report.pdf",
                sha256_checksum=str(index) * 64,
                extraction=ExtractionResult(
                    extraction_status=ExtractionStatus.SUCCESS,
                    extractor_used="test",
                    extraction_confidence=1.0,
                ),
                document_type=DocumentTypePrediction(
                    primary_type=DocumentType.EVENT_REPORT,
                    confidence=1.0,
                ),
                extracted_fields={
                    "event_title": ExtractedField(
                        field_name="event_title",
                        normalized_value="Shared Workshop",
                        confidence=1.0,
                    )
                },
            )
        )
    bundles, _ = EvidenceBundler().bundle(records, "RUN-TEST-BUNDLE")
    assert len(bundles) == 2
    assert {bundle.department for bundle in bundles} == {"CSE", "ECE"}
