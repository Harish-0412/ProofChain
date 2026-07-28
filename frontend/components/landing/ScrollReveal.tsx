"use client";

import { useEffect, useMemo, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import "./scroll-reveal.css";

gsap.registerPlugin(ScrollTrigger);

interface ScrollRevealProps {
  children: string;
  enableBlur?: boolean;
  baseOpacity?: number;
  baseRotation?: number;
  blurStrength?: number;
  containerClassName?: string;
  textClassName?: string;
  rotationEnd?: string;
  wordAnimationEnd?: string;
}

export function ScrollReveal({
  children,
  enableBlur = true,
  baseOpacity = 0.16,
  baseRotation = 2,
  blurStrength = 3,
  containerClassName = "",
  textClassName = "",
  rotationEnd = "bottom bottom-=10%",
  wordAnimationEnd = "bottom bottom-=8%",
}: ScrollRevealProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const words = useMemo(
    () =>
      children.split(/(\s+)/).map((word, index) =>
        /^\s+$/.test(word) ? (
          word
        ) : (
          <span className="scroll-reveal__word" key={`${word}-${index}`}>
            {word}
          </span>
        ),
      ),
    [children],
  );

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const context = gsap.context(() => {
      const wordElements = element.querySelectorAll(".scroll-reveal__word");
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      if (reducedMotion) {
        gsap.set(element, { rotate: 0 });
        gsap.set(wordElements, { opacity: 1, filter: "blur(0px)" });
        return;
      }

      gsap.fromTo(
        element,
        { transformOrigin: "0% 50%", rotate: baseRotation },
        {
          rotate: 0,
          ease: "none",
          scrollTrigger: {
            trigger: element,
            start: "top bottom",
            end: rotationEnd,
            scrub: true,
          },
        },
      );

      gsap.fromTo(
        wordElements,
        {
          opacity: baseOpacity,
          filter: enableBlur ? `blur(${blurStrength}px)` : "none",
        },
        {
          opacity: 1,
          filter: "blur(0px)",
          ease: "none",
          stagger: 0.045,
          scrollTrigger: {
            trigger: element,
            start: "top bottom-=18%",
            end: wordAnimationEnd,
            scrub: true,
          },
        },
      );
    }, element);

    return () => context.revert();
  }, [
    baseOpacity,
    baseRotation,
    blurStrength,
    enableBlur,
    rotationEnd,
    wordAnimationEnd,
  ]);

  return (
    <div ref={containerRef} className={`scroll-reveal ${containerClassName}`}>
      <p className={`scroll-reveal__text ${textClassName}`}>{words}</p>
    </div>
  );
}
