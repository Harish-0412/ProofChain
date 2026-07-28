# ProofChain Complete 22-Agent Architecture, Implementation, and Operations

## Document Purpose

This document is the complete implementation record for ProofChain after the Phase 1
and Phase 2 agentic expansions. It explains:

- What the project now does
- All 22 primary agents
- How every agent plans, acts, reflects, and completes
- How agents are connected
- Which components remain deterministic specialists
- How persistence, authorization, security, tenancy, submission, evaluation, and
  retrieval are governed
- Which artifacts are generated
- How to run and validate the complete project

Implementation date: 2026-07-27

Latest complete validation run: `RUN-20260727-0F23`

Automated validation: `80 passed`

---

## 1. Current System

ProofChain is a governed accreditation evidence platform with three connected layers.

```text
Accreditation Intelligence Core
    Agents 1-10

Production Control Plane
    Agents 11-16

Institutional Governance and Assurance
    Agents 17-22
```

The complete lifecycle is:

```text
Discover
    -> Understand
    -> Verify
    -> Defend
    -> Plan
    -> Assign
    -> Coordinate
    -> Revalidate
    -> Package
    -> Challenge
    -> Persist
    -> Resume
    -> Authorize
    -> Integrate
    -> Secure
    -> Recover
    -> Evolve Schemas
    -> Govern Policies
    -> Isolate Tenants
    -> Control Submission
    -> Evaluate Releases
    -> Retrieve Cited Guidance
```

The system uses deterministic reasoning and rules for all current decisions. The
model-governance manifest records zero external model calls.

---

## 2. Architectural Overview

```mermaid
flowchart TD
    U[Institutional User, CLI, or API] --> S[Master Goal Supervisor]

    subgraph Core["Agents 1-10: Accreditation Intelligence"]
        A1[1 Evidence Collector]
        A2[2 Evidence Classification]
        A3[3 Evidence Integrity]
        A4[4 Claim Intelligence]
        A5[5 Gap Resolution]
        A6[6 Ownership]
        A7[7 Department Liaison]
        A8[8 Closure Revalidation]
        A9[9 Audit Package Composer]
        A10[10 Adversarial Quality Review]
    end

    subgraph Production["Agents 11-16: Production Control Plane"]
        A11[11 Persistence and Recovery]
        A12[12 Continuation]
        A13[13 Identity and Authorization]
        A14[14 Integration and Notification]
        A15[15 Security Inspection]
        A16[16 Reliability and Incident Response]
    end

    subgraph Institution["Agents 17-22: Institutional Governance"]
        A17[17 Schema Evolution]
        A18[18 Policy Lifecycle]
        A19[19 Tenant Governance]
        A20[20 External Submission]
        A21[21 Continuous Evaluation]
        A22[22 Governed Retrieval]
    end

    S --> Core
    S --> Production
    S --> Institution

    A15 --> A1
    A13 --> A7
    A13 --> A14
    A14 --> A12
    A12 --> Core
    A9 --> A10
    A10 --> A20
    A13 --> A20
    A19 --> A20
    A17 --> Core
    A18 --> Core
    A21 --> Core
    A21 --> Production
    A21 --> Institution
    A22 --> A2
    A22 --> A4
    A22 --> A10
    A11 <--> Core
    A11 <--> Production
    A11 <--> Institution
```

---

## 3. What Counts as an Agent

A primary ProofChain agent must:

1. Accept a typed goal.
2. Observe current state.
3. Create an explicit plan.
4. Select allowlisted tools.
5. Interpret structured observations.
6. Retry or replan within a budget.
7. Persist working memory and reasoning.
8. Coordinate through the shared run graph.
9. Handle uncertainty and human-review boundaries.
10. Produce an explainable completion decision.

A fixed operation remains a service, repository, adapter, scanner, evaluator, or
deterministic specialist.

The current component registry contains:

```text
Primary goal agents: 22
Deterministic specialist modules: 132
External model calls: 0
```

---

## 4. Shared Goal-Agent Runtime

All 22 agents use the same bounded control model.

```text
Goal
    -> Plan
    -> Select Step
    -> Propose Allowlisted Action
    -> Execute Deterministic Tool
    -> Observe
    -> Reflect
    -> Continue, Retry, Replan, Wait, Escalate, or Complete
    -> Completion Decision
```

Every agent stores:

