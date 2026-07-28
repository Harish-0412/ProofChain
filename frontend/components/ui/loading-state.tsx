"use client";

import { cn } from "@/lib/cn";

interface SkeletonProps {
  className?: string;
  lines?: number;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} aria-hidden="true" />;
}

export function SkeletonCard({ lines = 3 }: SkeletonProps) {
  return (
    <div className="card card-body space-y-3" aria-busy="true" aria-label="Loading">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-3 w-full" />
      {lines > 1 && <Skeleton className="h-3 w-5/6" />}
      {lines > 2 && <Skeleton className="h-3 w-4/6" />}
    </div>
  );
}

interface LoadingStateProps {
  message?: string;
  detail?: string;
  className?: string;
}

export function LoadingState({
  message = "Loading…",
  detail,
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn("state-container", className)}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      {/* Animated chain nodes */}
      <div className="flex items-center gap-1 mb-2" aria-hidden="true">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-1">
            <div
              className="chain-node w-3 h-3 rounded-full bg-[var(--color-evidence-blue)]"
              style={{ animationDelay: `${i * 0.3}s` }}
            />
            {i < 4 && (
              <div className="w-4 h-px bg-[var(--color-border)]" />
            )}
          </div>
        ))}
      </div>

      <p className="text-sm font-semibold text-[var(--color-text-primary)]">
        {message}
      </p>
      {detail && (
        <p className="text-xs text-[var(--color-text-tertiary)] max-w-xs">
          {detail}
        </p>
      )}
    </div>
  );
}
