"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/cn";

interface HashDisplayProps {
  hash: string;
  /** Number of chars to show at each end (default 8) */
  truncateAt?: number;
  showCopy?: boolean;
  className?: string;
}

export function HashDisplay({
  hash,
  truncateAt = 8,
  showCopy = true,
  className,
}: HashDisplayProps) {
  const [copied, setCopied] = useState(false);

  const displayHash =
    hash.length > truncateAt * 2 + 3
      ? `${hash.slice(0, truncateAt)}…${hash.slice(-truncateAt)}`
      : hash;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable
    }
  };

  return (
    <span
      className={cn("inline-flex items-center gap-1.5", className)}
      title={hash}
    >
      <code className="hash-display" aria-label={`Hash: ${hash}`}>
        {displayHash}
      </code>
      {showCopy && (
        <button
          onClick={handleCopy}
          className="p-0.5 rounded text-[var(--color-text-tertiary)] hover:text-[var(--color-evidence-blue)] transition-colors duration-150"
          aria-label={copied ? "Copied!" : "Copy full hash"}
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
        </button>
      )}
    </span>
  );
}
