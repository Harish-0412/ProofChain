"use client";

import { cn } from "@/lib/cn";

interface ConfidenceBadgeProps {
  value: number; // 0–100
  showBar?: boolean;
  size?: "sm" | "md";
  className?: string;
}

function getConfidenceVariant(value: number) {
  if (value >= 90) return { variant: "verified", label: "High" };
  if (value >= 70) return { variant: "warning", label: "Medium" };
  if (value >= 50) return { variant: "warning", label: "Low" };
  return { variant: "blocked", label: "Very Low" };
}

export function ConfidenceBadge({
  value,
  showBar = false,
  size = "md",
  className,
}: ConfidenceBadgeProps) {
  const { variant } = getConfidenceVariant(value);
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div
      className={cn("inline-flex items-center gap-2", className)}
      aria-label={`Confidence: ${clamped.toFixed(1)}%`}
    >
      <span
        className={cn(
          "badge",
          `badge-${variant}`,
          size === "sm" && "text-[10px] px-1.5 py-0.5"
        )}
      >
        {clamped.toFixed(1)}%
      </span>

      {showBar && (
        <div
          className="w-16 h-1.5 rounded-full bg-[var(--color-border)]"
          role="meter"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${clamped.toFixed(1)}% confidence`}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${clamped}%`,
              backgroundColor:
                variant === "verified"
                  ? "var(--color-verified)"
                  : variant === "blocked"
                  ? "var(--color-blocked)"
                  : "var(--color-warning)",
            }}
          />
        </div>
      )}
    </div>
  );
}
