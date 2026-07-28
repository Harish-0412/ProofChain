from __future__ import annotations

from datetime import datetime, timedelta, timezone

from proofchain.repositories.sql_event_repository import SqliteEventRepository
from proofchain.schemas.production import (
    AuthorizationInput,
    DelegationGrant,
    FingerprintRecord,
    PriorApproval,
    RoleGrant,
)
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.authorization import evaluate_authorization
from proofchain.services.continuation import calculate_impact, fingerprint_references


def workflow(run_id: str = "RUN-PHASE1-UNIT") -> WorkflowContext:
    return WorkflowContext(
        run_id=run_id,
        correlation_id=f"CORR-{run_id}",
        requested_by="USR-001",
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )


def test_sql_event_store_rebuilds_and_validates_hash_chain(tmp_path):
    repository = SqliteEventRepository(tmp_path / "events.db")
    first = repository.append(
        run_id="RUN-SQL",
        event_type="RunCreated",
        aggregate_type="run",
        aggregate_id="RUN-SQL",
    )
    second = repository.append(
        run_id="RUN-SQL",
        event_type="TaskActivated",
        aggregate_type="task",
        aggregate_id="TASK-001",
        payload={"approval_id": "APR-001"},
    )

    assert first.sequence == 1
    assert second.sequence == 2
    assert second.previous_event_hash == first.event_hash
    assert repository.validate_chain("RUN-SQL") == []
    version, state_hash = repository.create_snapshot("RUN-SQL")
    assert version == 2
    assert len(state_hash) == 64
    assert repository.rebuild_state("RUN-SQL")["aggregates"]["task:TASK-001"]["version"] == 1


def test_authorization_blocks_self_approval_even_with_permission():
    request = AuthorizationInput(
        workflow=workflow(),
        subject_id="USR-001",
        identity_verified=True,
        action="approve_evidence",
        resource_id="EVD-001",
        tenant_id="TENANT-A",
        department_id="CSE",
        role_grants=[
            RoleGrant(
                role="approver",
                tenant_id="TENANT-A",
                departments=["CSE"],
                permissions=["approve_evidence"],
            )
        ],
        resource_creator_id="USR-001",
    )

    decision, permissions, reasons, _, _, separation_passed = evaluate_authorization(request)

    assert decision == "DENIED"
    assert "approve_evidence" in permissions
    assert not separation_passed
    assert any("self-approval" in reason for reason in reasons)


def test_authorization_supports_scoped_delegation_and_dual_approval():
    now = datetime.now(tz=timezone.utc)
    request = AuthorizationInput(
        workflow=workflow(),
        subject_id="USR-002",
        identity_verified=True,
        action="submit_package",
        resource_id="PKG-001",
        tenant_id="TENANT-A",
        department_id="CSE",
        delegations=[
            DelegationGrant(
                delegation_id="DEL-001",
                delegated_by="USR-ADMIN",
                delegated_to="USR-002",
                permissions=["submit_package"],
                tenant_id="TENANT-A",
                departments=["CSE"],
                reason="Accreditation submission coverage",
                valid_from=now - timedelta(hours=1),
                valid_until=now + timedelta(hours=1),
            )
        ],
        prior_approvals=[
            PriorApproval(approver_id="USR-003", decision="approved")
        ],
        high_risk=True,
    )

    decision, _, _, required, valid, separation_passed = evaluate_authorization(request)

    assert decision == "AUTHORIZED"
    assert required == 2
    assert valid == 1
    assert separation_passed


def test_continuation_fingerprints_and_traverses_dependencies(tmp_path):
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("corrected evidence", encoding="utf-8")
    current = fingerprint_references([str(evidence)])
    previous = [
        FingerprintRecord(
            reference=str(evidence.resolve()),
            sha256="0" * 64,
            entity_type="evidence",
        )
    ]
    graph = {
        str(evidence.resolve()): ["claim:C3.2.1"],
        "claim:C3.2.1": ["package:PKG-001"],
    }

    changed, stale, reusable, agents = calculate_impact(previous, current, graph)

    assert changed == [str(evidence.resolve())]
    assert stale == ["claim:C3.2.1", "package:PKG-001"]
    assert reusable == []
    assert "claim_intelligence" in agents
    assert "adversarial_quality_review" in agents

