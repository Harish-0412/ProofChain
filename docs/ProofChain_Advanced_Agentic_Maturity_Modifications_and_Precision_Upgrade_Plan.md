# ProofChain
## Advanced Agentic Maturity, Precision, and Modification Plan

**Current baseline:** 22 primary goal agents, 132 deterministic specialist modules, 80 passing tests  
**Reference run:** `RUN-20260727-0F23`  
**Objective:** Make the existing agents understand goals and inputs more accurately, produce stronger plans, reason over evidence more precisely, coordinate intelligently, replan safely, and prove completion without adding unnecessary new agents.

---

# 1. Executive Recommendation

ProofChain already has enough primary agents.

The next improvement should not be based on increasing the agent count. It should deepen the behavior of the existing 22 agents.

The target agent lifecycle should become:

```text
Receive Goal
    -> Interpret Goal
    -> Validate Inputs
    -> Build Context
    -> Form Hypotheses
    -> Create Plan
    -> Critique Plan
    -> Select Action
    -> Execute Tool
    -> Normalize Observation
    -> Reflect
    -> Calibrate Uncertainty
    -> Continue, Retry, Replan, Ask Peer, Ask Human, Block, or Complete
    -> Prove Completion
    -> Emit Explainable Decision
```

This upgrade preserves the current deterministic and governed architecture while making each agent substantially more autonomous, precise, transparent, and reliable.

---

# 2. Current Architecture Assessment

## Already Strong

The current implementation already provides:

- Typed goals
- Explicit plans
- Allowlisted tools
- Structured observations
- Reflections
- Working memory
- Peer coordination
- Bounded retries
- Completion decisions
- Event sourcing
- Recovery
- Authorization
- Security
- Tenant isolation
- Submission governance
- Continuous evaluation
- Governed retrieval

## Main Gaps to Address

1. Goal understanding is not yet treated as a first-class stage.
2. Input quality should be validated before planning.
3. Plans should be challenged before execution.
4. Competing hypotheses should be represented explicitly.
5. Uncertainty should be decomposed and calibrated.
6. Peer requests should contain acceptance criteria.
7. Replanning should clearly explain what changed.
8. Completion should require a machine-readable proof.
9. Prior validated cases should improve future planning.
10. Cross-agent contradictions should be resolved systematically.
11. Agentic quality should be measured separately from task accuracy.
12. Decision explanations should follow one standard format.

---

# 3. Shared Advanced Cognition Layer

Add the following internal runtime components. These are not new primary agents.

```text
proofchain/agentic/
├── goal_interpreter.py
├── input_validator.py
├── context_builder.py
├── hypothesis_manager.py
├── planning_engine.py
├── plan_critic.py
├── action_selector.py
├── observation_normalizer.py
├── reflection_engine.py
├── uncertainty_calibrator.py
├── peer_negotiator.py
├── contradiction_resolver.py
├── completion_prover.py
├── decision_explainer.py
├── experience_memory.py
├── scheduler.py
├── deadlock_detector.py
└── global_replanner.py
```

Every primary agent should use these shared components through `BaseGoalAgent`.

---

# 4. Goal Interpretation

A typed goal can still be vague.

Example:

```text
Validate C3.2.1 evidence.
```

Before planning, the agent must identify:

- Department
- Academic year
- Requirement version
- Claim scope
- Evidence scope
- Policies
- Prohibited actions
- Success conditions
- Human approval boundary

## Schema

```python
class InterpretedGoal(BaseModel):
    goal_id: str
    normalized_objective: str
    subject_entities: list[str]
    required_inputs: list[str]
    constraints: list[str]
    prohibited_actions: list[str]
    success_conditions: list[str]
    failure_conditions: list[str]
    ambiguity_flags: list[str]
    clarification_required: bool
    interpretation_confidence: float
```

## Gate

The agent must not create a plan until:

- Scope is known
- Mandatory inputs are identified
- Policy version is known
- Ambiguity is below threshold
- Prohibited actions are loaded

---

# 5. Input Understanding and Validation

Every agent should validate inputs before planning.

## Required Checks

- Artifact exists
- Checksum is valid
- Upstream checkpoint is valid
- Schema version is supported
- Artifact is current
- Tenant scope matches
- Department scope matches
- Required approval exists
- Required policy version is loaded

## Schema

