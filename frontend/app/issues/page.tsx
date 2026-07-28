"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Search } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { Issue } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { LivePageHeader, MetricStrip, EmptyDataRow } from "@/components/live/live-page";

export default function IssuesPage() {
  const [query, setQuery] = useState("");
  const resource = useRunResource<Issue[]>("issues", (runId) => getDataProvider().getIssues(runId));
  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    return (resource.data ?? []).filter((issue) =>
      !value || [issue.id, issue.title, issue.description, issue.status, issue.owner, issue.criterionId]
        .join(" ").toLowerCase().includes(value)
    );
  }, [query, resource.data]);

  if (resource.error) return <ErrorState title="Issue projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Loading canonical issue state" />;

  const open = resource.data.filter((issue) => issue.status !== "resolved").length;
  const resolved = resource.data.length - open;
  const assigned = resource.data.filter((issue) => Boolean(issue.owner)).length;
  const impact = resource.data.reduce((total, issue) => total + Math.abs(issue.readinessImpact), 0);

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Resolution planning / Agents 5-6"
          title="Canonical Issue Register"
          description="Integrity findings, claim failures, and evidence gaps are normalized into one issue identity and tracked through governed lifecycle states."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Canonical issues", value: resource.data.length, detail: "Deduplicated persisted identities" },
          { label: "Open", value: open, detail: "Not yet revalidated as resolved" },
          { label: "Resolved", value: resolved, detail: "Passed closure state transition" },
          { label: "Assigned", value: assigned, detail: `${impact}% total modeled readiness impact` },
        ]} />
      </motion.div>
      <motion.div variants={itemVariants} className="search-input max-w-xl">
        <Search size={14} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search issue, criterion, owner, or lifecycle state" />
      </motion.div>
      <motion.section variants={itemVariants}>
        {filtered.length === 0 ? (
          <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-10 text-center">
            {resource.data.length === 0 ? (
              <>
                <CheckCircle2 size={30} className="text-[var(--color-verified)] mx-auto" />
                <h2 className="text-sm font-bold mt-3">No canonical issues were generated</h2>
                <p className="text-xs text-[var(--color-text-tertiary)] mt-1">The selected sample run has no unresolved evidence, integrity, or claim gap.</p>
              </>
            ) : <EmptyDataRow message="No issue matches the active search." />}
          </div>
        ) : (
          <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-x-auto">
            <table className="pc-table">
              <thead><tr><th>Issue</th><th>Criterion</th><th>Severity</th><th>State</th><th>Owner</th><th>Readiness</th></tr></thead>
              <tbody>{filtered.map((issue) => (
                <tr key={issue.id}>
                  <td><p className="text-xs font-semibold">{issue.title}</p><code className="text-[10px] text-[var(--color-evidence-blue)]">{issue.id}</code></td>
                  <td><code className="text-xs">{issue.criterionId}</code></td>
                  <td><SeverityBadge severity={issue.severity} /></td>
                  <td><StatusBadge status={issue.status} size="sm" /></td>
                  <td className="text-xs">{issue.owner ?? "Unassigned"}</td>
                  <td className="text-xs font-semibold">{issue.readinessImpact}%</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </motion.section>
      {open > 0 && <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]"><AlertTriangle size={14} className="text-[var(--color-warning)]" />Uploading a correction does not resolve an issue; targeted closure revalidation must pass.</div>}
    </motion.div>
  );
}
