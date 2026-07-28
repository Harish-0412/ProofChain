from __future__ import annotations

from proofchain.core import paths
from proofchain.production import PhaseTwoSupervisor
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.agentic import Goal
from proofchain.schemas.institutional import PhaseTwoRequest


def test_phase_two_supervisor_runs_six_agents_and_resynchronizes(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS_DIR", tmp_path / "runs")
    run_id = "RUN-PHASE2-E2E"
    store = AtomicJsonStore()
    run_dir = paths.get_run_dir(run_id)
    run_dir.mkdir(parents=True)
    bundle = paths.get_audit_package_bundle_path(run_id)
    bundle.write_bytes(b"draft package with unresolved findings")
    store.write(
        paths.get_pipeline_result_path(run_id),
        {
            "run_id": run_id,
            "status": "blocked",
            "academic_year": "2025-2026",
            "department_scope": ["CSE"],
            "requirement_scope": ["C3.2.1"],
        },
    )
    store.write(
        run_dir / "phase_one_result.json",
        {"run_id": run_id, "status": "completed"},
    )
    store.write(
        paths.get_quality_review_path(run_id),
        {
            "package_id": f"PKG-{run_id}",
            "quality_status": "return_for_correction",
        },
    )
    top = Goal(
        goal_id=f"GOAL-{run_id}-TOP",
        run_id=run_id,
        assigned_agent="supervisor",
        objective="Govern institutional audit readiness.",
        goal_type="institutional",
    )
    coordination = JsonCoordinationRepository(store)
    coordination.initialize(top, [])
    JsonEventRepository().append(
        run_id=run_id,
        event_type="RunCreated",
        aggregate_type="run",
        aggregate_id=run_id,
    )

    result = PhaseTwoSupervisor(coordination=coordination, store=store).run(
        PhaseTwoRequest(run_id=run_id, department_id="CSE")
    )

    assert result.status == "completed_with_warnings"
    assert set(result.agent_statuses) == {
        "schema_evolution",
        "policy_lifecycle",
        "tenant_governance",
        "external_submission",
        "continuous_evaluation",
        "knowledge_retrieval",
    }
    assert all(status in {"completed", "completed_with_warnings"} for status in result.agent_statuses.values())
    assert result.persistence_synchronized is True
    assert (run_dir / "phase_two_result.json").exists()
    assert (run_dir / "schema_evolution_report.json").exists()
    assert (run_dir / "policy_lifecycle_report.json").exists()
    assert (run_dir / "tenant_access_decision.json").exists()
    assert (run_dir / "external_submission_report.json").exists()
    assert (run_dir / "continuous_evaluation_report.json").exists()
    assert (run_dir / "governed_knowledge_retrieval_report.json").exists()
    submission = store.read(run_dir / "external_submission_report.json")
    assert submission["submission_status"] == "not_submitted"
    assert submission["eligibility_decision"] == "NOT_ELIGIBLE"

