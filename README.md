# ProofChain

ProofChain is an accreditation evidence integrity and governance system for educational institutions.

## Three-Department Mock Institution

A deterministic synthetic dataset for `AIML`, `AIDS`, and `CSE` is available
under `sample_data/mock_institution`. It contains 30 students per department
(15 female and 15 male), 15 complete accreditation event bundles, and evidence
across every supported native format.

See [the mock dataset guide](sample_data/mock_institution/README.md) for the
data contract, validation command, and complete 22-agent run command.

## Complete Governed Reference Platform

ProofChain now provides a complete local 22-agent lifecycle with advanced
cognition, hash-linked coordination, SQLite/PostgreSQL operational persistence,
security and identity controls, institutional governance, ten release-assurance
golden scenarios, an artifact-backed FastAPI gateway, and a live Next.js
operator dashboard.

Run the complete lifecycle with:

```powershell
proofchain run-complete `
  --source sample_data/departments `
  --departments CSE `
  --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1
```

ProofChain registers every discovered file and returns an explicit native,
metadata-only, unsupported, or rejected processing outcome. It does not claim
that every proprietary binary format can be interpreted.

See the
[final completion, architecture, validation, and operations record](docs/ProofChain_Final_22_Agent_Completion_Architecture_Validation_and_Operations.md).

The MVP focuses on one complete evidence workflow:

```text
Requirement -> Claim -> Evidence -> Extraction -> Mapping -> Verification -> Gap -> Task -> Approval -> Audit Package
```

The first version should prove that an institution can upload or ingest evidence, extract useful facts, map documents to accreditation requirements, detect missing or inconsistent proof, create corrective tasks, and generate an audit-ready package with traceability.

## Current Implementation

The reference accreditation profile is intentionally bounded:

- Five departments
- Five accreditation requirements
- Filesystem and governed manual-source ingestion first
- Google Drive connector planned as optional ingestion
- Deterministic rules first
- One strong deterministic accreditation profile with advanced governed cognition
- JSON-backed audit exports with a transactional SQLite/PostgreSQL operational event store
- Resumable execution, identity authorization, notifications, evidence safety, and incidents

## First Workflow

The first demo workflow should use the CSE department and a student or industry activity requirement.

Example:

```text
CSE claims 120 students attended an industry workshop.
ProofChain checks the event report, attendance spreadsheet, approval document, certificates, and photos.
The system detects a count mismatch, missing signature, duplicate evidence, and missing documents.
It creates tasks, drafts a department notification, and generates an audit package after approval.
```

## Core MVP Modules

- Evidence registry
- Ingestion source tracking
- Document extraction
- Evidence mapping
- Integrity rule engine
- Gap analysis
- Corrective task generation
- Department notification draft workflow
- Human approval center
- Dashboard metrics
- Audit package generator
- Traceability log

## Documentation

- [MVP Modified Architecture](ProofChain_MVP_Modified_Project_Architecture.md)
- [MVP Build Phases and Workflow](docs/ProofChain_MVP_Phases_and_Workflow.md)
- [Phase 0 Foundation](docs/Phase_0_Project_Foundation.md)
- [Phase 1 Evidence Registry and Ingestion](docs/Phase_1_Evidence_Registry_and_Ingestion.md)
- [Phase 2 Sample Dataset Creation](docs/Phase_2_Sample_Dataset_Creation.md)
- [Phase 3 Document Extraction](docs/Phase_3_Document_Extraction.md)
- [Initial Data Schema Draft](docs/Initial_Data_Schema_Draft.md)
- [Agentic Agents Conversion Guide](docs/ProofChain_Agentic_Agents_Conversion_Guide.md)
- [Agents 4-6 Implementation and Operations](docs/ProofChain_Agents_4_6_Implementation_and_Operations.md)
- [Complete Agentic Implementation Report](docs/ProofChain_Complete_Agentic_Implementation_Report.md)
- [Advanced Ten-Agent Architecture and Workflow](docs/ProofChain_Advanced_Ten_Agent_Architecture_and_Workflow.md)
- [Next-Generation Agents Architecture and Plan](docs/ProofChain_Next_Generation_Agents_Architecture_and_Implementation_Plan.md)
- [Phase 1 Production Implementation Report](docs/ProofChain_Phase_1_Production_Implementation_Report.md)
- [Agentic Maturity Two-Phase Implementation Plan](docs/ProofChain_Agentic_Maturity_Two_Phase_Implementation_Plan.md)
- [Sample Dataset Structure](sample_data/README.md)

## Current Build Priority

Complete these first:

1. Phase 0: Project foundation
2. Phase 1: Evidence registry and ingestion
3. Phase 2: Sample dataset creation
4. Phase 3: Document extraction

After those are stable, move to evidence mapping and deterministic validation rules.

## Governed Ten-Agent Pipeline

The implemented pipeline has ten goal-driven domain agents coordinated by a
goal-oriented Supervisor:

1. Evidence Collector: discovery, checksums, durable IDs, versions, and duplicates.
2. Evidence Classification: extraction, type classification, field extraction, requirement
   mapping, confidence routing, and event consensus.
3. Evidence Integrity: event bundling, versioned rules, findings, gaps, and integrity scores.
4. Claim Intelligence: atomic claims, two-sided evidence, contradictions, sufficiency,
   lineage, fragility, and defensible claim alternatives.
5. Adaptive Gap Resolution: normalized gaps, root causes, resolution alternatives,
   dependencies, evidence debt, readiness simulation, and priority.
6. Accountability and Ownership: provenance, role matching, workload, permissions,
   independent approval, backups, and escalation recommendations.
7. Department Liaison: governed task activation, least-disclosure communication,
   response intake, and SLA escalation state.
8. Closure Revalidation: submitted-evidence checks, targeted revalidation, closure
   policy, issue transitions, and reopen/reject states.
9. Audit Package Composer: eligible evidence selection, exclusions, lineage,
   reproducible manifest hash, unresolved warning disclosure, and a deterministic
   internal ZIP evidence bundle.
10. Adversarial Quality Review: package completeness, reference checks, claim
    challenges, omission checks, reviewer friction, risk scoring, and correction routing.

Each agent accepts a goal, persists a plan, executes approved deterministic tools, records
observations and structured rationales, reflects within a bounded budget, coordinates through
a versioned run blackboard, and emits a policy-validated completion decision. Stage outputs
still use atomic JSON artifacts, append-only workflow events, canonical issue IDs,
SHA-256 synchronization checkpoints, machine-readable policy fingerprints,
tamper-evident event links, scheduler round audits, and run observability metrics.

```powershell
proofchain run-pipeline `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026 `
  --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1 `
  --objective "Determine whether the CSE evidence set is defensible." `
  --claim "CSE conducted 12 industry programmes involving 120 students during 2025-2026 for C3.2.1."
