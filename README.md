# ProofChain

ProofChain is an accreditation evidence integrity and governance system for educational institutions.

The MVP focuses on one complete evidence workflow:

```text
Requirement -> Claim -> Evidence -> Extraction -> Mapping -> Verification -> Gap -> Task -> Approval -> Audit Package
```

The first version should prove that an institution can upload or ingest evidence, extract useful facts, map documents to accreditation requirements, detect missing or inconsistent proof, create corrective tasks, and generate an audit-ready package with traceability.

## Current Implementation

The MVP is intentionally narrow:

- Five departments
- Five accreditation requirements
- Manual upload first
- Google Drive connector planned as optional ingestion
- Deterministic rules first
- One strong end-to-end workflow before advanced AI
- JSON-backed event-sourced operational MVP
- Database, notification, and external identity adapters remain deployment choices

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
```

The current verified reference run is `RUN-20260724-3A4C`. The full suite has
`63` passing tests. See the advanced architecture document for exact workflows,
governance boundaries, generated artifacts, lifecycle commands, and the
production-adapter roadmap.
