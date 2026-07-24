# ProofChain Advanced Three-Agent Implementation Plan

## Implementation Status

Status: Complete

Delivered on July 24, 2026:

- Three bounded `BaseAgent` implementations for collection, classification, and integrity
- Deterministic Supervisor with stage gates and partial-failure handling
- Atomic JSON repositories and stable evidence identity/version reuse
- SHA-256 synchronization checkpoints linking every committed stage artifact
- PDF, XLSX, CSV, DOCX, and image-metadata extraction dispatch
- Deterministic classification, field extraction, requirement mapping, and event consensus
- Department-safe evidence bundling
- Versioned YAML rule execution with pass/fail JSONL traces
- Findings, gaps, requirement summaries, and integrity scores
- Full and stage-only CLI workflows with run validation
- Unit, integration, resume synchronization, and end-to-end workflow tests

## Objective

Build a deterministic, traceable, supervisor-governed ProofChain MVP with three bounded agents:

1. Evidence Collector Agent
2. Evidence Classification Agent
3. Evidence Integrity Agent

The Supervisor is not counted as a domain agent. It is the workflow controller that creates the run, enforces stage gates, passes typed artifacts, handles partial failure, and writes the final pipeline result.

The final pipeline must transform raw institutional files into reproducible run artifacts:

- Evidence registry
- Classified evidence records
- Evidence bundles
- Integrity findings
- Evidence gaps
- Integrity summaries
- Pipeline trace
- Final pipeline report

## Current Repository State

Already present:

- `proofchain/agents/base.py`
- `proofchain/core/`
- `proofchain/schemas/`
- `proofchain/rules/`
- `config/`
- `sample_data/`
- `tests/`
- `tools/`
- `pyproject.toml`

Still required:

- Concrete agent implementations
- Service implementations
- JSON repositories
- Supervisor orchestration
- CLI entry point
- Run-specific output writer
- Rule execution engine integration
- Agent-level unit and workflow tests

## Architectural Boundaries

### Agent 1: Evidence Collector Agent

Owns evidence discovery, registration, identity, metadata, checksum, duplicate registration, and source preservation.

Must not:

- Extract full text
- Classify document type beyond MIME/extension
- Map to requirements
- Validate accreditation integrity
- Delete or mutate original files

Primary files to implement:

- `proofchain/agents/evidence_collector.py`
- `proofchain/services/file_scanner.py`
- `proofchain/services/checksum_service.py`
- `proofchain/services/metadata_service.py`
- `proofchain/repositories/json_evidence_repository.py`

Output contract:

- `CollectorAgentResult`
- `EvidenceRecord[]`

### Agent 2: Evidence Classification Agent

Owns document extraction, document-type classification, field extraction, requirement mapping, confidence scoring, and human-review routing.

Internally split into services so this agent can later be decomposed into separate extraction and mapping agents.

Must not:

- Approve evidence
- Produce integrity findings
- Resolve cross-document contradictions
- Invent missing fields
- Mutate source documents

Primary files to implement:

- `proofchain/agents/evidence_classification.py`
- `proofchain/services/document_extractor.py`
- `proofchain/services/pdf_extractor.py`
- `proofchain/services/spreadsheet_extractor.py`
- `proofchain/services/document_classifier.py`
- `proofchain/services/field_extractor.py`
- `proofchain/services/requirement_mapper.py`

Output contract:

- `ClassificationAgentResult`
- `ClassifiedEvidence[]`

### Agent 3: Evidence Integrity Agent

Owns evidence grouping, rule execution, formal findings, gaps, integrity scoring, reuse detection, and requirement-level summaries.

Must not:

- Scan raw folders
- Extract source document text
- Reclassify documents
- Change mappings silently
- Hide unresolved evidence

Primary files to implement:

- `proofchain/agents/evidence_integrity.py`
- `proofchain/services/evidence_bundler.py`
- `proofchain/services/duplicate_detector.py`
- `proofchain/services/rule_engine.py`
- `proofchain/repositories/json_findings_repository.py`

Output contract:

- `IntegrityAgentResult`
- `EvidenceBundle[]`
- `IntegrityFinding[]`
- `EvidenceGap[]`
- `IntegritySummary[]`

### Supervisor

Owns workflow orchestration, not domain judgment.

Primary files to implement:

- `proofchain/agents/supervisor.py`
- `proofchain/repositories/json_run_repository.py`
- `proofchain/cli.py`

Output contract:

- `PipelineResult`

## Target Runtime Flow

```text
SupervisorRequest
    |
    v
WorkflowContext + Run Directory
    |
    v
Evidence Collector Agent
    |
    v
Collector Gate
    |
    v
Evidence Classification Agent
    |
    v
Classification Gate
    |
    v
Evidence Integrity Agent
    |
    v
Integrity Gate
    |
    v
PipelineResult
```

## Implementation Sequence