```

Use `--max-agent-rounds`, `--max-replans`, and `--require-human-approval` to
control bounded autonomy. Run artifacts are written to `outputs/runs/{run_id}`.
Validate a completed run with:

```powershell
proofchain validate-run RUN-YYYYMMDD-XXXX
proofchain validate-agentic-run RUN-YYYYMMDD-XXXX
```

## Platform-Wide Advanced Cognition

All 22 primary agents use the `advanced-cognition-platform` profile. Every dispatched goal
interprets scope, validates inputs before planning, snapshots context, forms
competing hypotheses, creates and criticizes a risk-aware plan, selects actions
by expected information gain, normalizes tool observations, records structured
reflection and decomposed uncertainty, and emits a completion proof plus
decision explanation.

Canonical cognition artifacts are stored under:

```text
outputs/runs/{run_id}/agents/{agent_name}/{goal_id}/
```

The synchronized cross-agent decision ledger is:

```text
outputs/runs/{run_id}/agent_decisions.jsonl
```

The legacy profile remains available only for non-primary compatibility fixtures.
No production primary agent uses it after the Phase 2 migration. Supervisors now
audit every proof, calculate critical paths, enforce peer acceptance conditions,
detect contradictions, record trigger-based global replans, consolidate human
review, aggregate 22 scorecards, and issue an agentic release decision.

The original ten-agent verified reference run is `RUN-20260724-3A4C`. That baseline
had `63` passing tests. See the advanced architecture document for exact workflows,
governance boundaries, generated artifacts, lifecycle commands, and the
production-adapter roadmap.

## Phase 1 Production Agents

Six additional governed goal agents now surround the ten-agent accreditation core:

11. Operational Persistence and State Recovery: transactional SQLite/PostgreSQL
    events, snapshots, reconstruction, hash validation, and JSON reconciliation.
12. Workflow Continuation and Partial Re-Execution: fingerprints, change detection,
    dependency impact, stale scope, safe reuse, resume state, and duplicate suppression.
13. Enterprise Identity and Authorization: verified identity assertions, scoped roles,
    delegation, separation of duties, conflicts, and dual-approval decisions.
14. Integration and Notification: approval-gated recording, SMTP, Teams, Slack, and
    generic HTTPS webhook delivery with idempotency, fallback, and correlation.
15. Security Inspection and Evidence Safety: path boundaries, file limits, archive
    safety, spreadsheet formulas, prompt injection, PII, signatures, restrictions,
    and non-destructive quarantine.
16. Observability, Reliability, and Incident Response: telemetry correlation,
    severity classification, retry budgets, failover, pause, escalation, and
    integrity-aware incident reporting.

Attach these controls to an existing run:

```powershell
proofchain run-phase-one RUN-YYYYMMDD-XXXX
proofchain validate-run RUN-YYYYMMDD-XXXX
```

SQLite is the zero-configuration operational backend. For PostgreSQL:

```powershell
pip install -e ".[postgres]"
proofchain run-phase-one RUN-YYYYMMDD-XXXX `
  --backend postgres `
  --database-url $env:PROOFCHAIN_DATABASE_URL
