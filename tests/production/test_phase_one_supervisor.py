from __future__ import annotations

from proofchain.core import paths
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.agentic import Goal
from proofchain.schemas.production import PhaseOneRequest, TelemetryRecord
from proofchain.production import PhaseOneSupervisor


def test_phase_one_supervisor_runs_six_agents_and_persists_recovery(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS_DIR", tmp_path / "runs")
    run_id = "RUN-PHASE1-E2E"
    run_dir = paths.get_run_dir(run_id)
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("Approved accreditation evidence.", encoding="utf-8")
    store = AtomicJsonStore()
    store.write(
        paths.get_pipeline_result_path(run_id),
        {
            "run_id": run_id,
            "academic_year": "2025-2026",
            "department_scope": ["CSE"],
            "requirement_scope": ["C3.2.1"],
        },
    )
    store.write(
        paths.get_evidence_registry_path(run_id),
        [{"absolute_path": str(evidence)}],
    )
    top = Goal(
        goal_id=f"GOAL-{run_id}-TOP",
        run_id=run_id,
        assigned_agent="supervisor",
        objective="Validate audit readiness.",
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

    result = PhaseOneSupervisor(coordination=coordination, store=store).run(
        PhaseOneRequest(
            run_id=run_id,
            security_paths=[str(evidence)],
            telemetry=[
                TelemetryRecord(
                    source="phase-one",
                    signal_type="metric",
                    status="healthy",
                    message="Control plane responsive",
                )
            ],
        )
    )

    assert result.status == "completed"
    assert set(result.agent_statuses) == {
        "operational_persistence",
        "workflow_continuation",
        "identity_authorization",
        "integration_notification",
        "security_inspection",
        "reliability_incident_response",
    }
    assert all(status == "completed" for status in result.completion_decisions.values())
    assert (run_dir / "operational_state.db").exists()
    assert (run_dir / "phase_one_result.json").exists()
    assert (run_dir / "persistence_recovery_report.json").exists()
    assert (run_dir / "continuation_reexecution_plan.json").exists()
    assert (run_dir / "authorization_decision.json").exists()
    assert (run_dir / "notification_delivery_report.json").exists()
    assert (run_dir / "phase_one_security_report.json").exists()
    assert (run_dir / "incident_reliability_report.json").exists()


def test_phase_one_notification_is_idempotent_on_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS_DIR", tmp_path / "runs")
    run_id = "RUN-PHASE1-RESUME"
    store = AtomicJsonStore()
    store.write(
        paths.get_pipeline_result_path(run_id),
        {
            "run_id": run_id,
            "academic_year": "2025-2026",
            "department_scope": ["CSE"],
            "requirement_scope": ["C3.2.1"],
        },
    )
    store.write(paths.get_evidence_registry_path(run_id), [])
    top = Goal(
        goal_id=f"GOAL-{run_id}-TOP",
        run_id=run_id,
        assigned_agent="supervisor",
        objective="Validate audit readiness.",
        goal_type="institutional",
    )
    coordination = JsonCoordinationRepository(store)
    coordination.initialize(top, [])
    supervisor = PhaseOneSupervisor(coordination=coordination, store=store)

    supervisor.run(PhaseOneRequest(run_id=run_id))
    result = supervisor.run(PhaseOneRequest(run_id=run_id))
    report = store.read(paths.get_run_dir(run_id) / "notification_delivery_report.json")

    assert result.status == "completed_with_warnings"
    assert report["duplicate_suppressed"] is True
    assert report["delivery_status"] == "suppressed"

