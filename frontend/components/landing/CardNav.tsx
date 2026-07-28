"use client";

import Link from "next/link";
import { useLayoutEffect, useRef, useState } from "react";
import { ArrowUpRight, ShieldCheck } from "lucide-react";
import { gsap } from "gsap";
import "./card-nav.css";

export interface CardNavItem {
  label: string;
  tone: "ink" | "blue" | "green";
  links: Array<{
    label: string;
    href: string;
    ariaLabel: string;
  }>;
}

interface CardNavProps {
  items: CardNavItem[];
}

export function CardNav({ items }: CardNavProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const navRef = useRef<HTMLElement>(null);
  const cardsRef = useRef<Array<HTMLDivElement | null>>([]);
  const timelineRef = useRef<gsap.core.Timeline | null>(null);

  const calculateHeight = () => {
    const nav = navRef.current;
    if (!nav) return 296;
    if (!window.matchMedia("(max-width: 720px)").matches) return 296;

    const content = nav.querySelector<HTMLElement>(".card-nav__content");
    return content ? 64 + content.scrollHeight + 12 : 430;
  };

  useLayoutEffect(() => {
    const nav = navRef.current;
    if (!nav) return;

    const cards = cardsRef.current.filter(Boolean);
    gsap.set(nav, { height: 64 });
    gsap.set(cards, { y: 36, opacity: 0 });

    const timeline = gsap
      .timeline({ paused: true })
      .to(nav, { height: calculateHeight, duration: 0.42, ease: "power3.out" })
      .to(
        cards,
        { y: 0, opacity: 1, duration: 0.36, ease: "power3.out", stagger: 0.07 },
        "-=0.18",
      );

    timelineRef.current = timeline;

    const handleResize = () => {
      if (nav.classList.contains("card-nav--open")) {
        gsap.set(nav, { height: calculateHeight() });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      timeline.kill();
      timelineRef.current = null;
    };
  }, [items]);

  const toggleMenu = () => {
    const timeline = timelineRef.current;
    if (!timeline) return;

    if (isExpanded) {
      setIsExpanded(false);
      timeline.reverse();
    } else {
      setIsExpanded(true);
      timeline.play(0);
    }
  };

  const closeMenu = () => {
    if (!isExpanded) return;
    setIsExpanded(false);
    timelineRef.current?.reverse();
  };

  return (
    <div className="card-nav-shell">
      <nav
        ref={navRef}
        className={`card-nav ${isExpanded ? "card-nav--open" : ""}`}
        aria-label="Primary navigation"
      >
        <div className="card-nav__top">
          <button
            type="button"
            className={`card-nav__menu ${isExpanded ? "card-nav__menu--open" : ""}`}
            onClick={toggleMenu}
            aria-label={isExpanded ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={isExpanded}
          >
            <span />
            <span />
          </button>

          <Link href="/landing" className="card-nav__brand" onClick={closeMenu}>
            <span className="card-nav__mark" aria-hidden="true">
              <ShieldCheck size={19} />
            </span>
            <span>ProofChain</span>
            <small>Governed assurance</small>
          </Link>

          <Link href="/dashboard" className="card-nav__cta">
            Open Dashboard
            <ArrowUpRight size={16} aria-hidden="true" />
          </Link>
        </div>

        <div className="card-nav__content" aria-hidden={!isExpanded}>
          {items.slice(0, 3).map((item, index) => (
            <div
              key={item.label}
              className={`card-nav__card card-nav__card--${item.tone}`}
              ref={(element) => {
                cardsRef.current[index] = element;
              }}
            >
              <span className="card-nav__label">{item.label}</span>
              <div className="card-nav__links">
                {item.links.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    aria-label={link.ariaLabel}
                    className="card-nav__link"
                    onClick={closeMenu}
                    tabIndex={isExpanded ? 0 : -1}
                  >
                    <ArrowUpRight size={14} aria-hidden="true" />
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </nav>
    </div>
  );
}
