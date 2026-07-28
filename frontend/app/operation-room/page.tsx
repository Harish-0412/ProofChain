"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  FileSearch,
  FileText,
  GitBranch,
  Layers3,
  LockKeyhole,
  Package,
  Play,
  Route,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import {
  AgentExecution,
  ApprovalDecision,
  AuditPackage,
  Claim,
  DashboardMetrics,
  EvidenceRecord,
  GovernanceProjection,
  Issue,
  ResolutionTask,
  WorkflowEvent,
  WorkflowStatus,
} from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { GovernanceBoundaryNotice } from "@/components/ui/governance-boundary-notice";
import { LivePageHeader } from "@/components/live/live-page";

interface OperationRoomData {
  metrics: DashboardMetrics;
  workflow: WorkflowStatus;
  agents: AgentExecution[];
  events: WorkflowEvent[];
  evidence: EvidenceRecord[];
  claims: Claim[];
  issues: Issue[];
  tasks: ResolutionTask[];
  approvals: ApprovalDecision[];
  auditPackage: AuditPackage | null;
  governance: GovernanceProjection;
}

const PHASES = [
  {
    title: "Collect and understand",
    href: "/evidence",
    agents: [1, 2, 3],
    icon: FileSearch,
    detail: "Evidence identity, extraction, classification, integrity.",
  },
  {
    title: "Reason and challenge",
    href: "/claims",
    agents: [4, 5],
    icon: GitBranch,
    detail: "Claims, contradictions, canonical gaps, readiness impact.",
  },
  {
    title: "Assign and correct",
    href: "/tasks",
    agents: [6, 7, 8],
    icon: ClipboardCheck,
    detail: "Ownership, tasks, responses, targeted revalidation.",
  },
  {
    title: "Package and review",
    href: "/packages",
    agents: [9, 10],
    icon: Package,
    detail: "Manifest, exclusions, quality challenge, release risk.",
  },
  {
    title: "Govern and operate",
    href: "/governance",
    agents: [11, 12, 13, 14, 15, 16, 17, 18, 19],
    icon: ShieldCheck,
    detail: "Persistence, continuation, identity, policy, security, tenant boundaries.",
  },
  {
    title: "Submit and assure",
    href: "/system-health",
    agents: [20, 21, 22],
    icon: LockKeyhole,
    detail: "Submission eligibility, golden scenarios, governed retrieval.",
  },
];

const START_STEPS = [
  {
    title: "Start the governed run",
    command:
      "proofchain run-complete --source sample_data/mock_institution/departments --departments AIML AIDS CSE --academic-year 2025-2026 --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1 --tenant-id default-institution --department-id CSE",
    href: "/runs",
  },
  {
    title: "Validate the artifacts",
    command: "proofchain validate-run RUN-ID",
    href: "/governance",
  },
  {
    title: "Validate the agentic proofs",
    command: "proofchain validate-agentic-run RUN-ID",
    href: "/agents",
  },
  {
    title: "Inspect technical health",
    command: "proofchain health-check --run-id RUN-ID",
    href: "/system-health",
  },
];

