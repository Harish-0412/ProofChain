"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Archive, CheckCircle2, FileArchive, Fingerprint, ShieldCheck } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { AuditPackage } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { HashDisplay } from "@/components/ui/hash-display";
import { LivePageHeader, MetricStrip, EmptyDataRow } from "@/components/live/live-page";

export default function PackagesPage() {
  const [tab, setTab] = useState<"manifest" | "quality">("manifest");
  const resource = useRunResource<AuditPackage | null>("package", (runId) => getDataProvider().getPackage(runId));

  if (resource.error) return <ErrorState title="Package projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.activeRun) return <LoadingState message="Loading audit package manifest" />;
  if (!resource.data) {
    return (
      <div className="space-y-6">
        <LivePageHeader section="Audit output / Agents 9-10" title="Audit Package" description="No audit package artifact exists for the selected run." run={resource.activeRun} onRefresh={resource.refresh} />
        <EmptyDataRow message="Run the governed package composer before a manifest can be inspected." />
      </div>
    );
  }

  const pkg = resource.data;
  const quality = pkg.qualityReview;
  const evidenceCount = new Set(pkg.contents.flatMap((item) => item.evidenceIds)).size;
  const claimCount = new Set(pkg.contents.flatMap((item) => item.claimIds)).size;
  const ready = pkg.contents.filter((item) => item.ready).length;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Audit output / Agents 9-10"
          title="Audit Package and Quality Review"
          description="Inspect the frozen package scope, traceability manifest, package hash, quality decision, and corrections without confusing quality readiness with external release approval."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Package state", value: <StatusBadge status={pkg.status} size="md" />, detail: pkg.id },
          { label: "Requirements", value: pkg.contents.length, detail: `${ready} package-ready` },
          { label: "Evidence identities", value: evidenceCount, detail: "Eligible records in frozen scope" },
          { label: "Quality score", value: quality?.score != null ? `${quality.score}/100` : "N/A", detail: quality?.status ?? "No review artifact" },
        ]} />
      </motion.div>

      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
        <div className="p-5 flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-start gap-3">
            <FileArchive size={20} className="text-[var(--color-evidence-blue)] mt-0.5" />
            <div><code className="text-sm font-bold text-[var(--color-evidence-blue)]">{pkg.id}</code><p className="text-xs text-[var(--color-text-tertiary)] mt-1">{pkg.createdAt ? `Generated ${new Date(pkg.createdAt).toLocaleString()}` : "Generation timestamp not recorded"}</p></div>
          </div>
          <StatusBadge status={pkg.status} size="md" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 border-t border-[var(--color-border)]">
          <div className="p-4 md:border-r border-b md:border-b-0 border-[var(--color-border)]">
            <p className="text-subheading">Package hash</p>
            <div className="mt-2 flex items-center gap-2"><Fingerprint size={13} />{pkg.packageHash ? <HashDisplay hash={pkg.packageHash} /> : "Not recorded"}</div>
          </div>
          <div className="p-4 md:border-r border-b md:border-b-0 border-[var(--color-border)]">
            <p className="text-subheading">Bundle SHA-256</p>
            <div className="mt-2">{pkg.bundleSha256 ? <HashDisplay hash={pkg.bundleSha256} /> : "Not recorded"}</div>
          </div>
          <div className="p-4">
            <p className="text-subheading">Traceability</p>
            <p className="text-xs font-semibold mt-2">{evidenceCount} evidence - {claimCount} claims</p>
          </div>
        </div>
      </motion.section>

      <motion.section variants={itemVariants}>
        <div className="flex border-b border-[var(--color-border)] mb-4">
          <button className={`tab-item px-4 py-3 text-xs ${tab === "manifest" ? "active" : ""}`} onClick={() => setTab("manifest")}><Archive size={14} className="inline mr-2" />Manifest</button>
          <button className={`tab-item px-4 py-3 text-xs ${tab === "quality" ? "active" : ""}`} onClick={() => setTab("quality")}><ShieldCheck size={14} className="inline mr-2" />Quality review</button>
        </div>
        {tab === "manifest" ? (
          <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-x-auto">
            <table className="pc-table">
              <thead><tr><th>Requirement</th><th>Eligibility</th><th>Evidence</th><th>Claims</th><th>Explanation</th></tr></thead>
              <tbody>{pkg.contents.map((item) => (
                <tr key={item.criterionId}>
                  <td><code className="text-xs text-[var(--color-evidence-blue)]">{item.criterionId}</code></td>
                  <td><StatusBadge status={item.ready ? "verified" : "blocked"} size="sm" /></td>
                  <td className="text-xs">{item.evidenceIds.length}</td>
                  <td className="text-xs">{item.claimIds.length}</td>
                  <td className="text-xs max-w-lg">{item.eligibilityExplanation}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : quality ? (
          <div className="space-y-3">
            <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-5 flex items-center justify-between gap-4">
              <div><p className="text-subheading">Adversarial decision</p><p className="text-sm font-bold mt-1">{quality.status}</p></div>
              <StatusBadge status={quality.status} size="md" />
            </div>
            {quality.findings.length === 0 ? (
              <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-8 text-center">
                <CheckCircle2 size={28} className="text-[var(--color-verified)] mx-auto" />
                <h3 className="text-sm font-bold mt-3">No quality corrections were required</h3>
                <p className="text-xs text-[var(--color-text-tertiary)] mt-1">The persisted review passed the package for independent human approval.</p>
              </div>
            ) : quality.findings.map((finding) => (
              <div key={finding.id} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-5">
                <div className="flex items-center gap-3"><SeverityBadge severity={finding.severity} /><code className="text-xs">{finding.id}</code></div>
                <p className="text-sm font-semibold mt-3">{finding.description}</p>
                <p className="text-xs text-[var(--color-text-secondary)] mt-1">{finding.correctionRequired}</p>
              </div>
            ))}
          </div>
        ) : <EmptyDataRow message="No adversarial quality review artifact exists." />}
      </motion.section>
    </motion.div>
  );
}
