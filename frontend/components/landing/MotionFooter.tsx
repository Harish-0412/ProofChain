"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { ArrowUpRight, ShieldCheck } from "lucide-react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const MARQUEE_ITEMS = [
  "Evidence integrity",
  "Traceable reasoning",
  "Governed closure",
  "Human approval",
  "Audit readiness",
];

function MagneticLink({
  href,
  children,
  primary = false,
}: {
  href: string;
  children: React.ReactNode;
  primary?: boolean;
}) {
  const linkRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 210, damping: 18, mass: 0.55 });
  const springY = useSpring(y, { stiffness: 210, damping: 18, mass: 0.55 });

  return (
    <motion.div
      ref={linkRef}
      style={{ x: springX, y: springY }}
      onPointerMove={(event) => {
        if (window.matchMedia("(pointer: coarse)").matches) return;
        const rect = event.currentTarget.getBoundingClientRect();
        x.set((event.clientX - rect.left - rect.width / 2) * 0.16);
        y.set((event.clientY - rect.top - rect.height / 2) * 0.16);
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      <Link
        href={href}
        className={`motion-footer__action ${primary ? "motion-footer__action--primary" : ""}`}
      >
        {children}
        <ArrowUpRight size={16} aria-hidden="true" />
      </Link>
    </motion.div>
  );
}

export function MotionFooter() {
  const footerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const footer = footerRef.current;
    if (!footer) return;

    const context = gsap.context(() => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

      gsap.fromTo(
        ".motion-footer__curtain",
        { yPercent: 18, clipPath: "inset(18% 0 0 0)" },
        {
          yPercent: 0,
          clipPath: "inset(0% 0 0 0)",
          ease: "none",
          scrollTrigger: {
            trigger: footer,
            start: "top bottom",
            end: "top center",
            scrub: true,
          },
        },
      );

      gsap.fromTo(
        ".motion-footer__wordmark span",
        { yPercent: 115, opacity: 0 },
        {
          yPercent: 0,
          opacity: 1,
          stagger: 0.045,
          duration: 0.85,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ".motion-footer__wordmark",
            start: "top bottom-=6%",
            once: true,
          },
        },
      );
    }, footer);

    return () => context.revert();
  }, []);

  return (
    <footer ref={footerRef} id="motion-footer" className="motion-footer">
      <div className="motion-footer__grid" aria-hidden="true">
        {Array.from({ length: 8 }, (_, index) => <span key={index} />)}
      </div>

      <div className="motion-footer__curtain">
        <div className="motion-footer__marquee" aria-hidden="true">
          <div>
            {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, index) => (
              <span key={`${item}-${index}`}>
                {item}
                <i />
              </span>
            ))}
          </div>
        </div>

        <div className="motion-footer__inner">
          <div className="motion-footer__intro">
            <span className="motion-footer__eyebrow">
              <ShieldCheck size={15} aria-hidden="true" />
              Evidence-backed assurance
            </span>
            <h2>Ready to inspect the chain?</h2>
            <p>
              Enter the live operational view or review the system boundary before the next
              governed run.
            </p>
            <div className="motion-footer__actions">
              <MagneticLink href="/dashboard" primary>Open Dashboard</MagneticLink>
              <MagneticLink href="/system-health">System health</MagneticLink>
            </div>
          </div>

          <div className="motion-footer__links">
            <div>
              <span>Inspect</span>
              <Link href="/evidence">Evidence</Link>
              <Link href="/claims">Claims</Link>
              <Link href="/agents">Agents</Link>
            </div>
            <div>
              <span>Resolve</span>
              <Link href="/issues">Issues</Link>
              <Link href="/tasks">Tasks</Link>
              <Link href="/approvals">Approvals</Link>
            </div>
            <div>
              <span>Assure</span>
              <Link href="/packages">Packages</Link>
              <Link href="/governance">Governance</Link>
              <Link href="/runs">Run history</Link>
            </div>
          </div>
        </div>

        <div className="motion-footer__wordmark" aria-label="ProofChain">
          {"PROOFCHAIN".split("").map((character, index) => (
            <span key={`${character}-${index}`} aria-hidden="true">{character}</span>
          ))}
        </div>

        <div className="motion-footer__bottom">
          <span>ProofChain - governed accreditation evidence intelligence</span>
          <span>Human authority preserved at every release boundary</span>
        </div>
      </div>
    </footer>
  );
}
