"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Search, ShieldAlert } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { Claim } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivePageHeader, MetricStrip, EmptyDataRow } from "@/components/live/live-page";

export default function ClaimsPage() {
  const [query, setQuery] = useState("");
  const resource = useRunResource<Claim[]>("claims", (runId) => getDataProvider().getClaims(runId));
  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    return (resource.data ?? []).filter((claim) =>
      !value || [claim.id, claim.criterionId, claim.text, claim.status, claim.agentReasoning]
        .join(" ").toLowerCase().includes(value)
    );
  }, [query, resource.data]);

  if (resource.error) return <ErrorState title="Claim projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Loading persisted claim decisions" />;

  const supported = resource.data.filter((claim) => claim.status === "supported").length;
  const review = resource.data.filter((claim) => claim.reviewRequired).length;
  const evidenceLinks = resource.data.reduce((total, claim) => total + claim.supportingEvidenceIds.length, 0);
  const criteria = new Set(resource.data.map((claim) => claim.criterionId));

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Evidence reasoning / Agent 4"
          title="Claim Defensibility Matrix"
          description="Original institutional claims are shown beside the persisted defensibility decision and the exact evidence identities that support or contradict them."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Claims evaluated", value: resource.data.length, detail: `${criteria.size} requirements` },
          { label: "Supported", value: supported, detail: `${resource.data.length - supported} not fully supported` },
          { label: "Evidence links", value: evidenceLinks, detail: "Traceable supporting references" },
          { label: "Human review", value: review, detail: "Explicit review requirement" },
        ]} />
      </motion.div>
      <motion.div variants={itemVariants} className="search-input max-w-xl">
        <Search size={14} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search claim, requirement, text, or decision" />
      </motion.div>
      <motion.section variants={itemVariants} className="space-y-3">
        {filtered.map((claim) => (
          <article key={claim.id} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
            <div className="px-5 py-3 border-b border-[var(--color-border)] flex items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-3">
                <code className="text-xs text-[var(--color-evidence-blue)]">{claim.id}</code>
                <code className="text-[10px]">{claim.criterionId}</code>
              </div>
              <StatusBadge status={claim.status} size="sm" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2">
              <div className="p-5 lg:border-r border-b lg:border-b-0 border-[var(--color-border)]">
                <p className="text-subheading">Institutional claim</p>
                <p className="text-sm leading-relaxed mt-2">{claim.text}</p>
              </div>
              <div className="p-5">
                <p className="text-subheading">Defensible decision</p>
                <p className="text-sm leading-relaxed mt-2">{claim.agentReasoning ?? "No separate defensible wording was recorded."}</p>
              </div>
            </div>
            <div className="px-5 py-3 bg-[var(--color-border-subtle)] flex items-start gap-3 text-xs">
              {claim.reviewRequired ? <ShieldAlert size={14} className="text-[var(--color-warning)] mt-0.5" /> : <CheckCircle2 size={14} className="text-[var(--color-verified)] mt-0.5" />}
              <div>
                <p className="font-semibold">{claim.supportingEvidenceIds.length} supporting, {claim.contradictingEvidenceIds.length} contradicting evidence records</p>
                <p className="text-[10px] font-mono text-[var(--color-text-tertiary)] mt-1 break-all">{claim.supportingEvidenceIds.join(", ") || "No supporting IDs recorded"}</p>
              </div>
            </div>
          </article>
        ))}
        {filtered.length === 0 && <EmptyDataRow message="No claim decisions match the active search." />}
      </motion.section>
    </motion.div>
  );
}