```python
class InputValidationResult(BaseModel):
    valid: bool
    complete: bool
    authorized: bool
    current: bool
    missing_inputs: list[str]
    stale_inputs: list[str]
    conflicting_inputs: list[str]
    unauthorized_inputs: list[str]
    recoverable: bool
    recommended_action: str
```

Invalid inputs should result in:

```text
request_peer
request_human
block
or
recover through a safe tool
```

They should never be silently ignored.

---

# 6. Context Construction

Before planning, build one structured context snapshot.

```python
class AgentContext(BaseModel):
    goal: InterpretedGoal
    relevant_entities: list[str]
    artifacts: list[str]
    applicable_policies: list[str]
    applicable_rules: list[str]
    prior_observations: list[str]
    open_peer_requests: list[str]
    blockers: list[str]
    validated_case_ids: list[str]
    context_completeness: float
    unresolved_questions: list[str]
```

Context sources:

```text
Goal
Run state
Artifacts
Policies
Rules
Open messages
Prior observations
Human decisions
Validated prior cases
Budgets
Known blockers
```

Planning may begin only when context is complete enough or missing context is explicitly represented as uncertainty.

---

# 7. Explicit Hypothesis Management

Agents should compare competing explanations instead of selecting the first plausible answer.

```python
class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str
    supporting_observations: list[str]
    contradicting_observations: list[str]
    assumptions: list[str]
    confidence: float
    status: Literal[
        "proposed",
        "supported",
        "weakened",
        "rejected",
        "unresolved",
    ]
```

Example for a count mismatch:

```text
Hypothesis A:
Duplicate attendance rows inflated the report.

Hypothesis B:
Faculty and external attendees were included.

Hypothesis C:
The attendance sheet is incomplete.
```

The agent should gather observations that discriminate between these hypotheses.

---

# 8. Advanced Planning Engine

A plan should include more than an ordered list.

```python
class AdvancedPlanStep(BaseModel):
    step_id: str
    sequence: int
    objective: str
    preferred_tool: str | None
    fallback_tools: list[str]
    required_inputs: list[str]
    expected_observations: list[str]
    success_condition: str
    failure_condition: str
    risk_level: str
    reversible: bool
    requires_approval: bool
    on_success: str | None
    on_failure: str | None
    on_uncertainty: str | None
```

## Plan Quality Dimensions

- Coverage
- Dependency correctness
- Policy compliance
- Tool eligibility
- Risk awareness
- Fallback quality
- Completion-test quality
- Efficiency
- Expected runtime
- Human approval awareness

---

# 9. Plan Critic

Every non-trivial plan should be challenged before execution.

## Critic Questions

- Does the plan satisfy every success condition?
- Are mandatory rules included?
- Does it rely on stale evidence?
- Does it ignore contradictory evidence?
- Are tools allowlisted?
- Is the order correct?
- Is there a fallback?
- Could it duplicate an irreversible action?
- Is human approval required?
- Is completion measurable?

## Schema

```python
class PlanCritique(BaseModel):
    plan_id: str
    approved: bool
    missing_steps: list[str]
    unsafe_steps: list[str]
    unsupported_assumptions: list[str]
    policy_conflicts: list[str]
    efficiency_warnings: list[str]
    required_revisions: list[str]
    critique_confidence: float
```

A rejected plan must be revised before execution.

---

# 10. Action Selection

Actions should be selected using:

- Plan order
- Goal priority
- Input readiness
- Tool reliability
- Policy permission
- Expected information gain
- Risk
- Reversibility
- Cost
- Peer dependencies

```python
class ActionProposal(BaseModel):
    action_id: str
    goal_id: str
    step_id: str
    selected_tool: str
    arguments: dict
    alternatives: list[str]
    selection_reason: str
    expected_information_gain: float
    risk_level: str
    reversible: bool
    approval_required: bool
```

A useful unique feature is **information-gain-based action selection**. When several checks are possible, choose the action most likely to reduce uncertainty.

---

# 11. Observation Normalization

Agents should never reason directly over uncontrolled tool output.

Every result should be converted into:

```python
class Observation(BaseModel):
    observation_id: str
    source_tool: str
    source_version: str
    summary: str
    structured_data: dict
    source_references: list[str]
    data_quality: str
    confidence: float
    contradictions: list[str]
    missing_information: list[str]
    sufficient_for_step: bool
```

