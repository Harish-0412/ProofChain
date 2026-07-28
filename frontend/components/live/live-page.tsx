"use client";

import { RefreshCw, Database, Radio } from "lucide-react";
import { RunSummary } from "@/lib/data-provider";
import { StatusBadge } from "@/components/ui/status-badge";

interface LivePageHeaderProps {
  section: string;
  title: string;
  description: string;
  run?: RunSummary | null;
  onRefresh?: () => void;
  actions?: React.ReactNode;
}

export function LivePageHeader({
  section,
  title,
  description,
  run,
  onRefresh,
  actions,
}: LivePageHeaderProps) {
  return (
    <header className="space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0">
          <p className="text-subheading mb-1">{section}</p>
          <h1 className="text-display">{title}</h1>
          <p className="text-body mt-1 max-w-3xl">{description}</p>
        </div>
        <div className="flex items-center gap-2">
          {actions}
          {onRefresh && (
            <button className="btn btn-secondary btn-sm" onClick={onRefresh} title="Refresh persisted projection">
              <RefreshCw size={14} />
              Refresh
            </button>
          )}
        </div>
      </div>
      {run && <RunSourceBar run={run} />}
    </header>
  );
}

export function RunSourceBar({ run }: { run: RunSummary }) {
  return (
    <div className="flex items-center gap-x-4 gap-y-2 flex-wrap px-4 py-3 border-y border-[var(--color-border)] bg-[var(--color-border-subtle)] text-xs">
      <span className="flex items-center gap-1.5 font-semibold">
        <Database size={14} className="text-[var(--color-evidence-blue)]" />
        Persisted artifact projection
      </span>
      <code className="font-mono text-[var(--color-evidence-blue)]">{run.id}</code>
      <span>{run.department}</span>
      <span>{run.framework}</span>
      <span>{run.academicYear}</span>
      <span className="ml-auto flex items-center gap-1.5">
        <Radio size={12} className="text-[var(--color-verified)]" />
        <StatusBadge status={run.status} size="sm" />
      </span>
    </div>
  );
}

export function MetricStrip({
  items,
}: {
  items: Array<{ label: string; value: React.ReactNode; detail?: string }>;
}) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 border border-[var(--color-border)] rounded-lg overflow-hidden bg-[var(--color-panel-bg)]">
      {items.map((item) => (
        <div key={item.label} className="px-4 py-4 border-r border-b lg:border-b-0 last:border-r-0 border-[var(--color-border)] min-w-0">
          <p className="text-2xl font-bold">{item.value}</p>
          <p className="text-xs font-semibold mt-1">{item.label}</p>
          {item.detail && <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">{item.detail}</p>}
        </div>
      ))}
    </div>
  );
}

export function EmptyDataRow({ message }: { message: string }) {
  return (
    <div className="py-10 px-4 text-center border border-dashed border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-tertiary)]">
      {message}
    </div>
  );
}
