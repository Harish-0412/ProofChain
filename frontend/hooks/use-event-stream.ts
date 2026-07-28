"use client";

import { useEffect, useState } from "react";
import { WorkflowEvent } from "@/lib/data-provider";

interface UseEventStreamResult {
  events: WorkflowEvent[];
  isConnected: boolean;
  isFallbackPolling: boolean;
}

export function useEventStream(runId: string): UseEventStreamResult {
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isFallbackPolling, setIsFallbackPolling] = useState(false);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000/ui-api";
    const sseUrl = `${gatewayUrl}/runs/${runId}/events/stream`;

    eventSource = new EventSource(sseUrl);

    eventSource.onopen = () => {
      setIsConnected(true);
      setIsFallbackPolling(false);
    };

    eventSource.onmessage = (e) => {
      try {
        const event: WorkflowEvent = JSON.parse(e.data);
        setEvents((prev) => [event, ...prev]);
      } catch {
        // Ignore heartbeat or parse errors.
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      setIsFallbackPolling(true);
      eventSource?.close();

      pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`${gatewayUrl}/runs/${runId}/events?limit=50`);
          if (res.ok) {
            const data = await res.json();
            setEvents(data);
          }
        } catch {
          // Retry on the next bounded polling interval.
        }
      }, 4000);
    };

    return () => {
      eventSource?.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [runId]);

  return { events, isConnected, isFallbackPolling };
}