This creates consistency across all 132 deterministic specialist modules.

---

# 12. Structured Reflection

Reflection should evaluate measurable progress.

```python
class StructuredReflection(BaseModel):
    goal_id: str
    plan_revision: int
    new_facts: list[str]
    hypotheses_supported: list[str]
    hypotheses_rejected: list[str]
    success_conditions_met: list[str]
    success_conditions_remaining: list[str]
    blockers: list[str]
    decision: Literal[
        "continue",
        "retry",
        "replan",
        "ask_peer",
        "ask_human",
        "complete",
        "block",
        "fail",
    ]
    reason_summary: str
    confidence: float
```

Reflection must answer:

1. What did the action establish?
2. Which hypotheses changed?
3. Which conditions are satisfied?
4. Which blockers remain?
5. Is the plan still valid?
6. Is another agent required?
7. Is a retry useful?
8. Is human review required?
9. Can completion be proven?

Persist concise decision summaries, not unrestricted hidden chain-of-thought.

---

# 13. Uncertainty Calibration

Do not use one unexplained confidence value.

Separate:

```text
Input confidence
Tool confidence
Interpretation confidence
Decision confidence
Completion confidence
```

## Uncertainty Types

- Input
- Extraction
- Classification
- Rule
- Policy
- Identity
- Ownership
- Temporal
- Source authority
- Completion

## Suggested Policy

```text
>= 0.90
    Continue automatically

0.75 to 0.89
    Continue with a warning

0.50 to 0.74
    Retrieve more context or ask a peer

0.30 to 0.49
    Request human review

< 0.30
    Do not make a positive decision
```

Deterministic blocking rules always override confidence.

---

# 14. Peer Negotiation Contracts

Peer requests should specify exactly what is required.

```python
class AgentRequest(BaseModel):
    request_id: str
    source_agent: str
    target_agent: str
    goal_id: str
    requested_outcome: str
    reason: str
    required_inputs: list[str]
    related_entities: list[str]
    acceptance_conditions: list[str]
    priority: str
    deadline: datetime | None
    blocking: bool
```

## Request States

```text
OPEN
ACKNOWLEDGED
ACCEPTED
DECLINED
NEEDS_CLARIFICATION
IN_PROGRESS
RESOLVED
EXPIRED
CANCELLED
```

No peer request should be marked resolved until its acceptance conditions pass.

---

# 15. Contradiction Resolution

Add one shared contradiction-resolution capability.

```text
Identify contradiction
    -> Gather related observations
    -> Rank source authority
    -> Check versions and time
    -> Check scope
    -> Form alternative explanations
    -> Request targeted validation
    -> Resolve or escalate
```

```python
class ContradictionResolution(BaseModel):
    contradiction_id: str
    conflicting_observation_ids: list[str]
    likely_explanation: str | None
    resolution_status: str
    confidence: float
    required_followup: list[str]
    human_review_required: bool
```

This is especially useful when different agents interpret the same evidence differently.

---

# 16. Completion Proof

An agent is not complete merely because every plan step executed.

```python
class CompletionProof(BaseModel):
    goal_id: str
    all_success_conditions_evaluated: bool
    condition_results: list[dict]
    unresolved_blockers: list[str]
    unresolved_peer_requests: list[str]
    artifact_references: list[str]
    evidence_references: list[str]
    rule_references: list[str]
    completion_confidence: float
    final_status: str
```

Completion requires:

- Every success condition evaluated
- Mandatory inputs valid
- Required peer requests resolved
- No blocking policy conflict
- Output schema valid
- Completion proof persisted

---

# 17. Explainable Decision Standard

Every important decision should contain:

```text
Decision
Goal
Inputs Considered
Evidence Considered
Rules Applied
Policies Applied
Alternative Outcomes
Uncertainty
Why This Outcome Was Chosen
Next Action
Human Approval Requirement
```

Example:

```json
{
  "decision": "PARTIALLY_SUPPORTED",
  "goal": "Validate claim CLM-C3.2.1-001",
  "evidence_considered": [
    "event report",
    "attendance sheet",
    "certificate registry"
  ],
  "rules_applied": [
    "UNIQUE_PARTICIPANT_COUNT",
    "CLAIM_EVIDENCE_SUFFICIENCY"
  ],
  "alternatives_considered": [
    "SUPPORTED",
    "CONTRADICTED",
    "INSUFFICIENT_EVIDENCE"
  ],
  "uncertainty": [
    "Four attendance records have no certificate"
  ],
  "reason": "The evidence supports 108 unique students rather than 120.",
  "human_approval_required": true
}
```

