/** Typed read contract for persisted ProofChain run projections. */

export interface RunSummary {
  id: string;
  department: string;
  framework: string;
  academicYear: string;
  status: "running" | "completed" | "completed_with_warnings" | "blocked" | "failed" | "pending";
  startedAt: string;
  completedAt?: string;
  duration?: string;
  verifiedReadiness: number;
  projectedReadiness: number;
  openIssues: number;
  blockingIssues: number;
  projectionType?: string;
  projectionAssumptions?: string[];
}

export interface AgentExecution {
  id: number;
  slug: string;
  name: string;
  shortName: string;
  role: string;
  architectureLayer: string;
  status: "completed" | "running" | "warning" | "blocked" | "waiting" | "draft" | "returned" | "skipped";
  confidence?: number;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
  outputArtifacts: string[];
  inputArtifacts: string[];
  errorMessage?: string;
  goals: string[];
  messagesSent: number;
  messagesReceived: number;
  rounds: number;
  peersContacted: string[];
  decisionReason?: string;
  completionProofId?: string;
  explanationId?: string;
  humanApprovalRequired: boolean;
  nextAction?: string;
  policiesApplied: string[];
  rulesApplied: string[];
  uncertainty: string[];
}

export interface AgentPlanStep {
  id: string;
  sequence: number;
  objective: string;
  tool?: string;
  status: string;
  expectedObservation?: string;
  completionCondition?: string;
  requiredInputs: string[];
}

export interface AgentPlan {
  id: string;
  goalId: string;
  status: string;
  revision: number;
  rationale?: string;
  assumptions: string[];
  dependencies: string[];
  expectedOutputs: string[];
  steps: AgentPlanStep[];
}

export interface AgentCompletion {
  decisionId: string;
  finalStatus: string;
  goalSatisfied: boolean;
  confidence?: number;
  explanation?: string;
  successConditionsMet: string[];
  successConditionsUnmet: string[];
  blockers: string[];
  unresolvedQuestions: string[];
  supportingArtifacts: string[];
  createdAt?: string;
}

export interface CognitionRecord {
  observation_id?: string;
  reflection_id?: string;
  action_id?: string;
  summary?: string;
  progress_assessment?: string;
  reason?: string;
  decision?: string;
  selected_tool?: string;
  expected_information_gain?: number;
  confidence?: number;
  created_at?: string;
  [key: string]: unknown;
}

export interface ModelProfile {
  agent_name: string;
  execution_mode: string;
  external_model_calls: number;
  fallback_behavior: string;
  high_impact_actions_require_approval: boolean;
  model_id?: string;
  model_provider?: string;
  prompt_version?: string;
}

export interface GoalNode {
  id: string;
  title: string;
  agentId: number;
  agentName: string;
  status: "achieved" | "failed" | "active" | "pending" | "abandoned";
  confidence?: number;
  parentId?: string;
  criterionId?: string;
  reasoning?: string;
  toolCalls: ToolCall[];
  evidenceRefs: string[];
  createdAt: string;
  resolvedAt?: string;
}

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  result?: unknown;
  durationMs?: number;
}

export interface WorkflowEvent {
  id: string;
  timestamp: string;
  eventType: string;
  agentId?: number;
  agentName?: string;
  data: Record<string, unknown>;
  runId: string;
  sequenceNumber: number;
  eventHash?: string;
  previousEventHash?: string;
}

export interface PeerMessage {
  id: string;
  fromAgentId: number;
  fromAgentName: string;
  toAgentId: number;
  toAgentName: string;
  messageType: string;
  payload: Record<string, unknown>;
  timestamp: string;
  roundNumber: number;
}

export interface GovernanceCheckpoint {
  stage_name: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  input_sha256?: string;
  upstream_sha256?: string;
  output?: {
    path?: string;
    record_count?: number;
    sha256?: string;
    schema_version?: string;
  };
}

export interface AgentDetail {
  agent: AgentExecution;
  goal: GoalNode | null;
  goals: GoalNode[];
  plan: AgentPlan | null;
  completion: AgentCompletion | null;
  observations: CognitionRecord[];
  reflections: CognitionRecord[];
  actions: CognitionRecord[];
  toolCalls: CognitionRecord[];
  decisions: CognitionRecord[];
  events: WorkflowEvent[];
  messages: PeerMessage[];
  checkpoints: GovernanceCheckpoint[];
  modelProfile: ModelProfile | null;
  runtimeDirectory: string;
}

export interface GovernanceProjection {
  runId: string;
  checkpoints: GovernanceCheckpoint[];
  events: WorkflowEvent[];
  policyFingerprint?: string;
  policySetVersion?: string;
  policies: Array<{
    policy_id: string;
    schema_version: string;
    sha256: string;
    path: string;
  }>;
  modelProfiles: ModelProfile[];
  componentSummary: Record<string, number>;
  validation: {
    technicalComplete?: boolean;
    persistenceSynchronized?: boolean;
    standard: { valid?: boolean; errors?: string[] };
    agentic: { valid?: boolean; agents_validated?: number; errors?: string[] };
  };
}

export interface EvidenceRecord {
  id: string;
  filename: string;
  evidenceType: string;
  criterionId?: string;
  status: "registered" | "classified" | "verified" | "completed" | "completed_with_warnings" | "quarantined" | "stale";
  confidence?: number;
  hash?: string;
  registeredAt: string;
  source: string;
  tags: string[];
  integrityFindings?: IntegrityFinding[];
  capabilityReason?: string;
}

