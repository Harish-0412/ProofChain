"use client";

import { useEffect, useState } from "react";

/**
 * Returns true when the user prefers reduced motion.
 * All Framer Motion animations should be disabled when this returns true.
 */
export function useReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState(
    () =>
      typeof window !== "undefined"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = (e: MediaQueryListEvent) => setPrefersReduced(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return prefersReduced;
}
