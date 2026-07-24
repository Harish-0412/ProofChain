"""Evidence Classification Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agentic.completion_evaluator import evaluate_classification
from proofchain.core.enums import (
    DocumentType,
    ExtractionStatus,
    ProcessingStatus,
)
from proofchain.core.exceptions import SchemaValidationError
from proofchain.repositories.json_classification_repository import (
    JsonClassificationRepository,
)
from proofchain.schemas.classification import (
    ClassificationAgentResult,
    ClassificationInput,
    ClassifiedEvidence,
    DocumentTypePrediction,
    ExtractionResult,
)
from proofchain.schemas.common import AgentError
from proofchain.schemas.agentic import (
    CompletionDecision,
    CoordinationMessage,
    Goal,
    Observation,
)
from proofchain.services.checksum_service import ChecksumService
from proofchain.services.document_classifier import DocumentClassifier
from proofchain.services.document_extractor import DocumentExtractionService
from proofchain.services.field_extractor import FieldExtractor
from proofchain.services.requirement_mapper import RequirementMapper


class EvidenceClassificationAgent(
    BaseGoalAgent[ClassificationInput, ClassificationAgentResult]
):
    agent_name = "evidence_classification"
    agent_version = "3.0.0"
    agentic_tool_name = "extract_classify_and_map_evidence"
    preparation_objective = (
        "Inspect committed evidence identities and choose bounded extraction strategies."
    )
    execution_objective = (
        "Extract content, classify document hypotheses, and map evidence to requirements."
    )
    review_objective = (
        "Compare confidence, unresolved hypotheses, source references, and escalation needs."
    )
    expected_tool_output = "Classified evidence with extraction and mapping confidence."

    def __init__(
        self,
        *,
        extractor: DocumentExtractionService | None = None,
        classifier: DocumentClassifier | None = None,
        field_extractor: FieldExtractor | None = None,
        mapper: RequirementMapper | None = None,
        checksum_service: ChecksumService | None = None,
        repository: JsonClassificationRepository | None = None,
        tracer=None,
    ):
        super().__init__(tracer=tracer)
        self.extractor = extractor or DocumentExtractionService()
        self.classifier = classifier or DocumentClassifier()
        self.field_extractor = field_extractor or FieldExtractor()
        self.mapper = mapper or RequirementMapper()
        self.checksum_service = checksum_service or ChecksumService()
        self.repository = repository or JsonClassificationRepository()

    def validate_input(self, input_data: ClassificationInput) -> None:
        if not input_data.evidence_records:
            raise SchemaValidationError("Classification requires at least one evidence record.")
        if input_data.workflow.upstream_artifact_hash is None:
            raise SchemaValidationError("Classification requires a committed collector snapshot hash.")

    def execute(self, input_data: ClassificationInput) -> ClassificationAgentResult:
        started_at = datetime.now(tz=timezone.utc)
        records: list[ClassifiedEvidence] = []
        errors: list[AgentError] = []
        warnings: list[str] = []

        for evidence in input_data.evidence_records:
            path = Path(evidence.absolute_path)
            try:
                if not path.is_file():
                    raise FileNotFoundError(path)
                actual_checksum = self.checksum_service.sha256(path)
                if actual_checksum != evidence.sha256_checksum:
                    raise ValueError("Source checksum changed after collection.")
                extraction = self.extractor.extract(path, evidence.evidence_id)
                prediction = self.classifier.classify(evidence, extraction)
                fields = self.field_extractor.extract(evidence, extraction)
                mappings = self.mapper.map(
                    evidence,
                    extraction.text or "",
                    fields,
                    input_data.workflow.requirement_scope,
                )
                status = ProcessingStatus.COMPLETED
                item_warnings = list(extraction.warnings)
                if prediction.primary_type == DocumentType.UNKNOWN or not mappings:
                    status = ProcessingStatus.REQUIRES_HUMAN_REVIEW
                elif prediction.confidence < 0.75 or any(
                    mapping.confidence < 0.75 for mapping in mappings
                ):
                    status = ProcessingStatus.REQUIRES_HUMAN_REVIEW
                elif prediction.confidence < 0.9 or any(
                    mapping.confidence < 0.9 for mapping in mappings
                ):
                    status = ProcessingStatus.COMPLETED_WITH_WARNINGS
                if extraction.extraction_status in {
                    ExtractionStatus.FAILED,
                    ExtractionStatus.UNSUPPORTED,
                }:
                    status = ProcessingStatus.FAILED

                confidence_values = [prediction.confidence, extraction.extraction_confidence]
                confidence_values.extend(mapping.confidence for mapping in mappings)
                overall_confidence = (
                    sum(confidence_values) / len(confidence_values)
                    if confidence_values
                    else 0.0
                )
                record = ClassifiedEvidence(
                    evidence_id=evidence.evidence_id,
                    version_id=evidence.version_id,
                    department=evidence.department,
                    academic_year=evidence.academic_year,
                    original_filename=evidence.original_filename,
                    relative_path=evidence.relative_path,
                    absolute_path=evidence.absolute_path,
                    sha256_checksum=evidence.sha256_checksum,
                    duplicate_of_evidence_id=evidence.duplicate_of_evidence_id,
                    run_id=input_data.workflow.run_id,
                    agent_run_id=self.agent_run_id,
                    extraction=extraction,
                    document_type=prediction,
                    extracted_fields=fields,
                    requirement_mappings=mappings,
                    overall_confidence=round(overall_confidence, 4),
                    processing_status=status,
                    requires_human_review=status
                    in {
                        ProcessingStatus.REQUIRES_HUMAN_REVIEW,
                        ProcessingStatus.UNRESOLVED,
                    },
                    warnings=item_warnings,
                )
            except (OSError, ValueError, RuntimeError) as exc:
                error = AgentError(
                    error_code="CLASSIFIER_EXTRACTION_FAILED",
                    agent_name=self.agent_name,
                    evidence_id=evidence.evidence_id,
                    stage="classification",
                    severity="error",
                    recoverable=True,
                    message=f"Classification failed for {evidence.original_filename}",
                    technical_details=str(exc),
                )
                errors.append(error)
                extraction = ExtractionResult(
                    extraction_status=ExtractionStatus.FAILED,
                    extractor_used="none",
                    warnings=[str(exc)],
                )
                record = ClassifiedEvidence(
                    evidence_id=evidence.evidence_id,
                    version_id=evidence.version_id,
                    department=evidence.department,
                    academic_year=evidence.academic_year,
                    original_filename=evidence.original_filename,
                    relative_path=evidence.relative_path,
                    absolute_path=evidence.absolute_path,
                    sha256_checksum=evidence.sha256_checksum,
                    duplicate_of_evidence_id=evidence.duplicate_of_evidence_id,
                    run_id=input_data.workflow.run_id,
                    agent_run_id=self.agent_run_id,
                    extraction=extraction,
                    document_type=DocumentTypePrediction(
                        primary_type=DocumentType.UNKNOWN,
                        confidence=0.0,
                        reasons=[str(exc)],
                    ),
                    processing_status=ProcessingStatus.FAILED,
                    requires_human_review=True,
                    warnings=[str(exc)],
                )
            records.append(record)
            if self.tracer:
                self.tracer.log(
                    agent=self.agent_name,
                    event="evidence_classified",
                    evidence_id=evidence.evidence_id,
                    status=record.processing_status.value,
                    document_type=record.document_type.primary_type.value,
                    confidence=record.overall_confidence,
                )

        self.mapper.propagate_event_consensus(records)
        for record in records:
            if not record.requirement_mappings:
                warning = f"No requirement mapping resolved for {record.original_filename}"
                record.warnings.append(warning)
                warnings.append(warning)
                record.requires_human_review = True
                if record.processing_status == ProcessingStatus.COMPLETED:
                    record.processing_status = ProcessingStatus.REQUIRES_HUMAN_REVIEW
            elif record.processing_status != ProcessingStatus.FAILED:
                confidence_values = [
                    record.document_type.confidence,
                    record.extraction.extraction_confidence,
                    *(
                        mapping.confidence
                        for mapping in record.requirement_mappings
                    ),
                ]
                record.overall_confidence = round(
                    sum(confidence_values) / len(confidence_values), 4
                )
                minimum_confidence = min(confidence_values)
                if minimum_confidence < 0.75:
                    record.processing_status = ProcessingStatus.REQUIRES_HUMAN_REVIEW
                    record.requires_human_review = True
                elif minimum_confidence < 0.9:
                    record.processing_status = ProcessingStatus.COMPLETED_WITH_WARNINGS
                    record.requires_human_review = False
                else:
                    record.processing_status = ProcessingStatus.COMPLETED
                    record.requires_human_review = False

        artifact = self.repository.save_records(
            input_data.workflow.run_id,
            records,
            self.agent_run_id or "UNKNOWN",
        )
        unresolved_count = sum(
            record.document_type.primary_type == DocumentType.UNKNOWN
            or not record.requirement_mappings
            for record in records
        )
        failure_count = sum(
            record.processing_status == ProcessingStatus.FAILED for record in records
        )
        success_count = len(records) - failure_count
        warning_count = sum(bool(record.warnings) for record in records)
        status = "completed"
        if failure_count or warning_count or unresolved_count:
            status = "completed_with_warnings"
        if success_count == 0:
            status = "failed"

        return ClassificationAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            agent_version=self.agent_version,
            status=status,
            input_count=len(input_data.evidence_records),
            success_count=success_count,
            warning_count=warning_count,
            failure_count=failure_count,
            unresolved_count=unresolved_count,
            records=records,
            output_reference=artifact.path,
            input_snapshot_hash=self.compute_input_hash(input_data),
            output_snapshot_hash=artifact.sha256,
            warnings=warnings,
            errors=errors,
            started_at=started_at,
        )

    def validate_output(self, output_data: ClassificationAgentResult) -> None:
        if output_data.input_count != len(output_data.records):
            raise SchemaValidationError(
                "Classification must emit one explicit result for every evidence record."
            )
        for record in output_data.records:
            if not record.sha256_checksum or not record.relative_path:
                raise SchemaValidationError("Classified evidence lost source identity metadata.")

    def evaluate_goal_completion(
        self,
        goal: Goal,
        output: ClassificationAgentResult | None,
        observations: list[Observation],
    ) -> CompletionDecision:
        return evaluate_classification(goal, output, observations)

    def create_peer_requests(
        self, goal: Goal, output: ClassificationAgentResult | None
    ) -> list[CoordinationMessage]:
        if output is None:
            return []
        unresolved = [
            record
            for record in output.records
            if record.requires_human_review or not record.requirement_mappings
        ]
        if not unresolved:
            return []
        return [
            CoordinationMessage(
                message_id=f"MSG-{uuid4().hex[:12].upper()}",
                run_id=goal.run_id,
                goal_id=goal.goal_id,
                source_agent=self.agent_name,
                target_agent="evidence_collector",
                message_type="information_request",
                reason=(
                    "Classification needs additional source context for unresolved evidence."
                ),
                related_evidence_ids=[record.evidence_id for record in unresolved],
                payload={
                    "filenames": [record.original_filename for record in unresolved],
                    "requested_context": "alternate source or authoritative document context",
                },
                priority="high",
            )
        ]