```text
goal.json
plans.json
observations.jsonl
reflections.jsonl
working_memory.json
completion_decision.json
completion_decisions/{goal_id}.json
```

Every tool call records:

- Tool and version
- Agent and goal
- Status
- Execution time
- Result summary
- Source references
- Warnings and errors

Default limits:

```yaml
max_plan_revisions: 3
max_action_rounds: 12
max_tool_retries_per_step: 2
max_peer_requests: 6
max_runtime_seconds: 600
```

Budget exhaustion results in `BLOCKED` or `NEEDS_HUMAN_REVIEW`, never an infinite loop.

---

## 5. Agents 1-10: Accreditation Intelligence Core

### Agent 1: Evidence Collector

Purpose: discover and register institutional evidence.

Workflow:

```text
Scan approved source roots
    -> Identify files
    -> Calculate checksums
    -> Assign evidence and version IDs
    -> Detect exact duplicates
    -> Persist evidence registry
```

Produces `evidence_registry.json`.

It cannot interpret claims or approve evidence.

### Agent 2: Evidence Classification

Purpose: understand document type, fields, event identity, and requirement relevance.

Workflow:

```text
Load registered evidence
    -> Extract PDF, spreadsheet, image, or metadata content
    -> Classify document type
    -> Extract fields
    -> Map accreditation requirements
    -> Resolve event consensus
    -> Route uncertainty
```

Produces `classified_evidence.json`.

Extracted content is treated as untrusted data.

### Agent 3: Evidence Integrity

Purpose: verify evidence completeness and consistency.

Workflow:

```text
Bundle related evidence
    -> Apply versioned deterministic rules
    -> Detect missing documents
    -> Detect contradictions and duplicates
    -> Create integrity findings
    -> Create evidence gaps
    -> Calculate integrity status
```

Produces integrity findings, gaps, bundles, and summaries.

It cannot waive findings or close issues.

### Agent 4: Claim Intelligence

Purpose: determine whether institutional claims are defensible.

Workflow:

```text
Decompose claim
    -> Retrieve supporting evidence
    -> Retrieve contradicting evidence
    -> Evaluate sufficiency
    -> Judge defensibility
    -> Recommend bounded wording
```

Produces `claim_decisions.json`.

It does not rewrite the original human claim.

### Agent 5: Adaptive Gap Resolution

Purpose: create executable correction strategies.

Workflow:

```text
Normalize gaps
    -> Identify root cause
    -> Generate resolution alternatives
    -> Evaluate dependencies and evidence debt
    -> Simulate counterfactual readiness
    -> Prioritize resolution
```

Produces `gap_resolution_portfolio.json`.

Projected readiness is counterfactual and cannot replace current readiness.

### Agent 6: Accountability and Ownership

Purpose: recommend responsible and accountable institutional owners.

Workflow:

```text
Resolve provenance
    -> Match responsibilities to roles
    -> Evaluate workload
    -> Check permission boundaries
    -> Recommend owner and backup
    -> Plan escalation
```

Produces `ownership_assignments.json`.

Recommendations do not activate tasks without approval.

### Agent 7: Department Liaison

Purpose: turn approved resolutions into governed department tasks.

Workflow:

```text
Resolve communication scope
    -> Compose immutable task draft
    -> Draft minimum-disclosure message
    -> Verify approval
    -> Record dispatch state
    -> Correlate response
    -> Evaluate SLA escalation
```

Produces resolution task and communication artifacts.

Task state changes are append-only events.

### Agent 8: Closure Revalidation

Purpose: decide whether corrective evidence resolves an issue.

Workflow:

```text
Intake submitted correction
    -> Compare old and new evidence
    -> Run targeted validation
    -> Detect regression
    -> Verify closure conditions
    -> Resolve, reject, reopen, or escalate issue
```

Produces `closure_revalidation_report.json`.

Uploading a replacement never closes an issue automatically.

### Agent 9: Audit Package Composer

Purpose: build a reproducible internal audit package.

Workflow:

```text
Freeze scope
    -> Select eligible evidence
    -> Explain exclusions
    -> Order evidence
    -> Compose grounded narrative
    -> Build cross-reference index
    -> Apply privacy rules
    -> Assemble and hash package
```

Produces `audit_package_manifest.json` and `audit_package_internal.zip`.

It cannot externally submit the package.

### Agent 10: Adversarial Quality Review

