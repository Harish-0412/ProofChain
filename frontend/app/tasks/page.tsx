"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Clock3, UserRound } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { ResolutionTask } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivePageHeader, MetricStrip } from "@/components/live/live-page";

export default function TasksPage() {
  const resource = useRunResource<ResolutionTask[]>("tasks", (runId) => getDataProvider().getTasks(runId));

  if (resource.error) return <ErrorState title="Task projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Loading governed resolution tasks" />;

  const active = resource.data.filter((task) => task.status === "in progress").length;
  const completed = resource.data.filter((task) => task.status === "completed").length;
  const overdue = resource.data.filter((task) => task.status === "overdue").length;
  const owners = new Set(resource.data.map((task) => task.assignedTo).filter(Boolean));

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Resolution execution / Agent 7"
          title="Department Liaison Tasks"
          description="Governed correction tasks, owner assignment, due state, and communication references projected from the selected run."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Resolution tasks", value: resource.data.length, detail: "Canonical issue work items" },
          { label: "Active", value: active, detail: "Approved and in progress" },
          { label: "Completed", value: completed, detail: "Evidence response recorded" },
          { label: "Overdue", value: overdue, detail: `${owners.size} accountable owners` },
        ]} />
      </motion.div>

      <motion.section variants={itemVariants} className="space-y-3">
        {resource.data.length === 0 ? (
          <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-10 text-center">
            <CheckCircle2 size={30} className="text-[var(--color-verified)] mx-auto" />
            <h2 className="text-sm font-bold mt-3">No corrective tasks were required</h2>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-1">The selected run generated no canonical gaps, so the liaison agent correctly created no department work.</p>
          </div>
        ) : resource.data.map((task) => (
          <article key={task.id} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)]">
            <div className="p-5 flex items-start justify-between gap-4 flex-wrap">
              <div className="min-w-0">
                <div className="flex items-center gap-3">
                  <code className="text-xs text-[var(--color-evidence-blue)]">{task.id}</code>
                  <StatusBadge status={task.status} size="sm" />
                </div>
                <h2 className="text-sm font-bold mt-2">{task.title}</h2>
                <p className="text-xs text-[var(--color-text-secondary)] mt-1">{task.description}</p>
              </div>
              <code className="text-[10px]">{task.issueId}</code>
            </div>
            <div className="px-5 py-3 border-t border-[var(--color-border)] bg-[var(--color-border-subtle)] flex items-center gap-x-5 gap-y-2 flex-wrap text-xs">
              <span className="flex items-center gap-1.5"><UserRound size={13} />{task.assignedTo || "Unassigned"}</span>
              <span className="flex items-center gap-1.5"><Clock3 size={13} />{task.dueDate ? new Date(task.dueDate).toLocaleString() : "No due date"}</span>
              {task.draftCommunication && <code className="text-[10px]">communication: {task.draftCommunication}</code>}
            </div>
          </article>
        ))}
      </motion.section>
    </motion.div>
  );
}
