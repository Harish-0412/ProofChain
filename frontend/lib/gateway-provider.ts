import {
  ProofChainDataProvider,
  RunSummary,
  AgentExecution,
  AgentDetail,
  GoalNode,
  WorkflowEvent,
  PeerMessage,
  EvidenceRecord,
  Claim,
  Issue,
  ResolutionTask,
  ApprovalDecision,
  AuditPackage,
  DashboardMetrics,
  WorkflowStatus,
  PlatformHealth,
  GovernanceProjection,
} from "./data-provider";

const GATEWAY_BASE = process.env.NEXT_PUBLIC_GATEWAY_URL || "/proofchain-data";

export class GatewayDataProvider implements ProofChainDataProvider {
  private async fetchJson<T>(path: string): Promise<T> {
    const res = await fetch(`${GATEWAY_BASE}${path}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Gateway HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
  }

  async getRuns(): Promise<RunSummary[]> {
    return this.fetchJson<RunSummary[]>("/runs");
  }

  async getRunById(runId: string): Promise<RunSummary | null> {
    return this.fetchJson<RunSummary>(`/runs/${runId}`);
  }

  async getDashboardMetrics(runId: string): Promise<DashboardMetrics> {
    return this.fetchJson<DashboardMetrics>(`/runs/${runId}/metrics`);
  }

  async getWorkflowStatus(runId: string): Promise<WorkflowStatus> {
    return this.fetchJson<WorkflowStatus>(`/runs/${runId}/workflow-status`);
  }

  async getPlatformHealth(runId?: string): Promise<PlatformHealth> {
    return this.fetchJson<PlatformHealth>(
      `/health${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`
    );
  }

  async getAgents(runId: string): Promise<AgentExecution[]> {
    return this.fetchJson<AgentExecution[]>(`/runs/${runId}/agents`);
  }

  async getAgentById(runId: string, agentId: number): Promise<AgentDetail | null> {
    return this.fetchJson<AgentDetail>(`/runs/${runId}/agents/${agentId}`);
  }

  async getGoals(runId: string): Promise<GoalNode[]> {
    return this.fetchJson<GoalNode[]>(`/runs/${runId}/goals`);
  }

  async getEvents(runId: string, limit = 50, offset = 0): Promise<WorkflowEvent[]> {
    return this.fetchJson<WorkflowEvent[]>(`/runs/${runId}/events?limit=${limit}&offset=${offset}`);
  }

  async getPeerMessages(runId: string): Promise<PeerMessage[]> {
    return this.fetchJson<PeerMessage[]>(`/runs/${runId}/messages`);
  }

  async getEvidence(runId: string): Promise<EvidenceRecord[]> {
    return this.fetchJson<EvidenceRecord[]>(`/runs/${runId}/evidence`);
  }

  async getClaims(runId: string): Promise<Claim[]> {
    return this.fetchJson<Claim[]>(`/runs/${runId}/claims`);
  }

  async getIssues(runId: string): Promise<Issue[]> {
    return this.fetchJson<Issue[]>(`/runs/${runId}/issues`);
  }

  async getTasks(runId: string): Promise<ResolutionTask[]> {
    return this.fetchJson<ResolutionTask[]>(`/runs/${runId}/tasks`);
  }

  async getApprovals(runId: string): Promise<ApprovalDecision[]> {
    return this.fetchJson<ApprovalDecision[]>(`/runs/${runId}/approvals`);
  }

  async getPackage(runId: string): Promise<AuditPackage | null> {
    return this.fetchJson<AuditPackage>(`/runs/${runId}/package`);
  }

  async getGovernance(runId: string): Promise<GovernanceProjection> {
    return this.fetchJson<GovernanceProjection>(`/runs/${runId}/governance`);
  }
}
