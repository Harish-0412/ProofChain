// ProofChain Design Tokens
// "Institutional Evidence Graph" visual theme
// All values mirror the specification from the frontend implementation plan

export const colors = {
  // Primary
  deepNavy: "#0B1F33",
  evidenceBlue: "#2563EB",
  slate: "#475569",

  // Semantic
  verifiedGreen: "#16A34A",
  warningAmber: "#D97706",
  blockedRed: "#DC2626",
  reviewPurple: "#7C3AED",
  infoCyan: "#0891B2",

  // Background
  appBackground: "#F6F8FB",
  panelBackground: "#FFFFFF",
  darkBackground: "#09131F",
  darkPanel: "#0B1F33",
  border: "#D9E1EA",
  darkBorder: "#1E3A52",
} as const;

export const typography = {
  fontSans: "var(--font-inter)",
  fontMono: "var(--font-jetbrains)",
} as const;

// Agent status → semantic color mapping
export const agentStatusColors: Record<string, string> = {
  Created: "info",
  Planning: "info",
  Running: "info",
  "Waiting for Peer": "warning",
  "Waiting for Human": "warning",
  "Waiting for External Response": "warning",
  Replanning: "warning",
  Completed: "verified",
  "Completed with Warnings": "warning",
  Blocked: "blocked",
  Failed: "blocked",
  Cancelled: "slate",
};

// Issue severity → semantic color mapping
export const severityColors: Record<string, string> = {
  critical: "blocked",
  high: "blocked",
  medium: "warning",
  low: "info",
  informational: "slate",
};

// Navigation items
export const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { label: "Runs", href: "/runs", icon: "Play" },
  { label: "Agents", href: "/agents", icon: "Bot", sub: "agents" },
  { label: "Evidence", href: "/evidence", icon: "FileText" },
  { label: "Claims", href: "/claims", icon: "CheckSquare" },
  { label: "Issues", href: "/issues", icon: "AlertTriangle" },
  { label: "Tasks", href: "/tasks", icon: "ClipboardList" },
  { label: "Approvals", href: "/approvals", icon: "ShieldCheck" },
  { label: "Packages", href: "/packages", icon: "Package" },
  { label: "Governance", href: "/governance", icon: "Scale" },
  { label: "System Health", href: "/system-health", icon: "Activity" },
  { label: "Settings", href: "/settings", icon: "Settings" },
] as const;
