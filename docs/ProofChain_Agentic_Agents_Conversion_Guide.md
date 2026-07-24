# ProofChain Agentic Agents Conversion Guide

## Purpose

This guide explains:

1. How to run the current ProofChain project by yourself.
2. How to verify that it is behaving according to the intended workflow.
3. How the three agents now plan, reason, act, synchronize, and finish goals safely.

## Implementation Status

As of July 24, 2026, the governed agentic runtime described by this guide is
implemented. The original deterministic services remain the trusted action layer.
The agentic layer now provides:

- institutional top-level goals and decomposed agent subgoals
- persisted plans with revisions and explicit plan steps
- a bounded `observe -> plan -> act -> reflect -> finish` runtime
- strict per-agent tool routing
- observations, structured decision rationales, and working memory
- optimistic-lock coordination state and replayable messages
- Integrity-to-Collector and Integrity-to-Classification resolution requests
- supervisor routing, bounded rounds, resolution tasks, and terminal decisions
- policy-based agent and supervisor completion claims
- final states of `completed`, `completed_with_warnings`, `needs_human_review`,
  `blocked`, or `failed`

The runtime is policy-driven and does not require an LLM. A future LLM or
LangGraph layer can propose plans and decisions through these same typed contracts;
it must not bypass tool permissions, deterministic rules, completion policy, or
human approval.

## Current Architecture

ProofChain has a hybrid governed three-agent pipeline:

1. `EvidenceCollectorAgent`
2. `EvidenceClassificationAgent`
3. `EvidenceIntegrityAgent`

These agents are coordinated by the goal-oriented `Supervisor` in
[proofchain/agents/supervisor.py](/C:/SideQuest/ProofChain/proofchain/agents/supervisor.py).
Shared agentic components are under
[proofchain/agentic](/C:/SideQuest/ProofChain/proofchain/agentic) and the typed
contracts are in
[proofchain/schemas/agentic.py](/C:/SideQuest/ProofChain/proofchain/schemas/agentic.py).
The system provides:

- explicit goals, plans, observations, reflections, and completion decisions
- versioned shared coordination state and peer requests
- bounded retries and replanning
- typed inputs and outputs
- persisted JSON artifacts
- synchronization through artifact hashes
- deterministic stage gates
- reproducible validation

This is a good foundation for an agentic upgrade because the system already separates:

- control flow
- agent responsibilities
- persistence
- validation
- traceability

## How To Run The Current Project

### 1. Open the project

Work from:

`C:\SideQuest\ProofChain`

### 2. Install Python dependencies

If your environment does not already have the package dependencies:

```powershell
python -m pip install -e .
```

### 3. Run the full agentic pipeline

This is the main end-to-end command:

```powershell
python -m proofchain.cli run-pipeline `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026 `
  --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1 `
  --objective "Determine whether CSE evidence is defensible and disclose every blocker." `
  --max-agent-rounds 12 `
  --max-replans 3
```

You can also use the console entry point if it is installed:

```powershell
proofchain run-pipeline `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026 `
  --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1
```

### 4. Run a single stage

Collector only:

```powershell
python -m proofchain.cli collect `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026
```

Classification only from a previous run:

```powershell
python -m proofchain.cli classify `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026 `
  --from-run RUN-YYYYMMDD-XXXX
```

Integrity only from a previous run:

```powershell
python -m proofchain.cli integrity `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026 `
  --from-run RUN-YYYYMMDD-XXXX
```

### 5. Validate the artifact chain

```powershell
python -m proofchain.cli validate-run RUN-YYYYMMDD-XXXX
```

This checks that the run artifacts, hashes, and synchronization links are valid.

## Where Results Are Written

Each run is stored under:

`outputs/runs/{run_id}`

The important files are:

- `pipeline_result.json`
- `run_manifest.json`
- `pipeline_trace.jsonl`
- `evidence_registry.json`
- `classified_evidence.json`
- `integrity_findings.json`
- `integrity_summary.json`
- `errors.json`
- `top_level_goal.json`
- `goal_graph.json`
- `final_decision.json`
- `coordination/coordination_state.json`
- `coordination/messages.jsonl`
- `coordination/resolution_tasks.json`
- `coordination/decision_rationales.jsonl`
- `collector|classification|integrity/goal.json`
- `collector|classification|integrity/plans.json`
- `collector|classification|integrity/observations.jsonl`
- `collector|classification|integrity/reflections.jsonl`
- `collector|classification|integrity/working_memory.json`
- `collector|classification|integrity/completion_decision.json`

