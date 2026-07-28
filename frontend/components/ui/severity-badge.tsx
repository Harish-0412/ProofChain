"use client";

import { Flame, AlertTriangle, Info, Minus } from "lucide-react";
import { cn } from "@/lib/cn";

type Severity = "critical" | "high" | "medium" | "low" | "informational";

interface SeverityBadgeProps {
  severity: Severity | string;
  className?: string;
}

const SEVERITY_CONFIG: Record<
  Severity,
  { variant: string; icon: React.ReactNode; label: string }
> = {
  critical: {
    variant: "badge-blocked",
    icon: <Flame size={11} />,
    label: "Critical",
  },
  high: {
    variant: "badge-blocked",
    icon: <AlertTriangle size={11} />,
    label: "High",
  },
  medium: {
    variant: "badge-warning",
    icon: <AlertTriangle size={11} />,
    label: "Medium",
  },
  low: {
    variant: "badge-info",
    icon: <Info size={11} />,
    label: "Low",
  },
  informational: {
    variant: "badge-slate",
    icon: <Minus size={11} />,
    label: "Informational",
  },
};

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const normalized = severity.toLowerCase() as Severity;
  const config = SEVERITY_CONFIG[normalized] ?? SEVERITY_CONFIG.informational;

  return (
    <span
      className={cn("badge", config.variant, className)}
      aria-label={`Severity: ${config.label}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  );
}
