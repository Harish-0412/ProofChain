from __future__ import annotations

from datetime import datetime, timedelta, timezone

from proofchain.schemas.institutional import (
    HistoricalPolicyCase,
    PolicyChange,
    ResourceShare,
    SchemaArtifact,
    TenantGovernanceInput,
    TenantGrant,
)
from proofchain.schemas.workflow import WorkflowContext
from proofchain.services.policy_lifecycle import (
    detect_policy_conflicts,
    simulate_policy,
    validate_policy_change,
)
from proofchain.services.schema_evolution import (
    analyze_compatibility,
    convert_artifacts,
)
from proofchain.services.tenant_governance import evaluate_tenant_access


def workflow() -> WorkflowContext:
    return WorkflowContext(
        run_id="RUN-PHASE2-UNIT",
        correlation_id="CORR-PHASE2-UNIT",
        requested_by="USR-001",
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=["C3.2.1"],
    )


def test_schema_evolution_detects_breaking_change_and_preserves_original():
    current = {
        "required": ["run_id"],
        "properties": {"run_id": {"type": "string"}},
    }
    target = {
        "required": ["run_id", "tenant_id"],
        "properties": {
            "run_id": {"type": "string"},
            "tenant_id": {"type": "string"},
        },
    }
    artifact = SchemaArtifact(
        artifact_id="ART-001",
        schema_version="1.0.0",
        payload={"run_id": "RUN-001"},
    )

    compatibility, breaking, steps = analyze_compatibility(current, target)
    converted = convert_artifacts(
        [artifact], "2.0.0", {}, {"tenant_id": "TENANT-A"}
    )

    assert compatibility == "migration_required"
    assert "New required field: tenant_id" in breaking
    assert steps
    assert artifact.payload == {"run_id": "RUN-001"}
    assert converted[0].converted_payload["tenant_id"] == "TENANT-A"
    assert converted[0].original_hash != converted[0].converted_hash


def test_policy_lifecycle_blocks_governance_bypass_and_preserves_history():
    change = PolicyChange(
        policy_id="submission-policy",
        base_version="1.0.0",
        proposed_version="2.0.0",
        reason="Unsafe test",
        document={
            "policy_id": "submission-policy",
            "schema_version": "1.0.0",
            "default_effect": "allow",
            "bypass_human_approval": True,
            "simulation_effect": "override",
            "simulated_decision": "approved",
        },
    )
    cases = [
        HistoricalPolicyCase(
            case_id="CASE-001",
            facts={},
            previous_decision="blocked",
        )
    ]

    assert validate_policy_change(change) == []
    conflicts = detect_policy_conflicts({}, change)
    outcomes = simulate_policy(cases, change)

    assert len(conflicts) == 2
    assert outcomes[0].changed is True
    assert outcomes[0].previous_decision == "blocked"


def test_tenant_governance_denies_cross_tenant_access_without_share():
    request = TenantGovernanceInput(
        workflow=workflow(),
        subject_id="USR-001",
        requested_tenant_id="TENANT-A",
        requested_department_id="CSE",
        action="read_evidence",
        resource_id="EVD-001",
        resource_tenant_id="TENANT-B",
        resource_department_id="CSE",
        grants=[
            TenantGrant(
                subject_id="USR-001",
                tenant_id="TENANT-A",
                departments=["CSE"],
                permissions=["read_evidence"],
            )
        ],
    )

    decision, _, share_id, reasons = evaluate_tenant_access(request)

    assert decision == "DENY"
    assert share_id is None
    assert any("cross-tenant share" in reason for reason in reasons)


def test_tenant_governance_allows_explicit_scoped_share():
    request = TenantGovernanceInput(
        workflow=workflow(),
        subject_id="USR-001",
        requested_tenant_id="TENANT-A",
        requested_department_id="CSE",
        action="read_evidence",
        resource_id="EVD-001",
        resource_tenant_id="TENANT-B",
        resource_department_id="CSE",
        grants=[
            TenantGrant(
                subject_id="USR-001",
                tenant_id="TENANT-A",
                departments=["CSE"],
                permissions=[],
            )
        ],
        shares=[
            ResourceShare(
                share_id="SHARE-001",
                resource_id="EVD-001",
                source_tenant_id="TENANT-B",
                target_tenant_id="TENANT-A",
                departments=["CSE"],
                permissions=["read_evidence"],
                approved=True,
                expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
            )
        ],
    )

    decision, permissions, share_id, _ = evaluate_tenant_access(request)

    assert decision == "ALLOW"
    assert "read_evidence" in permissions
    assert share_id == "SHARE-001"