## How To Check If The Project Matches Your Intentions

Your stated intent is not only to process files, but to prove an evidence workflow:

`Requirement -> Claim -> Evidence -> Extraction -> Mapping -> Verification -> Gap -> Task -> Approval -> Audit Package`

The current implementation fully covers the middle verification spine well:

- evidence discovery and registration
- extraction and classification
- requirement mapping
- integrity findings and gaps
- synchronization and traceability

The current implementation does not yet fully complete these later product layers:

- corrective task generation is still limited
- approval workflow is not yet a full human approval center
- audit package generation is not yet the final polished output package
- human approval center UI and resume command
- polished audit-package publishing
- model-assisted planning and alternate OCR strategy selection
- LangGraph durable orchestration and visual graph inspection

So the honest reading is:

- The current project works as a governed, policy-driven agentic validation pipeline.
- It is not yet the complete accreditation operations product with human UI and publishing.

## Practical Validation Checklist

Use this checklist when you want to verify behavior after changes.

### Static validation

```powershell
python -m compileall -q proofchain tests
python -m ruff check proofchain tests
```

### Automated tests

```powershell
python -m pytest -q
```

### Expected current sample behavior

For the synthetic CSE sample, the expected result is:

- `15` evidence files registered
- `15` documents classified
- `9` integrity findings
- `5` evidence gaps
- final status `blocked`

The `blocked` result is expected because the sample data intentionally contains defects.

### What “working correctly” means today

The project is behaving according to the current implementation if:

1. the CLI completes without crashing
2. a new run folder is created in `outputs/runs`
3. `pipeline_result.json` contains counts and status
4. `validate-run` reports `"valid": true`
5. the test suite passes

## Agentic Boundaries

The agents are intentionally governed. They can:

- accept and persist goals
- plan, retry, replan, observe, and reflect
- invoke only allow-listed deterministic tools
- create peer requests and resolution tasks
- stop at budgets and request human review
- propose completion that a deterministic policy validates

They cannot modify original evidence, override blocking rules, approve institutional
claims, delete evidence, or publish audit packages. Those actions remain outside
autonomous authority.

## Definition Of An Agentic ProofChain

For this project, an agent should be considered agentic only if it can:

1. accept a goal, not just a stage input
2. create an explicit plan of substeps
3. reason over observations and prior outputs
4. select actions based on state
5. detect uncertainty and escalate or retry
6. synchronize with peer agents through shared state
7. determine when the goal is complete
8. emit a final explainable decision record

## Implemented Agentic Architecture

The implementation keeps the deterministic core and places a governed agentic
control layer above it.

### Layer 1: Deterministic execution tools

Reuse the existing services as tool primitives:

- file scanning
- checksum calculation
- metadata extraction
- document extraction
- classification
- field extraction
- requirement mapping
- bundling
- rule execution

These remain the reliable, replayable action layer.

### Layer 2: Agentic control loop

Each agent uses the reusable loop:

`observe -> plan -> act -> reflect -> update state -> continue or finish`

Each agent runs this loop inside a bounded budget:

- max planning rounds
- max action attempts
- max retries
- escalation rules

### Layer 3: Shared coordination and synchronization

Every run has shared coordination state for:

- run goal
- current agent plans
- open questions
- unresolved evidence
- inter-agent requests
- completion claims
- confidence and blockers

This state is persisted and versioned.

### Layer 4: Goal supervisor

The `Supervisor` acts as a goal orchestrator that:

- decomposes the top-level accreditation objective
- assigns goals to each agent
- tracks dependencies between goals
- arbitrates conflicts
- decides whether to continue, replan, escalate, or finish

## Implemented Components

Agentic runtime modules:

