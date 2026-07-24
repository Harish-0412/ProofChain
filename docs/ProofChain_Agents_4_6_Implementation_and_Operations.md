# ProofChain Agents 4-6: Implementation and Operations

## Implementation Status

Agents 4 through 6 are implemented as governed compound agents:

1. Claim Intelligence and Defensibility Agent
2. Adaptive Gap Resolution and Readiness Planning Agent
3. Accountability, Ownership, and Escalation Agent

They run after Evidence Integrity in the same goal graph and use the existing
`BaseGoalAgent` runtime. Each primary agent has five specialist tools, a persisted
five-step plan, observations, reflections, structured rationales, working memory,
peer requests, and a policy-validated completion decision.

The resulting workflow is:

```text
Collector
  -> Classification
  -> Integrity
  -> Claim Intelligence
  -> Adaptive Gap Resolution
  -> Accountability and Ownership
  -> Human Approval
```

## Specialist Architecture

Claim Intelligence:

- Claim Decomposition
- Evidence Retrieval
- Contradiction Investigation
- Sufficiency Evaluation
- Defensibility Decision

Adaptive Gap Resolution:

- Gap Detection
- Root-Cause Analysis
- Resolution Planning
- Readiness Simulation
- Gap Prioritization

Accountability and Ownership:

- Evidence Provenance
- Responsibility Matching
- Workload Balancing
- Escalation Planning
- Assignment Validation

These specialist steps are visible in
`outputs/runs/{run_id}/coordination/tool_calls.jsonl`.

## Run the Pipeline

From `C:\SideQuest\ProofChain`:

```powershell
python -m proofchain.cli run-pipeline `
  --source sample_data/departments `
  --departments CSE `
  --academic-year 2025-2026 `
  --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1 `
  --objective "Determine whether CSE evidence and claims are audit-ready." `
  --claim "CSE conducted 12 industry programmes involving 120 students during 2025-2026 for C3.2.1."
```

Repeat `--claim` for multiple institutional claims. If no claim is supplied,
ProofChain derives event-level claims from classified event reports.

## Validate a Run

```powershell
python -m proofchain.cli validate-run RUN-YYYYMMDD-XXXX
```

This validates all six checkpoint artifacts, their checksums, and the upstream
hash chain, plus the goal graph, coordination state, final decision, and extended
agent outputs.

## Human Approval

Agent outputs are recommendations. Claim revisions, resolution strategies,
ownership assignments, and escalations are not approved automatically.

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

The target ID must exist in that run. Approval records are written to
`human_approvals.json`; original evidence and decision artifacts are unchanged.

## Important Outputs

Run-level outputs:

- `claim_decisions.json`
- `gap_resolution_portfolio.json`
- `ownership_assignments.json`
- `claim_resolution_ownership_report.json`
- `human_approvals.json`, after an explicit decision
- `goal_graph.json`
- `final_decision.json`

Each primary agent also writes:

- `goal.json`
- `plans.json`
- `observations.jsonl`
- `reflections.jsonl`
- `working_memory.json`
- `completion_decision.json`

Coordination outputs include:

- `coordination_state.json`
- `messages.jsonl`
- `resolution_tasks.json`
- `decision_rationales.jsonl`
- `tool_calls.jsonl`

Peer requests create dynamic resolution subgoals in `goal_graph.json`. These
subgoals document whether the current committed evidence resolves the request,
remains blocked, or requires human review.

## Governance Boundaries

The agents may recommend claim text, resolution strategies, owners, deadlines,
and escalation paths. They may not:

- modify original evidence
- change an institutional claim automatically
- mark a gap resolved without closure evidence
- assign or message a person automatically
- approve their own recommendations
- override deterministic blocking rules
- expose information beyond the assignment data scope

## Validation Commands

```powershell
python -m compileall -q proofchain tests
python -m ruff check proofchain tests
python -m pytest -q
```

The test suite covers atomic decomposition, supporting and counter-evidence,
claim repair, duplicate gap merging, root causes, resolution alternatives,
readiness deltas, priorities, permissions, workload, backup owners, independent
approval, escalation paths, dynamic subgoals, six-stage hash synchronization,
and validated human approval records.

