# ProofChain Complete Agentic Implementation Report

This report records the ten-agent implementation baseline. The current
governance hardening, scheduler, policy, security, package, and observability
details are maintained in
`docs/ProofChain_Advanced_Ten_Agent_Architecture_and_Workflow.md`.

## Status

The ProofChain implementation now contains a governed ten-agent pipeline. The
original evidence workflow has been upgraded into an agentic workflow that can
accept an institutional objective, create explicit goals, execute bounded plans,
reason through evidence and gaps, coordinate across agents, preserve a
synchronization chain, and produce a human-reviewable final decision.

Latest validation completed on 2026-07-24:

- `python -m compileall -q proofchain tests`: passed
- `python -m ruff check proofchain tests`: passed
- `python -m pytest -q`: 63 passed
- `python -m proofchain.cli validate-run RUN-20260724-3A4C`: `valid: true`

The only validation warning was from pytest being unable to write its optional
`.pytest_cache` directory on Windows. This does not affect the implementation or
test results.

## Implemented Pipeline

The implemented workflow is:

```text
Evidence Collector
  -> Evidence Classification
  -> Evidence Integrity
  -> Claim Intelligence and Defensibility
  -> Adaptive Gap Resolution and Readiness Planning
  -> Accountability, Ownership, and Escalation
  -> Governed Department Liaison and Task Execution
  -> Evidence Closure and Continuous Revalidation
  -> Audit Package Composer and Evidence Manifest
  -> Adversarial Quality Review and Audit Simulation
  -> Human Approval Records
```

Each primary agent is goal-driven and uses the shared agentic runtime. Agents do
not simply execute a flat function. They receive a goal, persist a plan, call
approved tools, write observations, store reflections, publish coordination
messages, and emit a policy-validated completion decision.

## Agent 1: Evidence Collector

Purpose:

- Discover source evidence from approved input directories.
- Register supported file types.
- Assign durable evidence IDs.
- Compute SHA-256 checksums.
- Track source path, department, academic year, document type hints, and version
  metadata.
- Detect duplicate evidence content.

Important files:

- `proofchain/agents/evidence_collector.py`
- `proofchain/services/file_scanner.py`
- `proofchain/services/checksum_service.py`
- `proofchain/services/duplicate_detector.py`
- `proofchain/repositories/json_evidence_repository.py`

Main output:

- `outputs/runs/{run_id}/evidence_registry.json`

## Agent 2: Evidence Classification

Purpose:

- Extract document text and spreadsheet fields.
- Classify evidence type.
- Extract structured fields.
- Map evidence to accreditation requirements.
- Build event-level consensus from multiple evidence records.
- Route low-confidence or inconsistent evidence into warnings.

Important files:

- `proofchain/agents/evidence_classification.py`
- `proofchain/services/document_extractor.py`
- `proofchain/services/document_classifier.py`
- `proofchain/services/field_extractor.py`
- `proofchain/services/requirement_mapper.py`
- `proofchain/services/spreadsheet_extractor.py`
- `proofchain/repositories/json_classification_repository.py`

Main output:

- `outputs/runs/{run_id}/classified_evidence.json`

## Agent 3: Evidence Integrity

Purpose:

- Bundle evidence by event and requirement.
- Apply deterministic integrity rules.
- Detect missing required documents.
- Detect duplicate files, missing signatures, duplicate attendance rows, and
  participant-count mismatches.
- Produce integrity findings, evidence gaps, readiness scores, and blocking
  decisions.

Important files:

- `proofchain/agents/evidence_integrity.py`
- `proofchain/services/evidence_bundler.py`
- `proofchain/services/rule_engine.py`
- `proofchain/rules/*.yaml`
- `proofchain/repositories/json_findings_repository.py`

Main outputs:

- `outputs/runs/{run_id}/integrity_result.json`
- `outputs/runs/{run_id}/integrity_findings.json`
- `outputs/runs/{run_id}/evidence_gaps.json`
- `outputs/runs/{run_id}/integrity_summary.json`

## Agent 4: Claim Intelligence and Defensibility

Purpose:

