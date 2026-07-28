"use client";

import { motion } from "framer-motion";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Info,
  Minus,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { badgeVariants } from "@/lib/animations";
import { useReducedMotion } from "@/hooks/use-reduced-motion";

type StatusVariant =
  | "verified"
  | "warning"
  | "blocked"
  | "review"
  | "info"
  | "slate"
  | "neutral";

interface StatusBadgeProps {
  status: string;
  variant?: StatusVariant;
  showIcon?: boolean;
  size?: "sm" | "md";
  animate?: boolean;
  className?: string;
}

const STATUS_MAP: Record<
  string,
  { variant: StatusVariant; label?: string }
> = {
  // Run status
  running: { variant: "info" },
  completed: { variant: "verified" },
  completed_with_warnings: { variant: "warning", label: "completed with warnings" },
  blocked: { variant: "blocked" },
  failed: { variant: "blocked" },
  pending: { variant: "slate" },
  draft: { variant: "slate" },
  waiting: { variant: "slate" },
  skipped: { variant: "slate" },
  returned: { variant: "warning" },

  // Evidence / claim status
  supported: { variant: "verified" },
  contradicted: { variant: "blocked" },
  "partially supported": { variant: "warning" },
  "needs review": { variant: "review" },
  verified: { variant: "verified" },
  registered: { variant: "info" },
  classified: { variant: "info" },
  unverified: { variant: "slate" },
  quarantined: { variant: "blocked" },
  stale: { variant: "warning" },

  // Issue status
  open: { variant: "blocked" },
  planned: { variant: "info" },
  assigned: { variant: "info" },
  "in progress": { variant: "info" },
  "evidence submitted": { variant: "warning" },
  "under revalidation": { variant: "review" },
  resolved: { variant: "verified" },
  reopened: { variant: "warning" },
  "awaiting approval": { variant: "review" },

  // Package
  ready: { variant: "verified" },
  "correction required": { variant: "blocked" },
  approved: { variant: "verified" },
  rejected: { variant: "blocked" },
  passed: { variant: "verified" },
  pass_for_human_approval: { variant: "review", label: "pass for human approval" },
  not_eligible: { variant: "warning", label: "not eligible" },
};

const VARIANT_ICONS: Record<StatusVariant, React.ReactNode> = {
  verified: <CheckCircle2 size={11} />,
  warning: <AlertTriangle size={11} />,
  blocked: <XCircle size={11} />,
  review: <Clock size={11} />,
  info: <Info size={11} />,
  slate: <Minus size={11} />,
  neutral: <Minus size={11} />,
};

export function StatusBadge({
  status,
  variant,
  showIcon = true,
  size = "md",
  animate = false,
  className,
}: StatusBadgeProps) {
  const prefersReduced = useReducedMotion();
  const normalizedStatus = status.toLowerCase();
  const resolved = STATUS_MAP[normalizedStatus];
  const finalVariant = variant ?? resolved?.variant ?? "neutral";

  const content = (
    <span
      className={cn(
        "badge",
        `badge-${finalVariant}`,
        size === "sm" && "text-[10px] px-1.5 py-0.5",
        className
      )}
      role="status"
      aria-label={`Status: ${status}`}
    >
      {showIcon && (
        <span aria-hidden="true">{VARIANT_ICONS[finalVariant]}</span>
      )}
      {resolved?.label ?? status.replaceAll("_", " ")}
    </span>
  );

  if (animate && !prefersReduced) {
    return (
      <motion.span
        variants={badgeVariants}
        initial="hidden"
        animate="visible"
        style={{ display: "inline-flex" }}
      >
        {content}
      </motion.span>
    );
  }

  return content;
}
