"use client";
import { motion } from "framer-motion";
import { Settings } from "lucide-react";
import { containerVariants, itemVariants } from "@/lib/animations";
import { useUIStore } from "@/stores/ui-store";

export default function SettingsPage() {
  const { theme, setTheme } = useUIStore();

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={itemVariants}>
        <h1 className="text-heading">Settings</h1>
        <p className="text-body">Application preferences and configuration</p>
      </motion.div>

      <motion.div variants={itemVariants} className="card" style={{ maxWidth: 480 }}>
        <div className="card-header">
          <div className="flex items-center gap-2">
            <Settings size={15} className="text-[var(--color-evidence-blue)]" />
            <h2 className="text-sm font-semibold">Appearance</h2>
          </div>
        </div>
        <div className="card-body space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Theme</p>
              <p className="text-xs text-[var(--color-text-tertiary)]">Choose light or dark mode</p>
            </div>
            <div className="flex items-center gap-2">
              {["light", "dark"].map((t) => (
                <button
                  key={t}
                  onClick={() => setTheme(t as "light" | "dark")}
                  className={`btn btn-sm capitalize ${theme === t ? "btn-primary" : "btn-secondary"}`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
