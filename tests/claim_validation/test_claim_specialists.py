"""Claim decomposition, counter-evidence, sufficiency, and repair tests."""

from __future__ import annotations

import uuid

from proofchain.agents.claim_validation.claim_decomposer import (
    ClaimDecompositionSpecialist,
)
from proofchain.agents.claim_validation.contradiction_investigator import (
    ContradictionInvestigationSpecialist,
)
from proofchain.agents.claim_validation.defensibility_judge import (
    DefensibilityDecisionSpecialist,
)
from proofchain.agents.claim_validation.evidence_retriever import (
    EvidenceRetrievalSpecialist,
)
from proofchain.agents.claim_validation.sufficiency_evaluator import (
    SufficiencyEvaluationSpecialist,
)
from proofchain.core.enums import (
    DocumentType,
    ExtractionStatus,
    ProcessingStatus,
)
from proofchain.schemas.claims import ClaimValidationInput
from proofchain.schemas.classification import (
    ClassifiedEvidence,
    DocumentTypePrediction,
    ExtractedField,
    ExtractionResult,
    RequirementMapping,
)
from proofchain.schemas.workflow import WorkflowContext


def record(
    evidence_id: str,
    document_type: DocumentType,
    fields: dict,
    requirement_id: str = "C3.2.1",
):
    return ClassifiedEvidence(
        evidence_id=evidence_id,
        version_id=f"VER-{evidence_id}-01",
        department=str(fields.get("department", "CSE")),
        academic_year=str(fields.get("academic_year", "2025-2026")),
        original_filename=f"{evidence_id}.pdf",
        relative_path=f"sample/{evidence_id}.pdf",
        absolute_path=f"C:/sample/{evidence_id}.pdf",
        sha256_checksum="a" * 64,
        extraction=ExtractionResult(
            extraction_status=ExtractionStatus.SUCCESS,
            extractor_used="test",
            extraction_confidence=0.99,
        ),
        document_type=DocumentTypePrediction(
            primary_type=document_type,
            confidence=0.99,
        ),
        extracted_fields={
            name: ExtractedField(
                field_name=name,
                normalized_value=value,
                confidence=0.99,
            )
            for name, value in fields.items()
        },
        requirement_mappings=[
            RequirementMapping(requirement_id=requirement_id, confidence=0.99)
        ],
        overall_confidence=0.99,
        processing_status=ProcessingStatus.COMPLETED,
    )


def test_complex_claim_uses_support_and_counter_evidence_and_proposes_repair():
    workflow = WorkflowContext(
        run_id=f"RUN-CLAIM-{uuid.uuid4().hex[:8].upper()}",
        correlation_id=str(uuid.uuid4()),
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )
    records = [
        record(
            "EVD-REPORT",
            DocumentType.EVENT_REPORT,
            {
                "event_id": "EVT-CSE-001",
                "department": "CSE",
                "academic_year": "2025-2026",
                "reported_participant_count": 120,
            },
        ),
        record(
            "EVD-ATTENDANCE",
            DocumentType.ATTENDANCE_SHEET,
            {
                "event_id": "EVT-CSE-001",
                "department": "CSE",
                "unique_student_count": 108,
            },
        ),
    ]
    input_data = ClaimValidationInput(
        workflow=workflow,
        institutional_claims=[
            "CSE conducted 12 industry programmes involving 120 students "
            "during 2025-2026 for C3.2.1."
        ],
        classified_evidence=records,
        bundles=[],
    )
    claims = ClaimDecompositionSpecialist().run(input_data)
    values = {item.attribute: item.expected_value for item in claims[0].atomic_claims}
    assert values["activity_count"] == 12
    assert values["participant_count"] == 120
    assert values["department"] == "CSE"

    links = EvidenceRetrievalSpecialist().run(input_data, claims)
    participant_id = next(
        item.atomic_claim_id
        for item in claims[0].atomic_claims
        if item.attribute == "participant_count"
    )
    participant_links = [item for item in links if item.atomic_claim_id == participant_id]
    assert {item.relation for item in participant_links} == {"supports", "contradicts"}
    assert {item.observed_value for item in participant_links} == {120, 108}

    contradictions = ContradictionInvestigationSpecialist().run(links)
    assert any(item.atomic_claim_id == participant_id for item in contradictions)
    sufficiency = SufficiencyEvaluationSpecialist().run(
        claims, links, contradictions
    )
    decisions = DefensibilityDecisionSpecialist().run(
        claims, links, contradictions, sufficiency
    )
    decision = decisions[0]
    assert decision.status == "partially_supported"
    assert decision.counter_evidence == ["EVD-ATTENDANCE", "EVD-REPORT"]
    assert "participant_count=108" in decision.defensible_claim_text
    assert decision.requires_human_review
    assert decision.lineage.edges


def test_derived_claim_preserves_requirement_and_uses_independent_activity_evidence():
    workflow = WorkflowContext(
        run_id=f"RUN-CLAIM-{uuid.uuid4().hex[:8].upper()}",
        correlation_id=str(uuid.uuid4()),
        department_scope=["AIML"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1", "C5.1.3"],
    )
    shared = {
        "event_id": "EVT-AIML-002",
        "event_title": "Applied Machine Learning Skills Bootcamp",
        "department": "AIML",
        "academic_year": "2025-2026",
    }
    records = [
        record(
            "EVD-REPORT",
            DocumentType.EVENT_REPORT,
            {**shared, "reported_participant_count": 30},
            "C5.1.3",
        ),
        record(
            "EVD-ATTENDANCE",
            DocumentType.ATTENDANCE_SHEET,
            {**shared, "unique_student_count": 30},
            "C5.1.3",
        ),
        record(
            "EVD-APPROVAL",
            DocumentType.APPROVAL_DOCUMENT,
            shared,
            "C5.1.3",
        ),
    ]
    input_data = ClaimValidationInput(
        workflow=workflow,
        classified_evidence=records,
        bundles=[],
    )

    claims = ClaimDecompositionSpecialist().run(input_data)
    assert claims[0].claim_id == "CLM-C5.1.3-001"
    assert claims[0].requirement_id == "C5.1.3"

    links = EvidenceRetrievalSpecialist().run(input_data, claims)
    contradictions = ContradictionInvestigationSpecialist().run(links)
    sufficiency = SufficiencyEvaluationSpecialist().run(
        claims, links, contradictions
    )
    decisions = DefensibilityDecisionSpecialist().run(
        claims, links, contradictions, sufficiency
    )

    assert decisions[0].status == "supported"
    assert not decisions[0].requires_human_review