Purpose: challenge the package before human approval.

Workflow:

```text
Check completeness
    -> Resolve references
    -> Challenge claims
    -> Audit evidence reuse
    -> Review package policy
    -> Simulate reviewer journey
    -> Score audit failure risk
```

Produces `quality_review_report.json`.

It may require correction but cannot approve external submission.

---

## 6. Agents 11-16: Production Control Plane

### Agent 11: Operational Persistence and Recovery

Purpose: make workflow state durable and reconstructable.

Workflow:

```text
Check SQL store
    -> Reconcile JSON events
    -> Import missing events transactionally
    -> Rebuild aggregate state
    -> Create snapshot
    -> Validate sequence and hash chain
    -> Compare reconstruction hash
```

Supports SQLite and PostgreSQL. JSON remains an auditable export.

Produces `persistence_recovery_report.json` and `operational_state.db` locally.

### Agent 12: Continuation and Partial Re-Execution

Purpose: resume runs and calculate the smallest affected execution scope.

Workflow:

```text
Fingerprint artifacts
    -> Detect additions, removals, and changes
    -> Traverse dependencies
    -> Mark stale outputs
    -> Preserve reusable outputs
    -> Resume waiting goals
    -> Suppress duplicate actions
```

Produces `continuation_reexecution_plan.json`.

### Agent 13: Identity and Authorization

Purpose: enforce real institutional authority over protected actions.

Workflow:

```text
Resolve verified identity
    -> Load tenant and department roles
    -> Apply valid delegation
    -> Match permission
    -> Detect conflict and self-approval
    -> Count independent approvals
    -> Authorize, deny, or request another approval
```

Produces `authorization_decision.json`.

### Agent 14: Integration and Notification

Purpose: deliver approved work exactly once.

Workflow:

```text
Verify approval
    -> Select channel
    -> Build minimum-disclosure payload
    -> Check idempotency ledger
    -> Dispatch
    -> Retry or use fallback
    -> Persist receipt and correlation state
```

Supports recording, SMTP, Teams, Slack, and generic HTTPS webhooks.

Produces `notification_delivery_report.json`.

### Agent 15: Security Inspection and Evidence Safety

Purpose: stop unsafe evidence before ordinary processing.

Workflow:

```text
Verify path and file identity
    -> Enforce size and type limits
    -> Detect malware indicators
    -> Inspect archives
    -> Inspect spreadsheet formulas and hidden sheets
    -> Detect prompt injection
    -> Detect PII
    -> Allow, restrict, redact, quarantine, or reject
```

Produces `phase_one_security_report.json` and non-destructive quarantine copies.

### Agent 16: Reliability and Incident Response

Purpose: correlate failures and coordinate bounded recovery.

Workflow:

```text
Observe telemetry
    -> Detect abnormal signals
    -> Correlate failure group
    -> Classify severity
    -> Select retry, failover, pause, or human escalation
    -> Verify data integrity
    -> Persist incident
```

Produces `incident_reliability_report.json`.

---

## 7. Agents 17-22: Institutional Governance and Assurance

### Agent 17: Data Contract and Schema Evolution

Purpose: evolve schemas without silently breaking historical artifacts.

Independent plan:

```text
Read schema registry
    -> Compare current and target contracts
    -> Detect removed fields, new requirements, and type changes
    -> Plan mappings and defaults
    -> Convert immutable copies
    -> Calculate original and converted hashes
    -> Gate deployment
```

Decisions:

```text
Compatibility:
    backward_compatible
    migration_required
    incompatible

Deployment:
    PASS
    BLOCK
    NEEDS_HUMAN_APPROVAL
```

The agent never modifies historical artifacts. Conversion creates copies with linked
before-and-after hashes.

Specialists:

- Schema Registry Reader
- Compatibility Analyzer
- Migration Planner
- Artifact Converter
- Regression Validator
- Deployment Gate

Produces `schema_evolution_report.json`.

### Agent 18: Policy Lifecycle and Governance Consistency

Purpose: version policy safely and prevent contradictory or retroactive governance.

Independent plan:

```text
Parse proposed policy
    -> Validate identity and version
    -> Detect deny-by-default conflicts
    -> Detect approval bypass
    -> Replay historical cases
    -> Identify affected open runs
    -> Require approval before activation
```

Decisions:

