"""Evidence Collector Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agentic.completion_evaluator import evaluate_collector
from proofchain.core.enums import IngestionStatus
from proofchain.core.exceptions import DirectoryNotFoundError, SchemaValidationError
from proofchain.core.paths import ROOT
from proofchain.repositories.json_evidence_repository import JsonEvidenceRepository
from proofchain.schemas.common import AgentError
from proofchain.schemas.agentic import (
    CompletionDecision,
    CoordinationMessage,
    Goal,
    Observation,
)
from proofchain.schemas.evidence import CollectorAgentResult, CollectorInput
from proofchain.services.checksum_service import ChecksumService
from proofchain.services.file_scanner import FileScanner
from proofchain.services.ingestion_capabilities import IngestionCapabilityService
from proofchain.services.metadata_service import MetadataService


class EvidenceCollectorAgent(BaseGoalAgent[CollectorInput, CollectorAgentResult]):
    agent_name = "evidence_collector"
    agent_version = "3.0.0"
    agentic_tool_name = "scan_and_register_evidence"
    preparation_objective = (
        "Inspect approved source scopes, expected evidence coverage, and acquisition constraints."
    )
    execution_objective = (
        "Scan approved sources, checksum files, and register immutable evidence identities."
    )
    review_objective = (
        "Assess source coverage, skipped files, acquisition uncertainty, and follow-up needs."
    )
    expected_tool_output = "A checksum-backed evidence registry and acquisition warnings."

    def __init__(
        self,
        *,
        scanner: FileScanner | None = None,
        checksum_service: ChecksumService | None = None,
        metadata_service: MetadataService | None = None,
        capability_service: IngestionCapabilityService | None = None,
        repository: JsonEvidenceRepository | None = None,
        tracer=None,
    ):
        super().__init__(tracer=tracer)
        self.scanner = scanner or FileScanner()
        self.checksum_service = checksum_service or ChecksumService()
        self.metadata_service = metadata_service or MetadataService()
        self.capability_service = capability_service or IngestionCapabilityService()
        self.repository = repository or JsonEvidenceRepository()

    def validate_input(self, input_data: CollectorInput) -> None:
        if not input_data.source_directories:
            raise DirectoryNotFoundError("At least one evidence source directory is required.")
        if not any(Path(path).expanduser().is_dir() for path in input_data.source_directories):
            raise DirectoryNotFoundError(
                "None of the configured evidence source directories exists.",
                context={"source_directories": input_data.source_directories},
            )

    def execute(self, input_data: CollectorInput) -> CollectorAgentResult:
        started_at = datetime.now(tz=timezone.utc)
        candidates, missing = self.scanner.scan(
            input_data.source_directories,
            allowed_extensions=input_data.allowed_extensions,
            department_scope=input_data.workflow.department_scope,
            recursive=input_data.recursive,
        )
        records = []
        warnings: list[str] = []
        errors: list[AgentError] = []
        unsupported_count = 0

        for path in missing:
            message = f"Source directory was skipped because it does not exist: {path}"
            warnings.append(message)
            errors.append(
                AgentError(
                    error_code="COLLECTOR_DIRECTORY_NOT_FOUND",
                    agent_name=self.agent_name,
                    stage="collection",
                    severity="warning",
                    recoverable=True,
                    message=message,
                )
            )

        for candidate in candidates:
            try:
                capability = self.capability_service.assess(candidate.path)
                if not candidate.supported and capability.capability in {
                    "native_extraction",
                    "metadata_only",
                }:
                    capability = capability.model_copy(
                        update={
                            "capability": "unsupported",
                            "extractor": None,
                            "reason": "The file type is disabled by the active ingestion policy.",
                            "downstream_action": "human_conversion_required",
                        }
                    )
                if capability.capability in {"unsupported", "rejected"}:
                    unsupported_count += 1
                    warnings.append(
                        f"{capability.capability.title()} file registered with no "
                        f"downstream extraction: {candidate.path}"
                    )
                metadata = self.metadata_service.inspect(candidate.path)
                checksum = self.checksum_service.sha256(candidate.path)
                ingestion_status = {
                    "unsupported": IngestionStatus.UNSUPPORTED,
                    "rejected": IngestionStatus.REJECTED,
                }.get(capability.capability, IngestionStatus.REGISTERED)
                record = self.repository.register(
                    path=candidate.path,
                    project_root=ROOT,
                    department=candidate.department,
                    academic_year=input_data.workflow.academic_year,
                    sha256_checksum=checksum,
                    mime_type=metadata.mime_type,
                    file_size_bytes=metadata.file_size_bytes,
                    created_at=metadata.created_at,
                    modified_at=metadata.modified_at,
                    run_id=input_data.workflow.run_id,
                    agent_run_id=self.agent_run_id or "UNKNOWN",
                    ingestion_status=ingestion_status,
                    processing_capability=capability.capability,
                    capability_reason=capability.reason,
                )
                records.append(record)
                if self.tracer:
                    self.tracer.log(
                        agent=self.agent_name,
                        event="evidence_registered",
                        evidence_id=record.evidence_id,
                        duplicate_status=record.duplicate_status.value,
                        version_id=record.version_id,
                        processing_capability=record.processing_capability,
                    )
            except (OSError, ValueError) as exc:
                errors.append(
                    AgentError(
                        error_code="COLLECTOR_FILE_READ_FAILED",
                        agent_name=self.agent_name,
                        stage="collection",
                        severity="error",
                        recoverable=True,
                        message=f"Could not register {candidate.path.name}",
                        technical_details=str(exc),
                    )
                )
                if self.tracer:
                    self.tracer.log_error(
                        agent=self.agent_name,
                        error_code="COLLECTOR_FILE_READ_FAILED",
                        message=str(exc),
                    )

        artifact = self.repository.save_run_records(
            input_data.workflow.run_id,
            records,
            self.agent_run_id or "UNKNOWN",
        )
        duplicate_count = sum(record.duplicate_of_evidence_id is not None for record in records)
        status = "completed"
        if errors or warnings:
            status = "completed_with_warnings"
        if not records:
            status = "failed"

        return CollectorAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            agent_version=self.agent_version,
            status=status,
            input_count=len(candidates),
            success_count=len(records),
            warning_count=len(warnings),
            failure_count=len(errors),
            duplicate_count=duplicate_count,
            unsupported_count=unsupported_count,
            records=records,
            output_reference=artifact.path,
            input_snapshot_hash=self.compute_input_hash(input_data),
            output_snapshot_hash=artifact.sha256,
            warnings=warnings,
            errors=errors,
            started_at=started_at,
        )

    def validate_output(self, output_data: CollectorAgentResult) -> None:
        if output_data.run_id == "UNKNOWN":
            raise SchemaValidationError("Collector output is missing a valid run ID.")
        if output_data.success_count != len(output_data.records):
            raise SchemaValidationError("Collector success count does not match registry records.")
        for record in output_data.records:
            if not record.evidence_id or not record.sha256_checksum:
                raise SchemaValidationError("Evidence record is missing identity metadata.")

    def evaluate_goal_completion(
        self,
        goal: Goal,
        output: CollectorAgentResult | None,
        observations: list[Observation],
    ) -> CompletionDecision:
        return evaluate_collector(goal, output, observations)

    def create_peer_requests(
        self, goal: Goal, output: CollectorAgentResult | None
    ) -> list[CoordinationMessage]:
        if output is None:
            return []
        requests = []
        for error in output.errors:
            requests.append(
                CoordinationMessage(
                    message_id=f"MSG-{uuid4().hex[:12].upper()}",
                    run_id=goal.run_id,
                    goal_id=goal.goal_id,
                    source_agent=self.agent_name,
                    target_agent="supervisor",
                    message_type="information_request",
                    reason=error.message,
                    related_evidence_ids=[error.evidence_id]
                    if error.evidence_id
                    else [],
                    payload={
                        "error_code": error.error_code,
                        "recommended_action": error.recommended_action,
                    },
                    priority="high" if error.severity == "error" else "medium",
                )
            )
        return requests