### Phase 1: Harden Shared Foundation

Tasks:

- Confirm all schemas serialize with Pydantic v2.
- Add missing schema fields needed by downstream stages.
- Normalize status strings through enums where practical.
- Ensure `BaseAgent.run()` reliably stamps `agent_run_id`, timestamps, counts, trace events, and recoverable errors.
- Add a run-output path helper for `outputs/runs/{run_id}`.

Acceptance criteria:

- `pytest tests/unit/test_base_infrastructure.py -v` passes.
- Every agent result can be serialized to JSON.
- Trace logger writes valid JSONL.

### Phase 2: Implement JSON Repositories

Tasks:

- Add `JsonRunRepository`.
- Add `JsonEvidenceRepository`.
- Add `JsonClassificationRepository`.
- Add `JsonFindingsRepository`.
- Persist every artifact under a run-specific directory.
- Keep global registry support only for stable evidence ID reuse.

Expected output layout:

```text
outputs/runs/{run_id}/
  run_manifest.json
  evidence_registry.json
  classified_evidence.json
  evidence_bundles.json
  integrity_findings.json
  evidence_gaps.json
  integrity_summary.json
  pipeline_result.json
  pipeline_trace.jsonl
  errors.json
```

Acceptance criteria:

- Repositories perform atomic-ish writes through temp files followed by replace.
- Existing evidence IDs can be reused by checksum/path.
- Run artifacts are deterministic and easy to inspect.

### Phase 3: Complete Evidence Collector Agent

Tasks:

- Validate source directories.
- Scan supported extensions recursively.
- Infer department from path.
- Record relative and absolute path.
- Detect MIME type.
- Read file size and timestamps.
- Generate SHA-256 checksum.
- Detect exact duplicate checksums.
- Reuse existing evidence IDs where applicable.
- Generate version IDs for changed content.
- Return unsupported/corrupted records as structured warnings or errors.
- Persist `evidence_registry.json`.

Advanced design:

- `FileScanner` returns normalized file candidates.
- `ChecksumService` isolates hashing.
- `MetadataService` owns stat and MIME inspection.
- `JsonEvidenceRepository` owns stable ID and version reuse.
- Collector itself only coordinates these services.

Acceptance criteria:

- Supported files in `sample_data/departments` are registered.
- Duplicate event report is detected without deleting it.
- Re-running the collector does not create duplicate evidence IDs.
- Missing directory produces a recoverable structured error.

### Phase 4: Complete Evidence Classification Agent

Tasks:

- Validate file existence and checksum before extraction.
- Select extractor by extension/MIME.
- Extract text from PDFs.
- Extract sheet names, rows, tables, and counts from spreadsheets.
- Generate basic page/sheet source references.
- Classify document type using deterministic rules:
  - Filename
  - Folder name
  - Document keywords
  - Spreadsheet structure
- Extract MVP fields:
  - Event ID
  - Event title
  - Event date
  - Department
  - Academic year
  - Requirement ID
  - Participant count
  - Coordinator
  - Signature presence
  - Approval/reference number
- Map documents to requirements using `config/requirement_mapping.yaml`.
- Apply confidence routing:
  - `>= 0.90`: accepted
  - `0.75-0.89`: accepted with warning
  - `0.50-0.74`: requires human review
  - `< 0.50`: unresolved
- Persist `classified_evidence.json`.

Advanced design:

- `DocumentExtractionService` dispatches to PDF/spreadsheet/image/docx extractors.
- `DocumentClassifier` produces `DocumentTypePrediction`, never raw strings.
- `FieldExtractor` produces source-backed `ExtractedField` values.
- `RequirementMapper` maps evidence without declaring it valid.
- Optional LLM classification is behind an adapter and disabled for MVP unless explicitly configured.

Acceptance criteria:

- Event reports classify as `event_report`.
- Attendance workbooks classify as `attendance_sheet`.
- Approval documents classify as `approval_document`.
- Photographs classify as `photograph`.
- Low-confidence classifications are not silently accepted.
- Extracted values include source references when possible.

### Phase 5: Add Evidence Bundling

Tasks:

- Group classified evidence by event ID when present.
- Fall back to event title/date/department/folder similarity.
- Generate stable bundle IDs.
- Record grouping method and confidence.
- Mark unresolved bundles for review.

Advanced design:

- Bundling lives in `EvidenceBundler`, called by the Integrity Agent before rules execute.
- Cross-document rules only run inside bundles, preventing unrelated document comparison.

Acceptance criteria:

- CSE event report, attendance sheet, approval, certificates, and photo for the same event form one bundle.
- Unrelated documents are not compared.
- Low-confidence grouping produces warnings.

### Phase 6: Complete Evidence Integrity Agent

Tasks:

- Validate classified evidence input.
- Build evidence bundles.
- Execute first six rule families:
  1. Exact duplicate file
  2. Participant count reconciliation
  3. Academic-year validity
  4. Signature presence
  5. Required document checklist
  6. Evidence reuse across claims
