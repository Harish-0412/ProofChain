"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Check, Play, Search } from "lucide-react";
import { useActiveRun } from "@/hooks/use-active-run";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivePageHeader } from "@/components/live/live-page";

export default function RunsPage() {
  const [query, setQuery] = useState("");
  const runState = useActiveRun();
  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    return runState.runs.filter((run) => !value || [run.id, run.department, run.framework, run.academicYear, run.status].join(" ").toLowerCase().includes(value));
  }, [query, runState.runs]);

  if (runState.error) return <ErrorState title="Runs unavailable" message={runState.error} onRetry={runState.refresh} />;
  if (runState.loading) return <LoadingState message="Loading persisted runs" />;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader section="Run registry" title="Persisted Pipeline Runs" description="Choose the run that drives the Dashboard and every detailed projection. Selection is synchronized across the application." run={runState.activeRun} onRefresh={runState.refresh} />
      </motion.div>
      <motion.div variants={itemVariants} className="search-input max-w-xl"><Search size={14} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search run, department, year, framework, or status" /></motion.div>
      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-x-auto">
        <table className="pc-table">
          <thead><tr><th>Selected</th><th>Run</th><th>Scope</th><th>Status</th><th>Verified</th><th>Issues</th><th>Started</th><th /></tr></thead>
          <tbody>{filtered.map((run) => {
            const selected = run.id === runState.activeRunId;
            return (
              <tr key={run.id} className={selected ? "bg-[var(--color-border-subtle)]" : ""}>
                <td><button className={`btn p-2 ${selected ? "btn-primary" : "btn-ghost"}`} onClick={() => runState.setActiveRunId(run.id)} title="Use this run across the UI">{selected ? <Check size={14} /> : <Play size={14} />}</button></td>
                <td><code className="text-xs text-[var(--color-evidence-blue)]">{run.id}</code><p className="text-[10px] text-[var(--color-text-tertiary)]">{run.framework} - {run.academicYear}</p></td>
                <td className="text-xs max-w-xs">{run.department}</td>
                <td><StatusBadge status={run.status} size="sm" /></td>
                <td className="text-xs font-semibold">{run.verifiedReadiness}%</td>
                <td className="text-xs">{run.openIssues} open / {run.blockingIssues} blocking</td>
                <td className="text-[10px]">{run.startedAt ? new Date(run.startedAt).toLocaleString() : "Pending"}</td>
                <td><Link href="/dashboard" onClick={() => runState.setActiveRunId(run.id)} className="btn btn-ghost p-2" title="Open Dashboard for this run"><ArrowRight size={14} /></Link></td>
              </tr>
            );
          })}</tbody>
        </table>
      </motion.section>
    </motion.div>
  );
}
