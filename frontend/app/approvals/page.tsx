"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Fingerprint, LockKeyhole, ShieldAlert } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { ApprovalDecision } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { HashDisplay } from "@/components/ui/hash-display";
import { LivePageHeader, MetricStrip } from "@/components/live/live-page";

export default function ApprovalsPage() {
  const resource = useRunResource<ApprovalDecision[]>("approvals", (runId) => getDataProvider().getApprovals(runId));

  if (resource.error) return <ErrorState title="Approval projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Loading governed approval state" />;

  const pending = resource.data.filter((approval) => approval.status === "pending").length;
  const approved = resource.data.filter((approval) => approval.status === "approved").length;
  const rejected = resource.data.filter((approval) => approval.status === "rejected").length;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Human governance"
          title="Approval and Release Gates"
          description="Approvals authorize new state transitions; they never rewrite original evidence, decisions, or package hashes."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Approval records", value: resource.data.length, detail: "Recorded and derived governance gates" },
          { label: "Pending", value: pending, detail: "Human action still required" },
          { label: "Approved", value: approved, detail: "Authorized state transitions" },
          { label: "Rejected", value: rejected, detail: "Refused transitions" },
        ]} />
      </motion.div>

      <motion.div variants={itemVariants} className="flex items-start gap-3 p-4 border border-[var(--color-border)] rounded-lg bg-[var(--color-border-subtle)] text-xs">
        <LockKeyhole size={16} className="text-[var(--color-evidence-blue)] mt-0.5" />
        <div><p className="font-semibold">Separation of duties is enforced</p><p className="text-[var(--color-text-secondary)] mt-1">Package release approval must be independent and bound to the exact frozen package hash. A general verbal approval is insufficient.</p></div>
      </motion.div>

      <motion.section variants={itemVariants} className="space-y-3">
        {resource.data.length === 0 ? (
          <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-10 text-center">
            <CheckCircle2 size={30} className="text-[var(--color-verified)] mx-auto" />
            <h2 className="text-sm font-bold mt-3">No approval gate is open</h2>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-1">No persisted decision currently requires human authorization.</p>
          </div>
        ) : resource.data.map((approval) => (
          <article key={approval.id} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
            <div className="p-5 flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="flex items-center gap-3">
                  <ShieldAlert size={16} className="text-[var(--color-warning)]" />
                  <code className="text-xs text-[var(--color-evidence-blue)]">{approval.id}</code>
                  <StatusBadge status={approval.status} size="sm" />
                </div>
                <h2 className="text-sm font-bold mt-3">{approval.subject}</h2>
                <p className="text-xs text-[var(--color-text-secondary)] mt-1">{approval.reason ?? "No approval rationale was recorded."}</p>
              </div>
              <span className="text-[10px] uppercase font-bold border border-[var(--color-border)] rounded px-2 py-1">{approval.subjectType}</span>
            </div>
            <div className="px-5 py-3 border-t border-[var(--color-border)] bg-[var(--color-border-subtle)] grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div><p className="text-subheading">Required approver</p><p className="font-semibold mt-1">{approval.requiredApprover}</p></div>
              <div>
                <p className="text-subheading">Bound references</p>
                <div className="mt-1 flex items-center gap-2"><Fingerprint size={13} />{approval.relatedIds[0] ? <HashDisplay hash={approval.relatedIds[0]} /> : "No reference"}</div>
              </div>
            </div>
          </article>
        ))}
      </motion.section>
    </motion.div>
  );
}
