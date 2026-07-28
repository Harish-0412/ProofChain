from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from proofchain.agents.evidence_collector import EvidenceCollectorAgent
from proofchain.core.enums import IngestionStatus
from proofchain.repositories.json_evidence_repository import JsonEvidenceRepository
from proofchain.schemas.evidence import CollectorInput
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.document_extractor import DocumentExtractionService
from proofchain.services.ingestion_capabilities import IngestionCapabilityService


def _workflow(run_id: str) -> WorkflowContext:
    return WorkflowContext(
        run_id=run_id,
        correlation_id=str(uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )


def test_capability_registry_is_explicit_for_native_unknown_and_unsafe():
    service = IngestionCapabilityService()

    assert service.assess("evidence.json").capability == "native_extraction"
    assert service.assess("evidence.png").capability == "metadata_only"
    assert service.assess("evidence.bin").capability == "unsupported"
    assert service.assess("evidence.exe").capability == "rejected"


def test_text_json_xml_html_and_tsv_extractors(tmp_path: Path):
    fixtures = {
        "evidence.txt": "governed evidence",
        "evidence.json": json.dumps({"claim": "supported"}),
        "evidence.xml": "<root><claim>supported</claim></root>",
        "evidence.html": "<html><body><p>supported evidence</p></body></html>",
        "evidence.tsv": "name\tstatus\nitem\tsupported\n",
    }
    extractor = DocumentExtractionService()

    for filename, content in fixtures.items():
        path = tmp_path / filename
        path.write_text(content, encoding="utf-8")
        result = extractor.extract(path, f"EVD-{path.suffix[1:].upper()}")
        assert result.extraction_status.value == "success"
        assert result.extractor_used != "none"


def test_collector_registers_unsupported_and_rejected_files(tmp_path: Path):
    source = tmp_path / "CSE"
    source.mkdir()
    (source / "native.txt").write_text("evidence", encoding="utf-8")
    (source / "unknown.bin").write_bytes(b"unknown")
    (source / "unsafe.exe").write_bytes(b"MZ-not-executable")
    repository = JsonEvidenceRepository(index_path=tmp_path / "index.json")

    result = EvidenceCollectorAgent(repository=repository).run(
        CollectorInput(
            workflow=_workflow("RUN-TEST-HETEROGENEOUS"),
            source_directories=[str(source)],
            allowed_extensions=[".txt"],
        )
    )

    by_name = {item.original_filename: item for item in result.records}
    assert len(by_name) == 3
    assert by_name["native.txt"].ingestion_status == IngestionStatus.REGISTERED
    assert by_name["unknown.bin"].ingestion_status == IngestionStatus.UNSUPPORTED
    assert by_name["unsafe.exe"].ingestion_status == IngestionStatus.REJECTED
    assert result.unsupported_count == 2