- Convert institutional claims into atomic claims.
- Retrieve supporting and contradictory evidence.
- Investigate contradictions across evidence authorities.
- Evaluate sufficiency using coverage, authority, consistency, and independence.
- Decide whether a claim is supported, partially supported, contradicted, or
  unsupported.
- Produce a minimal defensible evidence set.
- Produce defensible alternative claim text.
- Build claim-to-evidence lineage.

Specialists implemented:

1. Claim Decomposer
2. Evidence Retriever
3. Contradiction Investigator
4. Sufficiency Evaluator
5. Defensibility Judge

Important files:

- `proofchain/agents/claim_validation/agent.py`
- `proofchain/agents/claim_validation/claim_decomposer.py`
- `proofchain/agents/claim_validation/evidence_retriever.py`
- `proofchain/agents/claim_validation/contradiction_investigator.py`
- `proofchain/agents/claim_validation/sufficiency_evaluator.py`
- `proofchain/agents/claim_validation/defensibility_judge.py`
- `proofchain/schemas/claims.py`

Main output:

- `outputs/runs/{run_id}/claim_decisions.json`

Validated behavior from `RUN-20260724-6B9A`:

- Claim assessed: `CSE conducted 12 industry programmes involving 120 students during 2025-2026 for C3.2.1.`
- Claim ID: `CLM-C3.2.1-001`
- Overall status: `partially_supported`
- Confidence: `0.822`
- Human review required: yes
- Defensible version: `Evidence currently supports: department=CSE; academic_year=2025-2026; activity_type=industry_programme; activity_count=1; participant_count=108.`
- Minimal defensible evidence set:
  - `EVD-CSE-2025-2026-00003`
  - `EVD-CSE-2025-2026-00001`
  - `EVD-CSE-2025-2026-00008`

The agent correctly refused to accept the stronger claim of 12 programmes and
120 students because the available evidence only supported one relevant
programme and showed 108 unique students in the attendance evidence.

## Agent 5: Adaptive Gap Resolution and Readiness Planning

Purpose:

- Normalize integrity findings, evidence gaps, and claim failures into one
  resolution portfolio.
- Merge duplicates so one real-world issue is not handled many times.
- Identify root causes and investigation paths.
- Generate alternative resolution strategies.
- Identify required closure evidence.
- Simulate readiness after resolution.
- Prioritize the minimal set of gaps needed to unblock defensibility.

Specialists implemented:

1. Gap Detector
2. Root-Cause Analyzer
3. Resolution Planner
4. Readiness Simulator
5. Gap Prioritizer

Important files:

- `proofchain/agents/gap_resolution/agent.py`
- `proofchain/agents/gap_resolution/gap_detector.py`
- `proofchain/agents/gap_resolution/root_cause_analyzer.py`
- `proofchain/agents/gap_resolution/resolution_planner.py`
- `proofchain/agents/gap_resolution/readiness_simulator.py`
- `proofchain/agents/gap_resolution/gap_prioritizer.py`
- `proofchain/schemas/gaps.py`

Main output:

- `outputs/runs/{run_id}/gap_resolution_portfolio.json`

Validated behavior from `RUN-20260724-6B9A`:

- Resolution gaps: 9
- Blocking gaps: 7
- Current readiness: `73.0`
- Projected readiness after recommended closure: `96.0`
- Evidence debt score: `76.34`
- Minimal resolution set:
  - `RGAP-0009`
  - `RGAP-0007`
  - `RGAP-0001`
  - `RGAP-0002`
  - `RGAP-0003`
  - `RGAP-0004`
  - `RGAP-0005`

The gap agent intentionally does not close gaps by itself. It creates
resolution plans and readiness projections, but closure still requires evidence,
revalidation, and human approval when applicable.

## Agent 6: Accountability, Ownership, and Escalation

Purpose:

- Resolve provenance and likely responsible roles.
- Match gaps to responsibility types and permissions.
- Balance assignments based on configured workload.
- Choose primary owner, backup owner, and independent approver.
- Produce escalation paths.
- Validate assignment authority and privacy scope.
- Keep recommendations separate from approval.

Specialists implemented:

1. Provenance Resolver
2. Responsibility Matcher
3. Workload Balancer
4. Escalation Planner
5. Assignment Validator

Important files:

