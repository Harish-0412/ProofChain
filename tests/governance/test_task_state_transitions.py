"""Approval-driven task transitions preserve immutable agent artifacts."""

from __future__ import annotations

import shutil
import uuid

from proofchain.cli import main
from proofchain.core.paths import (
    get_liaison_tasks_path,
    get_ownership_assignments_path,
    get_resolution_task_state_path,
    get_run_dir,
)
from proofchain.repositories.json_approval_repository import JsonApprovalRepository
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import AtomicJsonStore


def test_approval_activates_projected_task_state_without_mutating_task_artifact():
    run_id = f"RUN-TASK-{uuid.uuid4().hex[:8].upper()}"
    run_dir = get_run_dir(run_id)
    run_dir.mkdir(parents=True)
    store = AtomicJsonStore()
    task_path = get_liaison_tasks_path(run_id)
    store.write(
        task_path,
        {
            "tasks": [
                {
                    "task_id": "TASK-RGAP-0001",
                    "issue_id": "ISS-0001",
                    "gap_id": "RGAP-0001",
                    "status": "approval_required",
                    "approval_event_ids": [],
                }
            ]
        },
    )
    store.write(
        get_ownership_assignments_path(run_id),
        {
            "assignments": [
                {
                    "assignment_id": "ASN-RGAP-0001",
                    "gap_id": "RGAP-0001",
                    "status": "recommended",
                }
            ]
        },
    )
    original_task_bytes = task_path.read_bytes()
    try:
        assert (
            main(
                [
                    "activate-resolution-task",
                    run_id,
                    "--gap",
                    "RGAP-0001",
                ]
            )
            == 1
        )
        JsonApprovalRepository().record(
            run_id=run_id,
            approval_type="ownership_assignment",
            target_id="ASN-RGAP-0001",
            decision="approved",
            decided_by="iqac-chair",
            reason="Authorize governed department task activation.",
        )
        assert (
            main(
                [
                    "activate-resolution-task",
                    run_id,
                    "--gap",
                    "RGAP-0001",
                ]
            )
            == 0
        )
        assert task_path.read_bytes() == original_task_bytes
        state = store.read(get_resolution_task_state_path(run_id))
        assert state["TASK-RGAP-0001"]["status"] == "active"
        assert state["TASK-RGAP-0001"]["approval_ids"]

        assert (
            main(
                [
                    "record-task-response",
                    run_id,
                    "--task",
                    "TASK-RGAP-0001",
                    "--response",
                    "evidence_submitted",
                    "--artifact",
                    "EVD-CORRECTION-001",
                ]
            )
            == 0
        )
        state = store.read(get_resolution_task_state_path(run_id))
        assert state["TASK-RGAP-0001"]["status"] == "evidence_submitted"
        assert state["TASK-RGAP-0001"]["submitted_artifacts"] == [
            "EVD-CORRECTION-001"
        ]
        assert JsonEventRepository.validate_chain(run_id) == []
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
