"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ShieldCheck, Check, X } from "lucide-react";

interface ActionDialogProps {
  isOpen: boolean;
  title: string;
  commandName: string;
  description: string;
  warningText?: string;
  onConfirm: (rationale: string) => void;
  onClose: () => void;
}

export function ActionDialog({
  isOpen,
  title,
  commandName,
  description,
  warningText,
  onConfirm,
  onClose,
}: ActionDialogProps) {
  const [rationale, setRationale] = useState("");

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-xs"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          className="relative w-full max-w-md card p-6 bg-[var(--color-panel-bg)] space-y-4 shadow-xl z-10"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          role="dialog"
          aria-modal="true"
          aria-label={title}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck size={20} className="text-[var(--color-evidence-blue)]" />
              <h3 className="text-heading text-base">{title}</h3>
            </div>
            <button className="p-1 btn-ghost rounded" onClick={onClose} aria-label="Close dialog">
              <X size={16} />
            </button>
          </div>

          <p className="text-xs text-[var(--color-text-secondary)]">{description}</p>

          <div className="p-2.5 rounded bg-[var(--color-border-subtle)] font-mono text-[11px] text-[var(--color-text-tertiary)]">
            Command: <strong>proofchain {commandName}</strong>
          </div>

          {warningText && (
            <div className="p-3 rounded bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start gap-2">
              <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
              <span>{warningText}</span>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-xs font-semibold text-[var(--color-text-primary)] block">
              Governance Rationale / Explanation *
            </label>
            <textarea
              required
              rows={3}
              className="input text-xs"
              placeholder="State the institutional reason for this governed action…"
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button className="btn btn-secondary btn-sm" onClick={onClose}>
              Cancel
            </button>
            <button
              disabled={!rationale.trim()}
              className="btn btn-primary btn-sm disabled:opacity-50"
              onClick={() => {
                onConfirm(rationale);
                onClose();
              }}
            >
              <Check size={14} />
              Confirm Action
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
