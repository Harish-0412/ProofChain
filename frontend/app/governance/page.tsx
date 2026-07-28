"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Boxes, FileLock2, Link2, Scale, ShieldCheck } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { GovernanceProjection } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { HashDisplay } from "@/components/ui/hash-display";
import { LivePageHeader, MetricStrip } from "@/components/live/live-page";

export default function GovernancePage() {
  const [tab, setTab] = useState<"chain" | "policies" | "models">("chain");
  const resource = useRunResource<GovernanceProjection>("governance", (runId) =>
    getDataProvider().getGovernance(runId)
  );

  if (resource.error) return <ErrorState title="Governance projection unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Verifying persisted governance artifacts" />;

  const governance = resource.data;
  const deterministic = governance.modelProfiles.filter((profile) => profile.execution_mode === "deterministic").length;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Governance and synchronization"
          title="Decision Integrity and Policy Chain"
          description="The checkpoint lineage, append-only event hashes, active policy fingerprint, component boundaries, and model execution profiles for the selected run."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>
      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Checkpoints", value: governance.checkpoints.length, detail: "Core lifecycle state handoffs" },
          { label: "Hash-linked events", value: governance.events.length, detail: "Append-only workflow event chain" },
          { label: "Active policies", value: governance.policies.length, detail: `Policy set ${governance.policySetVersion ?? "unknown"}` },
          { label: "Agent profiles", value: governance.modelProfiles.length, detail: `${deterministic} deterministic profiles` },
        ]} />
      </motion.div>

      <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto]">
          <div className="p-5 lg:border-r border-b lg:border-b-0 border-[var(--color-border)]">
            <p className="text-subheading">Policy fingerprint</p>
            <div className="mt-2">{governance.policyFingerprint ? <HashDisplay hash={governance.policyFingerprint} /> : "Not recorded"}</div>
          </div>
          <div className="p-5 flex items-center gap-5 text-xs">
            <span className="flex items-center gap-1.5"><ShieldCheck size={14} className="text-[var(--color-verified)]" />Technical complete: {String(governance.validation.technicalComplete)}</span>
            <span className="flex items-center gap-1.5"><Link2 size={14} className="text-[var(--color-verified)]" />Synchronized: {String(governance.validation.persistenceSynchronized)}</span>
          </div>
        </div>
      </motion.section>

      <motion.div variants={itemVariants} className="flex border-b border-[var(--color-border)]">
        <button className={`tab-item px-4 py-3 text-xs ${tab === "chain" ? "active" : ""}`} onClick={() => setTab("chain")}><Link2 size={14} className="inline mr-2" />Execution chain</button>
        <button className={`tab-item px-4 py-3 text-xs ${tab === "policies" ? "active" : ""}`} onClick={() => setTab("policies")}><Scale size={14} className="inline mr-2" />Policies</button>
        <button className={`tab-item px-4 py-3 text-xs ${tab === "models" ? "active" : ""}`} onClick={() => setTab("models")}><Boxes size={14} className="inline mr-2" />Agent profiles</button>
      </motion.div>

      {tab === "chain" && (
        <motion.section variants={itemVariants} className="space-y-5">
          <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-x-auto">
            <table className="pc-table">
              <thead><tr><th>Stage</th><th>Status</th><th>Records</th><th>Upstream</th><th>Output SHA-256</th><th>Completed</th></tr></thead>
              <tbody>{governance.checkpoints.map((checkpoint, index) => (
                <tr key={`${checkpoint.stage_name}-${index}`}>
                  <td><span className="text-[10px] mr-2">{index + 1}</span><span className="text-xs font-semibold">{checkpoint.stage_name.replaceAll("_", " ")}</span></td>
                  <td><StatusBadge status={checkpoint.status} size="sm" /></td>
                  <td className="text-xs">{checkpoint.output?.record_count ?? 0}</td>
                  <td>{checkpoint.upstream_sha256 ? <HashDisplay hash={checkpoint.upstream_sha256} /> : <span className="text-xs">Root</span>}</td>
                  <td>{checkpoint.output?.sha256 ? <HashDisplay hash={checkpoint.output.sha256} /> : "None"}</td>
                  <td className="text-[10px]">{checkpoint.completed_at ? new Date(checkpoint.completed_at).toLocaleString() : "Pending"}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <div className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-hidden">
            <div className="px-5 py-4 border-b border-[var(--color-border)] flex items-center gap-2"><FileLock2 size={16} className="text-[var(--color-evidence-blue)]" /><h2 className="text-sm font-semibold">Append-only event chain</h2></div>
            <div className="divide-y divide-[var(--color-border-subtle)]">
              {governance.events.map((event) => (
                <div key={event.id} className="px-5 py-3 grid grid-cols-[42px_1fr_auto] gap-3 items-center">
                  <span className="text-xs font-bold">#{event.sequenceNumber}</span>
                  <div><p className="text-xs font-semibold">{event.eventType}</p><p className="text-[10px] text-[var(--color-text-tertiary)]">{event.agentName?.replaceAll("_", " ")}</p></div>
                  {event.eventHash && <HashDisplay hash={event.eventHash} />}
                </div>
              ))}
            </div>
          </div>
        </motion.section>
      )}

      {tab === "policies" && (
        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-x-auto">
          <table className="pc-table"><thead><tr><th>Policy</th><th>Schema</th><th>SHA-256</th><th>Persisted source</th></tr></thead><tbody>
            {governance.policies.map((policy) => <tr key={policy.policy_id}><td className="text-xs font-semibold">{policy.policy_id}</td><td><code className="text-xs">{policy.schema_version}</code></td><td><HashDisplay hash={policy.sha256} /></td><td className="text-[10px] max-w-md truncate">{policy.path}</td></tr>)}
          </tbody></table>
        </motion.section>
      )}

      {tab === "models" && (
        <motion.section variants={itemVariants} className="border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] overflow-x-auto">
          <table className="pc-table"><thead><tr><th>Agent</th><th>Execution</th><th>External calls</th><th>Fallback</th><th>High-impact approval</th></tr></thead><tbody>
            {governance.modelProfiles.map((profile) => <tr key={profile.agent_name}><td className="text-xs font-semibold">{profile.agent_name.replaceAll("_", " ")}</td><td><StatusBadge status={profile.execution_mode === "deterministic" ? "verified" : "warning"} size="sm" /></td><td className="text-xs">{profile.external_model_calls}</td><td className="text-xs">{profile.fallback_behavior.replaceAll("_", " ")}</td><td className="text-xs">{profile.high_impact_actions_require_approval ? "Required" : "Not required"}</td></tr>)}
          </tbody></table>
        </motion.section>
      )}
    </motion.div>
  );
}
