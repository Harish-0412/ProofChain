"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, Search, Workflow } from "lucide-react";
import { getDataProvider } from "@/lib/get-data-provider";
import { AgentExecution, GoalNode, WorkflowEvent } from "@/lib/data-provider";
import { useRunResource } from "@/hooks/use-run-resource";
import { containerVariants, itemVariants } from "@/lib/animations";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivePageHeader, MetricStrip } from "@/components/live/live-page";

interface AgentCenterData {
  agents: AgentExecution[];
  goals: GoalNode[];
  events: WorkflowEvent[];
}

export default function AgentsPage() {
  const [query, setQuery] = useState("");
  const [layer, setLayer] = useState("all");
  const resource = useRunResource<AgentCenterData>("agents", async (runId) => {
    const provider = getDataProvider();
    const [agents, goals, events] = await Promise.all([
      provider.getAgents(runId),
      provider.getGoals(runId),
      provider.getEvents(runId, 1000, 0),
    ]);
    return { agents, goals, events };
  });

  const layers = useMemo(
    () => Array.from(new Set(resource.data?.agents.map((agent) => agent.architectureLayer) ?? [])),
    [resource.data]
  );
  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    return (resource.data?.agents ?? []).filter((agent) => {
      const matchesLayer = layer === "all" || agent.architectureLayer === layer;
      const matchesQuery = !value || [agent.name, agent.role, agent.slug, agent.decisionReason]
        .join(" ")
        .toLowerCase()
        .includes(value);
      return matchesLayer && matchesQuery;
    });
  }, [layer, query, resource.data]);

  if (resource.error) return <ErrorState title="Agent projections unavailable" message={resource.error} onRetry={resource.refresh} />;
  if (resource.loading || !resource.data || !resource.activeRun) return <LoadingState message="Loading 22 persisted agent executions" />;

  const completed = resource.data.agents.filter((agent) => agent.status === "completed").length;
  const warnings = resource.data.agents.filter((agent) => agent.status === "warning").length;
  const blocked = resource.data.agents.filter((agent) => agent.status === "blocked").length;
  const achievedGoals = resource.data.goals.filter((goal) => goal.status === "achieved").length;

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <LivePageHeader
          section="Agent architecture"
          title="22-Agent Execution Directory"
          description="Every card is a route into that agent's persisted goal, plan, actions, observations, reflections, decision, and completion proof."
          run={resource.activeRun}
          onRefresh={resource.refresh}
        />
      </motion.div>

      <motion.div variants={itemVariants}>
        <MetricStrip items={[
          { label: "Primary agents", value: resource.data.agents.length, detail: "Independent goal agents" },
          { label: "Completed", value: completed, detail: `${warnings} completed with warnings` },
          { label: "Blocked", value: blocked, detail: "Governed refusals, not hidden failures" },
          { label: "Goals achieved", value: achievedGoals, detail: `${resource.data.events.length} workflow events` },
        ]} />
      </motion.div>

      <motion.div variants={itemVariants} className="flex items-center gap-3 flex-wrap">
        <div className="search-input flex-1 min-w-[240px] max-w-lg">
          <Search size={14} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search agent, role, decision, or slug" />
        </div>
        <select
          value={layer}
          onChange={(event) => setLayer(event.target.value)}
          className="border border-[var(--color-border)] bg-[var(--color-panel-bg)] rounded-md px-3 py-2 text-xs"
          aria-label="Filter agents by architecture layer"
        >
          <option value="all">All architecture layers</option>
          {layers.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
      </motion.div>

      <motion.section variants={itemVariants} className="space-y-5">
        {layers.map((architectureLayer) => {
          const layerAgents = filtered.filter((agent) => agent.architectureLayer === architectureLayer);
          if (layerAgents.length === 0) return null;
          return (
            <div key={architectureLayer} className="space-y-3">
              <div className="flex items-center gap-2 border-b border-[var(--color-border)] pb-2">
                <Workflow size={15} className="text-[var(--color-evidence-blue)]" />
                <h2 className="text-sm font-semibold">{architectureLayer}</h2>
                <span className="text-[10px] text-[var(--color-text-tertiary)]">{layerAgents.length} agents</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {layerAgents.map((agent) => (
                  <Link
                    key={agent.id}
                    href={`/agents/${agent.id}`}
                    className="group border border-[var(--color-border)] rounded-lg bg-[var(--color-panel-bg)] p-4 hover:border-[var(--color-evidence-blue)] transition-colors min-h-[205px] flex flex-col"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="w-8 h-8 rounded-md bg-[var(--color-border-subtle)] flex items-center justify-center text-xs font-bold text-[var(--color-evidence-blue)]">
                        {agent.id}
                      </span>
                      <StatusBadge status={agent.status} size="sm" />
                    </div>
                    <h3 className="text-sm font-bold mt-3 group-hover:text-[var(--color-evidence-blue)]">{agent.name}</h3>
                    <code className="text-[10px] text-[var(--color-text-tertiary)] mt-0.5">{agent.slug}</code>
                    <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed mt-2 line-clamp-3">{agent.role}</p>
                    <div className="mt-auto pt-3 border-t border-[var(--color-border-subtle)] flex items-center justify-between gap-2">
                      <span className="text-[10px] text-[var(--color-text-tertiary)]">
                        {agent.rounds} decision round{agent.rounds === 1 ? "" : "s"} - {agent.goals.length} linked goal{agent.goals.length === 1 ? "" : "s"}
                      </span>
                      <ArrowRight size={14} className="text-[var(--color-evidence-blue)]" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </motion.section>

      <motion.div variants={itemVariants} className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
        <CheckCircle2 size={15} className="text-[var(--color-verified)]" />
        Agent statuses and explanations are read from the selected run&apos;s decision ledger and cognition artifacts.
      </motion.div>
    </motion.div>
  );
}
