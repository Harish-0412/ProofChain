"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  BookOpenCheck,
  CheckCircle2,
  ClipboardCheck,
  FileCheck2,
  FileSearch,
  PackageCheck,
  ScanSearch,
  ShieldCheck,
} from "lucide-react";
import DotGrid from "@/components/ui/DotGrid";
import { AgentServices } from "@/components/landing/AgentServices";
import { CardNav, type CardNavItem } from "@/components/landing/CardNav";
import { GovernanceShowcase } from "@/components/landing/GovernanceShowcase";
import { LandingMotionController } from "@/components/landing/LandingMotionController";
import { MotionFooter } from "@/components/landing/MotionFooter";
import { ScrollFloat } from "@/components/landing/ScrollFloat";
import { ScrollReveal } from "@/components/landing/ScrollReveal";
import "./landing.css";

const NAV_ITEMS: CardNavItem[] = [
  {
    label: "Understand",
    tone: "ink",
    links: [
      { label: "Evidence workflow", href: "#workflow", ariaLabel: "View the evidence workflow" },
      { label: "22 goal agents", href: "#agents", ariaLabel: "Explore all 22 governed agents" },
      { label: "Governance controls", href: "#governance", ariaLabel: "Review governance controls" },
    ],
  },
  {
    label: "Inspect",
    tone: "blue",
    links: [
      { label: "Dashboard", href: "/dashboard", ariaLabel: "Open the ProofChain readiness dashboard" },
      { label: "Evidence register", href: "/evidence", ariaLabel: "Open the evidence register" },
      { label: "Agent records", href: "/agents", ariaLabel: "Open agent execution records" },
    ],
  },
  {
    label: "Govern",
    tone: "green",
    links: [
      { label: "Human approvals", href: "/approvals", ariaLabel: "Review pending human approvals" },
      { label: "Audit packages", href: "/packages", ariaLabel: "Inspect generated audit packages" },
      { label: "System health", href: "/system-health", ariaLabel: "Inspect platform health" },
    ],
  },
];

const WORKFLOW = [
  { label: "Discover", detail: "Approved source boundaries", icon: FileSearch },
  { label: "Understand", detail: "Extraction and classification", icon: ScanSearch },
  { label: "Verify", detail: "Integrity and claim support", icon: FileCheck2 },
  { label: "Resolve", detail: "Owned correction work", icon: ClipboardCheck },
  { label: "Revalidate", detail: "Targeted closure proof", icon: BadgeCheck },
  { label: "Package", detail: "Hash-bound audit output", icon: PackageCheck },
];

