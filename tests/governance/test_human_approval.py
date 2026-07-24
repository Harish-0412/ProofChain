"""Human approval records require a real governed target."""

from __future__ import annotations

import shutil
import uuid

import pytest

from proofchain.core.paths import (
    get_claim_decisions_path,
    get_human_approvals_path,
    get_run_dir,
)
from proofchain.repositories.json_approval_repository import JsonApprovalRepository
from proofchain.repositories.json_store import AtomicJsonStore


def test_human_approval_is_explicit_validated_and_auditable():
    run_id = f"RUN-APPROVAL-{uuid.uuid4().hex[:8].upper()}"
    run_dir = get_run_dir(run_id)
    run_dir.mkdir(parents=True)
    AtomicJsonStore().write(
        get_claim_decisions_path(run_id),
        {"decisions": [{"claim_id": "CLM-001"}]},
    )
    repository = JsonApprovalRepository()
    try:
        record = repository.record(
            run_id=run_id,
            approval_type="claim_revision",
            target_id="CLM-001",
            decision="approved",
            decided_by="iqac-chair",
            reason="Revised value matches verified attendance.",
            evidence_references=["EVD-ATTENDANCE"],
        )
        assert record.decision == "approved"
        assert record.decided_by == "iqac-chair"
        assert get_human_approvals_path(run_id).exists()
        assert repository.list(run_id) == [record]
        assert record.recommendation_hash
        assert all(record.authorization_checks.values())

        with pytest.raises(ValueError):
            repository.record(
                run_id=run_id,
                approval_type="claim_revision",
                target_id="CLM-MISSING",
                decision="approved",
                decided_by="iqac-chair",
                reason="Invalid target.",
            )
        with pytest.raises(ValueError, match="not authorized"):
            repository.record(
                run_id=run_id,
                approval_type="claim_revision",
                target_id="CLM-001",
                decision="approved",
                decided_by="unknown-reviewer",
                reason="Unknown actors must be denied by default.",
            )
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
