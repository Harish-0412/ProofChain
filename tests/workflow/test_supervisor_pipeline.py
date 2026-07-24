"""End-to-end workflow and synchronization validation."""

from __future__ import annotations

import json
import shutil
import zipfile

from proofchain.agents.supervisor import Supervisor
from proofchain.core.enums import RunMode
from proofchain.core.paths import (
    DEPARTMENTS_DIR,
    get_classified_evidence_path,
    get_evidence_registry_path,
    get_integrity_findings_path,
    get_run_dir,
    get_synchronization_path,
    get_top_level_goal_path,
    get_goal_graph_path,
    get_coordination_state_path,
    get_coordination_artifact_path,
    get_final_decision_path,
    get_agentic_agent_path,
    get_claim_decisions_path,
    get_gap_resolution_path,
    get_ownership_assignments_path,
    get_extended_pipeline_report_path,
    get_canonical_issues_path,
    get_liaison_tasks_path,
    get_communications_path,
    get_closure_report_path,
    get_audit_package_manifest_path,
    get_quality_review_path,
    get_workflow_events_path,
    get_component_registry_path,
    get_policy_manifest_path,
    get_model_governance_manifest_path,
    get_supervisor_rounds_path,
    get_observability_metrics_path,
    get_audit_package_bundle_path,
)
from proofchain.repositories.json_run_repository import JsonRunRepository
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_store import file_sha256
from proofchain.schemas.workflow import SupervisorRequest


REQUIREMENTS = ["C3.2.1", "C5.1.3", "C6.3.2", "C7.1.1", "C1.2.1"]


def request(mode=RunMode.FULL, resume_run_id=None):
    return SupervisorRequest(
        source_directories=[str(DEPARTMENTS_DIR)],
        department_scope=["CSE"],
        academic_year="2025-2026",
        requirement_scope=REQUIREMENTS,
        requested_by="pytest",
        run_mode=mode,
        resume_run_id=resume_run_id,
    )


