# ProofChain Frontend & UI Gateway — Master Architecture & Implementation Report

> **Project:** ProofChain — Governed Accreditation Evidence Intelligence Platform  
> **Status:** All 6 Base Phases + 2 UI Clarity Upgrade Phases Fully Implemented & Verified  
> **Web Application URL:** http://localhost:3000  
> **Python UI Gateway API:** http://localhost:8000/ui-api  

---

## 1. Executive Summary & Core Design Architecture

The **ProofChain Frontend** is a calm, transparent, institutional evidence command center designed for managing accreditation readiness (NAAC Criteria 1–7, NBA Tier-1).

It interfaces with the existing ProofChain multi-agent engine through a strictly read-only Python FastAPI sidecar (`ui_gateway`).

### Core Safety Guarantee
The existing ProofChain engine, CLI, 10 specialized agents, JSON/JSONL artifacts, and workflow logic **remain 100% untouched**. The frontend provides:
- **Plain-language executive clarity** (What Happened / What Needs Attention / What Happens Next)
- **Operational View vs. Technical View** toggle mode
- **Role-based view filtering** (IQAC Admin, Department Coordinator, Evidence Owner, Auditor)
- **Full visual time-travel replay** driven by `workflow_events.jsonl`
- **Governed CLI command dispatching** via an allowlisted sidecar executor

---

## 2. Complete Phase Implementation Matrix

| Phase | Category | Core Feature Deliverables | Status |
|---|---|---|---|
| **Phase 1** | Design Foundation | "Institutional Evidence Command Center" design system (`globals.css`), CSS variables, tokens, badges, dark mode, accessible app shell. | ✓ Complete |
| **Phase 2** | Static Prototype | `MockDataProvider` (`lib/mock-data.ts`), Command Palette (`Cmd+K`), Notification Drawer, Agent Center, Issue Kanban, Claims Workspace. | ✓ Complete |
| **Phase 3** | Python UI Gateway | FastAPI sidecar in `ui_gateway/`, `PathGuard` traversal protection, `ArtifactReader` for 15+ backend files, `GatewayDataProvider`. | ✓ Complete |
| **Phase 4** | Real-Time & Replay | SSE Event Streamer `/ui-api/runs/{id}/events/stream`, `useEventStream` React hook, `ReplayController` (Play/Pause, Step, 1x/2x/5x), `AiExplanationCard`. | ✓ Complete |
| **Phase 5** | Operational Workspaces | `Evidence Explorer` hash inspector, `Task & Liaison Workspace` with draft previews, `Approval Center` separation-of-duties queue, `Closure Revalidation`. | ✓ Complete |
| **Phase 6** | Package & CLI Execution | `Audit Package Workspace` builder, `Adversarial Quality Review` inspector, `Governance Center` 10-checkpoint sync chain, allowlisted `CommandExecutor`. | ✓ Complete |
| **Upgrade 1** | Clarity Foundation | `CurrentStateHero` (1-sentence run summary), `NextBestActions` (Top 3 prioritized), `ProcessClarityPanel` (What Happened/Now/Next), `Operational/Technical Toggle`. | ✓ Complete |
| **Upgrade 2** | Diagrams & Workspaces | `AgentFocusGraph` (Interactive upstream/downstream highlights), `GoalSatisfactionMap`, `HumanReadableMessageCard`, `ClaimComparisonPanel` (Side-by-side claim matrix), `ApprovalImpactPreview` (Impact boundary preview modal), `Task Progress Roadmap`, `Package Journey Roadmap`. | ✓ Complete |

---

## 3. Complete File & Directory Inventory

