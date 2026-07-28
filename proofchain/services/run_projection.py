"""Artifact-backed read projections for APIs and operator interfaces."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from proofchain.core.paths import RUNS_DIR


PRIMARY_AGENT_ORDER = [
    "evidence_collector",
    "evidence_classification",
    "evidence_integrity",
    "claim_intelligence",
    "adaptive_gap_resolution",
    "accountability_ownership",
    "department_liaison",
    "closure_revalidation",
    "audit_package_composer",
    "adversarial_quality_review",
    "operational_persistence",
    "workflow_continuation",
    "identity_authorization",
    "integration_notification",
    "security_inspection",
    "reliability_incident_response",
    "schema_evolution",
    "policy_lifecycle",
    "tenant_governance",
    "external_submission",
    "continuous_evaluation",
    "knowledge_retrieval",
]

AGENT_RUNTIME_DIRECTORIES = {
    "evidence_collector": "collector",
    "evidence_classification": "classification",
    "evidence_integrity": "integrity",
}

AGENT_METADATA = {
    "evidence_collector": (
        "Evidence foundation",
        "Discovers approved source files, assigns immutable evidence identities, and records checksums and acquisition outcomes.",
    ),
    "evidence_classification": (
        "Evidence foundation",
        "Extracts supported content, classifies each record, and maps evidence to accreditation requirements.",
    ),
    "evidence_integrity": (
        "Evidence foundation",
        "Tests integrity, consistency, sufficiency, provenance, and defensibility across evidence bundles.",
    ),
    "claim_intelligence": (
        "Evidence reasoning",
        "Decomposes institutional claims and judges each atomic claim against supporting and counter-evidence.",
    ),
    "adaptive_gap_resolution": (
        "Resolution planning",
        "Converts evidence and claim failures into canonical gaps, priorities, dependencies, and readiness projections.",
    ),
    "accountability_ownership": (
        "Resolution planning",
        "Maps governed issues to accountable institutional owners and validates assignment boundaries.",
    ),
    "department_liaison": (
        "Resolution execution",
        "Builds governed resolution tasks, communications, approval gates, response intake, and SLA monitoring.",
    ),
    "closure_revalidation": (
        "Resolution execution",
        "Revalidates submitted corrections and changes issue state only after closure conditions pass.",
    ),
    "audit_package_composer": (
        "Audit output",
        "Freezes package scope and composes traceable evidence, claim, privacy, and manifest artifacts.",
    ),
    "adversarial_quality_review": (
        "Audit output",
        "Challenges package completeness and simulates audit failure modes before human release approval.",
    ),
    "operational_persistence": (
        "Platform operations",
        "Synchronizes the append-only event stream, operational database, snapshots, and recovery checks.",
    ),
    "workflow_continuation": (
        "Platform operations",
        "Resumes interrupted work from durable state and creates bounded re-execution plans.",
    ),
    "identity_authorization": (
        "Access governance",
        "Evaluates identity, tenant, scope, permission, and approval policy before controlled actions.",
    ),
    "integration_notification": (
        "Platform operations",
        "Delivers idempotent governed notifications through configured adapters and records outcomes.",
    ),
    "security_inspection": (
        "Platform assurance",
        "Inspects untrusted content, prompt-injection indicators, privacy boundaries, and security policy.",
    ),
    "reliability_incident_response": (
        "Platform assurance",
        "Detects runtime incidents, evaluates recovery posture, and records bounded remediation decisions.",
    ),
    "schema_evolution": (
        "Platform assurance",
        "Checks schema compatibility and blocks unsafe artifact or contract evolution.",
    ),
    "policy_lifecycle": (
        "Policy governance",
        "Validates policy versions, conflicts, activation decisions, and historical decision preservation.",
    ),
    "tenant_governance": (
        "Access governance",
        "Enforces tenant isolation and evaluates cross-boundary access and sharing decisions.",
    ),
    "external_submission": (
        "External lifecycle",
        "Determines submission eligibility and refuses release without the required hash-bound approval.",
    ),
    "continuous_evaluation": (
        "Platform assurance",
        "Evaluates release quality, false approval risk, false closure risk, and agentic precision.",
    ),
    "knowledge_retrieval": (
        "Governed intelligence",
        "Retrieves policy-bound advisory knowledge with citations, conflict checks, and evidence separation.",
    ),
}


class RunProjectionService:
    """Build stable UI/API shapes without changing source artifacts."""

    def __init__(self, runs_dir: Path | None = None):
        self.runs_dir = (runs_dir or RUNS_DIR).resolve()

    def list_runs(self) -> list[dict[str, Any]]:
        if not self.runs_dir.is_dir():
            return []
        results = []
        for path in self.runs_dir.iterdir():
            if not path.is_dir() or path.name.startswith("."):
                continue
            if not (path / "run_manifest.json").is_file():
                continue
            results.append(self.run_summary(path.name))
        return sorted(
            results,
            key=lambda item: item.get("startedAt") or "",
            reverse=True,
        )

    def run_exists(self, run_id: str) -> bool:
        return self._run_dir(run_id).is_dir()

    def run_summary(self, run_id: str) -> dict[str, Any]:
        pipeline = self._json(run_id, "pipeline_result.json", {})
        manifest = self._json(run_id, "run_manifest.json", {})
        portfolio = self._json(run_id, "gap_resolution_portfolio.json", {}).get(
            "portfolio", {}
        )
        issues = self.issues(run_id)
        workflow = manifest.get("workflow", {})
        departments = pipeline.get("department_scope") or workflow.get(
            "department_scope", []
        )
        started = pipeline.get("started_at") or manifest.get("created_at")
        completed = pipeline.get("completed_at") or manifest.get("updated_at")
        duration_ms = pipeline.get("duration_ms")
        return {
            "id": run_id,
            "department": ", ".join(departments) if departments else "Unknown",
            "framework": manifest.get("framework", "NAAC"),
            "academicYear": pipeline.get("academic_year")
            or workflow.get("academic_year", "Unknown"),
            "status": pipeline.get("status") or manifest.get("status", "pending"),
            "startedAt": started,
            "completedAt": completed,
            "duration": self._duration(duration_ms),
            "verifiedReadiness": portfolio.get(
                "current_verified_readiness",
                portfolio.get("current_readiness", 0.0),
            ),
            "projectedReadiness": portfolio.get("projected_readiness", 0.0),
            "projectionType": portfolio.get("projection_type", "counterfactual"),
            "projectionAssumptions": portfolio.get("projection_assumptions", []),
            "openIssues": sum(item.get("status") != "resolved" for item in issues),
            "blockingIssues": sum(
                bool(item.get("blocking", True)) and item.get("status") != "resolved"
                for item in issues
            ),
        }

    def dashboard_metrics(self, run_id: str) -> dict[str, Any]:
        run = self.run_summary(run_id)
        evidence = self.evidence(run_id)
        claims = self.claims(run_id)
        reviews = self._json(run_id, "human_review_queue.json", [])
        approvals = self.approvals(run_id)
        return {
            "run": run,
            "verifiedReadiness": run["verifiedReadiness"],
            "projectedReadiness": run["projectedReadiness"],
            "openIssues": run["openIssues"],
            "blockingIssues": run["blockingIssues"],
            "claimsForReview": sum(item.get("reviewRequired", False) for item in claims),
            "pendingApprovals": sum(
                item.get("status") in {"pending", "PENDING"} for item in approvals
            )
            + len(reviews),
            "agentPipelineHealth": (
                "blocked"
                if run["status"] == "blocked"
                else "degraded"
                if run["status"] in {"completed_with_warnings", "failed"}
                else "healthy"
            ),
            "totalEvidence": len(evidence),
            "verifiedEvidence": sum(
                item.get("status")
                in {"registered", "classified", "verified", "completed"}
                for item in evidence
            ),
        }

    def agents(self, run_id: str) -> list[dict[str, Any]]:
        registry = self._json(run_id, "component_registry.json", {}).get(
            "components", []
        )
        components = {
            item.get("component_id"): item
            for item in registry
            if item.get("component_type") == "goal_agent"
        }
        decisions = self._jsonl(run_id, "agent_decisions.jsonl")
        latest = {}
        execution_counts = Counter()
        for item in decisions:
            name = item.get("agent_name")
            if name:
                latest[name] = item
                execution_counts[name] += 1
        messages = self._jsonl(run_id, "coordination/messages.jsonl")
        scorecards = self._json(run_id, "agentic_scorecards.json", [])
        scores: dict[str, float] = {}
        for card in scorecards:
            values = [
                value
                for key, value in card.items()
                if key not in {"agent_name", "run_id", "schema_version"}
                and isinstance(value, (int, float))
            ]
            if values:
                scores[card.get("agent_name", "")] = round(
                    sum(values) / len(values), 4
                )

        results = []
        for index, name in enumerate(PRIMARY_AGENT_ORDER, 1):
            decision = latest.get(name, {})
            component = components.get(name, {})
            layer, description = AGENT_METADATA.get(
                name, ("Governed agent", "Primary governed goal agent.")
            )
            raw_status = decision.get("decision", "waiting")
            status = {
                "completed_with_warnings": "warning",
                "needs_human_review": "warning",
                "failed": "blocked",
            }.get(raw_status, raw_status)
            results.append(
                {
                    "id": index,
                    "slug": name,
                    "name": name.replace("_", " ").title(),
                    "shortName": "".join(
                        part[0] for part in name.split("_")
                    ).upper()[:4],
                    "role": (
                        description
                        if component.get("description")
                        in {None, "", "Primary ProofChain governed goal agent."}
                        else component.get("description")
                    ),
                    "architectureLayer": layer,
                    "status": status,
                    "confidence": scores.get(name, decision.get("confidence")),
                    "outputArtifacts": decision.get("evidence_considered", []),
                    "inputArtifacts": decision.get("inputs_considered", []),
                    "errorMessage": (
                        decision.get("reason")
                        if raw_status in {"failed", "blocked", "needs_human_review"}
                        else None
                    ),
                    "goals": [decision.get("goal_id")]
                    if decision.get("goal_id")
                    else [],
                    "messagesSent": sum(
                        item.get("source_agent") == name for item in messages
                    ),
                    "messagesReceived": sum(
                        item.get("target_agent") == name for item in messages
                    ),
                    "rounds": execution_counts[name],
                    "peersContacted": sorted(
                        {
                            item.get("target_agent")
                            for item in messages
                            if item.get("source_agent") == name
                            and item.get("target_agent")
                        }
                        | {
                            item.get("source_agent")
                            for item in messages
                            if item.get("target_agent") == name
                            and item.get("source_agent")
                        }
                    ),
                    "decisionReason": decision.get("reason"),
                    "completionProofId": decision.get("completion_proof_id"),
                    "explanationId": decision.get("explanation_id"),
                    "humanApprovalRequired": decision.get(
                        "human_approval_required", False
                    ),
                    "nextAction": decision.get("next_action"),
                    "policiesApplied": decision.get("policies_applied", []),
                    "rulesApplied": decision.get("rules_applied", []),
                    "uncertainty": decision.get("uncertainty", []),
                }
            )
        return results

    def agent_detail(self, run_id: str, agent_id: int) -> dict[str, Any] | None:
        agent = next(
            (item for item in self.agents(run_id) if item["id"] == agent_id),
            None,
        )
        if agent is None:
            return None

        agent_name = PRIMARY_AGENT_ORDER[agent_id - 1]
        runtime_dir = AGENT_RUNTIME_DIRECTORIES.get(agent_name, agent_name)
        plans = self._json(run_id, f"{runtime_dir}/plans.json", [])
        completed_plans = [
            item for item in plans if item.get("status") == "completed"
        ]
        plan = (completed_plans or plans or [None])[-1]
        completion = self._json(
            run_id, f"{runtime_dir}/completion_decision.json", {}
        )
        observations = self._jsonl(run_id, f"{runtime_dir}/observations.jsonl")
        reflections = self._jsonl(run_id, f"{runtime_dir}/reflections.jsonl")
        actions = [
            item
            for item in self._jsonl(run_id, "coordination/actions.jsonl")
            if item.get("agent_name") == agent_name
        ]
        tool_calls = [
            item
            for item in self._jsonl(run_id, "coordination/tool_calls.jsonl")
            if item.get("agent_name") == agent_name
        ]
        decisions = [
            item
            for item in self._jsonl(run_id, "agent_decisions.jsonl")
            if item.get("agent_name") == agent_name
        ]
        model_profiles = self._json(
            run_id, "model_governance_manifest.json", {}
        ).get("profiles", [])
        model_profile = next(
            (
                item
                for item in model_profiles
                if item.get("agent_name") == agent_name
            ),
            None,
        )
        manifest = self._json(run_id, "run_manifest.json", {})
        checkpoints = [
            item
            for item in manifest.get("checkpoints", [])
            if item.get("stage_name") == agent_name
        ]
        goals = [
            item
            for item in self.goals(run_id)
            if item.get("agentName") == agent_name
        ]
        events = [
            item
            for item in self.events(run_id, limit=1000)
            if item.get("agentName") == agent_name
        ]
        messages = [
            item
            for item in self.messages(run_id)
            if item.get("fromAgentName") == agent_name
            or item.get("toAgentName") == agent_name
        ]
        return {
            "agent": agent,
            "goal": goals[-1] if goals else None,
            "goals": goals,
            "plan": self._project_plan(plan),
            "completion": self._project_completion(completion),
            "observations": observations,
            "reflections": reflections,
            "actions": actions,
            "toolCalls": tool_calls,
            "decisions": decisions,
            "events": events,
            "messages": messages,
            "checkpoints": checkpoints,
            "modelProfile": model_profile,
            "runtimeDirectory": runtime_dir,
        }

    def governance(self, run_id: str) -> dict[str, Any]:
        manifest = self._json(run_id, "run_manifest.json", {})
        policy = self._json(run_id, "governance_policy_manifest.json", {})
        model = self._json(run_id, "model_governance_manifest.json", {})
        components = self._json(run_id, "component_registry.json", {}).get(
            "components", []
        )
        summary = self._json(run_id, "complete_run_summary.json", {})
        return {
            "runId": run_id,
            "checkpoints": manifest.get("checkpoints", []),
            "events": self.events(run_id, limit=1000),
            "policyFingerprint": policy.get("policy_fingerprint"),
            "policySetVersion": policy.get("policy_set_version"),
            "policies": policy.get("policies", []),
            "modelProfiles": model.get("profiles", []),
            "componentSummary": dict(
                Counter(
                    item.get("component_type", "unknown") for item in components
                )
            ),
            "validation": {
                "technicalComplete": summary.get("technically_complete"),
                "persistenceSynchronized": summary.get(
                    "persistence_synchronized"
                ),
                "standard": summary.get("standard_validation", {}),
                "agentic": summary.get("agentic_validation", {}),
            },
        }

    def goals(self, run_id: str) -> list[dict[str, Any]]:
        payload = self._json(run_id, "goal_graph.json", {})
        agent_ids = {name: index for index, name in enumerate(PRIMARY_AGENT_ORDER, 1)}
        decisions = {
            item.get("goal_id"): item
            for item in self._jsonl(run_id, "agent_decisions.jsonl")
        }
        results = []
        for item in payload.get("goals", []):
            decision = decisions.get(item.get("goal_id"), {})
            raw_status = item.get("status", "pending")
            status = {
                "completed": "achieved",
                "completed_with_warnings": "achieved",
                "needs_human_review": "active",
                "blocked": "failed",
            }.get(raw_status, raw_status)
            results.append(
                {
                    "id": item.get("goal_id"),
                    "title": item.get("objective"),
                    "agentId": agent_ids.get(item.get("assigned_agent"), 0),
                    "agentName": item.get("assigned_agent", "supervisor"),
                    "status": status,
                    "confidence": decision.get("confidence"),
                    "parentId": item.get("parent_goal_id"),
                    "criterionId": None,
                    "reasoning": decision.get("reason"),
                    "toolCalls": [],
                    "evidenceRefs": decision.get("evidence_considered", []),
                    "createdAt": item.get("created_at"),
                    "resolvedAt": None,
                }
            )
        return results

    def events(
        self, run_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        events = self._jsonl(run_id, "workflow_events.jsonl")
        selected = events[offset : offset + max(0, min(limit, 1000))]
        return [
            {
                "id": item.get("event_id"),
                "timestamp": item.get("created_at"),
                "eventType": item.get("event_type"),
                "agentName": item.get("actor"),
                "data": item.get("payload", {}),
                "runId": item.get("run_id"),
                "sequenceNumber": item.get("sequence"),
                "eventHash": item.get("event_hash"),
                "previousEventHash": item.get("previous_event_hash"),
            }
            for item in selected
        ]

    def messages(self, run_id: str) -> list[dict[str, Any]]:
        agent_ids = {name: index for index, name in enumerate(PRIMARY_AGENT_ORDER, 1)}
        results = []
        for item in self._jsonl(run_id, "coordination/messages.jsonl"):
            source = item.get("source_agent", "")
            target = item.get("target_agent", "")
            results.append(
                {
                    "id": item.get("message_id"),
                    "fromAgentId": agent_ids.get(source, 0),
                    "fromAgentName": source,
                    "toAgentId": agent_ids.get(target, 0),
                    "toAgentName": target,
                    "messageType": item.get("message_type"),
                    "payload": item.get("payload", {}),
                    "timestamp": item.get("created_at"),
                    "roundNumber": item.get("round_number", 0),
                }
            )
        return results

    def evidence(self, run_id: str) -> list[dict[str, Any]]:
        records = self._json(run_id, "evidence_registry.json", [])
        classified = {
            item.get("evidence_id"): item
            for item in self._json(run_id, "classified_evidence.json", [])
        }
        findings_by_evidence: dict[str, list[dict[str, Any]]] = {}
        for finding in self._json(run_id, "integrity_findings.json", []):
            impacted = finding.get("impacted_evidence_ids", [])
            for evidence_id in impacted:
                findings_by_evidence.setdefault(evidence_id, []).append(
                    {
                        "ruleId": finding.get("rule_id"),
                        "ruleName": finding.get("finding_type", "integrity_rule"),
                        "status": finding.get("status", "failed"),
                        "detail": finding.get("description"),
                        "impactedEvidenceIds": impacted,
                    }
                )
        return [
            {
                "id": item.get("evidence_id"),
                "filename": item.get("original_filename"),
                "evidenceType": classified.get(item.get("evidence_id"), {})
                .get("document_type", {})
                .get(
                    "primary_type",
                    item.get("processing_capability", "registered_file"),
                ),
                "criterionId": (
                    classified.get(item.get("evidence_id"), {}).get(
                        "requirement_mappings", [{}]
                    )
                    or [{}]
                )[0].get("requirement_id"),
                "status": classified.get(item.get("evidence_id"), {}).get(
                    "processing_status",
                    item.get("ingestion_status", "registered"),
                ),
                "confidence": classified.get(item.get("evidence_id"), {}).get(
                    "overall_confidence"
                ),
                "hash": item.get("sha256_checksum"),
                "registeredAt": item.get("discovered_at"),
                "source": item.get("relative_path"),
                "tags": [
                    item.get("department", ""),
                    item.get("academic_year", ""),
                    item.get("file_extension", ""),
                ],
                "capabilityReason": item.get("capability_reason"),
                "integrityFindings": findings_by_evidence.get(
                    item.get("evidence_id"), []
                ),
            }
            for item in records
        ]

    def claims(self, run_id: str) -> list[dict[str, Any]]:
        decisions = self._json(run_id, "claim_decisions.json", {}).get(
            "decisions", []
        )
        return [
            {
                "id": item.get("claim_id"),
                "criterionId": item.get("requirement_id"),
                "text": item.get("original_claim"),
                "status": item.get("status"),
                "confidence": item.get("confidence"),
                "supportingEvidenceIds": item.get("supporting_evidence", []),
                "contradictingEvidenceIds": item.get("counter_evidence", []),
                "agentReasoning": item.get("defensible_claim_text"),
                "reviewRequired": item.get("requires_human_review", False),
                "createdAt": None,
            }
            for item in decisions
        ]

    def issues(self, run_id: str) -> list[dict[str, Any]]:
        issues = self._json(run_id, "canonical_issues.json", {}).get("issues", [])
        tasks = self._json(run_id, "resolution_tasks_detailed.json", {}).get(
            "tasks", []
        )
        tasks_by_issue = {item.get("issue_id"): item for item in tasks}
        gaps = self._json(run_id, "gap_resolution_portfolio.json", {}).get(
            "portfolio", {}
        ).get("gaps", [])
        gaps_by_id = {item.get("gap_id"): item for item in gaps}
        statuses = {
            "OPEN": "open",
            "PLANNED": "planned",
            "ASSIGNED_PENDING_APPROVAL": "awaiting approval",
            "ASSIGNED": "in progress",
            "IN_PROGRESS": "in progress",
            "EVIDENCE_SUBMITTED": "evidence submitted",
            "UNDER_REVALIDATION": "under revalidation",
            "RESOLVED": "resolved",
            "REOPENED": "reopened",
            "REJECTED": "open",
            "WAIVED_WITH_APPROVAL": "resolved",
            "CANCELLED": "open",
        }
        results = []
        for item in issues:
            task = tasks_by_issue.get(item.get("issue_id"), {})
            source_gap_ids = item.get("source_gap_ids", [])
            gap = gaps_by_id.get(source_gap_ids[0], {}) if source_gap_ids else {}
            issue_type = item.get("issue_type", "governed_issue")
            results.append(
                {
                    "id": item.get("issue_id"),
                    "criterionId": (item.get("affected_requirement_ids") or [""])[0],
                    "title": issue_type.replace("_", " ").title(),
                    "description": gap.get("description") or item.get("canonical_key"),
                    "severity": item.get("severity", "medium"),
                    "blocking": item.get("blocking", False),
                    "status": statuses.get(item.get("status"), "open"),
                    "owner": task.get("primary_owner_id"),
                    "readinessImpact": -abs(gap.get("readiness_impact", 0)),
                    "dueDate": task.get("due_at"),
                    "resolutionPlan": task.get("objective"),
                    "blockedByIds": [],
                    "taskIds": item.get("resolution_task_ids", []),
                    "claimIds": item.get("source_claim_ids", []),
                    "createdAt": item.get("created_at"),
                    "resolvedAt": (
                        item.get("updated_at") if item.get("status") == "RESOLVED" else None
                    ),
                    "canonicalKey": item.get("canonical_key"),
                }
            )
        return results

    def tasks(self, run_id: str) -> list[dict[str, Any]]:
        tasks = self._json(run_id, "resolution_tasks_detailed.json", {}).get(
            "tasks", []
        )
        states = self._json(run_id, "resolution_task_state.json", {})
        communications = {
            item.get("task_id"): item
            for item in self._json(run_id, "communications.json", [])
        }
        status_map = {
            "draft": "pending",
            "approval_required": "pending",
            "active": "in progress",
            "acknowledged": "in progress",
            "evidence_submitted": "completed",
            "blocked": "pending",
            "escalated": "overdue",
            "closed": "completed",
        }
        return [
            {
                "id": item.get("task_id"),
                "issueId": item.get("issue_id"),
                "title": item.get("title"),
                "description": item.get("objective"),
                "assignedTo": item.get("primary_owner_id"),
                "status": status_map.get(
                    states.get(item.get("task_id"), {}).get(
                        "status", item.get("status")
                    ),
                    "pending",
                ),
                "dueDate": item.get("due_at"),
                "draftCommunication": communications.get(
                    item.get("task_id"), {}
                ).get("content_hash"),
                "responseReceived": None,
                "createdAt": item.get("created_at"),
                "completedAt": None,
            }
            for item in tasks
        ]

    def approvals(self, run_id: str) -> list[dict[str, Any]]:
        payload = self._json(run_id, "human_approvals.json", [])
        approvals = (
            payload if isinstance(payload, list) else payload.get("approvals", [])
        )
        if approvals:
            return [
                {
                    "id": item.get("approval_id"),
                    "subject": item.get("target_id"),
                    "subjectType": item.get("approval_type", "custom"),
                    "requiredApprover": item.get("required_approver", "Authorized reviewer"),
                    "status": item.get("decision", item.get("approval_state", "pending")).lower(),
                    "reason": item.get("reason"),
                    "decidedAt": item.get("decided_at"),
                    "decidedBy": item.get("decided_by"),
                    "criterionId": None,
                    "relatedIds": item.get("evidence_references", []),
                    "createdAt": item.get("created_at"),
                }
                for item in approvals
            ]
        review_items = [
            {
                "id": f"REVIEW-{index:03d}",
                "subject": item.get("goal_id"),
                "subjectType": "custom",
                "requiredApprover": "Authorized human reviewer",
                "status": "pending",
                "reason": item.get("reason"),
                "decidedAt": None,
                "decidedBy": None,
                "criterionId": None,
                "relatedIds": [item.get("proof_id")] if item.get("proof_id") else [],
                "createdAt": None,
            }
            for index, item in enumerate(
                self._json(run_id, "human_review_queue.json", []), 1
            )
        ]
        submission = self._json(run_id, "external_submission_report.json", {})
        if (
            submission.get("eligibility_decision") == "NOT_ELIGIBLE"
            and submission.get("frozen_package_hash")
            and any(
                "approval" in reason.lower()
                for reason in submission.get("policy_reasons", [])
            )
        ):
            review_items.append(
                {
                    "id": f"SUBMISSION-APPROVAL-{run_id}",
                    "subject": submission.get("package_id"),
                    "subjectType": "package",
                    "requiredApprover": "Independent authorized approver",
                    "status": "pending",
                    "reason": "; ".join(submission.get("policy_reasons", [])),
                    "decidedAt": None,
                    "decidedBy": None,
                    "criterionId": None,
                    "relatedIds": [submission.get("frozen_package_hash")],
                    "createdAt": submission.get("completed_at"),
                }
            )
        return review_items

    def package(self, run_id: str) -> dict[str, Any]:
        payload = self._json(run_id, "audit_package_manifest.json", {})
        manifest = payload.get("manifest", payload)
        if not manifest:
            return {}
        quality = self._json(run_id, "quality_review_report.json", {})
        quality_status = quality.get("quality_status")
        package_status = {
            "pass_for_human_approval": "ready",
            "pass_with_warnings": "ready",
            "return_for_correction": "correction required",
            "block_package": "rejected",
        }.get(quality_status, "draft")
        if manifest.get("external_submission_approved"):
            package_status = "approved"
        evidence_ids = [
            item.get("evidence_id")
            for item in manifest.get("eligible_evidence", [])
            if item.get("included")
        ]
        findings = [
            {
                "id": f"QF-{index:03d}",
                "severity": "high",
                "description": correction,
                "criterionId": None,
                "correctionRequired": correction,
                "resolved": False,
            }
            for index, correction in enumerate(
                quality.get("required_corrections", []), 1
            )
        ]
        return {
            "id": manifest.get("package_id"),
            "runId": run_id,
            "status": package_status,
            "contents": [
                {
                    "criterionId": requirement,
                    "evidenceIds": evidence_ids,
                    "claimIds": manifest.get("claim_ids", []),
                    "eligibilityExplanation": (
                        "Evidence passed composer eligibility and unresolved warnings "
                        "remain disclosed."
                    ),
                    "ready": package_status in {"ready", "approved"},
                }
                for requirement in manifest.get("requirement_ids", [])
            ],
            "qualityReview": {
                "id": f"QUALITY-{manifest.get('package_id')}",
                "packageId": manifest.get("package_id"),
                "status": (
                    "passed"
                    if quality_status in {
                        "pass_for_human_approval",
                        "pass_with_warnings",
                    }
                    else "correction required"
                    if quality_status == "return_for_correction"
                    else "failed"
                ),
                "score": round((1.0 - quality.get("audit_failure_risk", 1.0)) * 100, 1),
                "findings": findings,
                "reviewedAt": quality.get("completed_at"),
            }
            if quality
            else None,
            "createdAt": manifest.get("generated_at"),
            "approvedAt": None,
            "downloadUrl": manifest.get("bundle_path"),
            "packageHash": manifest.get("package_hash"),
            "bundleSha256": manifest.get("bundle_sha256"),
        }

    def workflow_status(self, run_id: str) -> dict[str, Any]:
        run = self.run_summary(run_id)
        coordination = self._json(
            run_id, "coordination/coordination_state.json", {}
        )
        review_queue = self._json(run_id, "human_review_queue.json", [])
        final = self._json(run_id, "final_decision.json", {})
        quality = self._json(run_id, "quality_review_report.json", {})
        submission = self._json(run_id, "external_submission_report.json", {})
        happening = coordination.get("active_goals", [])
        blocked = [
            {
                "goalId": item.get("goal_id"),
                "agent": item.get("agent_name"),
                "reason": item.get("reason"),
                "priority": item.get("priority"),
            }
            for item in review_queue
        ]
        actions = [
            {
                "type": "human_review",
                "target": item.get("goal_id"),
                "owner": item.get("agent_name"),
                "reason": item.get("reason"),
            }
            for item in review_queue
        ]
        actions.extend(
            {
                "type": "package_correction",
                "target": quality.get("package_id"),
                "reason": correction,
            }
            for correction in quality.get("required_corrections", [])
        )
        next_steps = []
        if actions:
            next_steps.append("Resolve the governed human-action queue.")
        if run["blockingIssues"]:
            next_steps.append(
                "Submit corrective evidence and run targeted closure revalidation."
            )
        if quality.get("quality_status") in {"return_for_correction", "block_package"}:
            next_steps.append("Rebuild and challenge the corrected audit package.")
        if submission.get("submission_status") != "submitted":
            next_steps.append(
                "Obtain hash-bound independent approval before external submission."
            )
        return {
            "runId": run_id,
            "domainStatus": run["status"],
            "happened": {
                "completedGoals": coordination.get("completed_goals", []),
                "agentCount": len(self.agents(run_id)),
                "eventCount": len(self._jsonl(run_id, "workflow_events.jsonl")),
            },
            "happeningNow": happening,
            "blocked": blocked,
            "userMustDo": actions,
            "nextSteps": list(dict.fromkeys(next_steps)),
            "finalDecision": final,
            "qualityDecision": quality.get("quality_status"),
            "submissionDecision": submission.get("eligibility_decision"),
            "counterfactualProjection": {
                "value": run["projectedReadiness"],
                "type": run["projectionType"],
                "assumptions": run["projectionAssumptions"],
            },
        }

    def raw(self, run_id: str, filename: str, default: Any = None) -> Any:
        return self._json(run_id, filename, default)

    @staticmethod
    def _project_plan(plan: dict[str, Any] | None) -> dict[str, Any] | None:
        if not plan:
            return None
        return {
            "id": plan.get("plan_id"),
            "goalId": plan.get("goal_id"),
            "status": plan.get("status"),
            "revision": plan.get("revision"),
            "rationale": plan.get("rationale"),
            "assumptions": plan.get("assumptions", []),
            "dependencies": plan.get("dependencies", []),
            "expectedOutputs": plan.get("expected_outputs", []),
            "steps": [
                {
                    "id": item.get("step_id"),
                    "sequence": item.get("sequence"),
                    "objective": item.get("objective"),
                    "tool": item.get("proposed_tool"),
                    "status": item.get("status"),
                    "expectedObservation": item.get("expected_observation"),
                    "completionCondition": item.get("completion_condition"),
                    "requiredInputs": item.get("required_inputs", []),
                }
                for item in plan.get("steps", [])
            ],
        }

    @staticmethod
    def _project_completion(payload: dict[str, Any]) -> dict[str, Any] | None:
        if not payload:
            return None
        return {
            "decisionId": payload.get("decision_id"),
            "finalStatus": payload.get("final_status"),
            "goalSatisfied": payload.get("goal_satisfied"),
            "confidence": payload.get("confidence"),
            "explanation": payload.get("explanation"),
            "successConditionsMet": payload.get("success_conditions_met", []),
            "successConditionsUnmet": payload.get(
                "success_conditions_unmet", []
            ),
            "blockers": payload.get("blockers", []),
            "unresolvedQuestions": payload.get("unresolved_questions", []),
            "supportingArtifacts": payload.get("supporting_artifacts", []),
            "createdAt": payload.get("created_at"),
        }

    def _run_dir(self, run_id: str) -> Path:
        if not run_id or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in run_id):
            raise ValueError("Invalid run ID.")
        path = (self.runs_dir / run_id).resolve()
        if self.runs_dir not in path.parents:
            raise ValueError("Run path escapes the configured output directory.")
        return path

    def _json(self, run_id: str, filename: str, default: Any) -> Any:
        path = self._run_dir(run_id) / filename
        if not path.is_file():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def _jsonl(self, run_id: str, filename: str) -> list[dict[str, Any]]:
        path = self._run_dir(run_id) / filename
        if not path.is_file():
            return []
        results = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    results.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            return []
        return results

    @staticmethod
    def _duration(value: Any) -> str | None:
        if not isinstance(value, (int, float)):
            return None
        seconds = max(0, int(value / 1000))
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"