export interface IntegrityFinding {
  ruleId: string;
  ruleName: string;
  status: "passed" | "failed" | "warning";
  detail: string;
  impactedEvidenceIds: string[];
}

export interface Claim {
  id: string;
  criterionId: string;
  text: string;
  status: "supported" | "contradicted" | "partially supported" | "unverified" | "needs review";
  confidence?: number;
  supportingEvidenceIds: string[];
  contradictingEvidenceIds: string[];
  agentReasoning?: string;
  reviewRequired: boolean;
  createdAt: string;
}

export interface Issue {
  id: string;
  criterionId: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "informational";
  status: "open" | "planned" | "assigned" | "in progress" | "evidence submitted" | "under revalidation" | "resolved" | "reopened" | "awaiting approval";
  owner?: string;
  readinessImpact: number; // negative number, e.g. -12
  dueDate?: string;
  resolutionPlan?: string;
  blockedByIds: string[];
  taskIds: string[];
  claimIds: string[];
  createdAt: string;
  resolvedAt?: string;
}

export interface ResolutionTask {
  id: string;
  issueId: string;
  title: string;
  description: string;
  assignedTo: string;
  assignedToEmail?: string;
  status: "pending" | "in progress" | "completed" | "overdue";
  dueDate?: string;
  draftCommunication?: string;
  responseReceived?: string;
  createdAt: string;
  completedAt?: string;
}

export interface ApprovalDecision {
  id: string;
  subject: string;
  subjectType: "ownership" | "closure" | "package" | "claim" | "custom";
  requiredApprover: string;
  status: "pending" | "approved" | "rejected" | "superseded";
  reason?: string;
  decidedAt?: string;
  decidedBy?: string;
  criterionId?: string;
  relatedIds: string[];
  createdAt: string;
}

export interface AuditPackage {
  id: string;
  runId: string;
  status: "draft" | "ready" | "approved" | "correction required" | "rejected";
  contents: PackageItem[];
  qualityReview?: QualityReview;
  createdAt: string;
  approvedAt?: string;
  downloadUrl?: string;
  packageHash?: string;
  bundleSha256?: string;
}

export interface PackageItem {
  criterionId: string;
  evidenceIds: string[];
  claimIds: string[];
  eligibilityExplanation: string;
  ready: boolean;
}

export interface QualityReview {
  id: string;
  packageId: string;
  status: "passed" | "failed" | "correction required";
  score?: number;
  findings: QualityFinding[];
  reviewedAt: string;
}

export interface QualityFinding {
  id: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  criterionId?: string;
  correctionRequired: string;
  resolved: boolean;
}

export interface DashboardMetrics {
  run: RunSummary;
  verifiedReadiness: number;
  projectedReadiness: number;
  openIssues: number;
  blockingIssues: number;
  claimsForReview: number;
  pendingApprovals: number;
  agentPipelineHealth: "healthy" | "degraded" | "blocked";
  totalEvidence: number;
  verifiedEvidence: number;
}

export interface WorkflowStatus {
  runId: string;
  domainStatus: string;
  happened: {
    completedGoals: string[];
    agentCount: number;
    eventCount: number;
  };
  happeningNow: string[];
  blocked: Array<{
    goalId?: string;
    agent?: string;
    reason?: string;
    priority?: string;
  }>;
  userMustDo: Array<{
    type: string;
    target?: string;
    owner?: string;
    reason?: string;
  }>;
  nextSteps: string[];
  finalDecision?: Record<string, unknown>;
  qualityDecision?: string;
  submissionDecision?: string;
  counterfactualProjection?: {
    value: number;
    type: string;
    assumptions: string[];
  };
}

export interface PlatformHealth {
  status: "healthy" | "degraded" | "unhealthy";
  runId?: string;
  checks: Array<{
    name: string;
    status: "healthy" | "warning" | "error";
    healthy: boolean;
    detail: string;
  }>;
  summary: {
    passed: number;
    warnings: number;
    failed: number;
  };
}

/** All public read methods. The provider implementation never runs CLI commands. */
export interface ProofChainDataProvider {
  /** Run-level */
  getRuns(): Promise<RunSummary[]>;
  getRunById(runId: string): Promise<RunSummary | null>;
  getDashboardMetrics(runId: string): Promise<DashboardMetrics>;
  getWorkflowStatus(runId: string): Promise<WorkflowStatus>;
  getPlatformHealth(runId?: string): Promise<PlatformHealth>;

  /** Agents */
  getAgents(runId: string): Promise<AgentExecution[]>;
  getAgentById(runId: string, agentId: number): Promise<AgentDetail | null>;

  /** Goals */
  getGoals(runId: string): Promise<GoalNode[]>;

  /** Events */
  getEvents(runId: string, limit?: number, offset?: number): Promise<WorkflowEvent[]>;
  getPeerMessages(runId: string): Promise<PeerMessage[]>;

  /** Evidence */
  getEvidence(runId: string): Promise<EvidenceRecord[]>;

  /** Claims */
  getClaims(runId: string): Promise<Claim[]>;

  /** Issues */
  getIssues(runId: string): Promise<Issue[]>;

  /** Tasks */
  getTasks(runId: string): Promise<ResolutionTask[]>;

  /** Approvals */
  getApprovals(runId: string): Promise<ApprovalDecision[]>;

  /** Package */
  getPackage(runId: string): Promise<AuditPackage | null>;

  /** Governance */
  getGovernance(runId: string): Promise<GovernanceProjection>;
}
