"use client";

import { motion } from "framer-motion";
import { Link2, Plus } from "lucide-react";
import { cn } from "@/lib/cn";
import { containerVariants, itemVariants } from "@/lib/animations";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  action,
  icon,
  className,
}: EmptyStateProps) {
  return (
    <motion.div
      className={cn("state-container", className)}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      role="region"
      aria-label={title}
    >
      {/* Linked-node motif illustration */}
      <motion.div variants={itemVariants} className="mb-2" aria-hidden="true">
        {icon ?? (
          <div className="relative">
            <div className="flex items-center gap-1.5">
              {["Req", "Claim", "Evidence", "Issue", "Pkg"].map((node, i) => (
                <div key={node} className="flex items-center gap-1.5">
                  <div className="w-8 h-8 rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-panel-bg)] flex items-center justify-center text-[9px] font-bold text-[var(--color-text-tertiary)]">
                    {node.slice(0, 3)}
                  </div>
                  {i < 4 && (
                    <div className="w-3 h-px bg-[var(--color-border)]" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      <motion.div
        variants={itemVariants}
        className="state-icon bg-[var(--color-border-subtle)]"
      >
        <Link2 size={22} className="text-[var(--color-text-tertiary)]" />
      </motion.div>

      <motion.h3
        variants={itemVariants}
        className="text-base font-semibold text-[var(--color-text-primary)]"
      >
        {title}
      </motion.h3>

      <motion.p
        variants={itemVariants}
        className="text-sm text-[var(--color-text-secondary)] max-w-sm"
      >
        {description}
      </motion.p>

      {action && (
        <motion.button
          variants={itemVariants}
          onClick={action.onClick}
          className="btn btn-primary mt-2"
        >
          <Plus size={15} />
          {action.label}
        </motion.button>
      )}
    </motion.div>
  );
}