- `proofchain/agents/ownership/agent.py`
- `proofchain/agents/ownership/provenance_resolver.py`
- `proofchain/agents/ownership/responsibility_matcher.py`
- `proofchain/agents/ownership/workload_balancer.py`
- `proofchain/agents/ownership/escalation_planner.py`
- `proofchain/agents/ownership/assignment_validator.py`
- `proofchain/schemas/ownership.py`
- `config/organisation_roles.yaml`

Main output:

- `outputs/runs/{run_id}/ownership_assignments.json`

Validated behavior from `RUN-20260724-6B9A`:

- Ownership assignments: 9
- Unresolved ownership records: 0
- Human approvals required: 9
- Auto-approved assignments: 0
- Independent approvers present: yes

The ownership agent correctly produces recommendations only. It does not assign
work, message users, or approve its own recommendations.

## Shared Agentic Runtime

The runtime was extended so compound agents can expose multiple specialist tools
while still using one consistent governance model.

Implemented runtime capabilities:

- Goal creation and dependency-aware goal graph.
- Persisted agent plans.
- Bounded execution budgets.
- Tool routing and tool-call audit logs.
- Observations and reflections per agent.
- Working memory per agent.
- Coordination state shared across agents.
- Peer messages between agents.
- Dynamic resolution subgoals created from peer requests.
- Completion claims and completion decisions.
- Policy-based final decisions.
- Human review routing for unresolved or risky outcomes.

Important files:

- `proofchain/agentic/base_goal_agent.py`
- `proofchain/agentic/goal_manager.py`
- `proofchain/agentic/planner.py`
- `proofchain/agentic/tool_router.py`
- `proofchain/agentic/memory.py`
- `proofchain/agentic/completion_evaluator.py`
- `proofchain/agentic/policies.py`
- `proofchain/agentic/budgets.py`
- `proofchain/repositories/json_coordination_repository.py`

## Synchronization and Traceability

ProofChain now uses checkpointed JSON artifacts and SHA-256 hash references
between pipeline stages. The run repository validates that downstream artifacts
are tied to the committed upstream outputs.

Implemented synchronization artifacts:

- `run_manifest.json`
- `synchronization.json`
- `pipeline_trace.jsonl`
- `goal_graph.json`
- `final_decision.json`
- `coordination/coordination_state.json`
- `coordination/tool_calls.jsonl`
- `coordination/messages.jsonl`
- `coordination/resolution_tasks.json`
- `coordination/completion_claims.json`
- `coordination/decision_rationales.jsonl`

Six synchronized checkpoints are registered:

1. `collection`
2. `classification`
3. `integrity`
4. `claim_intelligence`
5. `adaptive_gap_resolution`
6. `accountability_ownership`

`validate-run` verifies the checkpoint files, checksums, upstream hash chain,
goal graph, coordination state, final decision, and extended outputs.

## Human Governance

Human approval has been implemented as an explicit audit record, not as an
automatic mutation.

Approval capabilities:

- Record approvals or rejections for claim revisions.
- Record approvals or rejections for gap resolution strategies.
- Record approvals or rejections for ownership assignments.
- Record approvals or rejections for escalations.
- Validate that the target object exists before accepting the approval record.
- Preserve original evidence, claims, and recommendations unchanged.

Important files:

- `proofchain/repositories/json_approval_repository.py`
- `proofchain/schemas/governance.py`
- `proofchain/cli.py`

Command:

```powershell
python -m proofchain.cli approve-decision RUN-YYYYMMDD-XXXX `
  --type claim_revision `
  --target CLM-C3.2.1-001 `
  --decision approved `
  --decided-by iqac-chair `
  --reason "Revised value matches verified attendance." `
  --evidence EVD-CSE-2025-2026-00003
```

Supported approval types:

- `claim_revision`
- `gap_resolution_strategy`
- `ownership_assignment`
- `escalation`

Output:

- `outputs/runs/{run_id}/human_approvals.json`

Approval records now also append workflow events. The approval event authorizes a
controlled state transition, such as activating a resolution task or creating a
claim revalidation goal. Original evidence, original claims, and original
recommendation artifacts remain unchanged.

## Agents 7-10

Agent 7, Governed Department Liaison and Task Execution, converts ownership and
resolution recommendations into auditable task decisions and least-disclosure
communications. Unapproved work remains paused.

