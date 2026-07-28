"use client";

import { useEffect } from "react";
import { useUIStore } from "@/stores/ui-store";

/**
 * AppProviders — wraps the application with all global providers:
 * - Theme injection (data-theme attribute on <html>)
 * - Future: TanStack Query, auth context, etc.
 */
export function AppProviders({ children }: { children: React.ReactNode }) {
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return <>{children}</>;
}