- `proofchain/agentic/base_goal_agent.py`
- `proofchain/agentic/planner.py`
- `proofchain/agentic/memory.py`
- `proofchain/agentic/goal_manager.py`
- `proofchain/agentic/dependency_manager.py`
- `proofchain/agentic/conflict_resolver.py`
- `proofchain/agentic/policies.py`
- `proofchain/agentic/budgets.py`
- `proofchain/agentic/tool_router.py`
- `proofchain/agentic/completion_evaluator.py`
- `proofchain/repositories/json_coordination_repository.py`
- `proofchain/schemas/agentic.py`

Recommended new schemas:

- `Goal`
- `PlanStep`
- `ActionProposal`
- `Observation`
- `ReflectionNote`
- `CoordinationMessage`
- `CompletionDecision`
- `EscalationDecision`

## Agent Conversion Strategy

Do not replace the current agents from scratch. Wrap and extend them.

### 1. Collector becomes an Evidence Acquisition Planner

Current role:

- scan files
- assign IDs
- compute checksums
- detect exact duplicates

Agentic role:

- plan collection by department, folder, and evidence category
- detect missing expected evidence patterns
- decide whether a file needs retry, quarantine, OCR, or human review
- request follow-up evidence from downstream gaps
- produce a collection completeness judgment

New collector loop:

1. Observe source directories and prior gaps.
2. Build a collection plan.
3. Execute discovery and metadata actions.
4. Reflect on missing or suspicious evidence.
5. Open follow-up tasks or requests.
6. Finish when the collection objective is satisfied or blocked.

### 2. Classification becomes an Evidence Understanding Planner

Current role:

- extract text and tabular data
- classify document type
- extract fields
- map to requirements

Agentic role:

- choose extraction strategy by file type and quality
- compare multiple hypotheses for document type
- reason over conflicting requirement mappings
- ask for supporting context from collector or integrity
- route uncertain evidence for human review or secondary extraction

New classification loop:

1. Observe the evidence bundle and upstream context.
2. Plan the extraction and mapping order.
3. Execute extraction and classification.
4. Reflect on confidence, ambiguity, and contradiction.
5. Re-run or re-strategize when confidence is low.
6. Finish when each evidence item has a justified classification state.

### 3. Integrity becomes a Verification and Resolution Planner

Current role:

- bundle evidence
- run rules
- emit findings and gaps
- summarize integrity

Agentic role:

- reason over the meaning of findings, not only emit them
- decide which findings are actionable, blocking, or informational
- group related failures into resolution tasks
- request more evidence from collector
- request reclassification from classifier
- decide whether the requirement claim is defensible

New integrity loop:

1. Observe classified evidence, mappings, and current claim scope.
2. Build a verification plan by requirement and event.
3. Execute bundling and rule evaluation.
4. Reflect on contradictions and sufficiency.
5. Trigger upstream requests when needed.
6. Finish when each requirement has a defensible status.

## Synchronization Design

This is the most important part of the upgrade.

The three agents should not communicate only through final stage artifacts. They should also synchronize through a run-level coordination store.

### Recommended coordination artifacts

Persist these inside each run directory:

- `coordination_state.json`
- `agent_plans.json`
- `open_questions.json`
- `completion_claims.json`
- `handoff_requests.json`
- `resolution_tasks.json`

### Suggested synchronization rules

1. Every agent writes a plan before taking non-trivial actions.
2. Every replan increments a revision number.
3. Every coordination message references:
   - `run_id`
   - `source_agent`
   - `target_agent`
   - `goal_id`
   - `related_evidence_ids`
   - `reason`
4. No agent may overwrite another agent's plan directly.
5. Shared state updates must be atomic.
6. Goal completion must require:
   - plan status `completed`
   - no unresolved blockers for required scope
   - signed completion decision

### Recommended state machine

For each agent goal:

- `created`
- `planning`
- `executing`
- `waiting_on_peer`
- `needs_human_review`
- `blocked`
- `completed`

## Keep Determinism Where It Matters

The best version of this system is not fully free-form. It should be hybrid.

Recommended split:

- deterministic for persistence, IDs, artifact hashes, rule execution, validation, and audit trail
- agentic for planning, retries, prioritization, ambiguity handling, and cross-agent coordination

This prevents the system from becoming impossible to trust during accreditation workflows.

## Implemented Migration Phases

Phases A through F below are implemented and covered by the automated suite.
Model-assisted planning, LangGraph, and a human-review UI remain later product work.

