"use client";

import { AlertCircle, RefreshCw, Copy } from "lucide-react";
import { cn } from "@/lib/cn";

interface ErrorStateProps {
  title?: string;
  message: string;
  detail?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  detail,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn("state-container", className)}
      role="alert"
      aria-live="assertive"
    >
      <div className="state-icon bg-red-50">
        <AlertCircle size={22} className="text-[var(--color-blocked)]" />
      </div>

      <h3 className="text-base font-semibold text-[var(--color-text-primary)]">
        {title}
      </h3>
      <p className="text-sm text-[var(--color-text-secondary)] max-w-sm">
        {message}
      </p>

      {detail && (
        <p className="text-xs text-[var(--color-text-tertiary)] font-mono bg-[var(--color-border-subtle)] px-3 py-2 rounded-md max-w-sm">
          {detail}
        </p>
      )}

      {/* Governance note */}
      <p className="text-xs text-[var(--color-text-tertiary)] max-w-xs">
        The backend artifact was not changed. Try validation or inspect the
        technical trace.
      </p>

      <div className="flex items-center gap-2 mt-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="btn btn-primary btn-sm"
            aria-label="Retry operation"
          >
            <RefreshCw size={13} />
            Retry
          </button>
        )}
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => navigator.clipboard.writeText(message)}
          aria-label="Copy error reference"
        >
          <Copy size={13} />
          Copy Error
        </button>
      </div>
    </div>
  );
}