```

The verified Phase 1 run is `RUN-20260727-09EB`. Its core audit-readiness
decision remained correctly blocked by evidence findings, while all six production
control goals completed successfully. That milestone had `71` passing tests.

## Phase 2 Institutional Governance Agents

The second expansion adds six more governed agents:

17. Data Contract and Schema Evolution
18. Policy Lifecycle and Governance Consistency
19. Multi-Tenant Institution Governance
20. External Submission and Regulatory Handoff
21. Continuous Evaluation and System Assurance
22. Governed Knowledge Retrieval and Research Assistance

Run Phase 2 after Phase 1:

```powershell
proofchain run-phase-two RUN-YYYYMMDD-XXXX `
  --tenant-id default-institution `
  --department-id CSE `
  --query "What governance rules apply to accreditation evidence?"
```

The latest complete advanced 22-agent validation run is `RUN-20260727-416B`.
It contains 22 primary goal agents, 132 deterministic specialist modules, 23
valid completion proofs including final persistence resynchronization, and 10
passing release-assurance scenarios. The complete suite has `100` passing
tests.

See [the Phase 2 platform-wide maturity implementation report](docs/ProofChain_Phase_2_Platform_Wide_Maturity_and_Global_Assurance_Implementation_Report.md).

## GitHub Pages

The public ProofChain landing experience is deployed at:

https://harish-0412.github.io/ProofChain/

GitHub Actions builds the Next.js frontend as a static export whenever frontend
or deployment-workflow files change on `main`. The export includes the landing
page and all statically generated interface routes, including detail routes for
Agents 1-22.

GitHub Pages hosts static files only. Live operational records, run execution,
approvals, and persisted agent state continue to require the ProofChain UI
gateway and backend services described above.

To validate the same Pages artifact locally:

```powershell
cd frontend
$env:GITHUB_PAGES = "true"
$env:GITHUB_REPOSITORY = "Harish-0412/ProofChain"
$env:PAGES_BASE_PATH = "/ProofChain"
$env:NEXT_PUBLIC_BASE_PATH = "/ProofChain"
npm run build
```
