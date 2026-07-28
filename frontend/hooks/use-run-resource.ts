"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useActiveRun } from "./use-active-run";

export function useRunResource<T>(
  resourceKey: string,
  loader: (runId: string) => Promise<T>
) {
  const run = useActiveRun();
  const loaderRef = useRef(loader);
  const [data, setData] = useState<T | null>(null);
  const [resourceLoading, setResourceLoading] = useState(true);
  const [resourceError, setResourceError] = useState<string | null>(null);

  useEffect(() => {
    loaderRef.current = loader;
  });

  const refreshResource = useCallback(async () => {
    if (!run.activeRunId) return;
    setResourceLoading(true);
    setResourceError(null);
    try {
      setData(await loaderRef.current(run.activeRunId));
    } catch (cause) {
      setResourceError(cause instanceof Error ? cause.message : "The live run projection is unavailable.");
    } finally {
      setResourceLoading(false);
    }
  }, [run.activeRunId]);

  useEffect(() => {
    if (!run.activeRunId) return;
    let active = true;
    const selectedRunId = run.activeRunId;
    Promise.resolve()
      .then(() => loaderRef.current(selectedRunId))
      .then((nextData) => {
        if (!active) return;
        setData(nextData);
        setResourceError(null);
      })
      .catch((cause) => {
        if (active) setResourceError(cause instanceof Error ? cause.message : "The live run projection is unavailable.");
      })
      .finally(() => {
        if (active) setResourceLoading(false);
      });
    return () => {
      active = false;
    };
  }, [resourceKey, run.activeRunId]);

  return {
    ...run,
    data,
    loading: resourceLoading || run.loading,
    error: resourceError ?? run.error,
    refresh: refreshResource,
  };
}