def test_full_pipeline_detects_injected_defects_and_validates_sync():
    result = Supervisor().run(request())
    try:
        assert result.status == "blocked"
        assert result.total_evidence_registered == 15
        assert result.total_documents_classified == 15
        assert result.total_findings == 9
        assert result.total_gaps == 5
        assert JsonRunRepository().validate(result.run_id) == []
        assert result.top_level_goal_id
        assert result.supervisor_rounds >= 1
        assert get_top_level_goal_path(result.run_id).exists()
        assert get_goal_graph_path(result.run_id).exists()
        assert get_coordination_state_path(result.run_id).exists()
        assert get_final_decision_path(result.run_id).exists()
        assert get_claim_decisions_path(result.run_id).exists()
        assert get_gap_resolution_path(result.run_id).exists()
        assert get_ownership_assignments_path(result.run_id).exists()
        assert get_extended_pipeline_report_path(result.run_id).exists()
        assert result.total_claims > 0
        assert result.total_resolution_gaps > 0
        assert result.total_ownership_assignments == result.total_resolution_gaps
        assert result.total_canonical_issues == result.total_resolution_gaps
        assert result.blocking_canonical_issues > 0
        assert result.total_resolution_tasks == result.total_canonical_issues
        assert result.total_closure_checks == result.total_canonical_issues
        assert result.resolved_issues == 0
        assert result.package_eligible_evidence > 0
        assert result.quality_required_corrections > 0
        assert get_canonical_issues_path(result.run_id).exists()
        assert get_liaison_tasks_path(result.run_id).exists()
        assert get_communications_path(result.run_id).exists()
        assert get_closure_report_path(result.run_id).exists()
        assert get_audit_package_manifest_path(result.run_id).exists()
        assert get_quality_review_path(result.run_id).exists()
        assert get_workflow_events_path(result.run_id).exists()
        assert get_component_registry_path(result.run_id).exists()
        assert get_policy_manifest_path(result.run_id).exists()
        assert get_model_governance_manifest_path(result.run_id).exists()
        assert get_supervisor_rounds_path(result.run_id).exists()
        assert get_observability_metrics_path(result.run_id).exists()
        assert get_audit_package_bundle_path(result.run_id).exists()
        assert JsonEventRepository.validate_chain(result.run_id) == []

        final_decision = json.loads(
            get_final_decision_path(result.run_id).read_text(encoding="utf-8")
        )
        assert final_decision["final_status"] == "blocked"
        assert final_decision["agent_name"] == "supervisor"

        coordination = json.loads(
            get_coordination_state_path(result.run_id).read_text(encoding="utf-8")
        )
        assert coordination["open_messages"] == []
        assert len(coordination["completion_claims"]) >= 7
        assert get_coordination_artifact_path(
            result.run_id, "resolution_tasks.json"
        ).exists()
        for agent_name in (
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
        ):
            assert get_agentic_agent_path(
                result.run_id, agent_name, "goal.json"
            ).exists()
            assert get_agentic_agent_path(
                result.run_id, agent_name, "plans.json"
            ).exists()
            assert get_agentic_agent_path(
                result.run_id, agent_name, "completion_decision.json"
            ).exists()
            assert get_agentic_agent_path(
                result.run_id, agent_name, "working_memory.json"
            ).exists()
        goal_graph = json.loads(
            get_goal_graph_path(result.run_id).read_text(encoding="utf-8")
        )
        primary_agents = {
            item["assigned_agent"]
            for item in goal_graph["goals"]
            if item["goal_type"]
            in {
                "validate_claim_defensibility",
                "plan_gap_resolution",
                "resolve_evidence_ownership",
                "coordinate_resolution_execution",
                "revalidate_issue_closure",
                "compose_audit_package",
                "challenge_audit_package",
            }
        }
        assert primary_agents == {
            "claim_intelligence",
            "adaptive_gap_resolution",
            "accountability_ownership",
            "department_liaison",
            "closure_revalidation",
            "audit_package_composer",
            "adversarial_quality_review",
        }
        assert any(
            item["goal_type"].startswith("resolve_")
            and item["goal_type"] != "resolve_evidence_ownership"
            for item in goal_graph["goals"]
        )

        findings = json.loads(
            get_integrity_findings_path(result.run_id).read_text(encoding="utf-8")
        )
        rule_ids = {finding["rule_id"] for finding in findings}
        assert {
            "DUP-001",
            "SIGN-001",
            "DUP-STUDENT-001",
            "EVT-COUNT-001",
            "DOC-001",
        }.issubset(rule_ids)

        checkpoints = json.loads(
            get_synchronization_path(result.run_id).read_text(encoding="utf-8")
        )
        assert [item["stage_name"] for item in checkpoints] == [
            "collection",
            "classification",
            "integrity",
            "claim_intelligence",
            "adaptive_gap_resolution",
            "accountability_ownership",
            "department_liaison",
            "closure_revalidation",
            "audit_package_composer",
            "adversarial_quality_review",
        ]
        for index in range(1, len(checkpoints)):
            assert checkpoints[index]["upstream_sha256"] == checkpoints[index - 1]["output"]["sha256"]

        issue_ledger = json.loads(
            get_canonical_issues_path(result.run_id).read_text(encoding="utf-8")
        )
        assert issue_ledger["canonical_issues"] == result.total_canonical_issues
        assert issue_ledger["raw_findings"] == result.total_findings

        report = json.loads(
            get_extended_pipeline_report_path(result.run_id).read_text(encoding="utf-8")
        )
        assert report["gap_assessment"]["projection_type"] == "counterfactual"
        assert report["gap_assessment"]["not_an_approval"] is True
        assert report["gap_assessment"]["canonical_issues"] == result.total_canonical_issues
        assert report["lifecycle_summary"]["quality_required_corrections"] > 0

        registry = json.loads(
            get_component_registry_path(result.run_id).read_text(encoding="utf-8")
        )
        by_id = {item["component_id"]: item for item in registry["components"]}
        assert by_id["department_liaison"]["component_type"] == "goal_agent"
        assert by_id["message_drafter"]["component_type"] == "deterministic_specialist_module"

        package = json.loads(
            get_audit_package_manifest_path(result.run_id).read_text(encoding="utf-8")
        )
        manifest = package["manifest"]
        assert manifest["bundle_format"] == "zip"
        assert manifest["external_submission_approved"] is False
        assert manifest["bundle_sha256"] == file_sha256(
            get_audit_package_bundle_path(result.run_id)
        )
        with zipfile.ZipFile(get_audit_package_bundle_path(result.run_id)) as archive:
            names = set(archive.namelist())
            assert "package_manifest.json" in names
            assert "claim_evidence_index.json" in names
            assert "evidence_index.csv" in names
            assert any(name.startswith("evidence/") for name in names)

        policy_manifest = json.loads(
            get_policy_manifest_path(result.run_id).read_text(encoding="utf-8")
        )
        assert len(policy_manifest["policies"]) == 7
        assert policy_manifest["policy_fingerprint"]

        model_governance = json.loads(
            get_model_governance_manifest_path(result.run_id).read_text(
                encoding="utf-8"
            )
        )
        assert model_governance["total_external_model_calls"] == 0
        assert {
            profile["execution_mode"]
            for profile in model_governance["profiles"]
        } == {"deterministic"}

        scheduler_rounds = json.loads(
            get_supervisor_rounds_path(result.run_id).read_text(encoding="utf-8")
        )
        assert scheduler_rounds[0]["phase"] == "preflight"
        assert scheduler_rounds[-1]["phase"] == "terminal"

        metrics = json.loads(
            get_observability_metrics_path(result.run_id).read_text(encoding="utf-8")
        )
        assert metrics["primary_agent_count"] == 10
        assert metrics["specialist_module_count"] == 43
        assert metrics["checkpoint_count"] == 10
        assert metrics["workflow_event_count"] > 0
    finally:
        shutil.rmtree(get_run_dir(result.run_id), ignore_errors=True)


def test_stage_only_runs_resume_from_committed_artifacts():
    collected = Supervisor().run(request(RunMode.COLLECT_ONLY))
    classified = None
    integrity = None
    try:
        assert get_evidence_registry_path(collected.run_id).exists()
        classified = Supervisor().run(
            request(RunMode.CLASSIFY_ONLY, resume_run_id=collected.run_id)
        )
        assert classified.total_documents_classified == 15
        assert get_classified_evidence_path(classified.run_id).exists()
        assert JsonRunRepository().validate(classified.run_id) == []

        integrity = Supervisor().run(
            request(RunMode.INTEGRITY_ONLY, resume_run_id=classified.run_id)
        )
        assert integrity.total_findings == 9
        assert integrity.total_gaps == 5
        assert JsonRunRepository().validate(integrity.run_id) == []
    finally:
        for item in (collected, classified, integrity):
            if item is not None:
                shutil.rmtree(get_run_dir(item.run_id), ignore_errors=True)