---

# 18. Validated Experience Memory

Allow agents to reuse previous successful plans only when those cases are validated.

```python
class ValidatedCase(BaseModel):
    case_id: str
    case_type: str
    context_features: dict
    successful_plan: list[str]
    successful_tools: list[str]
    outcome: str
    validation_status: str
    approved_by: str | None
    reusable: bool
```

Experience memory may influence planning.

It may never override:

- Current evidence
- Deterministic rules
- Governance policies
- Human approval requirements
- Tenant boundaries

---

# 19. Advanced Agent State Machine

Use:

```text
CREATED
INTERPRETING_GOAL
VALIDATING_INPUTS
BUILDING_CONTEXT
FORMING_HYPOTHESES
PLANNING
CRITIQUING_PLAN
EXECUTING
OBSERVING
REFLECTING
WAITING_FOR_PEER
WAITING_FOR_HUMAN
REPLANNING
VERIFYING_COMPLETION
COMPLETED
COMPLETED_WITH_WARNINGS
BLOCKED
FAILED
CANCELLED
```

Every transition should produce a workflow event.

---

# 20. Supervisor Upgrade

The Supervisor should additionally perform:

- Goal-interpretation validation
- Global plan review
- Cross-agent contradiction detection
- Priority scheduling
- Critical-path analysis
- Global budget management
- Deadlock prevention
- Plan conflict detection
- Completion-proof validation
- Human-review consolidation
- Multi-run fairness

## Global Replanning Triggers

- Critical goal failure
- Policy change
- Quality-review failure
- Security incident
- Tenant boundary change
- Submission deadline change
- Schema migration block
- New contradictory evidence

---

# 21. Agent-by-Agent Modifications

## Agent 1: Evidence Collector

Add:

- Expected evidence pattern planning
- Source priority
- Coverage matrix
- Source exhaustion proof
- Collection confidence
- Duplicate version lineage
- Explicit completeness decision

Unique feature:

**Evidence Acquisition Strategy** chooses the most reliable authorized source for each expected evidence category.

---

## Agent 2: Evidence Classification

Add:

- Multi-hypothesis classification
- Extraction strategy selection
- Alternate parser retry
- Field-level provenance
- Confidence calibration
- Contradiction-aware requirement mapping
- Human correction feedback

Unique feature:

**Extraction Strategy Planner** selects native parsing, OCR, table extraction, spreadsheet parsing, or human review based on quality.

---

## Agent 3: Evidence Integrity

Add:

- Dynamic rule applicability
- Rule coverage matrix
- Root-cause grouping
- False-positive checks
- Cross-year anomaly checks
- Historical consistency
- Rule explanation templates

Unique feature:

**Verification Coverage Matrix** proves which rules were applicable, executed, passed, and supported by evidence.

---

## Agent 4: Claim Intelligence

Add:

- Claim fragility score
- Atomic claim dependencies
- Contradiction ranking
- Minimal evidence set confidence
- Alternative claim simulation
- Claim version lineage
- Counterfactual repair plan

Unique feature:

**Claim Fragility** identifies claims that depend on a single weak or disputed source.

---

## Agent 5: Adaptive Gap Resolution

Add:

- Resolution success probability
- Resource-aware planning
- Deadline-aware planning
- Effort estimates
- Scenario comparison
- Strategy fallback
- Learning from closure outcomes

Unique feature:

**Resolution Portfolio Optimizer** selects the smallest action set that maximizes verified readiness under time, staffing, approval, and evidence constraints.

---

## Agent 6: Accountability and Ownership

Add:

- User availability
- Delegation
- Historical task success
- Workload forecast
- Conflict probability
- Backup depth
- Responsibility confidence

Unique feature:

**Explainable Responsibility Graph** links user, role, department, event, evidence, permission, and workload.

---

## Agent 7: Department Liaison

Add:

- Communication planning
- Recipient comprehension checks
- Message clarity score
- Language adaptation
- Follow-up strategy
- Assignment dispute handling
- Escalation simulation

Unique feature:

**Task Understandability Check** verifies that recipients can understand the problem, action, evidence, submission path, and deadline.

---

## Agent 8: Closure Revalidation

Add:

- Closure hypotheses
- Evidence-delta explanations
- Targeted rule coverage
- Regression probability
- Partial resolution score
- Reopen rationale
- Closure proof bundle

Unique feature:

**Closure Proof Bundle** contains the original issue, conditions, corrections, changes, rules, claim revalidation, regression checks, and final decision.

---

## Agent 9: Audit Package Composer

Add:

- Reviewer-persona ordering
- Minimal package score
- Evidence redundancy analysis
- Citation quality
- Reproducibility proof
- Package version comparison
- Privacy completeness

Unique feature:

**Reviewer Journey Planner** orders the package so auditors can move from requirement to claim, evidence, verification, and closure with minimal friction.

---

## Agent 10: Adversarial Quality Review

Add:

- Independent context isolation
- Omission challenge
- Count reproduction
- Source authority challenge
- Reviewer confusion analysis
- Package version challenge
- Privacy challenge

Unique feature:

**Independent Reproduction** recalculates key facts from raw evidence rather than trusting package summaries.

---

## Agent 11: Persistence and Recovery

Add:

- Recovery plan criticism
- Corruption hypotheses
- Snapshot confidence
- Cross-store reconciliation
- Transaction risk
- Disaster recovery simulation

Unique feature:

**State Reconstruction Proof** validates event count, sequence, hashes, snapshots, and artifact linkage.

---

## Agent 12: Continuation and Partial Re-Execution

Add:

- Change-impact reasoning
- Rerun cost estimates
- Cache safety proof
- Duplicate-action prediction
- Critical-path recalculation
- Resume readiness proof

Unique feature:

**Minimal Safe Rerun** explains why excluded agents do not need to rerun.

---

## Agent 13: Identity and Authorization

Add:

- Authority confidence
- Delegation-chain reasoning
- Dual-approval planning
- Temporal access
- Emergency access
- Separation-of-duties proof

Unique feature:

**Authorization Explanation Graph** shows actor, role, scope, permission, target, conflict check, and decision.

---

## Agent 14: Integration and Notification

Add:

- Channel success prediction
- Delivery fallback planning
- Recipient preferences
- Rate-limit awareness
- Response-correlation confidence
- Duplicate-suppression proof

Unique feature:

**Delivery Strategy Planner** selects the best approved channel using sensitivity, urgency, preference, health, and delivery history.

---

## Agent 15: Security Inspection

Add:

- Multi-stage security plans
- Suspicious-content hypotheses
- Sandbox inspection
- Security confidence
- Quarantine explanations
- Downstream risk propagation

Unique feature:

**Evidence Trust Envelope** records file safety, content trust, PII, prompt-injection risk, allowed uses, and controls.

---

## Agent 16: Reliability and Incident Response

Add:

- Failure prediction
- Incident hypothesis ranking
- Recovery simulation
- Blast-radius analysis
- Integrity verification
- Post-incident learning

Unique feature:

**Recovery Safety Proof** confirms no duplicate actions, lost events, corrupted artifacts, or approval bypass.

---

## Agent 17: Schema Evolution

Add:

- Schema dependency graph
- Migration risk
- Historical sampling
- Rollback plan
- Compatibility proof
- Deployment confidence

Unique feature:

**Migration Shadow Run** validates converted copies without replacing originals.

---

## Agent 18: Policy Lifecycle

Add:

- Policy ambiguity detection
- Conflict explanations
- Scenario simulation
- Effective-date planning
- Open-run impact
- Human-readable change summaries

Unique feature:

**Policy Counterfactual Simulator** shows which runs, decisions, and actions would change.

---

## Agent 19: Tenant Governance

Add:

- Tenant context proof
- Cross-tenant collaboration workflow
- Shared-resource expiry
- Tenant-specific policy comparison
- Isolation verification
- Data residency constraints

Unique feature:

**Tenant Boundary Explanation** clearly explains every allow or deny decision.

---

## Agent 20: External Submission

Add:

- Submission rehearsal
- Payload completeness
- Portal health
- Deadline risk
- Receipt confidence
- Resubmission planning

Unique feature:

**Dry-Run Submission** validates the full handoff without transmitting the package.

---

## Agent 21: Continuous Evaluation

Add:

- Agent-specific scorecards
- Scenario generation
- Policy regression tests
- Calibration tracking
- Release risk
- Failure-cluster analysis

Unique feature:

**Agentic Behavior Evaluation** measures goal interpretation, plan completeness, replan quality, peer-request quality, completion proof, and escalation quality.

---

## Agent 22: Governed Retrieval

Add:

- Query interpretation
- Source diversity
- Authority confidence
- Contradiction retrieval
- Freshness proof
- Citation completeness
- Retrieval uncertainty

Unique feature:

**Evidence-Aware Retrieval** considers requirement, claim, department, academic year, evidence type, policy version, and decision context.

---

# 22. Cross-Agent Precision Features

## Confidence Decomposition

Store:

```text
Input confidence
Tool confidence
Interpretation confidence
Decision confidence
Completion confidence
```

## Evidence Authority Ranking

```text
Official signed source
System-generated registry
Approved institutional document
Coordinator report
Derived summary
Generated narrative
```

Generated narrative never becomes evidence.

## Agent Decision Ledger

Create:

```text
agent_decisions.jsonl
```

Each record includes:

- Goal
- Plan revision
- Action
- Observation
- Decision
- Confidence
- Sources
- Policies
- Completion effect

## Agentic Contract Tests

Every agent must demonstrate:

```text
Goal understanding
Input rejection
Planning
Plan critique
Allowlisted tool use
Failure handling
Replanning
Peer request
Uncertainty handling
Completion proof
```

---

# 23. New Schemas

```text
proofchain/schemas/
├── interpreted_goal.py
├── input_validation.py
├── agent_context.py
├── hypotheses.py
├── advanced_plans.py
├── plan_critiques.py
├── action_proposals.py
├── uncertainty.py
├── peer_contracts.py
├── completion_proofs.py
├── decision_explanations.py
├── validated_cases.py
└── contradiction_resolution.py
```

---

# 24. Per-Agent Output Directory

```text
outputs/runs/{run_id}/agents/{agent_name}/{goal_id}/
├── goal.json
├── interpreted_goal.json
├── input_validation.json
├── context_snapshot.json
├── hypotheses.json
├── plans.json
├── plan_critiques.json
├── action_proposals.jsonl
├── tool_calls.jsonl
├── observations.jsonl
├── reflections.jsonl
├── peer_requests.jsonl
├── uncertainty_assessments.jsonl
├── completion_proof.json
├── completion_decision.json
└── decision_explanation.json
```

This provides complete transparency without exposing unrestricted hidden reasoning.

---

# 25. Evaluation Framework

## New Agentic Metrics

- Goal interpretation accuracy
- Input validation accuracy
- Plan completeness
- Plan-critique effectiveness
- Tool-selection accuracy
- Replan success rate
- Peer-request usefulness
- Uncertainty calibration
- Completion-proof accuracy
- Decision-explanation quality
- Human-escalation precision

## Example Scorecard

```json
{
  "agent": "claim_intelligence",
  "goal_interpretation_accuracy": 0.98,
  "plan_completeness": 0.95,
  "tool_selection_accuracy": 0.96,
  "replan_success_rate": 0.88,
  "completion_proof_accuracy": 1.0,
  "human_escalation_precision": 0.93
}
```

## Release Block Conditions

Block release when:

- False approval increases
- False closure increases
- Completion proof is invalid
- Unauthorized tools are selected
- Goal understanding regresses
- Cross-tenant leakage occurs
- Human approval is bypassed

---

# 26. Testing Plan

## Goal Tests

- Ambiguous goal
- Missing department
- Missing academic year
- Wrong requirement version
- Conflicting constraints
- Prohibited action

## Input Tests

- Missing artifact
- Stale artifact
- Invalid checksum
- Wrong tenant
- Unsupported schema
- Missing approval

## Planning Tests

- Complete success-condition coverage
- Fallback present
- Policy compliant
- Missing step detected
- Unsafe tool blocked
- Revision fixes critique

## Reflection Tests

- Continue after useful observation
- Retry after recoverable failure
- Replan after contradiction
- Ask peer on dependency
- Ask human on uncertainty
- Block when evidence is unavailable

## Completion Tests

- All conditions satisfied
- Mandatory condition missing
- Open peer request
- Invalid output
- Policy conflict
- Completion-proof mismatch