Agent 8, Evidence Closure and Continuous Revalidation, enforces the rule that
submitted evidence alone never closes a gap. Closure requires submitted evidence,
registration, classification, targeted integrity checks, affected-claim
revalidation, and closure policy satisfaction.

Agent 9, Audit Package Composer and Evidence Manifest, builds a reproducible
draft package manifest with eligible evidence, exclusions, claim lineage,
unresolved warning disclosures, and a package hash.

Agent 10, Adversarial Quality Review and Audit Simulation, challenges the draft
package as a skeptical reviewer. It checks package completeness, references,
claim support, evidence reuse, policy disclosure, reviewer friction, and audit
failure risk. It returns packages for correction when claims or warnings are not
ready for approval.

## Canonical Issues

The implementation now writes:

- `canonical_issues.json`
- `workflow_events.jsonl`
- `component_registry.json`
- `security_scan_result.json`
- `prompt_injection_findings.json`
- `pii_redaction_manifest.json`

The executive report separates raw findings from canonical issue counts:

```json
{
  "raw_findings": 9,
  "claim_failures": 1,
  "raw_gaps": 5,
  "canonical_issues": 9,
  "blocking_canonical_issues": 7,
  "resolution_tasks": 9
}
```

This prevents users from confusing raw validation findings, evidence gaps,
claim-level failures, and actionable resolution issues.

## Counterfactual Readiness

Projected readiness is now explicitly labeled as counterfactual:

```json
{
  "current_verified_readiness": 73.0,
  "projected_readiness": 96.0,
  "projection_type": "counterfactual",
  "projection_confidence": 0.78,
  "not_an_approval": true
}
```

The report includes assumptions, unresolved dependencies, and conservative,
expected, and optimistic scenario bands.

## CLI Commands

Run the ten-agent pipeline:

```powershell
python -m proofchain.cli run-pipeline `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026 `
  --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1 `
  --objective "Determine whether the CSE evidence and institutional claims are audit-ready." `
  --claim "CSE conducted 12 industry programmes involving 120 students during 2025-2026 for C3.2.1."
```

Validate a run:

```powershell
python -m proofchain.cli validate-run RUN-YYYYMMDD-XXXX
```

Run implementation checks:

```powershell
python -m compileall -q proofchain tests
python -m ruff check proofchain tests
python -m pytest -q
```

## Main Output Files

For each pipeline run, the most important files are written under:

```text
outputs/runs/{run_id}/
```

Key artifacts:

- `evidence_registry.json`: registered evidence and checksums.
- `classified_evidence.json`: extracted fields, document classification, and
  requirement mappings.
- `integrity_result.json`: integrity rules, findings, gaps, and stage result.
- `claim_decisions.json`: atomic claim validation, contradictions, sufficiency,
  defensible wording, and lineage.
- `gap_resolution_portfolio.json`: normalized gaps, root causes, strategies,
  dependency graph, readiness simulation, and priorities.
- `ownership_assignments.json`: primary owners, backups, approvers, escalation
  paths, and validation results.
- `claim_resolution_ownership_report.json`: consolidated executive report for
  claim, gap, ownership, lifecycle, package, and quality status.
- `canonical_issues.json`: canonical issue identities and lifecycle state.
- `resolution_tasks_detailed.json`: governed department liaison task decisions.
- `communications.json`: least-disclosure communication records.
- `closure_revalidation_report.json`: closure checks and issue transitions.
- `audit_package_manifest.json`: draft package manifest and package hash.
- `quality_review_report.json`: adversarial package review and correction route.
- `workflow_events.jsonl`: append-only operational event stream.
- `component_registry.json`: primary-agent and specialist-module declarations.
- `human_approvals.json`: explicit human approval or rejection records, when
  recorded.
- `goal_graph.json`: primary goals and dynamic resolution subgoals.
- `final_decision.json`: final policy decision for the run.
- `pipeline_trace.jsonl`: stage trace.
- `synchronization.json`: checkpoint hash chain.

## Validated End-to-End Sample Run

Latest run ID:

```text
RUN-20260724-3A4C
```

Validation command:

```powershell
python -m proofchain.cli validate-run RUN-20260724-3A4C
```