```text
NO_CHANGE
ACTIVATE
BLOCK
NEEDS_HUMAN_APPROVAL
```

Historical decisions are never rewritten. Simulation shows counterfactual impact only.

Specialists:

- Policy Parser
- Conflict Detector
- Impact Analyzer
- Historical Replay Simulator
- Policy Version Manager
- Activation Gate

Produces `policy_lifecycle_report.json`.

### Agent 19: Multi-Tenant Institution Governance

Purpose: prevent leakage between institutions, campuses, and departments.

Independent plan:

```text
Resolve subject and tenant
    -> Resolve resource tenant
    -> Evaluate department boundary
    -> Detect cross-tenant access
    -> Validate approved resource share
    -> Match effective permission
    -> Allow or deny
```

Default behavior is deny.

Cross-tenant access requires a resource-specific, approved, non-expired share with the
required permission and department scope.

Specialists:

- Tenant Resolver
- Scope Boundary Evaluator
- Cross-Tenant Access Detector
- Tenant Policy Resolver
- Resource Sharing Planner
- Isolation Completion Evaluator

Produces `tenant_access_decision.json`.

### Agent 20: External Submission and Regulatory Handoff

Purpose: submit only an approved, frozen, current package while preserving final human
control.

Independent plan:

```text
Verify quality status
    -> Calculate current package hash
    -> Compare approved hash
    -> Validate independent approval
    -> Check deadline
    -> Require final confirmation
    -> Check idempotency ledger
    -> Submit through approved portal
    -> Verify receipt
```

Decisions:

```text
Eligibility:
    ELIGIBLE
    NOT_ELIGIBLE
    NEEDS_FINAL_CONFIRMATION

Submission:
    not_submitted
    submitted
    duplicate_suppressed
    rejected
    failed
```

The agent cannot modify the package, submit a stale hash, hide rejection, bypass human
confirmation, or repeat an irreversible submission.

Adapters:

- Local recording submission portal
- HTTPS institutional or regulatory portal

Specialists:

- Submission Eligibility Evaluator
- Portal Adapter Selector
- Payload Validator
- Final Confirmation Gate
- Submission Executor
- Receipt Verifier
- Rejection Handler
- Completion Evaluator

Produces `external_submission_report.json`, `submission_outbox.jsonl`, and
`submission_idempotency.json`.

### Agent 21: Continuous Evaluation and System Assurance

Purpose: block releases that increase false approvals, false closures, or decision
regression.

Independent plan:

```text
Resolve golden dataset
    -> Bind release thresholds
    -> Run scenarios
    -> Compare expected and observed decisions
    -> Calculate accuracy
    -> Calculate false approvals and false closures
    -> Calculate calibration error
    -> Compare baseline
    -> Pass or block release
```

Measured metrics:

- Decision accuracy
- False approval rate
- False closure rate
- Calibration error
- Accuracy regression from baseline

Specialists:

- Dataset Resolver
- Evaluation Planner
- Scenario Runner
- Metric Calculator
- Regression Detector
- Calibration Evaluator
- Release Decision Evaluator

Produces `continuous_evaluation_report.json`.

### Agent 22: Governed Knowledge Retrieval and Research Assistance

Purpose: provide cited, authoritative context without becoming a decision authority.

Independent plan:

```text
Normalize query
    -> Reject unapproved sources
    -> Rank source authority
    -> Rank lexical relevance
    -> Retrieve supporting guidance
    -> Retrieve conflicting or superseding guidance
    -> Check freshness
    -> Build source hashes and citations
    -> Produce advisory answer
```

Source priority:

```text
Official framework
    -> Institutional policy
    -> Approved procedure
    -> Historical package
    -> Advisory example
```

Retrieved text is untrusted data. It cannot change instructions, policy, permissions,
claim decisions, closure decisions, or approvals.

Specialists:

- Query Planner
- Source Authority Evaluator
- Semantic Retriever
- Contradiction Retriever
- Citation Builder
- Freshness Evaluator
- Completion Evaluator

Produces `governed_knowledge_retrieval_report.json`.

---

## 8. Supervisor Wiring

### Core Supervisor

The core supervisor decomposes the accreditation objective into Agents 1-10 and manages
their dependency graph.

### Phase 1 Supervisor

The Phase 1 supervisor attaches operational controls to a completed core run:

```text
Security
    -> Authorization
    -> Integration
    -> Continuation
    -> Reliability
    -> Persistence synchronization
```

