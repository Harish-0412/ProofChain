"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Eye, FileCheck2, Search, X } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { EvidenceRecord } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { HashDisplay } from "@/components/ui/hash-display";
import { LivePageHeader, MetricStrip, EmptyDataRow } from "@/components/live/live-page";

export default function EvidencePage() {
  const [query, setQuery] = useState("");
  const [department, setDepartment] = useState("all");
  const [selected, setSelected] = useState<EvidenceRecord | null>(null);
  const resource = useRunResource<EvidenceRecord[]>("evidence", (runId) =>
    getDataProvider().getEvidence(runId)
  );

  const departments = useMemo(
    () => Array.from(new Set((resource.data ?? []).map((item) => item.tags[0]).filter(Boolean))).sort(),
    [resource.data]
  );
  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    return (resource.data ?? []).filter((item) => {
      const matchesDepartment = department === "all" || item.tags[0] === department;
      const matchesQuery = !value || [item.id, item.filename, item.evidenceType, item.source, ...item.tags]
        .join(" ")
        .toLowerCase()
        .includes(value);
      return matchesDepartment && matchesQuery;
    });
  }, [department, query, resource.data]);

  if (resource.error) return <ErrorState title="Evidence projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Loading registered evidence artifacts" />;

  const formats = new Set(resource.data.map((item) => item.tags[2]).filter(Boolean));
  const trusted = resource.data.filter((item) => ["registered", "classified", "verified", "completed"].includes(item.status)).length;
  const findings = resource.data.reduce((total, item) => total + (item.integrityFindings?.length ?? 0), 0);

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Evidence foundation / Agents 1-3"
          title="Evidence Registry and Trust"
          description="Every row comes from the selected run's immutable evidence registry, including its source, processing capability, department, format, and SHA-256 identity."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Registered records", value: resource.data.length, detail: "Persisted in evidence_registry.json" },
          { label: "Trusted state", value: trusted, detail: `${resource.data.length - trusted} require inspection` },
          { label: "Departments", value: departments.length, detail: departments.join(", ") },
          { label: "Native formats", value: formats.size, detail: `${findings} attached integrity findings` },
        ]} />
      </motion.div>

      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
        <div className="p-4 border-b border-[var(--color-border)] flex items-center gap-3 flex-wrap">
          <div className="search-input flex-1 min-w-[240px] max-w-xl">
            <Search size={14} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search ID, filename, type, path, or format" />
          </div>
          <select
            value={department}
            onChange={(event) => setDepartment(event.target.value)}
            className="border border-[var(--color-border)] bg-[var(--color-panel-bg)] rounded-md px-3 py-2 text-xs"
            aria-label="Filter evidence by department"
          >
            <option value="all">All departments</option>
            {departments.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <span className="text-xs text-[var(--color-text-tertiary)]">{filtered.length} visible</span>
        </div>
        {filtered.length === 0 ? <EmptyDataRow message="No evidence records match the active filters." /> : (
          <div className="overflow-x-auto">
            <table className="pc-table">
              <thead><tr><th>Evidence</th><th>Department</th><th>Processing</th><th>Status</th><th>SHA-256</th><th>Source</th><th aria-label="Inspect" /></tr></thead>
              <tbody>
                {filtered.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <p className="text-xs font-semibold max-w-[260px] truncate">{item.filename}</p>
                      <code className="text-[10px] text-[var(--color-evidence-blue)]">{item.id}</code>
                    </td>
                    <td className="text-xs">{item.tags[0] || "Unknown"}</td>
                    <td>
                      <p className="text-xs">{item.evidenceType.replaceAll("_", " ")}</p>
                      <code className="text-[10px] text-[var(--color-text-tertiary)]">{item.tags[2]}</code>
                    </td>
                    <td><StatusBadge status={item.status} size="sm" /></td>
                    <td>{item.hash ? <HashDisplay hash={item.hash} /> : "Not recorded"}</td>
                    <td className="text-[10px] text-[var(--color-text-tertiary)] max-w-[280px] truncate">{item.source}</td>
                    <td><button className="btn btn-ghost p-2" onClick={() => setSelected(item)} title="Inspect evidence record"><Eye size={14} /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.section>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <button className="absolute inset-0 bg-black/45" onClick={() => setSelected(null)} aria-label="Close evidence detail" />
          <section className="relative w-full max-w-2xl bg-[var(--color-panel-bg)] border border-[var(--color-border)] rounded-lg shadow-lg">
            <div className="p-5 border-b border-[var(--color-border)] flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 min-w-0">
                <FileCheck2 size={18} className="text-[var(--color-evidence-blue)] mt-0.5" />
                <div className="min-w-0"><h2 className="text-sm font-bold break-words">{selected.filename}</h2><code className="text-[10px]">{selected.id}</code></div>
              </div>
              <button className="btn btn-ghost p-2" onClick={() => setSelected(null)} title="Close"><X size={16} /></button>
            </div>
            <dl className="grid grid-cols-1 sm:grid-cols-[150px_1fr] text-xs">
              {[
                ["Status", selected.status],
                ["Department", selected.tags[0]],
                ["Academic year", selected.tags[1]],
                ["Format", selected.tags[2]],
                ["Processing", selected.evidenceType],
                ["Source", selected.source],
                ["Registered", selected.registeredAt ? new Date(selected.registeredAt).toLocaleString() : "Not recorded"],
                ["Capability reason", selected.capabilityReason ?? "Not recorded"],
                ["SHA-256", selected.hash ?? "Not recorded"],
              ].map(([label, value]) => (
                <div key={label} className="contents">
                  <dt className="px-5 py-3 border-b border-[var(--color-border-subtle)] font-semibold text-[var(--color-text-tertiary)]">{label}</dt>
                  <dd className="px-5 py-3 border-b border-[var(--color-border-subtle)] break-all">{value}</dd>
                </div>
              ))}
            </dl>
          </section>
        </div>
      )}
    </motion.div>
  );
}
