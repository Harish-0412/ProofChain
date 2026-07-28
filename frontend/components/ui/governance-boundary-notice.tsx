"use client";

import { cn } from "@/lib/cn";
import { Info } from "lucide-react";

interface GovernanceBoundaryNoticeProps {
  message: string;
  className?: string;
}

export function GovernanceBoundaryNotice({
  message,
  className,
}: GovernanceBoundaryNoticeProps) {
  return (
    <div
      className={cn("governance-notice", className)}
      role="note"
      aria-label="Governance boundary notice"
    >
      <Info size={14} className="text-[var(--color-info)] flex-shrink-0 mt-0.5" />
      <p>{message}</p>
    </div>
  );
}