### Phase 2 Supervisor

The Phase 2 supervisor requires a successful Phase 1 result and executes:

```text
Schema Evolution
    -> Policy Lifecycle
    -> Tenant Governance
    -> Submission Eligibility and Handoff
    -> Continuous Evaluation
    -> Governed Retrieval
    -> Agent 11 Persistence Resynchronization
```

Phase 2 then:

- Registers Agents 17-22
- Registers 40 Phase 2 deterministic specialists
- Refreshes the policy fingerprint
- Extends model-governance profiles
- Updates observability counts
- Synchronizes Phase 2 events into SQL
- Writes `phase_two_result.json`

---

## 9. Inter-Agent Synchronization

Agents coordinate through:

- Top-level goal
- Goal graph
- Versioned coordination state
- Agent plans
- Open and resolved messages
- Completion claims
- Append-only workflow events
- Hash-linked checkpoints
- Artifact references
- Canonical issue IDs
- Authorization and approval event IDs

No agent overwrites another agent's plan.

No shared state transition occurs without a persisted artifact or event.

Agent 11 reconstructs aggregate state after both Phase 1 and Phase 2 so the SQL event
store includes all governance decisions.

---

## 10. Governance Policies

The complete policy manifest fingerprints 16 required policies:

```text
agent_permissions.yaml
approval_policy.yaml
communication_policy.yaml
closure_policy.yaml
package_policy.yaml
security_policy.yaml
retention_policy.yaml
identity_policy.yaml
notification_policy.yaml
recovery_policy.yaml
schema_evolution_policy.yaml
policy_lifecycle_policy.yaml
tenant_policy.yaml
submission_policy.yaml
evaluation_policy.yaml
retrieval_policy.yaml
```

All agent permissions are deny by default.

High-impact actions remain human-controlled:

- Ownership activation
- Waiver
- Policy activation
- Breaking schema deployment
- External package submission

---

## 11. Data and Persistence

ProofChain uses:

```text
JSON artifacts
    Human-readable and auditable exports

JSONL workflow events
    Append-only local event history

SQLite
    Zero-configuration transactional operational store

PostgreSQL
    Production operational event-store adapter
```

The SQL store enforces:

- Event ID uniqueness
- Run sequence uniqueness
- Transaction commit and rollback
- Previous-event linkage
- SHA-256 hash linkage
- Snapshot version
- Reconstructable aggregate state

---

## 12. Complete Artifact Set

Important run artifacts include:

```text
pipeline_result.json
evidence_registry.json
classified_evidence.json
integrity_findings.json
evidence_gaps.json
claim_decisions.json
gap_resolution_portfolio.json
ownership_assignments.json
canonical_issues.json
resolution_tasks_detailed.json
closure_revalidation_report.json
audit_package_manifest.json
audit_package_internal.zip
quality_review_report.json

phase_one_result.json
persistence_recovery_report.json
continuation_reexecution_plan.json
authorization_decision.json
notification_delivery_report.json
phase_one_security_report.json
incident_reliability_report.json
operational_state.db

phase_two_result.json
schema_evolution_report.json
policy_lifecycle_report.json
tenant_access_decision.json
external_submission_report.json
continuous_evaluation_report.json
governed_knowledge_retrieval_report.json

goal_graph.json
coordination/coordination_state.json
workflow_events.jsonl
component_registry.json
governance_policy_manifest.json
model_governance_manifest.json
observability_metrics.json
```

---

## 13. How to Run the Complete Project

### Install

```powershell
cd C:\SideQuest\ProofChain
python -m pip install -e ".[dev]"
```

For PostgreSQL:

```powershell
python -m pip install -e ".[postgres]"
```

### Step 1: Run Agents 1-10

```powershell
python -m proofchain.cli run-pipeline `
  --source sample_data/departments/CSE `
  --departments CSE `
  --academic-year 2025-2026 `
  --requested-by local-user `
  --claim "CSE maintained complete evidence for criterion C3.2.1."
```

Record the returned run ID.

### Step 2: Run Agents 11-16

```powershell
python -m proofchain.cli run-phase-one RUN-YYYYMMDD-XXXX
```

### Step 3: Run Agents 17-22

```powershell
python -m proofchain.cli run-phase-two RUN-YYYYMMDD-XXXX `
  --tenant-id default-institution `
  --department-id CSE `
  --query "What governance rules apply to accreditation evidence and submission?"
```

