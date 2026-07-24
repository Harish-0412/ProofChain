"""Integration test for typed handoffs across all three domain agents."""

from __future__ import annotations

import shutil
import uuid

from proofchain.agents.evidence_classification import EvidenceClassificationAgent
from proofchain.agents.evidence_collector import EvidenceCollectorAgent
from proofchain.agents.evidence_integrity import EvidenceIntegrityAgent
from proofchain.core.paths import DEPARTMENTS_DIR, ROOT, get_run_dir
from proofchain.repositories.json_evidence_repository import JsonEvidenceRepository
from proofchain.schemas.classification import ClassificationInput
from proofchain.schemas.evidence import CollectorInput
from proofchain.schemas.integrity import IntegrityInput
from proofchain.schemas.workflow import WorkflowContext


def test_typed_agent_handoffs_preserve_snapshot_and_detect_bundle_defects():
    token = uuid.uuid4().hex[:10]
    temp_root = ROOT / "outputs" / "test_tmp" / token
    source = temp_root / "CSE"
    source.mkdir(parents=True)
    originals = [
        DEPARTMENTS_DIR
        / "CSE"
        / "event_reports"
        / "EVT-CSE-001_CSE_C3.2.1_event_report.pdf",
        DEPARTMENTS_DIR
        / "CSE"
        / "attendance_sheets"
        / "EVT-CSE-001_attendance.xlsx",
        DEPARTMENTS_DIR
        / "CSE"
        / "approval_documents"
        / "APR_EVT-CSE-001_approval.pdf",
    ]
    for original in originals:
        shutil.copy2(original, source / original.name)

    run_id = f"RUN-INT-{token.upper()}"
    workflow = WorkflowContext(
        run_id=run_id,
        correlation_id=str(uuid.uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )
    try:
        collector = EvidenceCollectorAgent(
            repository=JsonEvidenceRepository(index_path=temp_root / "evidence_index.json")
        ).run(
            CollectorInput(
                workflow=workflow,
                source_directories=[str(temp_root)],
                allowed_extensions=[".pdf", ".xlsx"],
            )
        )
        assert len(collector.records) == 3
        assert collector.output_snapshot_hash

        workflow.upstream_artifact_hash = collector.output_snapshot_hash
        classification = EvidenceClassificationAgent().run(
            ClassificationInput(
                workflow=workflow,
                evidence_records=collector.records,
            )
        )
        assert len(classification.records) == 3
        assert {record.document_type.primary_type.value for record in classification.records} == {
            "event_report",
            "attendance_sheet",
            "approval_document",
        }

        workflow.upstream_artifact_hash = classification.output_snapshot_hash
        integrity = EvidenceIntegrityAgent().run(
            IntegrityInput(
                workflow=workflow,
                classified_evidence=classification.records,
            )
        )
        rule_ids = {finding.rule_id for finding in integrity.findings}
        assert {"SIGN-001", "DUP-STUDENT-001", "EVT-COUNT-001"}.issubset(rule_ids)
        assert len(integrity.bundles) == 1
        assert integrity.output_snapshot_hash
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
        shutil.rmtree(get_run_dir(run_id), ignore_errors=True)