export default function LandingPage() {
  return (
    <main id="main-content" className="proof-landing">
      <LandingMotionController />
      <CardNav items={NAV_ITEMS} />

      <section className="proof-hero" aria-labelledby="proofchain-title">
        <div className="proof-hero__visual" aria-hidden="true">
          <DotGrid
            dotSize={5}
            gap={32}
            baseColor="#b7cad7"
            activeColor="#1565d8"
            proximity={190}
            shockRadius={280}
            shockStrength={7}
            resistance={900}
            returnDuration={1.4}
          />
        </div>
        <div className="proof-hero__wash" aria-hidden="true" />

        <div className="proof-hero__inner">
          <motion.div
            className="proof-hero__copy"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, ease: "easeOut" }}
          >
            <div className="proof-hero__kicker">
              <Activity size={15} aria-hidden="true" />
              Governed accreditation intelligence
            </div>
            <h1 id="proofchain-title">ProofChain</h1>
            <p className="proof-hero__statement">
              See how every source becomes evidence, every claim becomes a decision, and every
              decision remains open to inspection.
            </p>
            <div className="proof-hero__actions">
              <Link href="/dashboard" className="proof-button proof-button--primary">
                Open the Dashboard
                <ArrowRight size={17} aria-hidden="true" />
              </Link>
              <a href="#workflow" className="proof-button proof-button--secondary">
                Follow the evidence path
              </a>
            </div>
          </motion.div>

          <motion.div
            className="proof-hero__sequence"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.35 }}
            aria-label="ProofChain execution sequence"
          >
            <div className="proof-sequence__label">A governed run</div>
            {["Ingest", "Reason", "Coordinate", "Revalidate", "Approve"].map((step, index) => (
              <div className="proof-sequence__step" key={step}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{step}</strong>
                {index < 4 && <i aria-hidden="true" />}
              </div>
            ))}
          </motion.div>
        </div>

        <div className="proof-hero__facts" aria-label="ProofChain architecture facts">
          <div><strong>22</strong><span>Primary goal agents</span></div>
          <div><strong>6</strong><span>Governed lifecycle stages</span></div>
          <div><strong>SHA-256</strong><span>Linked evidence integrity</span></div>
          <div><strong>Human</strong><span>Release authority</span></div>
        </div>
      </section>

      <section id="workflow" className="proof-section proof-section--paper">
        <div className="proof-section__inner">
          <span className="proof-eyebrow">The evidence path</span>
          <ScrollFloat
            containerClassName="proof-section__heading"
            textClassName="proof-section__heading-text"
          >
            From source files to defensible decisions
          </ScrollFloat>
          <ScrollReveal
            containerClassName="proof-section__reveal"
            textClassName="proof-section__reveal-text"
          >
            ProofChain does not hide work behind a score. It preserves the chain of custody,
            reasoning, coordination, corrections, approvals, and unresolved uncertainty that
            produced the result.
          </ScrollReveal>

          <div
            className="proof-workflow"
            role="list"
            aria-label="Governed evidence lifecycle"
            data-motion="stagger"
          >
            {WORKFLOW.map((step, index) => {
              const Icon = step.icon;
              return (
                <div
                  className="proof-workflow__step"
                  role="listitem"
                  key={step.label}
                  data-motion-item
                >
                  <div className="proof-workflow__index">{String(index + 1).padStart(2, "0")}</div>
                  <div className="proof-workflow__icon" aria-hidden="true"><Icon size={19} /></div>
                  <strong>{step.label}</strong>
                  <span>{step.detail}</span>
                  {index < WORKFLOW.length - 1 && <i aria-hidden="true" />}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section id="agents" className="proof-section proof-section--ink">
        <div className="proof-section__inner">
          <span className="proof-eyebrow proof-eyebrow--light">Agent services</span>
          <ScrollFloat
            containerClassName="proof-section__heading proof-section__heading--light"
            textClassName="proof-section__heading-text"
            scrollStart="top bottom-=5%"
            scrollEnd="bottom center+=10%"
          >
            22 governed goal agents
          </ScrollFloat>
          <ScrollReveal
            containerClassName="proof-section__reveal proof-section__reveal--light"
            textClassName="proof-section__reveal-text"
            baseOpacity={0.22}
          >
            Six coordinated phases carry institutional evidence from collection through
            external handoff. Select a phase to inspect each agent and the bounded outcome it
            owns.
          </ScrollReveal>

          <div data-motion="rise">
            <AgentServices />
          </div>

          <div className="proof-section__action">
            <Link href="/agents" className="proof-button proof-button--light">
              Inspect live agent records
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      <section id="governance" className="proof-section proof-section--mint">
        <div className="proof-section__inner">
          <span className="proof-eyebrow">Transparent by architecture</span>
          <ScrollFloat
            containerClassName="proof-section__heading"
            textClassName="proof-section__heading-text"
          >
            Control without hidden state
          </ScrollFloat>
          <ScrollReveal
            containerClassName="proof-section__reveal"
            textClassName="proof-section__reveal-text"
          >
            The platform separates evidence, inference, counterfactual projections, and human
            authority so an operator can tell what happened, why it happened, and what still
            blocks readiness.
          </ScrollReveal>

          <GovernanceShowcase />

          <div className="proof-boundary" data-motion="rise">
            <ShieldCheck size={22} aria-hidden="true" />
            <div>
              <strong>Readiness is evidence-backed, never implied.</strong>
              <p>
                Current verified readiness and counterfactual projected readiness stay
                visibly separate until blocking gaps pass revalidation and governed approval.
              </p>
            </div>
            <CheckCircle2 size={20} aria-hidden="true" />
          </div>
        </div>
      </section>

      <section className="proof-section proof-section--closing">
        <div className="proof-section__inner proof-closing" data-motion="stagger">
          <BookOpenCheck size={30} aria-hidden="true" data-motion-item />
          <ScrollFloat
            containerClassName="proof-section__heading proof-section__heading--closing"
            textClassName="proof-section__heading-text"
            scrollStart="top bottom-=10%"
            scrollEnd="bottom center+=20%"
          >
            Open the Dashboard
          </ScrollFloat>
          <p data-motion-item>
            Inspect the active run, agent goals, event chain, evidence, issues, approvals,
            validation state, and package decision in one operational view.
          </p>
          <div className="proof-closing__actions" data-motion-item>
            <Link href="/dashboard" className="proof-button proof-button--primary">
              Enter ProofChain
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
            <Link href="/system-health" className="proof-button proof-button--secondary">
              Check system health
            </Link>
          </div>
        </div>
      </section>

      <MotionFooter />
    </main>
  );
}
