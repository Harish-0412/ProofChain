"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Play,
  FileText,
  CheckSquare,
  AlertTriangle,
  ClipboardList,
  ShieldCheck,
  Package,
  Scale,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bot,
  Link2,
} from "lucide-react";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

const NAV_SECTIONS = [
  {
    label: "Overview",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Runs", href: "/runs", icon: Play },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { label: "Agents", href: "/agents", icon: Bot },
      { label: "Evidence", href: "/evidence", icon: FileText },
      { label: "Claims", href: "/claims", icon: CheckSquare },
    ],
  },
  {
    label: "Operations",
    items: [
      { label: "Issues", href: "/issues", icon: AlertTriangle },
      { label: "Tasks", href: "/tasks", icon: ClipboardList },
      { label: "Approvals", href: "/approvals", icon: ShieldCheck },
      { label: "Closure", href: "/runs/closure", icon: Link2 },
    ],
  },
  {
    label: "Output",
    items: [
      { label: "Packages", href: "/packages", icon: Package },
      { label: "Governance", href: "/governance", icon: Scale },
      { label: "System Health", href: "/system-health", icon: Activity },
    ],
  },
  {
    label: "System",
    items: [{ label: "Settings", href: "/settings", icon: Settings }],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, mobileSidebarOpen, setMobileSidebarOpen } =
    useUIStore();
  const prefersReduced = useReducedMotion();

  const sidebarVariants = {
    expanded: { width: 248 },
    collapsed: { width: 68 },
  };

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileSidebarOpen && (
          <motion.div
            className="fixed inset-0 z-30 bg-black/50 backdrop-blur-xs lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        className={cn("sidebar", mobileSidebarOpen && "mobile-open")}
        variants={prefersReduced ? undefined : sidebarVariants}
        animate={sidebarCollapsed ? "collapsed" : "expanded"}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        aria-label="Main navigation"
        role="navigation"
      >
        {/* Header Branding */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-[var(--color-sidebar-border)] min-h-[60px]">
          <div className="w-8 h-8 rounded-lg bg-[var(--color-evidence-blue)] flex items-center justify-center flex-shrink-0 shadow-sm">
            <Link2 size={16} className="text-white rotate-45" />
          </div>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -6 }}
                transition={{ duration: 0.15 }}
                className="overflow-hidden"
              >
                <p className="text-white font-bold text-sm leading-tight tracking-tight">
                  ProofChain
                </p>
                <p className="text-[var(--color-sidebar-text)] text-[10px] opacity-75 leading-tight">
                  Evidence Intelligence
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto py-3 space-y-3" aria-label="Primary navigation">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label}>
              {!sidebarCollapsed && (
                <p className="nav-section-label">{section.label}</p>
              )}
              <div className="space-y-0.5 mt-1">
                {section.items.map((item) => {
                  const isActive = pathname.startsWith(item.href);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn("nav-item", isActive && "active")}
                      aria-current={isActive ? "page" : undefined}
                      data-tooltip={sidebarCollapsed ? item.label : undefined}
                      onClick={() => setMobileSidebarOpen(false)}
                    >
                      <Icon size={18} className="nav-icon" aria-hidden="true" />
                      <span className="nav-label">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Desktop Collapse Toggle */}
        <div className="hidden lg:flex border-t border-[var(--color-sidebar-border)] p-3 items-center justify-between">
          {!sidebarCollapsed && (
            <span className="text-[10px] text-[var(--color-sidebar-text)] opacity-60 font-mono pl-1">
              v1.0.0 Governed
            </span>
          )}
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg text-[var(--color-sidebar-text)] hover:text-white hover:bg-[var(--color-sidebar-hover)] transition-all duration-150 ml-auto"
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </motion.aside>
    </>
  );
}
