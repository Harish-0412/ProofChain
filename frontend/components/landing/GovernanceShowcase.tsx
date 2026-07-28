"use client";

import Image from "next/image";
import * as React from "react";
import { Fingerprint, GitBranch, ShieldCheck, UserCheck } from "lucide-react";

interface GovernanceProject {
  title: string;
  image: string;
  category: string;
  code: string;
  description: string;
  signal: string;
}

const publicAsset = (path: string) =>
  `${process.env.NEXT_PUBLIC_BASE_PATH || ""}${path}`;

const GOVERNANCE_PROJECTS: GovernanceProject[] = [
  {
    title: "Reasoning you can inspect",
    image: publicAsset("/images/governance/reasoning-chain.png"),
    category: "Inspectable cognition",
    code: "GOAL-PLAN-PROOF",
    description:
      "Interpreted intent, hypotheses, plan criticism, actions, observations, uncertainty, and completion proof remain visible.",
    signal: "Goal -> Plan -> Action -> Proof",
  },
  {
    title: "Evidence you can trace",
    image: publicAsset("/images/governance/evidence-custody.png"),
    category: "Evidence lineage",
    code: "SOURCE-HASH-DECISION",
    description:
      "Durable identities, SHA-256 hashes, canonical issue IDs, and event checkpoints keep each decision attached to its source.",
    signal: "Source -> Claim -> Decision",
  },
  {
    title: "Authority that stays human",
    image: publicAsset("/images/governance/human-authority.png"),
    category: "Governed authority",
    code: "HUMAN-RELEASE-GATE",
    description:
      "Closure, package release, and external submission remain scoped, hash-bound human approval decisions.",
    signal: "Recommendation -> Approval",
  },
];

const CONFIG = {
  scrollSpeed: 0.72,
  lerpFactor: 0.075,
  bufferSize: 4,
  maxVelocity: 150,
  snapDuration: 520,
  minimapItemHeight: 92,
};

const lerp = (start: number, end: number, factor: number) =>
  start + (end - start) * factor;

const normalizeIndex = (index: number) =>
  ((index % GOVERNANCE_PROJECTS.length) + GOVERNANCE_PROJECTS.length) %
  GOVERNANCE_PROJECTS.length;

const getProject = (index: number) => GOVERNANCE_PROJECTS[normalizeIndex(index)];

const getProjectNumber = (index: number) =>
  String(normalizeIndex(index) + 1).padStart(2, "0");

