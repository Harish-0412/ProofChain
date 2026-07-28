"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDashed,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  FileSearch,
  FileText,
  GitBranch,
  HelpCircle,
  ListChecks,
  PackageCheck,
  RefreshCw,
  Route,
  ShieldCheck,
  Sparkles,
  UserRoundCheck,
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
import { useUIStore } from "@/stores/ui-store";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { SeverityBadge } from "@/components/ui/severity-badge";
import styles from "./dashboard.module.css";

interface DashboardData {
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

interface WorkflowPhase {
  id: string;
  number: string;
  title: string;
  plainTitle: string;
  question: string;
  input: string;
  work: string;
  output: string;
  href: string;
  agentIds: number[];
  icon: LucideIcon;
}

interface NextAction {
  id: string;
  title: string;
  why: string;
  owner: string;
  due: string;
  impact: string;
  href: string;
  cta: string;
  urgency: "critical" | "high" | "normal";
}

const WORKFLOW_PHASES: WorkflowPhase[] = [
  {
    id: "collect",
    number: "01",
    title: "Collect & understand",
    plainTitle: "Read the evidence",
    question: "What information did the institution provide?",
    input: "Uploaded reports, spreadsheets, certificates, photos, and institutional records.",
    work: "Agents identify every file, extract fields, classify its purpose, and check integrity.",
    output: "A searchable evidence register with source, type, confidence, checksum, and any integrity warning.",
    href: "/evidence",
    agentIds: [1, 2, 3],
    icon: FileSearch,
  },
  {
    id: "reason",
    number: "02",
    title: "Reason & challenge",
    plainTitle: "Test every claim",
    question: "What can the evidence actually prove?",
    input: "Verified evidence records and the accreditation requirements they are expected to support.",
    work: "Agents build claims, compare sources, find contradictions, and refuse unsupported conclusions.",
    output: "Defensible claims plus a canonical list of gaps, contradictions, and readiness impact.",
    href: "/claims",
    agentIds: [4, 5],
    icon: GitBranch,
  },
  {
    id: "correct",
    number: "03",
    title: "Assign & correct",
    plainTitle: "Turn gaps into work",
    question: "Who must fix each problem, and what must they submit?",
    input: "Open issues, affected requirements, ownership rules, and due-date policies.",
    work: "Agents assign accountable owners, prepare correction tasks, track replies, and re-check new evidence.",
    output: "An owned task register that states the required deliverable, due date, and verification result.",
    href: "/tasks",
    agentIds: [6, 7, 8],
    icon: ClipboardCheck,
  },
  {
    id: "package",
    number: "04",
    title: "Package & review",
    plainTitle: "Build the audit package",
    question: "Is the evidence complete, defensible, and ready for human review?",
    input: "Verified evidence, supported claims, resolved issues, and approved exceptions.",
    work: "Agents assemble the manifest, record exclusions, challenge package quality, and return weak material.",
    output: "A reviewable audit package with a manifest, eligibility explanations, exclusions, and quality findings.",
    href: "/packages",
    agentIds: [9, 10],
    icon: PackageCheck,
  },
  {
    id: "govern",
    number: "05",
    title: "Govern & protect",
    plainTitle: "Prove the process was safe",
    question: "Can every action be traced, continued, and governed?",
    input: "Agent decisions, state transitions, policy versions, identities, and security signals.",
    work: "Agents persist the event chain, enforce permissions, protect tenant boundaries, and validate continuity.",
    output: "A tamper-evident governance trail with policies, checkpoints, approvals, and completion proofs.",
    href: "/governance",
    agentIds: [11, 12, 13, 14, 15, 16, 17, 18, 19],
    icon: ShieldCheck,
  },
  {
    id: "assure",
    number: "06",
    title: "Submit & assure",
    plainTitle: "Decide if release is allowed",
    question: "May this package leave ProofChain?",
    input: "The reviewed package, human approvals, validation proofs, and submission policy.",
    work: "Agents test submission eligibility, run assurance scenarios, and provide governed retrieval.",
    output: "A clear release decision: approved, blocked with reasons, or returned with exact corrections.",
    href: "/system-health",
    agentIds: [20, 21, 22],
    icon: FileCheck2,
  },
];

const SEVERITY_ORDER: Record<Issue["severity"], number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  informational: 4,
};

