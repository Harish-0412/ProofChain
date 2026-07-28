"use client";

import { motion } from "framer-motion";
import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";
import { CommandPalette } from "@/components/ui/command-palette";
import { NotificationPanel } from "@/components/ui/notification-panel";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/cn";
import { pageVariants } from "@/lib/animations";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const prefersReduced = useReducedMotion();

  return (
    <div className="app-shell">
      <Sidebar />

      {/* Main area */}
      <div
        className={cn(
          "main-content",
          sidebarCollapsed && "sidebar-collapsed"
        )}
      >
        <TopBar />

        <main
          id="main-content"
          className="page-content"
          tabIndex={-1}
        >
          <motion.div
            variants={prefersReduced ? undefined : pageVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {children}
          </motion.div>
        </main>
      </div>

      {/* Global Modals & Overlay Panels */}
      <CommandPalette />
      <NotificationPanel />
    </div>
  );
}