export function GovernanceShowcase() {
  const [visibleRange, setVisibleRange] = React.useState({
    min: -CONFIG.bufferSize,
    max: CONFIG.bufferSize,
  });
  const [activeIndex, setActiveIndex] = React.useState(0);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const projectsRef = React.useRef<Map<number, HTMLDivElement>>(new Map());
  const minimapRef = React.useRef<Map<number, HTMLButtonElement>>(new Map());
  const infoRef = React.useRef<Map<number, HTMLDivElement>>(new Map());
  const navigateRef = React.useRef<(index: number) => void>(() => undefined);

  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const runtime = {
      currentY: 0,
      targetY: 0,
      isDragging: false,
      isSnapping: false,
      isVisible: true,
      lastInputTime: performance.now(),
      dragStartY: 0,
      dragStartScrollY: 0,
      projectHeight: Math.max(container.clientHeight, 1),
      snapStartTime: 0,
      snapStartY: 0,
      snapTargetY: 0,
    };

    let renderedRange = {
      min: -CONFIG.bufferSize,
      max: CONFIG.bufferSize,
    };
    let lastActiveIndex = 0;
    let animationFrame = 0;

    const beginSnap = (targetY: number) => {
      runtime.isSnapping = true;
      runtime.snapStartTime = performance.now();
      runtime.snapStartY = runtime.targetY;
      runtime.snapTargetY = targetY;
    };

    const snapToNearestProject = () => {
      const logicalIndex = Math.round(-runtime.targetY / runtime.projectHeight);
      beginSnap(-logicalIndex * runtime.projectHeight);
    };

    navigateRef.current = (logicalIndex: number) => {
      runtime.isDragging = false;
      runtime.lastInputTime = performance.now();
      beginSnap(-logicalIndex * runtime.projectHeight);
    };

    const updatePositions = () => {
      const minimapY =
        (runtime.currentY * CONFIG.minimapItemHeight) / runtime.projectHeight;
      const minimapOffset = CONFIG.minimapItemHeight;

      projectsRef.current.forEach((element, index) => {
        const y = index * runtime.projectHeight + runtime.currentY;
        element.style.transform = `translate3d(0, ${y}px, 0)`;

        const image = element.querySelector("img");
        if (image) {
          const parallax = (-runtime.currentY - index * runtime.projectHeight) * 0.16;
          image.style.transform = `translate3d(0, ${parallax}px, 0) scale(1.18)`;
        }
      });

      minimapRef.current.forEach((element, index) => {
        const y = index * CONFIG.minimapItemHeight + minimapY + minimapOffset;
        element.style.transform = `translate3d(0, ${y}px, 0)`;

        const image = element.querySelector("img");
        if (image) {
          const parallax = (-minimapY - index * CONFIG.minimapItemHeight) * 0.12;
          image.style.transform = `translate3d(0, ${parallax}px, 0) scale(1.22)`;
        }
      });

      infoRef.current.forEach((element, index) => {
        const y = index * CONFIG.minimapItemHeight + minimapY + minimapOffset;
        element.style.transform = `translate3d(0, ${y}px, 0)`;
      });
    };

    const animate = (now: number) => {
      if (
        !runtime.isSnapping &&
        !runtime.isDragging &&
        now - runtime.lastInputTime > 110
      ) {
        const snapPoint =
          -Math.round(-runtime.targetY / runtime.projectHeight) * runtime.projectHeight;
        if (Math.abs(runtime.targetY - snapPoint) > 0.75) beginSnap(snapPoint);
      }

      if (runtime.isSnapping) {
        const progress = Math.min(
          (now - runtime.snapStartTime) / CONFIG.snapDuration,
          1,
        );
        const eased = 1 - Math.pow(1 - progress, 3);
        runtime.targetY =
          runtime.snapStartY +
          (runtime.snapTargetY - runtime.snapStartY) * eased;
        if (progress >= 1) runtime.isSnapping = false;
      }

      if (!runtime.isDragging) {
        runtime.currentY = lerp(
          runtime.currentY,
          runtime.targetY,
          CONFIG.lerpFactor,
        );
      }

      if (runtime.isVisible) updatePositions();

      const logicalIndex = Math.round(-runtime.targetY / runtime.projectHeight);
      const normalized = normalizeIndex(logicalIndex);
      if (normalized !== lastActiveIndex) {
        lastActiveIndex = normalized;
        setActiveIndex(normalized);
      }

      const nextRange = {
        min: logicalIndex - CONFIG.bufferSize,
        max: logicalIndex + CONFIG.bufferSize,
      };
      if (
        nextRange.min !== renderedRange.min ||
        nextRange.max !== renderedRange.max
      ) {
        renderedRange = nextRange;
        setVisibleRange(nextRange);
      }

      animationFrame = window.requestAnimationFrame(animate);
    };

    const handleWheel = (event: WheelEvent) => {
      event.preventDefault();
      runtime.isSnapping = false;
      runtime.lastInputTime = performance.now();
      const delta = Math.max(
        Math.min(event.deltaY * CONFIG.scrollSpeed, CONFIG.maxVelocity),
        -CONFIG.maxVelocity,
      );
      runtime.targetY -= delta;
    };

    const handlePointerDown = (event: PointerEvent) => {
      if (event.button !== 0) return;
      runtime.isDragging = true;
      runtime.isSnapping = false;
      runtime.dragStartY = event.clientY;
      runtime.dragStartScrollY = runtime.targetY;
      runtime.lastInputTime = performance.now();
      container.setPointerCapture(event.pointerId);
    };

    const handlePointerMove = (event: PointerEvent) => {
      if (!runtime.isDragging) return;
      event.preventDefault();
      runtime.targetY =
        runtime.dragStartScrollY + (event.clientY - runtime.dragStartY) * 1.35;
      runtime.currentY = lerp(runtime.currentY, runtime.targetY, 0.22);
      runtime.lastInputTime = performance.now();
    };

    const handlePointerUp = (event: PointerEvent) => {
      if (!runtime.isDragging) return;
      runtime.isDragging = false;
      runtime.lastInputTime = performance.now();
      if (container.hasPointerCapture(event.pointerId)) {
        container.releasePointerCapture(event.pointerId);
      }
      snapToNearestProject();
    };

    const resizeObserver = new ResizeObserver(() => {
      const previousHeight = runtime.projectHeight;
      const nextHeight = Math.max(container.clientHeight, 1);
      if (previousHeight === nextHeight) return;

      const logicalPosition = -runtime.targetY / previousHeight;
      runtime.projectHeight = nextHeight;
      runtime.targetY = -logicalPosition * nextHeight;
      runtime.currentY = runtime.targetY;
      updatePositions();
    });

    const visibilityObserver = new IntersectionObserver(
      ([entry]) => {
        runtime.isVisible = entry.isIntersecting;
      },
      { threshold: 0.02 },
    );

    container.addEventListener("wheel", handleWheel, { passive: false });
    container.addEventListener("pointerdown", handlePointerDown);
    container.addEventListener("pointermove", handlePointerMove);
    container.addEventListener("pointerup", handlePointerUp);
    container.addEventListener("pointercancel", handlePointerUp);
    resizeObserver.observe(container);
    visibilityObserver.observe(container);
    updatePositions();
    animationFrame = window.requestAnimationFrame(animate);

    return () => {
      container.removeEventListener("wheel", handleWheel);
      container.removeEventListener("pointerdown", handlePointerDown);
      container.removeEventListener("pointermove", handlePointerMove);
      container.removeEventListener("pointerup", handlePointerUp);
      container.removeEventListener("pointercancel", handlePointerUp);
      resizeObserver.disconnect();
      visibilityObserver.disconnect();
      window.cancelAnimationFrame(animationFrame);
      navigateRef.current = () => undefined;
    };
  }, []);

  const indices = React.useMemo(() => {
    const result: number[] = [];
    for (let index = visibleRange.min; index <= visibleRange.max; index += 1) {
      result.push(index);
    }
    return result;
  }, [visibleRange]);

  const activeProject = GOVERNANCE_PROJECTS[activeIndex];
  const ActiveIcon = [GitBranch, Fingerprint, UserCheck][activeIndex];

  return (
    <div
      ref={containerRef}
      className="governance-parallax"
      data-motion="rise"
      tabIndex={0}
      aria-label="Interactive governance controls"
    >
      <div className="governance-parallax__projects" aria-live="off">
        {indices.map((index) => {
          const project = getProject(index);
          return (
            <div
              key={index}
              className="governance-parallax__project"
              ref={(element) => {
                if (element) projectsRef.current.set(index, element);
                else projectsRef.current.delete(index);
              }}
              aria-hidden={normalizeIndex(index) !== activeIndex}
            >
              <Image
                src={project.image}
                alt=""
                fill
                sizes="(max-width: 720px) calc(100vw - 32px), 1180px"
                loading={index === 0 ? "eager" : "lazy"}
                fetchPriority={index === 0 ? "high" : "auto"}
                draggable={false}
                unoptimized
              />
            </div>
          );
        })}
      </div>

      <div className="governance-parallax__scrim" aria-hidden="true" />

      <div className="governance-parallax__topbar">
        <span>
          <ShieldCheck size={15} aria-hidden="true" />
          Governance control viewer
        </span>
        <code>{activeProject.code}</code>
      </div>

      <div className="governance-parallax__active">
        <div
          key={activeProject.code}
          className="governance-parallax__active-content"
        >
          <span>{getProjectNumber(activeIndex)} / 03</span>
          <div className="governance-parallax__active-icon" aria-hidden="true">
            <ActiveIcon size={20} />
          </div>
          <h3>{activeProject.title}</h3>
          <p>{activeProject.description}</p>
          <code>{activeProject.signal}</code>
        </div>
      </div>

      <div className="governance-minimap" aria-label="Governance control minimap">
        <div className="governance-minimap__viewport" aria-hidden="true" />
        <div className="governance-minimap__images">
          {indices.map((index) => {
            const project = getProject(index);
            return (
              <button
                type="button"
                key={index}
                className="governance-minimap__image"
                ref={(element) => {
                  if (element) minimapRef.current.set(index, element);
                  else minimapRef.current.delete(index);
                }}
                onClick={() => navigateRef.current(index)}
                aria-label={`Show ${project.title}`}
              >
                <Image
                  src={project.image}
                  alt=""
                  fill
                  sizes="88px"
                  draggable={false}
                  unoptimized
                />
              </button>
            );
          })}
        </div>

        <div className="governance-minimap__info" aria-live="polite">
          {indices.map((index) => {
            const project = getProject(index);
            return (
              <div
                key={index}
                className="governance-minimap__info-item"
                ref={(element) => {
                  if (element) infoRef.current.set(index, element);
                  else infoRef.current.delete(index);
                }}
                aria-hidden={normalizeIndex(index) !== activeIndex}
              >
                <div>
                  <strong>{getProjectNumber(index)}</strong>
                  <span>{project.title}</span>
                </div>
                <div>
                  <span>{project.category}</span>
                  <code>{project.code}</code>
                </div>
                <p>{project.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
