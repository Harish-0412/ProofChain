"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Bell, AlertTriangle, Activity, CheckCircle2 } from "lucide-react";
import { useUIStore } from "@/stores/ui-store";
import { useActiveRun } from "@/hooks/use-active-run";
import { getDataProvider } from "@/lib/get-data-provider";
import { WorkflowEvent, WorkflowStatus } from "@/lib/data-provider";

export function NotificationPanel() {
  const { notificationsPanelOpen, setNotificationsPanelOpen } = useUIStore();
  const { activeRunId } = useActiveRun();
  const [workflow, setWorkflow] = useState<WorkflowStatus | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);

  useEffect(() => {
    if (!notificationsPanelOpen || !activeRunId) return;
    void Promise.all([
      getDataProvider().getWorkflowStatus(activeRunId),
      getDataProvider().getEvents(activeRunId, 8, 0),
    ]).then(([nextWorkflow, nextEvents]) => {
      setWorkflow(nextWorkflow);
      setEvents(nextEvents.slice().reverse());
    });
  }, [activeRunId, notificationsPanelOpen]);

  const queue = workflow?.userMustDo ?? [];

  return (
    <AnimatePresence>
      {notificationsPanelOpen && (
        <>
          <motion.div
            className="fixed inset-0 z-40 bg-black/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setNotificationsPanelOpen(false)}
          />
          <motion.aside
            className="notif-panel"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            role="dialog"
            aria-label="Live run activity"
          >
            <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
              <div className="flex items-center gap-2">
                <Bell size={17} className="text-[var(--color-evidence-blue)]" />
                <div>
                  <h2 className="text-sm font-semibold">Live Run Activity</h2>
                  <p className="text-[10px] font-mono text-[var(--color-text-tertiary)]">{activeRunId ?? "No run selected"}</p>
                </div>
              </div>
              <button className="p-1 btn-ghost rounded" onClick={() => setNotificationsPanelOpen(false)} aria-label="Close activity">
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              <div className="p-4 border-b border-[var(--color-border)]">
                <p className="text-subheading mb-2">Human action queue</p>
                {queue.length === 0 ? (
                  <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
                    <CheckCircle2 size={15} className="text-[var(--color-verified)]" />
                    No governed human action is currently queued.
                  </div>
                ) : queue.map((item, index) => (
                  <div key={`${item.target}-${index}`} className="py-2 flex gap-2 text-xs">
                    <AlertTriangle size={14} className="text-[var(--color-warning)] mt-0.5" />
                    <div>
                      <p className="font-semibold">{item.reason ?? item.type.replaceAll("_", " ")}</p>
                      <p className="text-[10px] text-[var(--color-text-tertiary)]">{item.owner ?? "Authorized reviewer"}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4">
                <p className="text-subheading mb-2">Latest persisted events</p>
                {events.map((event) => (
                  <div key={event.id} className="py-2.5 border-b border-[var(--color-border-subtle)] flex gap-2">
                    <Activity size={14} className="text-[var(--color-evidence-blue)] mt-0.5" />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold">{event.eventType.replaceAll("_", " ")}</p>
                      <p className="text-[10px] text-[var(--color-text-tertiary)] truncate">
                        {event.agentName?.replaceAll("_", " ") ?? "system"} - event #{event.sequenceNumber}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
