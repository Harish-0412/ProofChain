"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Archive,
  BadgeCheck,
  Boxes,
  BrainCircuit,
  FileSearch,
  Send,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

interface AgentDefinition {
  id: number;
  name: string;
  role: string;
}

interface AgentPhase {
  id: string;
  label: string;
  title: string;
  description: string;
  icon: LucideIcon;
  agents: AgentDefinition[];
}

const AGENT_PHASES: AgentPhase[] = [
  {
    id: "evidence",
    label: "Evidence foundation",
    title: "Collect and establish evidence",
    description:
      "Build the trusted evidence inventory, classify content, and test provenance before any institutional claim is evaluated.",
    icon: FileSearch,
    agents: [
      { id: 1, name: "Evidence Collector", role: "Discovers files, assigns durable identities, and records checksums." },
      { id: 2, name: "Evidence Classification", role: "Extracts content and maps evidence to requirements." },
      { id: 3, name: "Evidence Integrity", role: "Tests consistency, sufficiency, provenance, and defensibility." },
    ],
  },
  {
    id: "reasoning",
    label: "Evidence reasoning",
    title: "Test claims and expose gaps",
    description:
      "Turn broad accreditation statements into atomic claims, challenge them with evidence, and create canonical resolution work.",
    icon: BrainCircuit,
    agents: [
      { id: 4, name: "Claim Intelligence", role: "Judges atomic claims against support and counter-evidence." },
      { id: 5, name: "Adaptive Gap Resolution", role: "Creates gaps, dependencies, priorities, and projections." },
      { id: 6, name: "Accountability Ownership", role: "Maps governed issues to accountable institutional owners." },
    ],
  },
  {
    id: "resolution",
    label: "Resolution execution",
    title: "Coordinate correction and closure",
    description:
      "Route work to departments, govern response intake, and require targeted revalidation before an issue can close.",
    icon: BadgeCheck,
    agents: [
      { id: 7, name: "Department Liaison", role: "Builds tasks, communications, approval gates, and SLA monitoring." },
      { id: 8, name: "Closure Revalidation", role: "Revalidates corrections before changing issue state." },
    ],
  },
  {
    id: "audit",
    label: "Audit output",
    title: "Compose and challenge the package",
    description:
      "Freeze a traceable submission scope, assemble manifests, then simulate external audit failure modes before release.",
    icon: Archive,
    agents: [
      { id: 9, name: "Audit Package Composer", role: "Composes evidence, claim, privacy, and manifest artifacts." },
      { id: 10, name: "Adversarial Quality Review", role: "Challenges completeness before human release approval." },
    ],
  },
  {
    id: "governance",
    label: "Platform governance",
    title: "Operate under durable controls",
    description:
      "Persist state, resume safely, enforce access boundaries, deliver governed notifications, and defend the runtime.",
    icon: ShieldCheck,
    agents: [
      { id: 11, name: "Operational Persistence", role: "Synchronizes events, databases, snapshots, and recovery checks." },
      { id: 12, name: "Workflow Continuation", role: "Resumes interrupted work with bounded re-execution plans." },
      { id: 13, name: "Identity Authorization", role: "Evaluates identity, tenant, scope, and approval policy." },
      { id: 14, name: "Integration Notification", role: "Delivers idempotent governed notifications." },
      { id: 15, name: "Security Inspection", role: "Inspects untrusted content, privacy, and injection risk." },
      { id: 16, name: "Reliability Incident Response", role: "Detects incidents and records bounded remediation." },
    ],
  },
  {
    id: "institutional",
    label: "Institutional assurance",
    title: "Govern change and external handoff",
    description:
      "Control contract evolution, policy activation, tenant isolation, regulatory submission, evaluation, and cited knowledge retrieval.",
    icon: Send,
    agents: [
      { id: 17, name: "Schema Evolution", role: "Blocks unsafe artifact or contract evolution." },
      { id: 18, name: "Policy Lifecycle", role: "Validates policy versions, conflicts, and activation." },
      { id: 19, name: "Tenant Governance", role: "Enforces tenant isolation and sharing decisions." },
      { id: 20, name: "External Submission", role: "Refuses release without hash-bound approval." },
      { id: 21, name: "Continuous Evaluation", role: "Evaluates release quality and false-approval risk." },
      { id: 22, name: "Knowledge Retrieval", role: "Retrieves cited, policy-bound advisory knowledge." },
    ],
  },
];

export function AgentServices() {
  const [currentPhase, setCurrentPhase] = useState(0);
  const [progress, setProgress] = useState(0);
  const phaseRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const railRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setProgress((current) => (current >= 100 ? 100 : current + 1));
    }, 90);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (progress < 100) return;
    const timer = window.setTimeout(() => {
      setCurrentPhase((current) => (current + 1) % AGENT_PHASES.length);
      setProgress(0);
    }, 250);
    return () => window.clearTimeout(timer);
  }, [progress]);

  useEffect(() => {
    const active = phaseRefs.current[currentPhase];
    const rail = railRef.current;
    if (!active || !rail || window.matchMedia("(min-width: 901px)").matches) return;

    rail.scrollTo({
      left: active.offsetLeft - (rail.clientWidth - active.clientWidth) / 2,
      behavior: "smooth",
    });
  }, [currentPhase]);

  const phase = AGENT_PHASES[currentPhase];
  const PhaseIcon = phase.icon;

  return (
    <div className="agent-services">
      <div className="agent-services__rail" ref={railRef}>
        {AGENT_PHASES.map((item, index) => {
          const Icon = item.icon;
          const isActive = currentPhase === index;
          return (
            <button
              type="button"
              key={item.id}
              ref={(element) => {
                phaseRefs.current[index] = element;
              }}
              className={`agent-service-tab ${isActive ? "agent-service-tab--active" : ""}`}
              onClick={() => {
                setCurrentPhase(index);
                setProgress(0);
              }}
              aria-pressed={isActive}
            >
              <span className="agent-service-tab__icon" aria-hidden="true">
                <Icon size={18} />
              </span>
              <span className="agent-service-tab__copy">
                <strong>{item.label}</strong>
                <small>{item.agents.length} goal agents</small>
              </span>
              <span className="agent-service-tab__progress" aria-hidden="true">
                {isActive && (
                  <motion.span
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.1, ease: "linear" }}
                  />
                )}
              </span>
            </button>
          );
        })}
      </div>

      <motion.div
        className="agent-services__stage"
        key={phase.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <div className="agent-services__stage-header">
          <span className="agent-services__stage-icon" aria-hidden="true">
            <PhaseIcon size={22} />
          </span>
          <div>
            <span className="agent-services__eyebrow">
              Phase {currentPhase + 1} of {AGENT_PHASES.length}
            </span>
            <h3>{phase.title}</h3>
          </div>
        </div>
        <p className="agent-services__description">{phase.description}</p>
        <div className="agent-services__list">
          {phase.agents.map((agent) => (
            <Link href={`/agents/${agent.id}`} className="agent-services__agent" key={agent.id}>
              <span className="agent-services__number">{String(agent.id).padStart(2, "0")}</span>
              <span>
                <strong>{agent.name}</strong>
                <small>{agent.role}</small>
              </span>
              <Boxes size={15} aria-hidden="true" />
            </Link>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