### Step 4: Validate

```powershell
python -m proofchain.cli validate-run RUN-YYYYMMDD-XXXX
```

### Step 5: Replay Events

```powershell
python -m proofchain.cli replay-run RUN-YYYYMMDD-XXXX
```

---

## 14. PostgreSQL Operation

```powershell
$env:PROOFCHAIN_DATABASE_URL = "postgresql://user:password@host:5432/proofchain"

python -m proofchain.cli run-phase-one RUN-YYYYMMDD-XXXX `
  --backend postgres `
  --database-url $env:PROOFCHAIN_DATABASE_URL

python -m proofchain.cli run-phase-two RUN-YYYYMMDD-XXXX `
  --backend postgres `
  --database-url $env:PROOFCHAIN_DATABASE_URL
```

Use an institutional secret manager in production.

---

## 15. External Submission Procedure

ProofChain does not submit the intentionally defective sample package.

A real submission requires:

1. Quality status `pass_for_human_approval` or `pass_with_warnings`.
2. Current package file exists.
3. Current package SHA-256 matches the approved hash.
4. Independent approval references that exact hash.
5. No rejection exists.
6. Submission deadline is valid.
7. Final human confirmation is true.
8. Idempotency key has not been used.
9. Approved portal adapter is configured.

Only then can Agent 20 create a receipt.

---

## 16. Validation Results

Commands:

```powershell
python -m compileall -q proofchain tests
python -m ruff check proofchain tests
python -m pytest -q
```

Results:

```text
Compilation: passed
Ruff lint: passed
Tests: 80 passed
```

Complete end-to-end validation:

```text
Run ID: RUN-20260727-0F23
Core status: blocked
Phase 1 status: completed
Phase 2 status: completed_with_warnings
Run validation: valid = true
Primary agents: 22
Deterministic specialists: 132
Fingerprint policies: 16
Persisted operational events: 30
Recovery verified: true
Corruption findings: 0
Evaluation accuracy: 1.0
False approval rate: 0.0
False closure rate: 0.0
Evaluation release decision: PASS
Knowledge citations: 5
Retrieval advisory-only: true
Submission eligibility: NOT_ELIGIBLE
Submission status: not_submitted
```

The Phase 2 warning is correct. The sample package still has unresolved quality
corrections and no independent hash-bound submission approval. Agent 20 refused to
submit it.

---

## 17. New Phase 2 Tests

Nine Phase 2 tests validate:

- Breaking schema detection
- Immutable artifact conversion
- Policy bypass conflict detection
- Historical policy simulation
- Cross-tenant access denial
- Explicit scoped sharing
- Hash-bound independent submission approval
- Exactly-once submission
- False approval and false closure regression gates
- Approved and current citation sources
- Complete Phase 2 supervisor orchestration
- Final SQL event-store synchronization

Together with the existing tests, the complete suite contains 80 passing tests.

---

## 18. Deployment Boundaries

The project is executable locally. Live institutional deployment requires configuration:

- PostgreSQL connection and Psycopg package
- Institutional SSO assertion provider
- SMTP or Teams/Slack webhook credentials
- Production malware-scanner integration
- Regulatory portal endpoint and credentials
- Institution-approved source corpus
- Production metrics, traces, logs, and queue signals

Missing external configuration does not bypass governance. The system uses safe local
recording adapters, refuses the action, or routes it for human review.

---

## 19. Final Architecture Status

ProofChain now provides:

- Governed accreditation evidence analysis
- Defensible claim evaluation
- Canonical gaps and accountable resolution
- Formal revalidation and closure
- Reproducible audit packages
- Adversarial package review
- Durable transactional recovery
- Resumable partial execution
- Enterprise authorization controls
- Idempotent communication
- Evidence safety and quarantine
- Incident classification and recovery
- Backward-compatible schema evolution
- Versioned policy governance
- Tenant and department isolation
- Human-controlled external submission
- Continuous release assurance
- Authoritative cited retrieval

The next engineering work should focus on deployment surfaces rather than adding more
primary agents:

```text
REST API
    -> Enterprise SSO
    -> PostgreSQL deployment
    -> Queue workers
    -> Production notification providers
    -> Regulatory portal adapters
    -> Operations dashboard
    -> Multi-institution deployment
```