function percent(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function byStatus(agents: AgentExecution[], ids: number[]) {
  const phaseAgents = agents.filter((agent) => ids.includes(agent.id));
  return {
    agents: phaseAgents,
    complete: phaseAgents.filter((agent) => agent.status === "completed").length,
    blocked: phaseAgents.filter((agent) => ["blocked", "returned", "warning"].includes(agent.status)).length,
  };
}

function formatDecision(value?: string) {
  return value ? value.replaceAll("_", " ") : "not recorded";
}

export default function OperationRoomPage() {
  const resource = useRunResource<OperationRoomData>("operation-room", async (runId) => {
    const provider = getDataProvider();
    const [
      metrics,
      workflow,
      agents,
      events,
      evidence,
      claims,
      issues,
      tasks,
      approvals,
      auditPackage,
      governance,
    ] = await Promise.all([
      provider.getDashboardMetrics(runId),
      provider.getWorkflowStatus(runId),
      provider.getAgents(runId),
      provider.getEvents(runId, 120, 0),
      provider.getEvidence(runId),
      provider.getClaims(runId),
      provider.getIssues(runId),
      provider.getTasks(runId),
      provider.getApprovals(runId),
      provider.getPackage(runId),
      provider.getGovernance(runId),
    ]);
    return {
      metrics,
      workflow,
      agents,
      events,
      evidence,
      claims,
      issues,
      tasks,
      approvals,
      auditPackage,
      governance,
    };
  });

  if (resource.error) {
    return <ErrorState title="Operation room unavailable" message={resource.error} onRetry={resource.refresh} />;
  }
  if (resource.loading || !resource.data || !resource.activeRun) {
    return <LoadingState message="Opening the persisted ProofChain operation room" />;
  }

  const {
    metrics,
    workflow,
    agents,
    events,
    evidence,
    claims,
    issues,
    tasks,
    approvals,
    auditPackage,
    governance,
  } = resource.data;

  const completedAgents = agents.filter((agent) => agent.status === "completed").length;
  const pendingApprovals = approvals.filter((approval) => approval.status === "pending");
  const openIssues = issues.filter((issue) => issue.status !== "resolved");
  const activeTasks = tasks.filter((task) => task.status !== "completed");
  const reviewClaims = claims.filter((claim) => claim.reviewRequired);
  const latestEvents = events.slice(-8).reverse();
  const latestEvent = latestEvents[0];
  const validationState = governance.validation;
  const runId = resource.activeRun.id;
  const validationCommands = START_STEPS.slice(1).map((step) => ({
    ...step,
    command: step.command.replace("RUN-ID", runId),
  }));

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Transparent agentic command surface"
          title="ProofChain Operation Room"
          description="A live run map that shows how evidence becomes a governed decision, which agents produced each layer, and exactly what must be started, checked, corrected, or approved next."
          run={resource.activeRun}
          onRefresh={resource.refresh}
          actions={
            <Link className="btn btn-primary btn-sm" href="/agents">
              <Bot size={14} />
              Agent map
            </Link>
          }
        />
      </motion.div>

      <motion.section variants={itemVariants} className="grid grid-cols-1 2xl:grid-cols-[1.15fr_0.85fr] gap-5">
        <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center justify-between gap-3 flex-wrap">
            <div>
              <p className="text-subheading">Current truth</p>
              <h2 className="text-heading">Evidence-backed decision state</h2>
            </div>
            <StatusBadge status={workflow.domainStatus} size="md" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="p-5 border-b lg:border-b-0 lg:border-r border-[var(--color-border)]">
              <p className="text-sm font-semibold capitalize">{formatDecision(workflow.domainStatus)}</p>
              <p className="text-xs text-[var(--color-text-secondary)] mt-2">
                Quality review is {formatDecision(workflow.qualityDecision)}. External submission is {formatDecision(workflow.submissionDecision)}.
              </p>
              <div className="mt-5 space-y-4">
                <ReadinessMeter
                  label="Verified readiness"
                  value={metrics.verifiedReadiness}
                  detail="Current proof-backed value"
                />
                <ReadinessMeter
                  label="Projected readiness"
                  value={metrics.projectedReadiness}
                  detail={`${metrics.run.projectionType ?? "counterfactual"} projection`}
                  muted
                />
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4">
              <TruthTile label="Agents complete" value={`${completedAgents}/${agents.length}`} detail={`${workflow.happened.agentCount} recorded`} icon={Bot} />
              <TruthTile label="Evidence" value={metrics.totalEvidence} detail={`${metrics.verifiedEvidence} usable`} icon={FileText} />
              <TruthTile label="Open issues" value={metrics.openIssues} detail={`${metrics.blockingIssues} blocking`} icon={AlertTriangle} />
              <TruthTile label="Event chain" value={workflow.happened.eventCount} detail={latestEvent?.eventType.replaceAll("_", " ") ?? "No event"} icon={Activity} />
            </div>
          </div>
        </div>

        <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--color-border)]">
            <p className="text-subheading">Start and validate</p>
            <h2 className="text-heading">Operator launch rail</h2>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            <LaunchStep
              number="01"
              title={START_STEPS[0].title}
              command={START_STEPS[0].command}
              href={START_STEPS[0].href}
            />
            {validationCommands.map((step, index) => (
              <LaunchStep
                key={step.title}
                number={String(index + 2).padStart(2, "0")}
                title={step.title}
                command={step.command}
                href={step.href}
              />
            ))}
          </div>
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
        <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p className="text-subheading">Workflow spine</p>
            <h2 className="text-heading">How the run moves from evidence to decision</h2>
          </div>
          <Link className="btn btn-secondary btn-sm" href="/governance">
            Governance trace <ArrowRight size={14} />
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
          {PHASES.map((phase, index) => {
            const state = byStatus(agents, phase.agents);
            const Icon = phase.icon;
            return (
              <Link
                key={phase.title}
                href={phase.href}
                className="group p-5 border-b md:border-r border-[var(--color-border-subtle)] hover:bg-[var(--color-panel-hover)] transition-colors min-h-[178px]"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-md bg-[var(--color-panel-active)] text-[var(--color-evidence-blue)] flex items-center justify-center">
                      <Icon size={16} />
                    </span>
                    <span className="text-[10px] font-mono text-[var(--color-text-tertiary)]">PHASE {String(index + 1).padStart(2, "0")}</span>
                  </div>
                  <ArrowRight size={15} className="text-[var(--color-text-tertiary)] group-hover:text-[var(--color-evidence-blue)]" />
                </div>
                <h3 className="text-sm font-semibold mt-4 group-hover:text-[var(--color-evidence-blue)]">{phase.title}</h3>
                <p className="text-xs text-[var(--color-text-secondary)] mt-2">{phase.detail}</p>
                <div className="mt-4 flex items-center justify-between gap-2 text-[11px]">
                  <span>{state.complete}/{state.agents.length} agents complete</span>
                  <span className={state.blocked > 0 ? "text-[var(--color-warning)] font-semibold" : "text-[var(--color-verified)] font-semibold"}>
                    {state.blocked > 0 ? `${state.blocked} need attention` : "clear"}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </motion.section>

      <div className="grid grid-cols-1 2xl:grid-cols-[1.35fr_0.65fr] gap-5">
        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center justify-between gap-3 flex-wrap">
            <div>
              <p className="text-subheading">Agent constellation</p>
              <h2 className="text-heading">22 governed agents by architecture layer</h2>
            </div>
            <Link className="btn btn-secondary btn-sm" href="/agents">
              Inspect details <ArrowRight size={14} />
            </Link>
          </div>
          <div className="p-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {PHASES.map((phase) => {
              const layerAgents = agents.filter((agent) => phase.agents.includes(agent.id));
              return (
                <div key={phase.title} className="border border-[var(--color-border-subtle)] rounded-lg overflow-hidden">
                  <div className="px-4 py-3 bg-[var(--color-border-subtle)] flex items-center justify-between gap-2">
                    <p className="text-xs font-bold">{phase.title}</p>
                    <span className="text-[10px] font-mono text-[var(--color-text-tertiary)]">{layerAgents.length} agents</span>
                  </div>
                  <div className="divide-y divide-[var(--color-border-subtle)]">
                    {layerAgents.map((agent) => (
                      <Link key={agent.id} href={`/agents/${agent.id}`} className="block px-4 py-3 hover:bg-[var(--color-panel-hover)]">
                        <div className="flex items-start gap-3">
                          <span className="w-7 h-7 rounded-md border border-[var(--color-border)] flex items-center justify-center text-[10px] font-mono flex-shrink-0">
                            {agent.id}
                          </span>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-2">
                              <p className="text-xs font-semibold truncate">{agent.shortName || agent.name}</p>
                              <StatusBadge status={agent.status} size="sm" />
                            </div>
                            <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1 line-clamp-2">{agent.decisionReason ?? agent.nextAction ?? agent.role}</p>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--color-border)]">
            <p className="text-subheading">Needs attention</p>
            <h2 className="text-heading">Human action queue</h2>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {workflow.userMustDo.slice(0, 5).map((action, index) => (
              <ActionRow
                key={`${action.type}-${action.target ?? index}`}
                label={action.type.replaceAll("_", " ")}
                value={action.reason ?? action.target ?? "Human decision required"}
                href="/approvals"
              />
            ))}
            {pendingApprovals.slice(0, 4).map((approval) => (
              <ActionRow
                key={approval.id}
                label={approval.subjectType}
                value={`${approval.subject} requires ${approval.requiredApprover}`}
                href="/approvals"
              />
            ))}
            {workflow.userMustDo.length === 0 && pendingApprovals.length === 0 && (
              <div className="px-5 py-8 text-sm text-[var(--color-text-tertiary)]">No pending human action is projected for this run.</div>
            )}
          </div>
        </motion.section>
      </div>

      <motion.section variants={itemVariants} className="grid grid-cols-1 xl:grid-cols-[1fr_1fr_0.8fr] gap-5">
        <TracePanel
          title="Evidence to decision trace"
          icon={Route}
          rows={[
            { label: "Evidence records", value: evidence.length, href: "/evidence" },
            { label: "Claims evaluated", value: claims.length, href: "/claims" },
            { label: "Claims needing review", value: reviewClaims.length, href: "/claims" },
            { label: "Open canonical issues", value: openIssues.length, href: "/issues" },
            { label: "Active correction tasks", value: activeTasks.length, href: "/tasks" },
          ]}
        />
        <TracePanel
          title="Package and approval state"
          icon={FileCheck2}
          rows={[
            { label: "Package status", value: auditPackage?.status ?? "not generated", href: "/packages" },
            { label: "Package items", value: auditPackage?.contents.length ?? 0, href: "/packages" },
            { label: "Quality score", value: auditPackage?.qualityReview?.score ?? "not scored", href: "/packages" },
            { label: "Pending approvals", value: pendingApprovals.length, href: "/approvals" },
            { label: "Submission decision", value: formatDecision(workflow.submissionDecision), href: "/packages" },
          ]}
        />
        <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
            <Layers3 size={16} className="text-[var(--color-evidence-blue)]" />
            <h2 className="text-sm font-semibold">Validation state</h2>
          </div>
          <div className="p-5 space-y-3">
            <ValidationPill label="Standard validation" ok={validationState.standard.valid === true} />
            <ValidationPill label="Agentic validation" ok={validationState.agentic.valid === true} />
            <ValidationPill label="Persistence synchronized" ok={validationState.persistenceSynchronized === true} />
            <ValidationPill label="Technical complete" ok={validationState.technicalComplete === true} />
            <p className="text-xs text-[var(--color-text-tertiary)] pt-2">
              {validationState.agentic.agents_validated ?? agents.length} agent proofs represented in validation projection.
            </p>
          </div>
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className="grid grid-cols-1 xl:grid-cols-[0.95fr_1.05fr] gap-5">
        <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
            <Clock3 size={16} className="text-[var(--color-evidence-blue)]" />
            <h2 className="text-sm font-semibold">Latest synchronized events</h2>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {latestEvents.map((event) => (
              <div key={event.id} className="px-5 py-3 flex items-start gap-3">
                <span className="text-[10px] font-mono text-[var(--color-text-tertiary)] w-10 flex-shrink-0">
                  #{event.sequenceNumber}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold">{event.eventType.replaceAll("_", " ")}</p>
                  <p className="text-[10px] text-[var(--color-text-tertiary)] mt-0.5">
                    {event.agentName?.replaceAll("_", " ") ?? "system"} {event.timestamp ? `- ${new Date(event.timestamp).toLocaleString()}` : ""}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} className="text-[var(--color-warning)]" />
              <h2 className="text-sm font-semibold">Blocking issue register</h2>
            </div>
            <Link href="/issues" className="btn btn-secondary btn-sm">
              Open register <ArrowRight size={14} />
            </Link>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {openIssues.slice(0, 6).map((issue) => (
              <Link key={issue.id} href="/issues" className="block px-5 py-3 hover:bg-[var(--color-panel-hover)]">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs font-semibold truncate">{issue.title}</p>
                    <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">
                      {issue.criterionId} - {issue.status} - owner {issue.owner ?? "unassigned"}
                    </p>
                  </div>
                  <SeverityBadge severity={issue.severity} />
                </div>
              </Link>
            ))}
            {openIssues.length === 0 && (
              <div className="px-5 py-8 text-sm text-[var(--color-text-tertiary)]">No unresolved issue is projected for this run.</div>
            )}
          </div>
        </div>
      </motion.section>

      <motion.div variants={itemVariants}>
        <GovernanceBoundaryNotice message={`Verified readiness is ${metrics.verifiedReadiness}%. The ${metrics.projectedReadiness}% projected value is counterfactual until required corrections, approvals, and revalidation pass.`} />
      </motion.div>
    </motion.div>
  );
}

function ReadinessMeter({
  label,
  value,
  detail,
  muted = false,
}: {
  label: string;
  value: number;
  detail: string;
  muted?: boolean;
}) {
  const bounded = percent(value);
  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="font-semibold">{label}</span>
        <span className="font-mono font-bold">{bounded}%</span>
      </div>
      <div className="h-2 mt-2 rounded-full bg-[var(--color-border-subtle)] overflow-hidden">
        <div
          className={muted ? "h-full bg-[var(--color-warning)]" : "h-full bg-[var(--color-evidence-blue)]"}
          style={{ width: `${bounded}%` }}
        />
      </div>
      <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">{detail}</p>
    </div>
  );
}

function TruthTile({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string;
  value: ReactNode;
  detail: string;
  icon: LucideIcon;
}) {
  return (
    <div className="p-5 border-b border-r border-[var(--color-border-subtle)] min-h-[132px]">
      <div className="flex items-center justify-between gap-3">
        <Icon size={16} className="text-[var(--color-evidence-blue)]" />
        <CheckCircle2 size={14} className="text-[var(--color-text-tertiary)]" />
      </div>
      <p className="text-2xl font-bold mt-4">{value}</p>
      <p className="text-xs font-semibold mt-1">{label}</p>
      <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">{detail}</p>
    </div>
  );
}

function LaunchStep({
  number,
  title,
  command,
  href,
}: {
  number: string;
  title: string;
  command: string;
  href: string;
}) {
  return (
    <Link href={href} className="block px-5 py-4 hover:bg-[var(--color-panel-hover)]">
      <div className="flex items-start gap-3">
        <span className="w-8 h-8 rounded-md border border-[var(--color-border)] flex items-center justify-center text-[10px] font-mono flex-shrink-0">
          {number}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Play size={13} className="text-[var(--color-evidence-blue)]" />
            <p className="text-xs font-semibold">{title}</p>
          </div>
          <code className="block mt-2 text-[10px] leading-5 font-mono text-[var(--color-text-secondary)] bg-[var(--color-border-subtle)] border border-[var(--color-border)] rounded-md p-2 overflow-x-auto">
            {command}
          </code>
        </div>
      </div>
    </Link>
  );
}

function ActionRow({ label, value, href }: { label: string; value: string; href: string }) {
  return (
    <Link href={href} className="block px-5 py-4 hover:bg-[var(--color-panel-hover)]">
      <p className="text-[10px] uppercase font-bold text-[var(--color-text-tertiary)]">{label}</p>
      <p className="text-xs font-semibold mt-1">{value}</p>
    </Link>
  );
}

function TracePanel({
  title,
  icon: Icon,
  rows,
}: {
  title: string;
  icon: LucideIcon;
  rows: Array<{ label: string; value: ReactNode; href: string }>;
}) {
  return (
    <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
      <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
        <Icon size={16} className="text-[var(--color-evidence-blue)]" />
        <h2 className="text-sm font-semibold">{title}</h2>
      </div>
      <div className="divide-y divide-[var(--color-border-subtle)]">
        {rows.map((row) => (
          <Link key={row.label} href={row.href} className="px-5 py-3 flex items-center justify-between gap-3 hover:bg-[var(--color-panel-hover)]">
            <span className="text-xs text-[var(--color-text-secondary)]">{row.label}</span>
            <span className="text-xs font-bold text-right">{row.value}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

function ValidationPill({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 border border-[var(--color-border-subtle)] rounded-md px-3 py-2">
      <span className="text-xs font-semibold">{label}</span>
      <span className={ok ? "text-[var(--color-verified)]" : "text-[var(--color-warning)]"}>
        {ok ? <CheckCircle2 size={15} /> : <Clock3 size={15} />}
      </span>
    </div>
  );
}
