"""ProofChain command line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from proofchain.agents.supervisor import Supervisor
from proofchain.core.enums import RunMode
from proofchain.core.paths import (
    get_audit_package_manifest_path,
    get_closure_report_path,
    get_liaison_tasks_path,
    get_ownership_assignments_path,
    get_quality_review_path,
    get_resolution_task_state_path,
)
from proofchain.repositories.json_run_repository import JsonRunRepository
from proofchain.repositories.json_approval_repository import JsonApprovalRepository
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.workflow import SupervisorRequest
from proofchain.schemas.tasks import ResolutionTaskState


DEFAULT_REQUIREMENTS = ["C3.2.1", "C5.1.3", "C6.3.2", "C7.1.1", "C1.2.1"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proofchain",
        description="Governed agentic accreditation evidence validation pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command, help_text in (
        ("run-pipeline", "Run collection, classification, and integrity."),
        ("collect", "Collect and register evidence only."),
        ("classify", "Classify evidence from a prior run."),
        ("integrity", "Validate classified evidence from a prior run."),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("--source", action="append", default=[])
        child.add_argument("--departments", nargs="+", required=True)
        child.add_argument("--academic-year", default="2025-2026")
        child.add_argument("--requirements", nargs="+", default=DEFAULT_REQUIREMENTS)
        child.add_argument("--requested-by", default="cli")
        child.add_argument(
            "--claim",
            action="append",
            default=[],
            help="Institutional claim to validate; repeat for multiple claims.",
        )
        child.add_argument("--objective")
        child.add_argument("--max-agent-rounds", type=int, default=12)
        child.add_argument("--max-replans", type=int, default=3)
        child.add_argument(
            "--require-human-approval",
            action="store_true",
            help="End positive automated decisions in needs_human_review.",
        )
        if command in {"classify", "integrity"}:
            child.add_argument("--from-run", required=True)

    validate = subparsers.add_parser(
        "validate-run", help="Validate artifact presence, hashes, and synchronization links."
    )
    validate.add_argument("run_id")
    approve = subparsers.add_parser(
        "approve-decision",
        help="Record an explicit human approval or rejection for a governed decision.",
    )
    approve.add_argument("run_id")
    approve.add_argument(
        "--type",
        required=True,
        choices=[
            "claim_revision",
            "gap_resolution_strategy",
            "ownership_assignment",
            "escalation",
        ],
    )
    approve.add_argument("--target", required=True)
    approve.add_argument(
        "--decision", required=True, choices=["approved", "rejected"]
    )
    approve.add_argument("--decided-by", required=True)
    approve.add_argument("--reason", required=True)
    approve.add_argument("--evidence", action="append", default=[])

    activate = subparsers.add_parser(
        "activate-resolution-task",
        help="Activate an approved resolution task if governance gates are satisfied.",
    )
    activate.add_argument("run_id")
    activate.add_argument("--gap", required=True)

    response = subparsers.add_parser(
        "record-task-response",
        help="Record an append-only department task response event.",
    )
    response.add_argument("run_id")
    response.add_argument("--task", required=True)
    response.add_argument("--response", required=True)
    response.add_argument("--artifact", action="append", default=[])
    response.add_argument("--message")
    response.add_argument("--responder", default="department-user")

    revalidate = subparsers.add_parser(
        "revalidate-closure",
        help="Report the current closure revalidation artifact for a task.",
    )
    revalidate.add_argument("run_id")
    revalidate.add_argument("--task", required=True)

    build_package = subparsers.add_parser(
        "build-audit-package",
        help="Report the current generated audit package manifest for a requirement.",
    )
    build_package.add_argument("run_id")
    build_package.add_argument("--requirement", required=True)

    review_package = subparsers.add_parser(
        "review-audit-package",
        help="Report the current adversarial quality review artifact for a package.",
    )
    review_package.add_argument("run_id")
    review_package.add_argument("--package", required=True)

    resume = subparsers.add_parser(
        "resume-run",
        help="Record a run-resume event for replayable coordination.",
    )
    resume.add_argument("run_id")

    replay = subparsers.add_parser(
        "replay-run",
        help="List replayable workflow events for a run.",
    )
    replay.add_argument("run_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-run":
        errors = JsonRunRepository().validate(args.run_id)
        if errors:
            print(json.dumps({"run_id": args.run_id, "valid": False, "errors": errors}, indent=2))
            return 1
        print(json.dumps({"run_id": args.run_id, "valid": True}, indent=2))
        return 0
    if args.command == "approve-decision":
        try:
            approval = JsonApprovalRepository().record(
                run_id=args.run_id,
                approval_type=args.type,
                target_id=args.target,
                decision=args.decision,
                decided_by=args.decided_by,
                reason=args.reason,
                evidence_references=args.evidence,
            )
        except ValueError as exc:
            print(json.dumps({"recorded": False, "error": str(exc)}, indent=2))
            return 1
        print(
            json.dumps(
                {
                    "recorded": True,
                    "approval_id": approval.approval_id,
                    "run_id": approval.run_id,
                    "type": approval.approval_type,
                    "target": approval.target_id,
                    "decision": approval.decision,
                },
                indent=2,
            )
        )
        return 0
    if args.command == "activate-resolution-task":
        store = AtomicJsonStore()
        path = get_liaison_tasks_path(args.run_id)
        payload = store.read(path, default={})
        tasks = payload.get("tasks", [])
        task = next((item for item in tasks if item.get("gap_id") == args.gap), None)
        if not task:
            print(json.dumps({"activated": False, "error": "task_not_found"}, indent=2))
            return 1
        ownership = store.read(
            get_ownership_assignments_path(args.run_id),
            default={},
        )
        assignment = next(
            (
                item
                for item in ownership.get("assignments", [])
                if item.get("gap_id") == args.gap
            ),
            None,
        )
        approvals = JsonApprovalRepository().list(args.run_id)
        approval = next(
            (
                item
                for item in reversed(approvals)
                if assignment
                and item.approval_type == "ownership_assignment"
                and item.target_id == assignment.get("assignment_id")
                and item.approval_state == "APPROVED"
            ),
            None,
        )
        if approval is None:
            print(
                json.dumps(
                    {
                        "activated": False,
                        "task_id": task["task_id"],
                        "error": "approval_required",
                    },
                    indent=2,
                )
            )
            return 1
        event = JsonEventRepository().append(
            run_id=args.run_id,
            event_type="TaskActivated",
            aggregate_type="task",
            aggregate_id=task["task_id"],
            actor="cli",
            payload={
                "gap_id": args.gap,
                "approval_id": approval.approval_id,
                "authorization_event_id": approval.transition_event_id,
                "original_task_artifact_unchanged": True,
            },
        )
        projection = ResolutionTaskState(
            run_id=args.run_id,
            task_id=task["task_id"],
            issue_id=task["issue_id"],
            gap_id=task["gap_id"],
            status="active",
            approval_ids=[approval.approval_id],
            approval_event_ids=[approval.transition_event_id]
            if approval.transition_event_id
            else [],
            last_event_id=event.event_id,
        )
        states_path = get_resolution_task_state_path(args.run_id)
        states = store.read(states_path, default={})
        states[task["task_id"]] = projection
        store.write(states_path, states)
        print(
            json.dumps(
                {
                    "activated": True,
                    "task_id": task["task_id"],
                    "event_id": event.event_id,
                    "task_state": str(states_path.resolve()),
                },
                indent=2,
            )
        )
        return 0
    if args.command == "record-task-response":
        store = AtomicJsonStore()
        task_payload = store.read(get_liaison_tasks_path(args.run_id), default={})
        task = next(
            (
                item
                for item in task_payload.get("tasks", [])
                if item.get("task_id") == args.task
            ),
            None,
        )
        if task is None:
            print(json.dumps({"recorded": False, "error": "task_not_found"}, indent=2))
            return 1
        states_path = get_resolution_task_state_path(args.run_id)
        states = store.read(states_path, default={})
        previous = states.get(args.task, {})
        if previous.get("status") not in {
            "active",
            "acknowledged",
            "evidence_submitted",
        }:
            print(
                json.dumps(
                    {
                        "recorded": False,
                        "task_id": args.task,
                        "error": "task_not_active",
                    },
                    indent=2,
                )
            )
            return 1
        event = JsonEventRepository().append(
            run_id=args.run_id,
            event_type="EvidenceSubmitted"
            if args.response == "evidence_submitted"
            else "TaskResponseRecorded",
            aggregate_type="task",
            aggregate_id=args.task,
            actor=args.responder,
            payload={
                "response": args.response,
                "message": args.message,
                "artifacts": args.artifact,
            },
        )
        projection = ResolutionTaskState(
            run_id=args.run_id,
            task_id=args.task,
            issue_id=task["issue_id"],
            gap_id=task["gap_id"],
            status=(
                "evidence_submitted"
                if args.response == "evidence_submitted"
                else previous.get("status", "active")
            ),
            approval_ids=previous.get("approval_ids", []),
            approval_event_ids=previous.get("approval_event_ids", []),
            response_event_ids=[
                *previous.get("response_event_ids", []),
                event.event_id,
            ],
            submitted_artifacts=list(
                dict.fromkeys(
                    [
                        *previous.get("submitted_artifacts", []),
                        *args.artifact,
                    ]
                )
            ),
            last_event_id=event.event_id,
        )
        states[args.task] = projection
        store.write(states_path, states)
        print(
            json.dumps(
                {
                    "recorded": True,
                    "event_id": event.event_id,
                    "task_status": projection.status,
                    "task_state": str(states_path.resolve()),
                },
                indent=2,
            )
        )
        return 0
    if args.command == "revalidate-closure":
        path = get_closure_report_path(args.run_id)
        exists = path.exists()
        print(
            json.dumps(
                {
                    "available": exists,
                    "task": args.task,
                    "closure_report": str(path.resolve()) if exists else None,
                },
                indent=2,
            )
        )
        return 0 if exists else 1
    if args.command == "build-audit-package":
        path = get_audit_package_manifest_path(args.run_id)
        exists = path.exists()
        print(
            json.dumps(
                {
                    "available": exists,
                    "requirement": args.requirement,
                    "package_manifest": str(path.resolve()) if exists else None,
                },
                indent=2,
            )
        )
        return 0 if exists else 1
    if args.command == "review-audit-package":
        path = get_quality_review_path(args.run_id)
        exists = path.exists()
        print(
            json.dumps(
                {
                    "available": exists,
                    "package": args.package,
                    "quality_review": str(path.resolve()) if exists else None,
                },
                indent=2,
            )
        )
        return 0 if exists else 1
    if args.command == "resume-run":
        event = JsonEventRepository().append(
            run_id=args.run_id,
            event_type="RunResumed",
            aggregate_type="run",
            aggregate_id=args.run_id,
            actor="cli",
        )
        print(json.dumps({"resumed": True, "event_id": event.event_id}, indent=2))
        return 0
    if args.command == "replay-run":
        events = JsonEventRepository().list(args.run_id)
        print(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "events": [event.model_dump(mode="json") for event in events],
                },
                indent=2,
            )
        )
        return 0

    mode = {
        "run-pipeline": RunMode.FULL,
        "collect": RunMode.COLLECT_ONLY,
        "classify": RunMode.CLASSIFY_ONLY,
        "integrity": RunMode.INTEGRITY_ONLY,
    }[args.command]
    sources = [str(Path(source).expanduser().resolve()) for source in args.source]
    request = SupervisorRequest(
        source_directories=sources,
        department_scope=args.departments,
        academic_year=args.academic_year,
        requirement_scope=args.requirements,
        requested_by=args.requested_by,
        run_mode=mode,
        objective=args.objective,
        maximum_agent_rounds=args.max_agent_rounds,
        maximum_replans_per_agent=args.max_replans,
        human_approval_for_final_decision=args.require_human_approval,
        institutional_claims=args.claim,
        resume_run_id=getattr(args, "from_run", None),
    )
    result = Supervisor().run(request)
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "status": result.status,
                "registered": result.total_evidence_registered,
                "classified": result.total_documents_classified,
                "findings": result.total_findings,
                "gaps": result.total_gaps,
                "claims": result.total_claims,
                "resolution_gaps": result.total_resolution_gaps,
                "assignments": result.total_ownership_assignments,
                "canonical_issues": result.total_canonical_issues,
                "resolution_tasks": result.total_resolution_tasks,
                "closure_checks": result.total_closure_checks,
                "resolved_issues": result.resolved_issues,
                "package_eligible_evidence": result.package_eligible_evidence,
                "quality_required_corrections": result.quality_required_corrections,
                "goal": result.top_level_goal_id,
                "supervisor_rounds": result.supervisor_rounds,
                "final_decision": result.final_decision_path,
                "extended_report": result.extended_report_path,
                "quality_review": result.quality_review_output_path,
                "audit_package_bundle": result.audit_package_bundle_path,
                "policy_manifest": result.policy_manifest_path,
                "observability_metrics": result.observability_metrics_path,
                "manifest": result.run_manifest_path,
            },
            indent=2,
        )
    )
    return 1 if result.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