function clampPercent(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function humanize(value?: string) {
  return value?.replaceAll("_", " ").trim() || "Not recorded";
}

function formatDate(value?: string) {
  if (!value) return "No due date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function formatTime(value?: string) {
  if (!value) return "Time not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function getPhaseState(agents: AgentExecution[], ids: number[]) {
  const phaseAgents = agents.filter((agent) => ids.includes(agent.id));
  if (phaseAgents.some((agent) => ["blocked", "returned"].includes(agent.status))) return "blocked";
  if (phaseAgents.some((agent) => agent.status === "running")) return "running";
  if (phaseAgents.some((agent) => agent.status === "warning")) return "warning";
  if (phaseAgents.length > 0 && phaseAgents.every((agent) => agent.status === "completed")) return "completed";
  return "waiting";
}

function phaseStateLabel(state: string) {
  if (state === "completed") return "Complete";
  if (state === "running") return "Working now";
  if (state === "blocked") return "Needs attention";
  if (state === "warning") return "Completed with warning";
  return "Waiting";
}

function phaseStateIcon(state: string) {
  if (state === "completed") return <Check size={14} />;
  if (state === "running") return <Activity size={14} />;
  if (state === "blocked" || state === "warning") return <AlertTriangle size={14} />;
  return <Clock3 size={14} />;
}

function currentStateSentence(data: DashboardData) {
  const { metrics, workflow, approvals } = data;
  const pendingApprovals = approvals.filter((approval) => approval.status === "pending").length;
  if (metrics.blockingIssues > 0) {
    return `ProofChain has analysed ${metrics.totalEvidence} evidence records, but this run is not audit-ready because ${metrics.blockingIssues} blocking ${metrics.blockingIssues === 1 ? "issue remains" : "issues remain"}.`;
  }
  if (pendingApprovals > 0) {
    return `The evidence checks are clear. ${pendingApprovals} human ${pendingApprovals === 1 ? "approval is" : "approvals are"} still required before the package can move forward.`;
  }
  if (workflow.domainStatus === "completed") {
    return `ProofChain completed the governed evidence journey and recorded the supporting decisions for this run.`;
  }
  return `ProofChain is processing the selected run. The page below shows what has finished, what is happening now, and what comes next.`;
}

function actionHref(type: string) {
  const value = type.toLowerCase();
  if (value.includes("approval") || value.includes("review")) return "/approvals";
  if (value.includes("evidence") || value.includes("upload")) return "/evidence";
  if (value.includes("task") || value.includes("response")) return "/tasks";
  if (value.includes("package")) return "/packages";
  return "/issues";
}

function buildNextActions(data: DashboardData): NextAction[] {
  const actions: NextAction[] = [];

  data.workflow.userMustDo.forEach((item, index) => {
    actions.push({
      id: `workflow-${item.type}-${item.target ?? index}`,
      title: humanize(item.type),
      why: item.reason || `This human decision is required before the governed workflow can continue.`,
      owner: item.owner || "Assigned human reviewer",
      due: "As soon as possible",
      impact: item.target ? `Unblocks ${item.target}` : "Unblocks the next workflow stage",
      href: actionHref(item.type),
      cta: item.type.toLowerCase().includes("approval") ? "Review decision" : "Open required work",
      urgency: "high",
    });
  });

  data.approvals
    .filter((approval) => approval.status === "pending")
    .forEach((approval) => {
      actions.push({
        id: `approval-${approval.id}`,
        title: `Review ${humanize(approval.subjectType)}: ${approval.subject}`,
        why: approval.reason || "ProofChain cannot make this human-governed state transition on its own.",
        owner: approval.requiredApprover || "Required approver",
        due: "No due date recorded",
        impact: approval.criterionId
          ? `Allows ${approval.criterionId} to continue`
          : "Allows the governed workflow to continue",
        href: "/approvals",
        cta: "Review approval",
        urgency: "high",
      });
    });

  data.issues
    .filter((issue) => issue.status !== "resolved")
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
    .forEach((issue) => {
      actions.push({
        id: `issue-${issue.id}`,
        title: `Resolve ${issue.title}`,
        why: issue.resolutionPlan || issue.description || `This issue weakens ${issue.criterionId}.`,
        owner: issue.owner || "Owner not assigned",
        due: formatDate(issue.dueDate),
        impact:
          issue.readinessImpact !== 0
            ? `${Math.abs(issue.readinessImpact)} readiness points at risk`
            : `Required for ${issue.criterionId}`,
        href: "/issues",
        cta: "Inspect issue",
        urgency: issue.severity === "critical" ? "critical" : issue.severity === "high" ? "high" : "normal",
      });
    });

  data.tasks
    .filter((task) => task.status !== "completed")
    .forEach((task) => {
      actions.push({
        id: `task-${task.id}`,
        title: task.title,
        why: task.description || "This correction must be produced and submitted for revalidation.",
        owner: task.assignedTo || "Owner not assigned",
        due: formatDate(task.dueDate),
        impact: `Produces the correction for ${task.issueId}`,
        href: "/tasks",
        cta: "Open task",
        urgency: task.status === "overdue" ? "critical" : "normal",
      });
    });

  const urgency = { critical: 0, high: 1, normal: 2 };
  return Array.from(new Map(actions.map((action) => [action.title.toLowerCase(), action])).values())
    .sort((a, b) => urgency[a.urgency] - urgency[b.urgency])
    .slice(0, 3);
}

function eventExplanation(event: WorkflowEvent) {
  const data = event.data;
  const candidates = [
    data.summary,
    data.reason,
    data.decision,
    data.explanation,
    data.message,
    data.detail,
    data.status,
  ];
  const detail = candidates.find((value) => typeof value === "string" && value.trim());
  if (typeof detail === "string") return detail;
  return `${event.agentName || "ProofChain"} recorded a governed ${humanize(event.eventType).toLowerCase()} event.`;
}

export default function DashboardPage() {
  const viewMode = useUIStore((state) => state.viewMode);
  const [selectedPhaseId, setSelectedPhaseId] = useState(WORKFLOW_PHASES[0].id);
  const resource = useRunResource<DashboardData>("dashboard", async (runId) => {
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
    return <ErrorState title="Dashboard unavailable" message={resource.error} onRetry={resource.refresh} />;
  }
  if (resource.loading || !resource.data || !resource.activeRun) {
    return <LoadingState message="Building a plain-language view of this ProofChain run" />;
  }

  const data = resource.data;
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
  } = data;
  const selectedPhase =
    WORKFLOW_PHASES.find((phase) => phase.id === selectedPhaseId) || WORKFLOW_PHASES[0];
  const selectedAgents = agents.filter((agent) => selectedPhase.agentIds.includes(agent.id));
  const completedAgents = agents.filter((agent) => agent.status === "completed").length;
  const pendingApprovals = approvals.filter((approval) => approval.status === "pending");
  const openIssues = issues
    .filter((issue) => issue.status !== "resolved")
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
  const activeTasks = tasks.filter((task) => task.status !== "completed");
  const reviewClaims = claims.filter((claim) => claim.reviewRequired);
  const latestEvents = events.slice(-6).reverse();
  const nextActions = buildNextActions(data);
  const requirementRows = (() => {
    const ids = new Set<string>();
    evidence.forEach((record) => record.criterionId && ids.add(record.criterionId));
    claims.forEach((claim) => claim.criterionId && ids.add(claim.criterionId));
    issues.forEach((issue) => issue.criterionId && ids.add(issue.criterionId));
    auditPackage?.contents.forEach((item) => item.criterionId && ids.add(item.criterionId));
    return Array.from(ids)
      .sort()
      .map((criterionId) => {
        const criterionEvidence = evidence.filter((record) => record.criterionId === criterionId);
        const verified = criterionEvidence.filter((record) =>
          ["verified", "completed"].includes(record.status)
        ).length;
        const criterionClaims = claims.filter((claim) => claim.criterionId === criterionId);
        const supportedClaims = criterionClaims.filter((claim) => claim.status === "supported").length;
        const criterionIssues = openIssues.filter((issue) => issue.criterionId === criterionId);
        const packageItem = auditPackage?.contents.find((item) => item.criterionId === criterionId);
        const coverage = criterionEvidence.length
          ? clampPercent((verified / criterionEvidence.length) * 100)
          : 0;
        return {
          criterionId,
          evidence: criterionEvidence.length,
          verified,
          claims: criterionClaims.length,
          supportedClaims,
          blockers: criterionIssues.filter((issue) =>
            ["critical", "high"].includes(issue.severity)
          ).length,
          coverage,
          packageReady: packageItem?.ready === true,
          nextDeliverable:
            activeTasks.find((task) =>
              criterionIssues.some((issue) => issue.id === task.issueId)
            )?.title ||
            criterionIssues[0]?.resolutionPlan ||
            (packageItem?.ready ? "No correction currently required" : "Complete evidence and claim review"),
        };
      });
  })();
  const phaseState = getPhaseState(agents, selectedPhase.agentIds);
  const humanWorkCount = workflow.userMustDo.length + pendingApprovals.length;
  const agentWorkCount = agents.filter((agent) => agent.status !== "completed").length;
  const packageCorrections =
    auditPackage?.qualityReview?.findings.filter((finding) => !finding.resolved).length || 0;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className={styles.dashboard}
    >
      <motion.header variants={itemVariants} className={styles.pageHeader}>
        <div>
          <div className={styles.eyebrow}>
            <Sparkles size={13} />
            Accreditation readiness, explained clearly
          </div>
          <h1>ProofChain dashboard</h1>
          <p>
            See what the agents checked, why the run is in its current state, what still needs
            attention, and exactly what will be produced next.
          </p>
        </div>
        <div className={styles.headerActions}>
          <Link className="btn btn-secondary btn-sm" href="/agents">
            <Bot size={14} />
            Inspect all agents
          </Link>
          <button className="btn btn-primary btn-sm" onClick={resource.refresh}>
            <RefreshCw size={14} />
            Refresh run
          </button>
        </div>
      </motion.header>

      <motion.div variants={itemVariants} className={styles.runContext}>
        <div className={styles.runIdentity}>
          <span className={styles.liveDot} aria-hidden="true" />
          <div>
            <span>Selected run</span>
            <strong>{resource.activeRun.id}</strong>
          </div>
        </div>
        <ContextItem label="Department" value={resource.activeRun.department} />
        <ContextItem label="Academic year" value={resource.activeRun.academicYear} />
        <ContextItem label="Framework" value={resource.activeRun.framework} />
        <div className={styles.runStatus}>
          <span>Current status</span>
          <StatusBadge status={resource.activeRun.status} />
        </div>
      </motion.div>

      <motion.section variants={itemVariants} className={styles.stateHero}>
        <div className={styles.stateCopy}>
          <div className={styles.sectionLabel}>
            <span>01</span>
            Current state
          </div>
          <h2>{currentStateSentence(data)}</h2>
          <p>
            Verified readiness only counts proof that has passed the current checks. Projected
            readiness is an estimate of what may become possible after the listed corrections
            and approvals are completed.
          </p>
          <div className={styles.stateActions}>
            <Link className="btn btn-primary" href={metrics.blockingIssues > 0 ? "/issues" : "/packages"}>
              {metrics.blockingIssues > 0 ? "See what is blocking readiness" : "Review the package"}
              <ArrowRight size={15} />
            </Link>
            <Link className={styles.textLink} href="/governance">
              How this decision was governed <ChevronRight size={14} />
            </Link>
          </div>
        </div>
        <div className={styles.readinessPanel}>
          <ReadinessGauge
            label="Verified now"
            value={metrics.verifiedReadiness}
            detail={`${metrics.verifiedEvidence} of ${metrics.totalEvidence} evidence records are usable`}
          />
          <div className={styles.gaugeDivider} />
          <ReadinessGauge
            label="Possible after fixes"
            value={metrics.projectedReadiness}
            detail="Counterfactual projection — not an approval"
            projected
          />
          <div className={styles.readinessFoot}>
            <span>
              <AlertTriangle size={14} />
              {metrics.blockingIssues} blocking
            </span>
            <span>
              <UserRoundCheck size={14} />
              {pendingApprovals.length} approvals
            </span>
          </div>
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className={styles.section}>
        <SectionHeading
          number="02"
          eyebrow="What you should do"
          title="Next best actions"
          description="The three highest-priority actions for this run, with responsibility and impact made explicit."
          action={<Link href="/tasks">See all pending work <ArrowRight size={14} /></Link>}
        />
        {nextActions.length > 0 ? (
          <div className={styles.actionGrid}>
            {nextActions.map((action, index) => (
              <Link key={action.id} href={action.href} className={styles.actionCard}>
                <div className={styles.actionTop}>
                  <span className={`${styles.actionNumber} ${styles[action.urgency]}`}>
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className={styles.actionUrgency}>
                    {action.urgency === "critical"
                      ? "Do this now"
                      : action.urgency === "high"
                        ? "Human decision"
                        : "Pending work"}
                  </span>
                </div>
                <h3>{action.title}</h3>
                <p>{action.why}</p>
                <dl className={styles.actionMeta}>
                  <div>
                    <dt>Responsible</dt>
                    <dd>{action.owner}</dd>
                  </div>
                  <div>
                    <dt>Due</dt>
                    <dd>{action.due}</dd>
                  </div>
                  <div>
                    <dt>Expected impact</dt>
                    <dd>{action.impact}</dd>
                  </div>
                </dl>
                <span className={styles.cardCta}>
                  {action.cta} <ArrowRight size={14} />
                </span>
              </Link>
            ))}
          </div>
        ) : (
          <ClearState
            title="No immediate human action is required"
            detail="ProofChain has not projected any pending approval, blocking correction, or operator task for this run."
          />
        )}
      </motion.section>

      <motion.section variants={itemVariants} className={styles.section}>
        <SectionHeading
          number="03"
          eyebrow="Agent transparency"
          title="How the agents move evidence to a decision"
          description="Choose any stage to see what goes in, what the agents do, what they produce, and how the next stage receives it."
          action={<Link href="/agents">Open agent directory <ArrowRight size={14} /></Link>}
        />
        <div className={styles.workflowShell}>
          <div className={styles.workflowRail} role="tablist" aria-label="ProofChain workflow stages">
            {WORKFLOW_PHASES.map((phase, index) => {
              const state = getPhaseState(agents, phase.agentIds);
              const Icon = phase.icon;
              const selected = phase.id === selectedPhase.id;
              return (
                <div key={phase.id} className={styles.phaseWrap}>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={selected}
                    aria-controls="workflow-stage-detail"
                    className={`${styles.phaseButton} ${styles[state]} ${selected ? styles.selected : ""}`}
                    onClick={() => setSelectedPhaseId(phase.id)}
                  >
                    <span className={styles.phaseIcon}><Icon size={17} /></span>
                    <span className={styles.phaseNumber}>Stage {phase.number}</span>
                    <strong>{phase.plainTitle}</strong>
                    <span className={styles.phaseAgents}>
                      Agents {phase.agentIds[0]}–{phase.agentIds[phase.agentIds.length - 1]}
                    </span>
                    <span className={styles.phaseStatus}>
                      {phaseStateIcon(state)}
                      {phaseStateLabel(state)}
                    </span>
                  </button>
                  {index < WORKFLOW_PHASES.length - 1 && (
                    <span className={styles.phaseConnector} aria-hidden="true">
                      <ArrowRight size={15} />
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          <div id="workflow-stage-detail" role="tabpanel" className={styles.phaseDetail}>
            <div className={styles.phaseDetailIntro}>
              <span className={styles.detailIcon}><selectedPhase.icon size={20} /></span>
              <div>
                <span>Stage {selectedPhase.number} · {phaseStateLabel(phaseState)}</span>
                <h3>{selectedPhase.title}</h3>
                <p>{selectedPhase.question}</p>
              </div>
              <Link href={selectedPhase.href} className="btn btn-secondary btn-sm">
                Inspect this stage <ArrowRight size={14} />
              </Link>
            </div>
            <div className={styles.transparencyGrid}>
              <TransparencyStep number="1" label="Receives" text={selectedPhase.input} />
              <TransparencyStep number="2" label="Agents do" text={selectedPhase.work} />
              <TransparencyStep number="3" label="Produces" text={selectedPhase.output} />
            </div>
            <div className={styles.agentStrip}>
              <div>
                <span className={styles.agentStripLabel}>Agents responsible for this stage</span>
                <p>
                  Each agent links to its goal, plan, observations, decisions, tools, hand-offs,
                  confidence, and completion proof.
                </p>
              </div>
              <div className={styles.agentChips}>
                {selectedAgents.map((agent) => (
                  <Link key={agent.id} href={`/agents/${agent.id}`} className={styles.agentChip}>
                    <span>{agent.id}</span>
                    <div>
                      <strong>{agent.shortName || agent.name}</strong>
                      <small>{humanize(agent.status)}</small>
                    </div>
                    <ChevronRight size={13} />
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.workflowSummary}>
          <WorkflowSummaryItem
            icon={CheckCircle2}
            label="Completed"
            value={`${completedAgents} of ${agents.length} agents`}
            detail={`${workflow.happened.eventCount} governed events recorded`}
            tone="green"
          />
          <WorkflowSummaryItem
            icon={Activity}
            label="Happening now"
            value={workflow.happeningNow[0] || `${agentWorkCount} agents remain in the workflow`}
            detail={workflow.happeningNow[1] || "Open a stage above for its current state"}
            tone="blue"
          />
          <WorkflowSummaryItem
            icon={AlertTriangle}
            label="Blocked or waiting"
            value={`${metrics.blockingIssues} blockers · ${humanWorkCount} human actions`}
            detail={workflow.blocked[0]?.reason || "No additional blocking reason was recorded"}
            tone="amber"
          />
          <WorkflowSummaryItem
            icon={Route}
            label="Next"
            value={workflow.nextSteps[0] || "Continue the governed run"}
            detail={workflow.nextSteps[1] || "The next state depends on the work listed above"}
            tone="purple"
          />
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className={styles.twoColumnSection}>
        <div className={styles.panel}>
          <SectionHeading
            number="04"
            eyebrow="Pending work"
            title="What remains, and what must be produced"
            description="Every remaining item is separated by responsibility so a first-time user knows who acts next."
            compact
          />
          <div className={styles.workSummary}>
            <WorkCount
              icon={UserRoundCheck}
              label="You or another reviewer"
              count={humanWorkCount}
              detail="Decisions and approvals"
              href="/approvals"
              tone="purple"
            />
            <WorkCount
              icon={Bot}
              label="ProofChain agents"
              count={agentWorkCount}
              detail="Checks still active or waiting"
              href="/agents"
              tone="blue"
            />
            <WorkCount
              icon={ClipboardCheck}
              label="Evidence owners"
              count={activeTasks.length}
              detail="Corrections or submissions"
              href="/tasks"
              tone="amber"
            />
            <WorkCount
              icon={PackageCheck}
              label="Package reviewer"
              count={packageCorrections}
              detail="Quality corrections"
              href="/packages"
              tone="red"
            />
          </div>
          <div className={styles.deliverableList}>
            {activeTasks.slice(0, 4).map((task) => (
              <DeliverableRow
                key={task.id}
                type="Correction to produce"
                title={task.title}
                detail={task.description}
                owner={task.assignedTo}
                status={task.status}
                href="/tasks"
              />
            ))}
            {pendingApprovals.slice(0, 3).map((approval) => (
              <DeliverableRow
                key={approval.id}
                type="Decision to provide"
                title={approval.subject}
                detail={approval.reason || `Approve or reject this ${approval.subjectType} transition.`}
                owner={approval.requiredApprover}
                status={approval.status}
                href="/approvals"
              />
            ))}
            {activeTasks.length === 0 && pendingApprovals.length === 0 && (
              <ClearState
                title="The remaining-work queue is clear"
                detail="There are no open correction tasks or pending human approvals in the selected run."
                compact
              />
            )}
          </div>
        </div>

        <div className={styles.panel}>
          <SectionHeading
            number="05"
            eyebrow="Why readiness is blocked"
            title="Top blocking issues"
            description="These are canonical issues: one governed record is reused everywhere instead of creating conflicting copies."
            action={<Link href="/issues">All issues <ArrowRight size={14} /></Link>}
            compact
          />
          <div className={styles.issueList}>
            {openIssues.slice(0, 5).map((issue) => (
              <Link key={issue.id} href="/issues" className={styles.issueRow}>
                <div className={styles.issueTitle}>
                  <SeverityBadge severity={issue.severity} />
                  <div>
                    <strong>{issue.title}</strong>
                    <span>{issue.criterionId} · {issue.id}</span>
                  </div>
                </div>
                <div className={styles.issueOwner}>
                  <span>Responsible</span>
                  <strong>{issue.owner || "Unassigned"}</strong>
                </div>
                <div className={styles.issueImpact}>
                  <span>Readiness impact</span>
                  <strong>{issue.readinessImpact || 0} pts</strong>
                </div>
                <ChevronRight size={15} />
              </Link>
            ))}
            {openIssues.length === 0 && (
              <ClearState
                title="No open canonical issues"
                detail="The selected run has no unresolved issue record."
                compact
              />
            )}
          </div>
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className={styles.section}>
        <SectionHeading
          number="06"
          eyebrow="Evidence readiness"
          title="Readiness by requirement"
          description="This table separates evidence coverage, claim support, blockers, and the next expected deliverable. Coverage is not the same as final approval."
          action={<Link href="/evidence">Inspect evidence <ArrowRight size={14} /></Link>}
        />
        <div className={styles.tableWrap}>
          <table className={styles.requirementTable}>
            <thead>
              <tr>
                <th>Requirement</th>
                <th>Evidence verified</th>
                <th>Claims supported</th>
                <th>Blocking issues</th>
                <th>Package</th>
                <th>Next deliverable</th>
              </tr>
            </thead>
            <tbody>
              {requirementRows.map((row) => (
                <tr key={row.criterionId}>
                  <td><strong>{row.criterionId}</strong></td>
                  <td>
                    <div className={styles.coverageCell}>
                      <div className={styles.miniBar}>
                        <span style={{ width: `${row.coverage}%` }} />
                      </div>
                      <span>{row.verified}/{row.evidence}</span>
                    </div>
                  </td>
                  <td>{row.supportedClaims}/{row.claims}</td>
                  <td>
                    <span className={row.blockers > 0 ? styles.blockerCount : styles.clearCount}>
                      {row.blockers > 0 ? `${row.blockers} blocking` : "Clear"}
                    </span>
                  </td>
                  <td>
                    <StatusBadge
                      status={row.packageReady ? "ready" : "draft"}
                      size="sm"
                    />
                  </td>
                  <td className={styles.deliverableCell}>{row.nextDeliverable}</td>
                </tr>
              ))}
              {requirementRows.length === 0 && (
                <tr>
                  <td colSpan={6}>No requirement-level records are available in this run.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className={styles.tableNote}>
          <HelpCircle size={14} />
          <span>
            “Evidence verified” means a record passed the current integrity checks. It does not
            automatically prove a claim or authorize package release.
          </span>
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className={styles.twoColumnSection}>
        <div className={styles.panel}>
          <SectionHeading
            number="07"
            eyebrow="Decision activity"
            title="Latest agent events"
            description="A readable view of the governed event chain. Structured decision explanations are shown; hidden chain-of-thought is never exposed."
            action={<Link href="/governance">Full event chain <ArrowRight size={14} /></Link>}
            compact
          />
          <div className={styles.timeline}>
            {latestEvents.map((event) => (
              <div key={event.id} className={styles.timelineRow}>
                <span className={styles.timelineDot} aria-hidden="true" />
                <div className={styles.timelineBody}>
                  <div>
                    <strong>{humanize(event.eventType)}</strong>
                    <span>#{event.sequenceNumber} · {formatTime(event.timestamp)}</span>
                  </div>
                  <p>{eventExplanation(event)}</p>
                  <small>{event.agentName || "ProofChain system"}</small>
                </div>
              </div>
            ))}
            {latestEvents.length === 0 && (
              <ClearState
                title="No synchronized event is available"
                detail="The selected run has not exposed an event record to the dashboard."
                compact
              />
            )}
          </div>
        </div>

        <div className={styles.panel}>
          <SectionHeading
            number="08"
            eyebrow="What ProofChain produces"
            title="Your governed outputs"
            description="These are the concrete records and packages created by the workflow—not generic AI answers."
            compact
          />
          <div className={styles.outputGrid}>
            <OutputCard
              icon={FileText}
              label="Evidence register"
              value={`${evidence.length} records`}
              detail={`${metrics.verifiedEvidence} currently usable`}
              href="/evidence"
            />
            <OutputCard
              icon={GitBranch}
              label="Defensible claim set"
              value={`${claims.length} claims`}
              detail={`${reviewClaims.length} need human review`}
              href="/claims"
            />
            <OutputCard
              icon={ListChecks}
              label="Correction register"
              value={`${activeTasks.length} active tasks`}
              detail={`${openIssues.length} open canonical issues`}
              href="/tasks"
            />
            <OutputCard
              icon={PackageCheck}
              label="Audit package"
              value={humanize(auditPackage?.status || "not generated")}
              detail={`${auditPackage?.contents.length || 0} requirement sections`}
              href="/packages"
            />
          </div>
          <div className={styles.releaseDecision}>
            <div>
              <span>External release decision</span>
              <strong>{humanize(workflow.submissionDecision)}</strong>
            </div>
            <StatusBadge
              status={
                workflow.submissionDecision === "approved"
                  ? "approved"
                  : workflow.submissionDecision || "pending"
              }
            />
          </div>
        </div>
      </motion.section>

      {viewMode === "technical" ? (
        <motion.section variants={itemVariants} className={styles.technicalPanel}>
          <div className={styles.technicalHeader}>
            <div>
              <span>Technical transparency view</span>
              <h2>Validation, provenance, and governance state</h2>
              <p>
                The operational explanation above remains the source of truth for people. This
                section exposes the implementation evidence used to verify that explanation.
              </p>
            </div>
            <Link className="btn btn-secondary btn-sm" href="/operation-room">
              Open technical operation room <ArrowRight size={14} />
            </Link>
          </div>
          <div className={styles.technicalGrid}>
            <TechnicalCheck
              label="Standard artifact validation"
              ok={governance.validation.standard.valid === true}
              detail={`${governance.validation.standard.errors?.length || 0} validation errors`}
            />
            <TechnicalCheck
              label="Agentic completion proofs"
              ok={governance.validation.agentic.valid === true}
              detail={`${governance.validation.agentic.agents_validated || 0} agents validated`}
            />
            <TechnicalCheck
              label="Persistence synchronized"
              ok={governance.validation.persistenceSynchronized === true}
              detail={`${governance.checkpoints.length} recorded checkpoints`}
            />
            <TechnicalCheck
              label="Technical completion"
              ok={governance.validation.technicalComplete === true}
              detail={`${governance.policies.length} governed policies loaded`}
            />
          </div>
          <div className={styles.hashLine}>
            <span>Policy fingerprint</span>
            <code>{governance.policyFingerprint || "Not recorded for this run"}</code>
          </div>
        </motion.section>
      ) : (
        <motion.div variants={itemVariants} className={styles.technicalHint}>
          <div>
            <Route size={18} />
            <span>
              Need hashes, validation proofs, policy versions, or synchronized checkpoints?
            </span>
          </div>
          <span>Switch the top-bar view from Operational to Technical.</span>
        </motion.div>
      )}
    </motion.div>
  );
}

function ContextItem({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.contextItem}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ReadinessGauge({
  label,
  value,
  detail,
  projected = false,
}: {
  label: string;
  value: number;
  detail: string;
  projected?: boolean;
}) {
  const safeValue = clampPercent(value);
  return (
    <div className={styles.gauge}>
      <div className={styles.gaugeTop}>
        <span>{label}</span>
        <strong>{safeValue}%</strong>
      </div>
      <div className={`${styles.gaugeTrack} ${projected ? styles.projected : ""}`}>
        <span style={{ width: `${safeValue}%` }} />
      </div>
      <p>{detail}</p>
    </div>
  );
}

function SectionHeading({
  number,
  eyebrow,
  title,
  description,
  action,
  compact = false,
}: {
  number: string;
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
  compact?: boolean;
}) {
  return (
    <div className={`${styles.sectionHeading} ${compact ? styles.compactHeading : ""}`}>
      <div className={styles.sectionNumber}>{number}</div>
      <div className={styles.sectionHeadingCopy}>
        <span>{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {action && <div className={styles.sectionAction}>{action}</div>}
    </div>
  );
}

function TransparencyStep({
  number,
  label,
  text,
}: {
  number: string;
  label: string;
  text: string;
}) {
  return (
    <div className={styles.transparencyStep}>
      <span>{number}</span>
      <div>
        <strong>{label}</strong>
        <p>{text}</p>
      </div>
    </div>
  );
}

function WorkflowSummaryItem({
  icon: Icon,
  label,
  value,
  detail,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
  tone: "green" | "blue" | "amber" | "purple";
}) {
  return (
    <div className={styles.workflowSummaryItem}>
      <span className={`${styles.summaryIcon} ${styles[tone]}`}><Icon size={16} /></span>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <p>{detail}</p>
      </div>
    </div>
  );
}

function WorkCount({
  icon: Icon,
  label,
  count,
  detail,
  href,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  count: number;
  detail: string;
  href: string;
  tone: "purple" | "blue" | "amber" | "red";
}) {
  return (
    <Link href={href} className={styles.workCount}>
      <span className={`${styles.workIcon} ${styles[tone]}`}><Icon size={16} /></span>
      <div>
        <strong>{count}</strong>
        <span>{label}</span>
        <small>{detail}</small>
      </div>
      <ChevronRight size={14} />
    </Link>
  );
}

function DeliverableRow({
  type,
  title,
  detail,
  owner,
  status,
  href,
}: {
  type: string;
  title: string;
  detail: string;
  owner: string;
  status: string;
  href: string;
}) {
  return (
    <Link href={href} className={styles.deliverableRow}>
      <span className={styles.deliverableIcon}><FileCheck2 size={16} /></span>
      <div className={styles.deliverableMain}>
        <span>{type}</span>
        <strong>{title}</strong>
        <p>{detail}</p>
      </div>
      <div className={styles.deliverableOwner}>
        <span>{owner || "Owner not assigned"}</span>
        <StatusBadge status={status} size="sm" />
      </div>
      <ChevronRight size={14} />
    </Link>
  );
}

function OutputCard({
  icon: Icon,
  label,
  value,
  detail,
  href,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
  href: string;
}) {
  return (
    <Link href={href} className={styles.outputCard}>
      <span><Icon size={17} /></span>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
        <p>{detail}</p>
      </div>
      <ChevronRight size={14} />
    </Link>
  );
}

function TechnicalCheck({
  label,
  ok,
  detail,
}: {
  label: string;
  ok: boolean;
  detail: string;
}) {
  return (
    <div className={styles.technicalCheck}>
      <span className={ok ? styles.techOk : styles.techPending}>
        {ok ? <CheckCircle2 size={17} /> : <CircleDashed size={17} />}
      </span>
      <div>
        <strong>{label}</strong>
        <p>{detail}</p>
      </div>
    </div>
  );
}

function ClearState({
  title,
  detail,
  compact = false,
}: {
  title: string;
  detail: string;
  compact?: boolean;
}) {
  return (
    <div className={`${styles.clearState} ${compact ? styles.clearStateCompact : ""}`}>
      <span><CheckCircle2 size={18} /></span>
      <div>
        <strong>{title}</strong>
        <p>{detail}</p>
      </div>
    </div>
  );
}