### Phase A: Add agentic schemas and coordination store

Build:

- plan and goal schemas
- coordination repository
- completion decision schema
- persisted run-level blackboard

Acceptance:

- plans and messages can be stored and replayed
- stage results remain backward compatible

### Phase B: Add a reusable agentic base class

Create something like:

- `BaseGoalAgent`

Responsibilities:

- load goal context
- generate plan
- execute one step at a time
- capture observations
- reflect and decide next action
- persist state after every transition

Acceptance:

- one agent can run a multi-step plan with retries and reflection

### Phase C: Convert collector first

Why first:

- lowest reasoning risk
- strongest place to introduce goal decomposition
- easiest to test for synchronization and retries

Acceptance:

- collector can detect missing expected evidence and create follow-up requests

### Phase D: Convert classifier second

Acceptance:

- classifier can compare alternate hypotheses and justify the chosen result

### Phase E: Convert integrity third

Acceptance:

- integrity can trigger upstream requests and close the loop on requirement readiness

### Phase F: Upgrade supervisor into a goal orchestrator

Acceptance:

- supervisor can coordinate multi-agent replanning until goals are completed, blocked, or escalated

## Example Target Runtime

Top-level goal:

`Validate whether CSE requirement C3.2.1 for academic year 2025-2026 is defensible with current evidence.`

Execution sketch:

1. Supervisor creates run goal.
2. Collector plans acquisition and detects a missing signed approval letter.
3. Collector posts a handoff request.
4. Classifier processes available evidence and marks one report as ambiguous.
5. Integrity detects participant mismatch and missing approval evidence.
6. Integrity requests recollection and reclassification.
7. Supervisor waits for open blockers to clear or marks the run blocked with a structured explanation.

That is the behavior shift from a stage pipeline to an agentic workflow.

## Concrete Code Changes Implemented

The conversion changed these areas:

- add `proofchain/agentic/` package
- add `proofchain/repositories/json_coordination_repository.py`
- add `proofchain/schemas/agentic.py`
- add `proofchain/agentic/base_goal_agent.py`
- update [proofchain/agents/supervisor.py](/C:/SideQuest/ProofChain/proofchain/agents/supervisor.py)
- update [proofchain/agents/evidence_collector.py](/C:/SideQuest/ProofChain/proofchain/agents/evidence_collector.py)
- update [proofchain/agents/evidence_classification.py](/C:/SideQuest/ProofChain/proofchain/agents/evidence_classification.py)
- update [proofchain/agents/evidence_integrity.py](/C:/SideQuest/ProofChain/proofchain/agents/evidence_integrity.py)
- update [proofchain/schemas/workflow.py](/C:/SideQuest/ProofChain/proofchain/schemas/workflow.py)

## Testing Strategy For The Agentic Upgrade

The suite now includes deterministic and agentic tests.

Implemented coverage includes:

1. plan-generation tests
2. replan-on-failure tests
3. coordination message tests
4. synchronization conflict tests
5. completion decision tests
6. bounded-retry tests
7. blocked-state tests
8. human-review escalation tests

### Minimum validation commands

```powershell
python -m compileall -q proofchain tests
python -m ruff check proofchain tests
python -m pytest -q
```

### Remaining scenario expansions

- collector requests missing approval evidence
- classifier retries extraction after low-confidence OCR
- integrity asks classifier to revisit ambiguous mapping
- supervisor resolves a multi-agent dependency chain
- run ends in `completed` when blockers are closed
- run ends in `blocked` when required evidence cannot be obtained

## Conversion Acceptance Criteria

The current governed conversion satisfies these criteria:

1. each of the three agents accepts a goal and emits an explicit plan
2. each agent can replan at least once based on observations
3. coordination between agents is persisted and replayable
4. final run completion is based on goal satisfaction, not only stage execution
5. all important decisions are explainable and auditable
6. deterministic validation still works on persisted artifacts

## Architecture Decision

The deterministic collector, classifier, and integrity implementations remain the
trusted execution substrate. The agentic runtime governs plans, retries, replanning,
peer requests, completion, and audit memory around those tools. Future model-based
reasoning must use these contracts and preserve synchronization checkpoints,
permissions, blocking rules, and human authority.
