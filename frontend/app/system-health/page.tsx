"use client";

import { motion } from "framer-motion";
import { Activity, CheckCircle2, ServerCog } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { PlatformHealth } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivePageHeader, MetricStrip } from "@/components/live/live-page";

export default function SystemHealthPage() {
  const resource = useRunResource<PlatformHealth>("health", (runId) => getDataProvider().getPlatformHealth(runId));
  if (resource.error) return <ErrorState title="Health service unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Inspecting run-aware platform health" />;
  const health = resource.data;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader section="Platform operations / Agents 11-22" title="System and Run Health" description="Technical service health is shown separately from domain readiness, so a governed refusal is never mislabeled as a platform failure." run={resource.activeRun} onRefresh={resource.refresh} />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Platform status", value: <StatusBadge status={health.status === "healthy" ? "verified" : health.status === "degraded" ? "warning" : "blocked"} size="md" />, detail: health.runId ?? resource.activeRun.id },
          { label: "Checks passed", value: health.summary.passed, detail: "Healthy technical controls" },
          { label: "Warnings", value: health.summary.warnings, detail: "Degraded controls" },
          { label: "Failed", value: health.summary.failed, detail: "Technical failures" },
        ]} />
      </motion.div>
      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
        <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2"><ServerCog size={16} className="text-[var(--color-evidence-blue)]" /><h2 className="text-sm font-semibold">Technical control checks</h2></div>
        <div className="divide-y divide-[var(--color-border-subtle)]">
          {health.checks.map((check) => (
            <div key={check.name} className="px-5 py-4 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">{check.healthy ? <CheckCircle2 size={15} className="text-[var(--color-verified)] mt-0.5" /> : <Activity size={15} className="text-[var(--color-warning)] mt-0.5" />}<div><p className="text-xs font-semibold">{check.name.replaceAll("_", " ")}</p><p className="text-[11px] text-[var(--color-text-tertiary)] mt-1">{check.detail}</p></div></div>
              <StatusBadge status={check.status === "healthy" ? "verified" : check.status === "warning" ? "warning" : "blocked"} size="sm" />
            </div>
          ))}
        </div>
      </motion.section>
    </motion.div>
  );
}
