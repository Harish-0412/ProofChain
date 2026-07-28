"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ViewMode = "operational" | "technical";
export type UserRole = "iqac_admin" | "dept_coordinator" | "evidence_owner" | "reviewer";

interface UIState {
  // Theme
  theme: "light" | "dark";
  setTheme: (theme: "light" | "dark") => void;
  toggleTheme: () => void;

  // View Mode (Phase 1 Upgrade: Operational vs Technical)
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  toggleViewMode: () => void;

  // Active Role (Phase 1 Upgrade: Role-based views)
  activeRole: UserRole;
  setActiveRole: (role: UserRole) => void;

  // Sidebar
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  mobileSidebarOpen: boolean;
  setMobileSidebarOpen: (open: boolean) => void;

  // Run selection
  activeRunId: string | null;
  setActiveRunId: (runId: string | null) => void;

  // Modals & Drawers
  notificationsPanelOpen: boolean;
  setNotificationsPanelOpen: (open: boolean) => void;
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: "light",
      setTheme: (theme) => set({ theme }),
      toggleTheme: () =>
        set((state) => ({ theme: state.theme === "light" ? "dark" : "light" })),

      viewMode: "operational",
      setViewMode: (viewMode) => set({ viewMode }),
      toggleViewMode: () =>
        set((state) => ({
          viewMode: state.viewMode === "operational" ? "technical" : "operational",
        })),

      activeRole: "iqac_admin",
      setActiveRole: (activeRole) => set({ activeRole }),

      sidebarCollapsed: false,
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      mobileSidebarOpen: false,
      setMobileSidebarOpen: (mobileSidebarOpen) => set({ mobileSidebarOpen }),

      activeRunId: null,
      setActiveRunId: (activeRunId) => set({ activeRunId }),

      notificationsPanelOpen: false,
      setNotificationsPanelOpen: (notificationsPanelOpen) =>
        set({ notificationsPanelOpen }),

      commandPaletteOpen: false,
      setCommandPaletteOpen: (commandPaletteOpen) =>
        set({ commandPaletteOpen }),
    }),
    {
      name: "proofchain-ui-storage",
      partialize: (state) => ({
        theme: state.theme,
        viewMode: state.viewMode,
        activeRole: state.activeRole,
        sidebarCollapsed: state.sidebarCollapsed,
        activeRunId: state.activeRunId,
      }),
    }
  )
);
