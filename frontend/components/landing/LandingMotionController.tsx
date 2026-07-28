"use client";

import { useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function LandingMotionController() {
  useEffect(() => {
    const root = document.querySelector(".proof-landing");
    if (!root) return;

    const context = gsap.context(() => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        gsap.set("[data-motion]", { opacity: 1, x: 0, y: 0, scale: 1 });
        return;
      }

      gsap.utils.toArray<HTMLElement>("[data-motion='rise']").forEach((element) => {
        gsap.fromTo(
          element,
          { opacity: 0, y: 42 },
          {
            opacity: 1,
            y: 0,
            duration: 0.85,
            ease: "power3.out",
            scrollTrigger: {
              trigger: element,
              start: "top bottom-=12%",
              once: true,
            },
          },
        );
      });

      gsap.utils.toArray<HTMLElement>("[data-motion='stagger']").forEach((group) => {
        const items = group.querySelectorAll("[data-motion-item]");
        gsap.fromTo(
          items,
          { opacity: 0, y: 34, scale: 0.98 },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.72,
            stagger: 0.08,
            ease: "power3.out",
            scrollTrigger: {
              trigger: group,
              start: "top bottom-=12%",
              once: true,
            },
          },
        );
      });

      gsap.utils.toArray<HTMLElement>("[data-motion='line']").forEach((line) => {
        gsap.fromTo(
          line,
          { scaleX: 0, transformOrigin: "0% 50%" },
          {
            scaleX: 1,
            duration: 1.1,
            ease: "power2.inOut",
            scrollTrigger: {
              trigger: line,
              start: "top bottom-=8%",
              once: true,
            },
          },
        );
      });
    }, root);

    return () => context.revert();
  }, []);

  return null;
}