## Multi-Agent Tests

- Collector requests context
- Classification requests recollection
- Integrity requests reclassification
- Claim Agent requests clarification
- Quality Agent creates correction goals
- Supervisor resolves contradictory observations

## Memory Tests

- Validated case reused
- Invalid case rejected
- Historical case cannot override policy
- Stale experience ignored

---

# 27. Implementation Phases

## Phase A: Schemas

Implement:

- Interpreted goals
- Input validation
- Context
- Hypotheses
- Plan critique
- Uncertainty
- Completion proof

## Phase B: Shared Runtime

Implement:

- Goal Interpreter
- Input Validator
- Context Builder
- Planning Engine
- Plan Critic
- Reflection Engine
- Completion Prover

## Phase C: Convert Agents 1-3

These have strong deterministic tools and clear contracts.

## Phase D: Convert Agents 4-10

Add hypotheses, contradiction resolution, scenario planning, peer contracts, and completion proofs.

## Phase E: Convert Agents 11-22

Apply the same cognition layer to operational, governance, evaluation, and retrieval agents.

## Phase F: Upgrade Supervisor

Add global planning, conflict resolution, critical-path scheduling, and proof validation.

## Phase G: Evaluation

Add agentic behavior metrics and release gates.

---

# 28. Recommended Implementation Order

```text
1. Goal Interpreter
2. Input Validator
3. Context Builder
4. Advanced Plan Schema
5. Plan Critic
6. Structured Reflection
7. Uncertainty Calibrator
8. Completion Prover
9. Peer Request Contracts
10. Contradiction Resolver
11. Experience Memory
12. Convert Agents 1-3
13. Convert Agents 4-10
14. Convert Agents 11-22
15. Upgrade Supervisor
16. Add agentic evaluation gates
```

---

# 29. Demonstration Scenario

```text
1. Supervisor receives an accreditation objective.
2. Goal Interpreter normalizes the scope.
3. Input Validator detects a missing requirement version.
4. Governed Retrieval provides the current version.
5. Collector creates a source acquisition plan.
6. Plan Critic adds an omitted shared-drive source.
7. Collector discovers and registers evidence.
8. Classification forms two document hypotheses.
9. It retries OCR and selects the stronger hypothesis.
10. Integrity detects a count contradiction.
11. Claim Agent compares competing explanations.
12. Gap Agent generates three strategies.
13. Ownership Agent reasons over workload and authority.
14. Liaison verifies task understandability.
15. Closure validates corrected evidence.
16. Package Agent plans the reviewer journey.
17. Quality Agent independently reproduces counts.
18. Supervisor validates every completion proof.
19. Human approves the final governed action.
```

This demonstrates genuine agentic behavior rather than sequential function calls.

---

# 30. Definition of Done

The upgrade is complete when:

1. Every agent interprets its goal.
2. Every agent validates inputs.
3. Every agent builds context.
4. Non-trivial agents form hypotheses.
5. Every agent creates an explicit plan.
6. Every non-trivial plan is critiqued.
7. Every action has a selection reason.
8. Tool outputs become normalized observations.
9. Agents reflect after meaningful actions.
10. Agents calibrate uncertainty.
11. Peer requests include acceptance conditions.
12. Every replan records what changed.
13. Every agent emits a completion proof.
14. Every decision has an explanation.
15. Human approval remains mandatory for high-impact actions.
16. Experience memory contains only validated cases.
17. Deterministic rules remain authoritative.
18. The Supervisor validates cross-agent consistency.
19. Agentic behavior is measured.
20. All tests and release gates pass.

---

# 31. Final Recommendation

ProofChain already has complete functional coverage.

Do not add more primary agents at this stage.

Make the existing 22 agents deeper and more capable through:

```text
Goal Interpretation
    -> Input Validation
    -> Context Construction
    -> Hypothesis Formation
    -> Planning
    -> Plan Criticism
    -> Action Selection
    -> Observation
    -> Reflection
    -> Uncertainty Calibration
    -> Peer Negotiation
    -> Completion Proof
    -> Explainable Decision
```

The next major milestone should be:

```text
Better understanding
Better plans
Better evidence reasoning
Better coordination
Better uncertainty handling
Better completion proofs
```

This will make ProofChain more precise, unique, mature, trustworthy, and genuinely agentic without destabilizing the successful architecture already implemented.