Validation result:

```json
{
  "run_id": "RUN-20260724-3A4C",
  "valid": true
}
```

Pipeline result:

- Status: `blocked`
- Evidence registered: 15
- Documents classified: 15
- Integrity findings: 9
- Integrity gaps: 5
- Claims assessed: 1
- Resolution gaps: 9
- Ownership assignments: 9
- Canonical issues: 9
- Resolution tasks: 9
- Closure checks: 9
- Resolved issues: 0
- Package eligible evidence: 14
- Quality required corrections: 2
- Unresolved ownership: 0
- Claims requiring review: 1
- Blocking findings: 12
- Supervisor rounds: 1
- Extended report:
  `outputs/runs/RUN-20260724-3A4C/claim_resolution_ownership_report.json`

The `blocked` result is correct for the sample dataset. The sample data contains
intentional problems such as missing required documents, a missing signature,
duplicate attendance rows, duplicate evidence content, and a mismatch between
reported participants and unique attendance identifiers. A correct agentic
system should not declare this run audit-ready.

## Tests Added or Extended

Claim validation tests:

- `tests/claim_validation/test_claim_specialists.py`
- Tests claim decomposition, supporting evidence, counter-evidence, partial
  support, defensible claim repair, and lineage.

Gap resolution tests:

- `tests/gap_resolution/test_gap_specialists.py`
- Tests gap normalization, duplicate merging, root-cause analysis, resolution
  strategies, required closure evidence, readiness deltas, dependencies, and
  priority ranking.

Ownership tests:

- `tests/ownership/test_ownership_specialists.py`
- Tests owner selection, workload balancing, independent approver selection,
  backup owners, escalation paths, and unresolved unauthorized ownership cases.

Governance tests:

- `tests/governance/test_human_approval.py`
- Tests human approval target validation and rejection of invalid approval
  targets.

Workflow tests:

- `tests/workflow/test_supervisor_pipeline.py`
- Verifies the ten-stage pipeline, checkpoint artifacts, extended outputs,
  primary agent traces, dynamic resolution subgoals, goal completion records,
  and run validation.

## Implementation Completeness Checklist

- Six primary agents implemented: complete.
- Agents 4, 5, and 6 implemented as compound agents: complete.
- Five specialists per new compound agent: complete.
- Agentic goals, plans, observations, reflections, memory, and completion
  decisions: complete.
- Supervisor integration after integrity: complete.
- Goal dependency order: complete.
- Dynamic peer-resolution subgoals: complete.
- JSON artifact persistence for claims, gaps, ownership, and consolidated
  report: complete.
- SHA-linked synchronization checkpoints: complete.
- Human approval repository and CLI command: complete.
- Validation for approval target existence: complete.
- Tests for claim, gap, ownership, governance, and workflow behavior: complete.
- End-to-end run validation: complete.
- Documentation and operating instructions: complete.

## Current Boundaries

The system is intentionally governed:

- It recommends claim revisions but does not rewrite institutional claims.
- It recommends resolution strategies but does not mark gaps closed.
- It recommends owners but does not assign work or send messages.
- It records human approvals but does not mutate evidence or decision artifacts.
- It blocks final readiness when evidence remains defective.

These boundaries are important for accreditation workflows because the system
must be explainable, traceable, and auditable.

## How to Confirm It Yourself

From the project root:

```powershell
cd C:\SideQuest\ProofChain
python -m compileall -q proofchain tests
python -m ruff check proofchain tests
python -m pytest -q
python -m proofchain.cli validate-run RUN-20260724-6B9A
```

Then open:

```text
outputs/runs/RUN-20260724-6B9A/claim_resolution_ownership_report.json
```

You should see:

- `overall_status`: `not_yet_defensible`
- `human_approval_required`: `true`
- `claim_assessment.total_claims`: `1`
- `gap_assessment.total_gaps`: `9`
- `gap_assessment.blocking_gaps`: `7`
- `ownership_summary.assigned_tasks`: `9`
- `ownership_summary.unresolved_ownership`: `0`

That confirms the implementation is functioning according to the intended
agentic workflow: it plans, reasons, coordinates, produces recommendations,
preserves synchronization, and refuses to falsely pass weak evidence.