```
ProofChain/
├── frontend/                                # Next.js 16 Web Application
│   ├── app/
│   │   ├── layout.tsx                       # Root layout (fonts, metadata, skip link, providers)
│   │   ├── page.tsx                         # Root redirect to /dashboard
│   │   ├── globals.css                      # Master design system CSS tokens & styles
│   │   ├── dashboard/
│   │   │   └── page.tsx                     # 5-Zone Executive Readiness Dashboard
│   │   ├── runs/
│   │   │   ├── page.tsx                     # Pipeline runs listing table
│   │   │   ├── agents/
│   │   │   │   └── page.tsx                 # Agent Collaboration Center (Story Mode, Pipeline, Goal, Message)
│   │   │   └── closure/
│   │   │       └── page.tsx                 # Stage 8 Closure & Revalidation Workspace
│   │   ├── evidence/
│   │   │   └── page.tsx                     # Registered Evidence Explorer & Trust Inspector
│   │   ├── claims/
│   │   │   └── page.tsx                     # Claim Defensibility Workspace (Side-by-Side Comparison)
│   │   ├── issues/
│   │   │   └── page.tsx                     # Canonical Issue Center (Prioritized List, Kanban, Table, Dependencies)
│   │   ├── tasks/
│   │   │   └── page.tsx                     # Task & Liaison Workspace with Task Progress Roadmap
│   │   ├── approvals/
│   │   │   └── page.tsx                     # Approval Center & Separation of Duties
│   │   ├── packages/
│   │   │   └── page.tsx                     # Audit Package Workspace & Package Journey Roadmap
│   │   ├── governance/
│   │   │   └── page.tsx                     # Governance Center & 10-Checkpoint Sync Chain
│   │   ├── system-health/
│   │   │   └── page.tsx                     # System Health & Backend Status
│   │   └── settings/
│   │       └── page.tsx                     # Settings & Theme Toggle
│   │
│   ├── components/
│   │   ├── clarity/
│   │   │   ├── process-clarity-panel.tsx    # Universal "What Happened / What Now / What Later" panel
│   │   │   ├── current-state-hero.tsx       # Dominant executive hero card with 1-sentence state summary
│   │   │   └── next-best-actions.tsx        # Top 3 prioritized actions with why it matters, owner & impact
│   │   ├── layout/
│   │   │   ├── sidebar.tsx                  # Collapsible sidebar with 5 navigation sections
│   │   │   ├── top-bar.tsx                  # TopBar with run selector, search, notifications, mode toggle
│   │   │   └── app-shell.tsx                # Page wrapper with animated transitions & modals
│   │   ├── ui/
│   │   │   ├── status-badge.tsx             # StatusBadge component (semantic colors + icons)
│   │   │   ├── confidence-badge.tsx         # ConfidenceBadge with progress meter
│   │   │   ├── severity-badge.tsx           # SeverityBadge (critical/high/medium/low)
│   │   │   ├── hash-display.tsx             # HashDisplay with truncation and copy-to-clipboard
│   │   │   ├── governance-boundary-notice.tsx # Inline governance boundary notice
│   │   │   ├── command-palette.tsx          # Cmd+K searchable command palette modal
│   │   │   ├── notification-panel.tsx       # Slide-in notification drawer
│   │   │   ├── action-dialog.tsx            # Governed CLI action confirmation modal
│   │   │   └── ai-explanation-card.tsx      # Transparent AI decision card
│   │   ├── agents/
│   │   │   ├── agent-detail-drawer.tsx      # Simplified 4-tab deep inspection drawer for agents
│   │   │   ├── agent-focus-graph.tsx        # Interactive 10-agent flow diagram with dependency highlighting
│   │   │   └── human-readable-message-card.tsx # Human-readable peer communication card
│   │   ├── claims/
│   │   │   └── claim-comparison-panel.tsx   # Side-by-side claim comparison card
│   │   ├── evidence/
│   │   │   └── evidence-trust-card.tsx      # Evidence file safety & trust status card
│   │   ├── approvals/
│   │   │   └── approval-impact-preview.tsx  # Modal displaying exact approval boundaries & rationale input
│   │   ├── goals/
│   │   │   └── goal-satisfaction-map.tsx    # Sub-goal success condition map
│   │   └── runs/
│   │       └── replay-controller.tsx        # Time-travel replay control bar
│   │
│   ├── lib/
│   │   ├── cn.ts                            # Tailwind class merge utility
│   │   ├── tokens.ts                        # Design system tokens as TypeScript constants
│   │   ├── animations.ts                    # Framer Motion animation variants & motion tokens
│   │   ├── data-provider.ts                 # Master TypeScript interface for all ProofChain artifacts
│   │   ├── mock-data.ts                     # MockDataProvider class with realistic MVP dataset
│   │   ├── gateway-provider.ts              # GatewayDataProvider class making HTTP calls to Python UI Gateway
│   │   └── get-data-provider.ts             # Factory function for data provider selection
│   │
│   ├── hooks/
│   │   ├── use-reduced-motion.ts            # System prefers-reduced-motion accessibility hook
│   │   └── use-event-stream.ts              # SSE event streaming hook with polling fallback
│   │
│   └── stores/
│       └── ui-store.ts                      # Zustand state store (theme, viewMode, activeRole, sidebar)
│
└── ui_gateway/                              # Python FastAPI UI Gateway Sidecar
    ├── app/
    │   ├── main.py                          # FastAPI entry point & API route definitions
    │   ├── config.py                        # Gateway settings, CORS origins, allowlisted commands
    │   └── services/
    │       ├── artifact_reader.py           # Read-only JSON/JSONL artifact parser
    │       ├── path_guard.py                # Security service preventing path traversal attacks
    │       ├── event_streamer.py            # SSE streamer tailing workflow_events.jsonl
    │       └── command_executor.py          # Governed CLI command execution dispatcher
    ├── pyproject.toml                       # Python package dependencies
    └── README.md                            # Setup and execution guide
```

---

## 4. Detailed Component Catalogue & Architectural Responsibilities

### Clarity & Executive Layer
1. **`CurrentStateHero` (`components/clarity/current-state-hero.tsx`):**
   - Dominant top card on Dashboard.
   - Explains run status in 1 clear plain-language sentence.
   - Shows Verified Readiness (73%), Projected Readiness (96%), Primary Blocker, and Action CTA.
