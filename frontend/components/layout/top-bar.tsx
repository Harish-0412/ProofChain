"use client";

import { motion } from "framer-motion";
import { Bell, Search, Sun, Moon, Menu, Eye, Code, Database } from "lucide-react";
import { useUIStore, UserRole } from "@/stores/ui-store";
import { useActiveRun } from "@/hooks/use-active-run";
import { cn } from "@/lib/cn";

const ROLES: { id: UserRole; label: string }[] = [
  { id: "iqac_admin", label: "IQAC Admin" },
  { id: "dept_coordinator", label: "Department Coordinator" },
  { id: "evidence_owner", label: "Evidence Owner" },
  { id: "reviewer", label: "Auditor / Reviewer" },
];

export function TopBar() {
  const {
    theme,
    toggleTheme,
    viewMode,
    setViewMode,
    activeRole,
    setActiveRole,
    mobileSidebarOpen,
    setMobileSidebarOpen,
    notificationsPanelOpen,
    setNotificationsPanelOpen,
    setCommandPaletteOpen,
  } = useUIStore();
  const { activeRun, activeRunId, runs, setActiveRunId, loading } = useActiveRun();
  const notificationCount = activeRun
    ? activeRun.blockingIssues + (activeRun.status === "completed_with_warnings" ? 1 : 0)
    : 0;

  return (
    <header className="topbar" role="banner">
      <button
        className="lg:hidden p-2 rounded-md btn-ghost"
        onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        aria-label="Toggle navigation menu"
      >
        <Menu size={20} />
      </button>

      <div className="flex items-center gap-3 flex-1 min-w-0">
        <Database size={16} className="hidden sm:block text-[var(--color-evidence-blue)]" />
        <div className="hidden md:block min-w-0">
          <p className="text-[10px] uppercase font-bold text-[var(--color-text-tertiary)]">Persisted run</p>
          <p className="text-xs font-semibold truncate">{activeRun?.department ?? "Connecting to ProofChain"}</p>
        </div>
        <select
          value={activeRunId ?? ""}
          onChange={(event) => setActiveRunId(event.target.value || null)}
          disabled={loading || runs.length === 0}
          className="min-w-0 max-w-[230px] bg-[var(--color-panel-bg)] border border-[var(--color-border)] text-xs font-mono font-semibold rounded-md px-2.5 py-2 outline-none"
          aria-label="Select persisted run"
        >
          {runs.length === 0 && <option value="">No persisted runs</option>}
          {runs.map((run) => (
            <option key={run.id} value={run.id}>
              {run.id} - {run.status.replaceAll("_", " ")}
            </option>
          ))}
        </select>
        {activeRun && (
          <span className="hidden sm:inline-flex text-[10px] uppercase font-bold border border-[var(--color-border)] rounded px-2 py-1 text-[var(--color-text-secondary)]">
            {activeRun.academicYear}
          </span>
        )}
      </div>

      <button
        className="hidden xl:flex items-center gap-2 px-3 py-2 rounded-md border border-[var(--color-border)] bg-[var(--color-border-subtle)] text-xs text-[var(--color-text-tertiary)] min-w-[190px]"
        onClick={() => setCommandPaletteOpen(true)}
        aria-label="Open navigation search"
      >
        <Search size={14} />
        <span>Navigate ProofChain</span>
        <kbd className="ml-auto text-[10px] font-mono">Ctrl K</kbd>
      </button>

      <div className="hidden sm:flex items-center p-1 rounded-md bg-[var(--color-border-subtle)] border border-[var(--color-border)]">
        <button
          onClick={() => setViewMode("operational")}
          className={cn(
            "flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded",
            viewMode === "operational" ? "bg-[var(--color-evidence-blue)] text-white" : "text-[var(--color-text-tertiary)]"
          )}
          title="Operational view"
        >
          <Eye size={13} />
          <span className="hidden lg:inline">Operational</span>
        </button>
        <button
          onClick={() => setViewMode("technical")}
          className={cn(
            "flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded",
            viewMode === "technical" ? "bg-[var(--color-evidence-blue)] text-white" : "text-[var(--color-text-tertiary)]"
          )}
          title="Technical view"
        >
          <Code size={13} />
          <span className="hidden lg:inline">Technical</span>
        </button>
      </div>

      <select
        value={activeRole}
        onChange={(event) => setActiveRole(event.target.value as UserRole)}
        className="hidden lg:block bg-[var(--color-border-subtle)] border border-[var(--color-border)] text-xs font-semibold rounded-md px-2.5 py-2 outline-none"
        aria-label="Select operator role"
      >
        {ROLES.map((role) => <option key={role.id} value={role.id}>{role.label}</option>)}
      </select>

      <div className="flex items-center gap-1">
        <button
          className="btn btn-ghost relative p-2"
          onClick={() => setNotificationsPanelOpen(!notificationsPanelOpen)}
          aria-label="Open live run notifications"
        >
          <Bell size={18} />
          {notificationCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute top-0 right-0 min-w-4 h-4 px-1 bg-[var(--color-warning)] rounded-full text-white text-[9px] font-bold flex items-center justify-center"
            >
              {notificationCount}
            </motion.span>
          )}
        </button>
        <button className="btn btn-ghost p-2" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}
