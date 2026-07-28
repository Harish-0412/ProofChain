"use client";

import { motion } from "framer-motion";
import { CheckCircle2, RefreshCcw, ShieldCheck } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { AgentDetail, DashboardMetrics, Issue } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivePageHeader, MetricStrip } from "@/components/live/live-page";

interface ClosureData {
  metrics: DashboardMetrics;
  issues: Issue[];
  agent: AgentDetail | null;
}

export default function ClosurePage() {
  const resource = useRunResource<ClosureData>("closure", async (runId) => {
    const provider = getDataProvider();
    const [metrics, issues, agent] = await Promise.all([
      provider.getDashboardMetrics(runId),
      provider.getIssues(runId),
      provider.getAgentById(runId, 8),
    ]);
    return { metrics, issues, agent };
  });

  if (resource.error) return <ErrorState title="Closure projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Loading closure and revalidation state" />;

  const open = resource.data.issues.filter((issue) => issue.status !== "resolved");
  const resolved = resource.data.issues.filter((issue) => issue.status === "resolved");
  const agent = resource.data.agent;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Resolution execution / Agent 8"
          title="Evidence Closure and Revalidation"
          description="Correction upload, targeted revalidation, regression inspection, and canonical issue transition are shown as separate governed states."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Verified readiness", value: `${resource.data.metrics.verifiedReadiness}%`, detail: "Current, not projected" },
          { label: "Open issues", value: open.length, detail: "Still require closure" },
          { label: "Resolved issues", value: resolved.length, detail: "Passed revalidation" },
          { label: "Agent decision", value: agent ? <StatusBadge status={agent.agent.status} size="md" /> : "Unavailable", detail: agent?.agent.decisionReason },
        ]} />
      </motion.div>

      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
        <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2">
          <RefreshCcw size={16} className="text-[var(--color-evidence-blue)]" />
          <h2 className="text-sm font-semibold">Revalidation plan</h2>
        </div>
        <div className="divide-y divide-[var(--color-border-subtle)]">
          {agent?.plan?.steps.map((step) => (
            <div key={step.id} className="px-5 py-4 grid grid-cols-[32px_1fr_auto] gap-3 items-start">
              <span className="w-7 h-7 rounded-md bg-[var(--color-border-subtle)] flex items-center justify-center text-xs font-bold">{step.sequence}</span>
              <div><p className="text-xs font-semibold">{step.objective}</p>{step.completionCondition && <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">{step.completionCondition}</p>}</div>
              <StatusBadge status={step.status} size="sm" />
            </div>
          ))}
        </div>
      </motion.section>

      {resource.data.issues.length === 0 ? (
        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-10 text-center">
          <ShieldCheck size={30} className="text-[var(--color-verified)] mx-auto" />
          <h2 className="text-sm font-bold mt-3">No issue required a closure transition</h2>
          <p className="text-xs text-[var(--color-text-tertiary)] mt-1">The agent still executed its bounded closure checks and completed with zero undisclosed regression or unresolved gap.</p>
        </motion.section>
      ) : (
        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-x-auto">
          <table className="pc-table"><thead><tr><th>Issue</th><th>State</th><th>Owner</th><th>Resolution</th></tr></thead><tbody>
            {resource.data.issues.map((issue) => <tr key={issue.id}><td><code className="text-xs">{issue.id}</code></td><td><StatusBadge status={issue.status} size="sm" /></td><td className="text-xs">{issue.owner ?? "Unassigned"}</td><td className="text-xs">{issue.resolutionPlan ?? "No plan recorded"}</td></tr>)}
          </tbody></table>
        </motion.section>
      )}

      {agent?.completion?.goalSatisfied && (
        <motion.div variants={itemVariants} className="flex items-start gap-2 text-xs text-[var(--color-text-secondary)]">
          <CheckCircle2 size={14} className="text-[var(--color-verified)] mt-0.5" />
          {agent.completion.explanation}
        </motion.div>
      )}
    </motion.div>
  );
}