2. **`NextBestActions` (`components/clarity/next-best-actions.tsx`):**
   - Displays top 3 prioritized actions only.
   - Shows action title, why it matters, responsible role, due date, readiness impact (+12%), and CTA button.
3. **`ProcessClarityPanel` (`components/clarity/process-clarity-panel.tsx`):**
   - Universal clarity panel used across Dashboard, Agent Center, Claims, Issues, Tasks, Approvals, and Packages.
   - Plainly states *What Happened*, *What Needs to Happen Now*, and *What Happens After That*.

### Agent Intelligence Layer
1. **`AgentCenterPage` (`app/runs/agents/page.tsx`):**
   - Default **Story Mode** displaying plain-language chronological agent activities.
   - Interactive **`AgentFocusGraph`** in Pipeline View highlighting upstream dependencies & downstream impact on click.
   - Interactive **`GoalSatisfactionMap`** in Goal Graph View.
   - **`HumanReadableMessageCard`** stream in Message Flow View.
2. **`AgentDetailDrawer` (`components/agents/agent-detail-drawer.tsx`):**
   - Simplified 4 top-level tabs: `Summary`, `Work & Plan`, `Collaboration`, and `Technical`.

### Operational Governance Workspaces
1. **`ClaimsPage` (`app/claims/page.tsx`) & `ClaimComparisonPanel`:**
   - Side-by-side comparison: *Original Claim* vs. *Verified Evidence Support* vs. *Recommended Defensible Wording*.
2. **`IssuesPage` (`app/issues/page.tsx`):**
   - Default **Prioritized Issue Action List** view + Kanban + Table + Dependency graph modes.
3. **`ApprovalsPage` (`app/approvals/page.tsx`) & `ApprovalImpactPreview`:**
   - Modal showing exact impact boundaries (*This WILL do X* vs. *This WILL NOT do Y*) and mandatory governance rationale input.
4. **`ClosurePage` (`app/runs/closure/page.tsx`):**
   - Revalidation matrix showing Before (73%), Delta (+9%), and Projected After (82%) readiness with regression alerts.
5. **`PackagesPage` (`app/packages/page.tsx`) & Package Journey Roadmap:**
   - 6-stage Package Journey roadmap, criterion package builder, quality score inspector (72/100), and CLI action triggers.
6. **`TasksPage` (`app/tasks/page.tsx`) & Task Progress Roadmap:**
   - 6-stage Task Progress roadmap (`Drafted → Activated → Delivered → Submitted → Revalidated → Resolved`), corrective task list, owner assignments, and draft notification previews.
7. **`EvidencePage` (`app/evidence/page.tsx`) & `EvidenceTrustCard`:**
   - Evidence trust cards displaying file safety, trust status, criterion mapping, SHA-256 hash, and integrity check results.

---

## 5. Security & Governed CLI Command Execution

The Python UI Gateway sidecar (`ui_gateway`) guarantees backend safety:
- **Strict Read-Only Access:** Files in `outputs/` are parsed without modification.
- **PathGuard Protection:** All `run_id` parameters validated to reject path traversal vectors (`../`).
- **Governed Command Allowlist:** Only 10 predefined commands can be dispatched:
  1. `run-pipeline`
  2. `validate-run`
  3. `approve-decision`
  4. `activate-resolution-task`
  5. `record-task-response`
  6. `revalidate-closure`
  7. `build-audit-package`
  8. `review-audit-package`
  9. `resume-run`
  10. `replay-run`

---

## 6. Verification & How to Run

### Automated Route Verification Results
- `/dashboard` → `200 OK` (CurrentStateHero, NextBestActions, ProcessClarityPanel)
- `/runs/agents` → `200 OK` (Story Mode, AgentFocusGraph, GoalSatisfactionMap, 4-Tab Drawer)
- `/claims` → `200 OK` (ClaimComparisonPanel, ProcessClarityPanel)
- `/issues` → `200 OK` (Prioritized Action List, ProcessClarityPanel)
- `/approvals` → `200 OK` (ApprovalImpactPreview, ProcessClarityPanel)
- `/evidence` → `200 OK` (EvidenceTrustCard, Hash Inspector, ProcessClarityPanel)
- `/tasks` → `200 OK` (Task Progress Roadmap, Draft Previews, ProcessClarityPanel)
- `/runs/closure` → `200 OK` (Closure Revalidation Matrix, ProcessClarityPanel)
- `/packages` → `200 OK` (Package Journey Roadmap, Quality Review)
- `/governance` → `200 OK` (10-Checkpoint Sync Chain)

### Execution Commands

**Web Frontend:**
```bash
cd c:\SideQuest\ProofChain\frontend
npm run dev
# Dashboard accessible at http://localhost:3000
```

**Python UI Gateway:**
```bash
cd c:\SideQuest\ProofChain\ui_gateway
uvicorn app.main:app --port 8000 --reload
# API accessible at http://localhost:8000/ui-api
```
