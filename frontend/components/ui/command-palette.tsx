"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  LayoutDashboard,
  Route,
  Play,
  Bot,
  FileText,
  CheckSquare,
  AlertTriangle,
  ClipboardList,
  ShieldCheck,
  Package,
  Scale,
  Activity,
  Settings,
  X,
} from "lucide-react";
import { useUIStore } from "@/stores/ui-store";

const COMMANDS = [
  { id: "dashboard", label: "Open Readiness Dashboard", href: "/dashboard", category: "Navigation", icon: LayoutDashboard },
  { id: "operation-room", label: "Open Technical Operation Room", href: "/operation-room", category: "Technical", icon: Route },
  { id: "runs", label: "View Pipeline Runs", href: "/runs", category: "Navigation", icon: Play },
  { id: "agents", label: "22-Agent Execution Directory", href: "/agents", category: "Intelligence", icon: Bot },
  { id: "evidence", label: "Evidence Explorer", href: "/evidence", category: "Intelligence", icon: FileText },
  { id: "claims", label: "Claim Defensibility Workspace", href: "/claims", category: "Intelligence", icon: CheckSquare },
  { id: "issues", label: "Canonical Issue Center", href: "/issues", category: "Operations", icon: AlertTriangle },
  { id: "tasks", label: "Task & Liaison Workspace", href: "/tasks", category: "Operations", icon: ClipboardList },
  { id: "approvals", label: "Approval Center", href: "/approvals", category: "Operations", icon: ShieldCheck },
  { id: "packages", label: "Audit Package Workspace", href: "/packages", category: "Output", icon: Package },
  { id: "governance", label: "Governance & Transparency Center", href: "/governance", category: "Output", icon: Scale },
  { id: "system-health", label: "System Health", href: "/system-health", category: "System", icon: Activity },
  { id: "settings", label: "Settings", href: "/settings", category: "System", icon: Settings },
];

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filtered = COMMANDS.filter(
    (c) =>
      c.label.toLowerCase().includes(query.toLowerCase()) ||
      c.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
      if (e.key === "Escape" && commandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  const handleSelect = (href: string) => {
    setCommandPaletteOpen(false);
    setQuery("");
    router.push(href);
  };

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <div className="command-overlay" onClick={() => setCommandPaletteOpen(false)}>
          <motion.div
            className="command-box"
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.15 }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
          >
            <div className="command-input-row">
              <Search size={18} className="text-[var(--color-text-tertiary)] flex-shrink-0" />
              <input
                autoFocus
                placeholder="Type a command or search screens…"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
              />
              <button
                className="p-1 btn-ghost rounded"
                onClick={() => setCommandPaletteOpen(false)}
                aria-label="Close command palette"
              >
                <X size={16} />
              </button>
            </div>

            <div className="command-results">
              {filtered.length === 0 ? (
                <div className="p-4 text-center text-xs text-[var(--color-text-tertiary)]">
                  No matching commands found.
                </div>
              ) : (
                filtered.map((cmd, index) => {
                  const Icon = cmd.icon;
                  const isSelected = index === selectedIndex;
                  return (
                    <div
                      key={cmd.id}
                      className={`command-item ${isSelected ? "selected" : ""}`}
                      onClick={() => handleSelect(cmd.href)}
                      onMouseEnter={() => setSelectedIndex(index)}
                    >
                      <Icon size={16} className="text-[var(--color-text-tertiary)] flex-shrink-0" />
                      <span className="flex-1 font-medium">{cmd.label}</span>
                      <span className="text-[10px] uppercase font-bold text-[var(--color-text-tertiary)] tracking-wider">
                        {cmd.category}
                      </span>
                    </div>
                  );
                })
              )}
            </div>

            <div className="command-footer">
              <span>
                <kbd>↑</kbd> <kbd>↓</kbd> navigate
              </span>
              <span>
                <kbd>↵</kbd> select
              </span>
              <span>
                <kbd>esc</kbd> close
              </span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
