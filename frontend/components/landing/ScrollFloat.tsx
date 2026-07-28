"use client";

import { Fragment, useEffect, useMemo, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import "./scroll-float.css";

gsap.registerPlugin(ScrollTrigger);

interface ScrollFloatProps {
  children: string;
  containerClassName?: string;
  textClassName?: string;
  animationDuration?: number;
  ease?: string;
  scrollStart?: string;
  scrollEnd?: string;
  stagger?: number;
}

export function ScrollFloat({
  children,
  containerClassName = "",
  textClassName = "",
  animationDuration = 1,
  ease = "back.inOut(2)",
  scrollStart = "center bottom+=35%",
  scrollEnd = "bottom bottom-=25%",
  stagger = 0.025,
}: ScrollFloatProps) {
  const containerRef = useRef<HTMLHeadingElement>(null);
  const characters = useMemo(
    () =>
      children.split(" ").map((word, wordIndex, words) => (
        <Fragment key={`${word}-${wordIndex}`}>
          <span className="scroll-float__word" aria-hidden="true">
            {word.split("").map((character, characterIndex) => (
              <span
                className="scroll-float__char"
                key={`${character}-${wordIndex}-${characterIndex}`}
              >
                {character}
              </span>
            ))}
          </span>
          {wordIndex < words.length - 1 ? " " : null}
        </Fragment>
      )),
    [children],
  );

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const context = gsap.context(() => {
      const characterElements = element.querySelectorAll(".scroll-float__char");
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      if (reducedMotion) {
        gsap.set(characterElements, { opacity: 1, yPercent: 0, scaleX: 1, scaleY: 1 });
        return;
      }

      gsap.fromTo(
        characterElements,
        {
          opacity: 0,
          yPercent: 115,
          scaleY: 1.8,
          scaleX: 0.82,
          transformOrigin: "50% 0%",
        },
        {
          opacity: 1,
          yPercent: 0,
          scaleY: 1,
          scaleX: 1,
          duration: animationDuration,
          ease,
          stagger,
          scrollTrigger: {
            trigger: element,
            start: scrollStart,
            end: scrollEnd,
            scrub: true,
          },
        },
      );
    }, element);

    return () => context.revert();
  }, [animationDuration, ease, scrollEnd, scrollStart, stagger]);

  return (
    <h2
      ref={containerRef}
      aria-label={children}
      className={`scroll-float ${containerClassName}`}
    >
      <span className={`scroll-float__text ${textClassName}`}>{characters}</span>
    </h2>
  );
}