- Generate findings with rule ID, rule version, evidence IDs, severity, blocking status, and recommended action.
- Generate gaps for missing required documents and unresolved mappings.
- Generate requirement-level summaries and integrity score.
- Persist integrity artifacts.

Advanced design:

- `RuleEngine` loads versioned YAML rule definitions.
- Each rule emits a typed pass/fail trace entry.
- Rule execution is deterministic and testable without LLM calls.
- Registry-level duplicate detection becomes formal integrity findings here.

Acceptance criteria:

- Participant mismatches produce high-severity blocking findings.
- Missing approval letter produces an evidence gap.
- Duplicate files produce duplicate findings with original reference.
- Wrong academic-year evidence is excluded from current requirement coverage.
- Reused evidence across unrelated bundles is flagged.

### Phase 7: Implement Supervisor

Tasks:

- Create `WorkflowContext`.
- Create run directory.
- Initialize `TraceLogger`.
- Run collector, classifier, and integrity agents in order.
- Enforce stage gates.
- Support partial failure.
- Write final `PipelineResult`.
- Print a clear console summary.

Stage gates:

- Collector to Classification:
  - At least one readable evidence record.
  - Required metadata present.
  - Registry output schema valid.
- Classification to Integrity:
  - Extraction results exist for eligible files.
  - Unknown types are explicit.
  - Requirement mappings use valid IDs.
  - Failed documents are recorded.
- Integrity completion:
  - Eligible classified evidence evaluated.
  - Rule executions traceable.
  - Summary counts match findings and gaps.

Acceptance criteria:

- A corrupted or unsupported file does not destroy the entire run.
- Final status can be `completed`, `completed_with_warnings`, `requires_correction`, `blocked`, or `failed`.
- `pipeline_result.json` references every generated artifact.

### Phase 8: CLI and Developer Workflow

Tasks:

- Add `proofchain/cli.py`.
- Support:
  - `proofchain run-pipeline`
  - `proofchain collect`
  - `proofchain classify`
  - `proofchain integrity`
  - `proofchain validate-run`
- Accept source path, departments, academic year, and requirement scope.

Example:

```bash
proofchain run-pipeline \
  --source sample_data/departments \
  --academic-year 2025-2026 \
  --departments CSE \
  --requirements C3.2.1
```

Acceptance criteria:

- CLI uses the same Supervisor class as tests.
- CLI writes run artifacts to `outputs/runs/{run_id}`.
- Console output summarizes counts, warnings, findings, gaps, and output path.

### Phase 9: Testing Matrix

Unit tests:

- Collector file scanning
- Checksum generation
- Stable ID reuse
- Duplicate detection
- PDF extraction
- Spreadsheet extraction
- Document-type rules
- Requirement mapping
- Confidence routing
- Evidence bundling
- Rule execution

Integration tests:

- Collector to Classification
- Classification to Integrity
- Full Supervisor pipeline

Workflow scenarios:

- Clean evidence bundle
- Participant mismatch
- Missing approval letter
- Duplicate report
- Corrupted PDF
- Wrong academic year
- Reused photograph

Acceptance criteria:

- `pytest tests/unit -v` passes.
- `pytest tests/integration -v` passes.
- `pytest tests/workflow -v` passes.
- Full pipeline produces deterministic JSON outputs from sample data.

## Build Order Checklist

- [x] Repository layer
- [x] Collector services
- [x] Collector agent
- [x] Classification extractors
- [x] Classification rules and mapper
- [x] Classification agent
- [x] Evidence bundler
- [x] Duplicate detector
- [x] Rule engine
- [x] Integrity agent
- [x] Supervisor
- [x] Synchronization checkpoints
- [x] CLI
- [x] Tests
- [x] README update

## Definition of Done

The MVP is complete when:

- All three domain agents are implemented as `BaseAgent` subclasses.
- Each agent has a strict input/output Pydantic contract.
- Agents communicate only through typed persisted artifacts.
- The Supervisor can run all three agents end to end.
- Every run has a unique run directory and JSONL trace.
- Partial failures are represented as structured errors.
- Confidence routing is explicit.
- Integrity findings and gaps are rule-backed and versioned.
- The sample data pipeline can be executed from the CLI.
- Unit, integration, and workflow tests cover the main success and failure paths.

## Delivered Validation

Automated verification:

- `python -m compileall -q proofchain tests`
- `python -m ruff check proofchain tests`
- `python -m pytest -q`

Expected synthetic CSE result:

- 15 evidence files registered
- 15 documents classified
- 9 integrity findings
- 5 evidence gaps
- Final status `blocked` because the sample intentionally contains blocking defects
- Three synchronized checkpoints: collection, classification, and integrity
- `proofchain validate-run {run_id}` reports a valid artifact chain
