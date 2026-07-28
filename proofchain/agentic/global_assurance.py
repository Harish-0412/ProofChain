"""Cross-agent proof auditing, trigger-based replanning, and release gates."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from uuid import uuid4

from proofchain.agentic.cognition_profiles import ALL_AGENT_FEATURES
from proofchain.agentic.scheduler import GoalScheduler
from proofchain.core.paths import (
    get_goal_graph_path,
    get_quality_review_path,
    get_run_dir,
)
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.agentic import Goal
from proofchain.schemas.global_assurance import (
    AgenticReleaseDecision,
    CompletionProofAudit,
    CriticalPathSchedule,
    CrossAgentContradictionReport,
    GlobalReplanRecord,
    HumanReviewQueueItem,
    SupervisorAssuranceReport,
)


class GlobalAssuranceService:
    def __init__(self, store: AtomicJsonStore | None = None):
        self.store = store or AtomicJsonStore()

    def evaluate(
        self,
        run_id: str,
        *,
        stage: str,
    ) -> SupervisorAssuranceReport:
        run_dir = get_run_dir(run_id)
        goals = self._goals(run_id)
        executed = self._executed_agent_goals(run_dir, goals)
        proof_audit = self._audit_proofs(run_id, run_dir, executed)
        contradictions = self._contradictions(run_id, run_dir)
        schedule = self._schedule(run_id, goals)
        replans = self._replans(
            run_id, run_dir, goals, contradictions
        )
        review_queue = self._human_review_queue(run_dir, executed)
        scorecards = self._scorecards(run_dir)
        failures = self._failure_clusters(
            proof_audit, contradictions, replans, scorecards
        )
        release = self._release_decision(
            run_id,
            stage,
            executed,
            proof_audit,
            scorecards,
            failures,
            run_dir,
        )
        report = SupervisorAssuranceReport(
            run_id=run_id,
            stage=stage,
            completion_proof_audit=proof_audit,
            contradiction_report=contradictions,
            critical_path_schedule=schedule,
            replan_records=replans,
            human_review_queue=review_queue,
            release_decision=release,
            metrics={
                "advanced_agents_executed": len(executed),
                "human_review_items": len(review_queue),
                "global_replan_triggers": len(replans),
                "scorecards": len(scorecards),
            },
        )
        self.store.write(run_dir / "completion_proof_audit.json", proof_audit)
        self.store.write(run_dir / "cross_agent_contradictions.json", contradictions)
        self.store.write(run_dir / "critical_path_schedule.json", schedule)
        self.store.write(run_dir / "global_replans.json", replans)
        self.store.write(run_dir / "human_review_queue.json", review_queue)
        self.store.write(run_dir / "agentic_scorecards.json", scorecards)
        self.store.write(run_dir / "agentic_failure_clusters.json", failures)
        self.store.write(run_dir / "agentic_release_decision.json", release)
        self.store.write(run_dir / "supervisor_assurance_report.json", report)
        return report

    def _goals(self, run_id: str) -> list[Goal]:
        payload = self.store.read(get_goal_graph_path(run_id), default={})
        return [
            Goal.model_validate(item)
            for item in payload.get("goals", [])
            if item.get("assigned_agent") in ALL_AGENT_FEATURES
        ]

    @staticmethod
    def _executed_agent_goals(run_dir: Path, goals: list[Goal]) -> list[Goal]:
        return [
            goal
            for goal in goals
            if (
                run_dir
                / "agents"
                / goal.assigned_agent
                / goal.goal_id
                / "completion_proof.json"
            ).exists()
        ]

    def _audit_proofs(
        self, run_id: str, run_dir: Path, goals: list[Goal]
    ) -> CompletionProofAudit:
        valid: list[str] = []
        invalid: list[str] = []
        missing: list[str] = []
        mismatches: list[str] = []
        for goal in goals:
            root = run_dir / "agents" / goal.assigned_agent / goal.goal_id
            proof = self.store.read(root / "completion_proof.json")
            explanation = self.store.read(root / "decision_explanation.json")
            if not proof:
                missing.append(goal.goal_id)
                continue
            (valid if proof.get("proof_valid") else invalid).append(
                proof.get("proof_id", goal.goal_id)
            )
            if not explanation or (
                explanation.get("completion_proof_id") != proof.get("proof_id")
                or explanation.get("decision") != proof.get("final_status")
            ):
                mismatches.append(goal.goal_id)
        return CompletionProofAudit(
            run_id=run_id,
            proofs_expected=len(goals),
            proofs_found=len(goals) - len(missing),
            valid_proof_ids=valid,
            invalid_proof_ids=invalid,
            missing_goal_ids=missing,
            decision_mismatches=mismatches,
            audit_passed=not (invalid or missing or mismatches),
        )

    def _contradictions(
        self, run_id: str, run_dir: Path
    ) -> CrossAgentContradictionReport:
        records = []
        agents = []
        for path in (run_dir / "agents").glob(
            "*/**/contradiction_resolution.json"
        ):
            payload = self.store.read(path, default={})
            if payload:
                records.append(payload)
                try:
                    agents.append(path.parents[1].name)
                except IndexError:
                    pass
        unresolved = sum(
            item.get("resolution_status") in {"identified", "investigating", "unresolved"}
            for item in records
        )
        escalated = sum(
            item.get("resolution_status") == "escalated" for item in records
        )
        return CrossAgentContradictionReport(
            run_id=run_id,
            contradiction_ids=[
                item.get("contradiction_id") for item in records
            ],
            source_agents=sorted(set(agents)),
            unresolved_count=unresolved,
            escalated_count=escalated,
            report_status=(
                "clear"
                if not records
                else "escalated"
                if unresolved or escalated
                else "resolved"
            ),
        )

    @staticmethod
    def _schedule(run_id: str, goals: list[Goal]) -> CriticalPathSchedule:
        scheduler = GoalScheduler()
        ordered, path, scores = scheduler.global_order(goals)
        return CriticalPathSchedule(
            run_id=run_id,
            critical_path_goal_ids=path,
            ordered_goal_ids=[goal.goal_id for goal in ordered],
            priority_scores=scores,
            agent_allocation_counts=dict(
                Counter(goal.assigned_agent for goal in ordered)
            ),
        )

    def _replans(
        self,
        run_id: str,
        run_dir: Path,
        goals: list[Goal],
        contradictions: CrossAgentContradictionReport,
    ) -> list[GlobalReplanRecord]:
        triggers: list[tuple[str, str]] = []
        if any(
            goal.priority == "critical"
            and goal.status in {"blocked", "failed"}
            for goal in goals
        ):
            triggers.append(
                ("critical_goal_failure", "A critical goal ended blocked or failed.")
            )
        quality = self.store.read(get_quality_review_path(run_id), default={})
        if quality.get("quality_status") in {
            "return_for_correction",
            "block_package",
        }:
            triggers.append(
                ("quality_review_failure", "Quality review requires correction.")
            )
        security = self.store.read(
            run_dir / "phase_one_security_report.json", default={}
        )
        if security.get("overall_decision") in {"BLOCK", "QUARANTINE"}:
            triggers.append(
                ("security_incident", "Security inspection restricted evidence.")
            )
        tenant = self.store.read(
            run_dir / "tenant_access_decision.json", default={}
        )
        if tenant.get("cross_tenant_request") or tenant.get(
            "access_decision"
        ) in {"DENY", "NEEDS_SHARING_APPROVAL"}:
            triggers.append(
                ("tenant_boundary_change", "Tenant boundary requires replanning.")
            )
        submission = self.store.read(
            run_dir / "external_submission_report.json", default={}
        )
        if any(
            "deadline" in str(reason).lower()
            for reason in submission.get("policy_reasons", [])
        ):
            triggers.append(
                ("submission_deadline_change", "Submission deadline risk changed.")
            )
        schema = self.store.read(
            run_dir / "schema_evolution_report.json", default={}
        )
        if schema.get("deployment_decision") == "BLOCK":
            triggers.append(
                ("schema_migration_block", "Schema migration is blocked.")
            )
        policy = self.store.read(
            run_dir / "policy_lifecycle_report.json", default={}
        )
        if policy.get("activation_decision") in {"ACTIVATE", "BLOCK"}:
            triggers.append(
                ("policy_version_change", "Policy lifecycle changed the active plan.")
            )
        if contradictions.report_status == "escalated":
            triggers.append(
                (
                    "new_contradictory_evidence",
                    "Cross-agent contradiction requires targeted validation.",
                )
            )
        affected = [
            goal.goal_id
            for goal in goals
            if goal.status != "completed"
        ]
        invalidated = self._invalidated_steps(run_dir, affected)
        return [
            GlobalReplanRecord(
                replan_id=f"GRP-{uuid4().hex[:12].upper()}",
                run_id=run_id,
                trigger=trigger,
                reason=reason,
                affected_goal_ids=affected,
                changed_assumptions=[reason],
                invalidated_step_ids=invalidated,
                new_scope=[
                    "Revalidate affected artifacts and proofs.",
                    "Recalculate critical path before downstream continuation.",
                ],
                decision=(
                    "pause_for_human"
                    if trigger
                    in {
                        "tenant_boundary_change",
                        "schema_migration_block",
                        "policy_version_change",
                    }
                    else "targeted_revalidation"
                ),
            )
            for trigger, reason in dict(triggers).items()
        ]

    def _invalidated_steps(
        self, run_dir: Path, affected_goal_ids: list[str]
    ) -> list[str]:
        steps = []
        for goal_id in affected_goal_ids:
            for path in (run_dir / "agents").glob(
                f"*/{goal_id}/plans/plan_revision_*.json"
            ):
                payload = self.store.read(path, default={})
                steps.extend(item.get("step_id") for item in payload.get("steps", []))
        return list(dict.fromkeys(item for item in steps if item))

    def _human_review_queue(
        self, run_dir: Path, goals: list[Goal]
    ) -> list[HumanReviewQueueItem]:
        queue = []
        for goal in goals:
            root = run_dir / "agents" / goal.assigned_agent / goal.goal_id
            explanation = self.store.read(
                root / "decision_explanation.json", default={}
            )
            proof = self.store.read(root / "completion_proof.json", default={})
            if explanation.get("human_approval_required") or explanation.get(
                "decision"
            ) in {"needs_human_review", "blocked"}:
                queue.append(
                    HumanReviewQueueItem(
                        goal_id=goal.goal_id,
                        agent_name=goal.assigned_agent,
                        reason=explanation.get("reason", "Governed review required."),
                        priority=goal.priority,
                        proof_id=proof.get("proof_id"),
                    )
                )
        return queue

    def _scorecards(self, run_dir: Path) -> list[dict]:
        scorecards = []
        for path in (run_dir / "agents").glob("*/**/agentic_scorecard.json"):
            payload = self.store.read(path)
            if payload:
                scorecards.append(payload)
        return scorecards

    @staticmethod
    def _failure_clusters(
        proof_audit,
        contradictions,
        replans,
        scorecards,
    ) -> list[dict]:
        clusters = defaultdict(list)
        clusters["invalid_completion_proof"].extend(
            proof_audit.invalid_proof_ids
        )
        clusters["completion_decision_mismatch"].extend(
            proof_audit.decision_mismatches
        )
        if contradictions.report_status == "escalated":
            clusters["cross_agent_contradiction"].extend(
                contradictions.contradiction_ids
            )
        for replan in replans:
            clusters[f"global_replan:{replan.trigger}"].append(replan.replan_id)
        for score in scorecards:
            if score.get("human_escalation_precision", 1.0) < 0.9:
                clusters["human_escalation_regression"].append(
                    score.get("agent_name")
                )
        return [
            {"cluster": key, "items": values, "count": len(values)}
            for key, values in sorted(clusters.items())
            if values
        ]

    def _release_decision(
        self,
        run_id,
        stage,
        goals,
        proof_audit,
        scorecards,
        failures,
        run_dir,
    ) -> AgenticReleaseDecision:
        final_stage = stage == "phase_two"
        scorecard_names = {item.get("agent_name") for item in scorecards}
        required_names = set(ALL_AGENT_FEATURES) if final_stage else {
            goal.assigned_agent for goal in goals
        }
        tenant = self.store.read(
            run_dir / "tenant_access_decision.json", default={}
        )
        submission = self.store.read(
            run_dir / "external_submission_report.json", default={}
        )
        peer_requests = self._read_jsonl(
            run_dir / "coordination" / "peer_requests.jsonl"
        )
        latest_peers = {}
        for item in peer_requests:
            latest_peers[item.get("request_id")] = item
        falsely_resolved = [
            request_id
            for request_id, item in latest_peers.items()
            if item.get("status") == "RESOLVED"
            and not set(item.get("acceptance_conditions", []))
            <= set(item.get("satisfied_acceptance_conditions", []))
        ]
        gates = {
            "completion_proofs_valid": proof_audit.audit_passed,
            "all_required_scorecards_present": required_names <= scorecard_names,
            "no_cross_tenant_leakage": not (
                tenant.get("cross_tenant_request")
                and tenant.get("access_decision") == "ALLOW"
                and not tenant.get("applied_share_id")
            ),
            "submission_human_controlled": not (
                submission.get("submission_status") == "submitted"
                and submission.get("eligibility_decision") != "ELIGIBLE"
            ),
            "peer_acceptance_enforced": not falsely_resolved,
            "no_unauthorized_plan": not any(
                item.get("cluster") == "unauthorized_tool" for item in failures
            ),
        }
        reasons = [name for name, passed in gates.items() if not passed]
        decision = (
            "BLOCK"
            if reasons
            else "PASS"
            if final_stage and len(scorecard_names) >= 22
            else "NEEDS_HUMAN_REVIEW"
        )
        return AgenticReleaseDecision(
            run_id=run_id,
            decision=decision,
            scorecards_expected=22 if final_stage else len(required_names),
            scorecards_found=len(scorecard_names),
            gates=gates,
            blocking_reasons=reasons,
            warnings=[]
            if final_stage
            else ["Final release decision requires the complete Phase 2 run."],
        )

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict]:
        if not path.exists():
            return []
        values = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    values.append(json.loads(line))
        return values
