"use client";

import { useCallback, useEffect, useState } from "react";
import { getDataProvider } from "@/lib/get-data-provider";
import { RunSummary } from "@/lib/data-provider";
import { useUIStore } from "@/stores/ui-store";

export function useActiveRun() {
  const activeRunId = useUIStore((state) => state.activeRunId);
  const setActiveRunId = useUIStore((state) => state.setActiveRunId);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applyRuns = useCallback((nextRuns: RunSummary[]) => {
    setRuns(nextRuns);
    const selected = nextRuns.find((run) => run.id === activeRunId);
    const resolvedId = selected?.id ?? nextRuns[0]?.id ?? null;
    if (resolvedId !== activeRunId) setActiveRunId(resolvedId);
  }, [activeRunId, setActiveRunId]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      applyRuns(await getDataProvider().getRuns());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load persisted runs.");
    } finally {
      setLoading(false);
    }
  }, [applyRuns]);

  useEffect(() => {
    let active = true;
    getDataProvider().getRuns()
      .then((nextRuns) => {
        if (!active) return;
        applyRuns(nextRuns);
        setError(null);
      })
      .catch((cause) => {
        if (active) setError(cause instanceof Error ? cause.message : "Unable to load persisted runs.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [applyRuns]);

  return {
    activeRunId,
    activeRun: runs.find((run) => run.id === activeRunId) ?? null,
    runs,
    loading,
    error,
    refresh,
    setActiveRunId,
  };
}
