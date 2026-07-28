"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  CircleDashed,
  FileOutput,
  Gauge,
  ListChecks,
  MessageSquare,
  ShieldCheck,
  Wrench,
} from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { AgentDetail } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivePageHeader, MetricStrip, EmptyDataRow } from "@/components/live/live-page";
import { HashDisplay } from "@/components/ui/hash-display";

export default function AgentDetailPage() {
  const params = useParams<{ agentId: string }>();
  const agentId = Number(params.agentId);
  const resource = useRunResource<AgentDetail>(`agent-${agentId}`, (runId) =>
    getDataProvider().getAgentById(runId, agentId).then((detail) => {
      if (!detail) throw new Error(`Agent ${agentId} was not found in this run.`);
      return detail;
    })
  );

  if (!Number.isInteger(agentId) || agentId < 1 || agentId > 22) {
    return <ErrorState title="Unknown agent" message="Agent IDs must be between 1 and 22." />;
  }
  if (resource.error) return <ErrorState title="Agent detail unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message={`Loading persisted cognition for agent ${agentId}`} />;

  const detail = resource.data;
  const agent = detail.agent;
  const completedSteps = detail.plan?.steps.filter((step) => step.status === "completed").length ?? 0;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section={`${agent.architectureLayer} / Agent ${agent.id}`}
          title={agent.name}
          description={agent.role}
          run={resource.activeRun}
          onRefresh={resource.refresh}
          actions={
            <Link href="/agents" className="btn btn-secondary btn-sm">
              <ArrowLeft size={14} /> All agents
            </Link>
          }
        />
      </motion.div>

      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Decision", value: <StatusBadge status={agent.status} size="md" />, detail: agent.decisionReason },
          { label: "Plan progress", value: `${completedSteps}/${detail.plan?.steps.length ?? 0}`, detail: detail.plan ? `Revision ${detail.plan.revision}` : "No plan artifact" },
          { label: "Observations", value: detail.observations.length, detail: `${detail.reflections.length} structured reflections` },
          { label: "Tool actions", value: detail.actions.length, detail: `${detail.toolCalls.length} recorded calls` },
        ]} />
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.35fr_0.65fr] gap-5">
        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <ListChecks size={16} className="text-[var(--color-evidence-blue)]" />
              <h2 className="text-sm font-semibold">Goal and bounded plan</h2>
            </div>
            {detail.plan && <code className="text-[10px] text-[var(--color-text-tertiary)]">{detail.plan.id}</code>}
          </div>
          <div className="p-5 border-b border-[var(--color-border-subtle)]">
            <p className="text-subheading">Independent goal</p>
            <p className="text-sm font-semibold mt-1">{detail.goal?.title ?? agent.goals[0] ?? "No goal artifact"}</p>
            {detail.plan?.rationale && <p className="text-xs text-[var(--color-text-secondary)] mt-2">{detail.plan.rationale}</p>}
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {detail.plan?.steps.map((step) => (
              <div key={step.id} className="px-5 py-4 grid grid-cols-[32px_1fr] gap-3">
                <div className="w-7 h-7 rounded-md bg-[var(--color-border-subtle)] flex items-center justify-center text-xs font-bold">{step.sequence}</div>
                <div className="min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-xs font-semibold">{step.objective}</p>
                    <StatusBadge status={step.status} size="sm" />
                  </div>
                  {step.tool && (
                    <p className="text-[10px] font-mono text-[var(--color-evidence-blue)] mt-1 flex items-center gap-1">
                      <Wrench size={11} /> {step.tool}
                    </p>
                  )}
                  {step.expectedObservation && <p className="text-[11px] text-[var(--color-text-tertiary)] mt-1">{step.expectedObservation}</p>}
                </div>
              </div>
            )) ?? <EmptyDataRow message="No plan steps were persisted for this agent." />}
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
            <ShieldCheck size={16} className="text-[var(--color-evidence-blue)]" />
            <h2 className="text-sm font-semibold">Completion proof</h2>
          </div>
          {detail.completion ? (
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between gap-3">
                <code className="text-[10px] text-[var(--color-evidence-blue)]">{detail.completion.decisionId}</code>
                <StatusBadge status={detail.completion.finalStatus} size="sm" />
              </div>
              <p className="text-xs leading-relaxed">{detail.completion.explanation}</p>
              <div>
                <p className="text-subheading mb-2">Conditions met</p>
                <div className="space-y-2">
                  {detail.completion.successConditionsMet.map((condition) => (
                    <div key={condition} className="flex items-start gap-2 text-xs">
                      <CheckCircle2 size={14} className="text-[var(--color-verified)] mt-0.5 shrink-0" />
                      <span>{condition}</span>
                    </div>
                  ))}
                </div>
              </div>
              {agent.completionProofId && (
                <div>
                  <p className="text-subheading mb-1">Proof identity</p>
                  <code className="text-xs">{agent.completionProofId}</code>
                </div>
              )}
            </div>
          ) : <EmptyDataRow message="No completion decision was persisted." />}
        </motion.section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
            <BrainCircuit size={16} className="text-[var(--color-evidence-blue)]" />
            <h2 className="text-sm font-semibold">Observe and reflect loop</h2>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)] max-h-[460px] overflow-y-auto">
            {detail.observations.map((observation, index) => {
              const reflection = detail.reflections[index];
              return (
                <div key={observation.observation_id ?? index} className="p-5 space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[10px] font-mono text-[var(--color-evidence-blue)]">{observation.observation_id}</span>
                    <span className="text-[10px] text-[var(--color-text-tertiary)]">{observation.created_at ? new Date(observation.created_at).toLocaleString() : ""}</span>
                  </div>
                  <p className="text-xs">{observation.summary}</p>
                  {reflection && (
                    <div className="border-l-2 border-[var(--color-evidence-blue)] pl-3">
                      <p className="text-[10px] uppercase font-bold text-[var(--color-text-tertiary)]">Reflection: {reflection.decision}</p>
                      <p className="text-xs text-[var(--color-text-secondary)] mt-1">{reflection.reason ?? reflection.progress_assessment}</p>
                    </div>
                  )}
                </div>
              );
            })}
            {detail.observations.length === 0 && <EmptyDataRow message="No observation records were persisted." />}
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
          <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
            <Gauge size={16} className="text-[var(--color-evidence-blue)]" />
            <h2 className="text-sm font-semibold">Action selection and governance</h2>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)] max-h-[460px] overflow-y-auto">
            {detail.actions.map((action, index) => (
              <div key={action.action_id ?? index} className="p-5">
                <div className="flex items-center justify-between gap-3">
                  <code className="text-[10px] text-[var(--color-evidence-blue)]">{action.selected_tool ?? "bounded action"}</code>
                  <span className="text-[10px] font-semibold">IG {Number(action.expected_information_gain ?? 0).toFixed(2)}</span>
                </div>
                <p className="text-xs mt-2">{action.reason}</p>
              </div>
            ))}
            {detail.actions.length === 0 && <EmptyDataRow message="No selected action records were persisted." />}
          </div>
        </motion.section>
      </div>

      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
        <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
          <FileOutput size={16} className="text-[var(--color-evidence-blue)]" />
          <h2 className="text-sm font-semibold">Technical trace</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-[var(--color-border)]">
          <div className="p-4">
            <p className="text-subheading">Execution mode</p>
            <p className="text-xs font-semibold mt-1">{detail.modelProfile?.execution_mode ?? "Not recorded"}</p>
            <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">{detail.modelProfile?.external_model_calls ?? 0} external model calls</p>
          </div>
          <div className="p-4">
            <p className="text-subheading">Runtime directory</p>
            <code className="text-xs mt-1 block">{detail.runtimeDirectory}</code>
          </div>
          <div className="p-4">
            <p className="text-subheading">Coordination</p>
            <p className="text-xs font-semibold mt-1 flex items-center gap-1"><MessageSquare size={12} /> {agent.messagesSent + agent.messagesReceived} messages</p>
            <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">{agent.peersContacted.length} peer contacts</p>
          </div>
          <div className="p-4">
            <p className="text-subheading">Checkpoint</p>
            {detail.checkpoints[0]?.output?.sha256 ? <HashDisplay hash={detail.checkpoints[0].output.sha256} /> : (
              <p className="text-xs mt-1 flex items-center gap-1"><CircleDashed size={12} /> Event-backed stage</p>
            )}
          </div>
        </div>
      </motion.section>

      <div className="flex items-center justify-between">
        {agent.id > 1 ? <Link className="btn btn-secondary btn-sm" href={`/agents/${agent.id - 1}`}><ArrowLeft size={14} /> Previous</Link> : <span />}
        {agent.id < 22 && <Link className="btn btn-secondary btn-sm" href={`/agents/${agent.id + 1}`}>Next <ArrowRight size={14} /></Link>}
      </div>
    </motion.div>
  );
}
