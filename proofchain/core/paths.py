"""
core/paths.py
Central path management for ProofChain.

All file system paths are resolved relative to the project root.
Agents and services must use these path helpers instead of hardcoding paths.
"""

from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# Project Root
# ---------------------------------------------------------------------------

# Resolve from this file: proofchain/core/paths.py -> proofchain/core -> proofchain -> ROOT
ROOT = Path(__file__).resolve().parents[2]

PROOFCHAIN_PACKAGE = ROOT / "proofchain"
POLICIES_DIR = PROOFCHAIN_PACKAGE / "policies"


# ---------------------------------------------------------------------------
# Sample Data
# ---------------------------------------------------------------------------

SAMPLE_DATA = ROOT / "sample_data"
DEPARTMENTS_DIR = SAMPLE_DATA / "departments"
REQUIREMENTS_DIR = SAMPLE_DATA / "requirements"


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

OUTPUTS_DIR = ROOT / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
REGISTRY_DIR = OUTPUTS_DIR / "registry"
CLASSIFICATION_DIR = OUTPUTS_DIR / "classification"
INTEGRITY_DIR = OUTPUTS_DIR / "integrity"
TRACES_DIR = OUTPUTS_DIR / "traces"
REPORTS_DIR = OUTPUTS_DIR / "reports"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_DIR = ROOT / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"
DOCUMENT_TYPES_FILE = CONFIG_DIR / "document_types.yaml"
REQUIREMENT_MAPPING_FILE = CONFIG_DIR / "requirement_mapping.yaml"
ORGANISATION_ROLES_FILE = CONFIG_DIR / "organisation_roles.yaml"


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

RULES_DIR = ROOT / "proofchain" / "rules"
COMMON_RULES_FILE = RULES_DIR / "common_rules.yaml"
EVENT_EVIDENCE_RULES_FILE = RULES_DIR / "event_evidence_rules.yaml"
ACADEMIC_YEAR_RULES_FILE = RULES_DIR / "academic_year_rules.yaml"
REQUIRED_DOCUMENT_RULES_FILE = RULES_DIR / "required_document_rules.yaml"


# ---------------------------------------------------------------------------
# Run-specific output helpers
# ---------------------------------------------------------------------------

def get_run_dir(run_id: str) -> Path:
    """Return the output directory for a specific pipeline run."""
    return RUNS_DIR / run_id


def get_run_manifest_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "run_manifest.json"


def get_evidence_registry_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "evidence_registry.json"


def get_classified_evidence_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "classified_evidence.json"


def get_evidence_bundles_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "evidence_bundles.json"


def get_integrity_findings_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "integrity_findings.json"


def get_evidence_gaps_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "evidence_gaps.json"


def get_integrity_summary_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "integrity_summary.json"


def get_pipeline_result_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "pipeline_result.json"


def get_pipeline_trace_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "pipeline_trace.jsonl"


def get_errors_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "errors.json"


def get_synchronization_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "synchronization.json"


def get_top_level_goal_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "top_level_goal.json"


def get_goal_graph_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "goal_graph.json"


def get_final_decision_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "final_decision.json"


def get_claim_decisions_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "claim_decisions.json"


def get_gap_resolution_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "gap_resolution_portfolio.json"


def get_ownership_assignments_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "ownership_assignments.json"


def get_extended_pipeline_report_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "claim_resolution_ownership_report.json"


def get_human_approvals_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "human_approvals.json"


def get_canonical_issues_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "canonical_issues.json"


def get_liaison_tasks_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "resolution_tasks_detailed.json"


def get_resolution_task_state_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "resolution_task_state.json"


def get_communications_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "communications.json"


def get_closure_report_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "closure_revalidation_report.json"


def get_audit_package_manifest_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "audit_package_manifest.json"


def get_quality_review_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "quality_review_report.json"


def get_workflow_events_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "workflow_events.jsonl"


def get_component_registry_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "component_registry.json"


def get_security_scan_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "security_scan_result.json"


def get_prompt_injection_findings_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "prompt_injection_findings.json"


def get_pii_redaction_manifest_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "pii_redaction_manifest.json"


def get_access_decision_log_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "access_decision_log.jsonl"


def get_policy_manifest_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "governance_policy_manifest.json"


def get_model_governance_manifest_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "model_governance_manifest.json"


def get_supervisor_rounds_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "supervisor_rounds.json"


def get_observability_metrics_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "observability_metrics.json"


def get_audit_package_bundle_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "audit_package_internal.zip"


def get_coordination_dir(run_id: str) -> Path:
    return get_run_dir(run_id) / "coordination"


def get_coordination_state_path(run_id: str) -> Path:
    return get_coordination_dir(run_id) / "coordination_state.json"


def get_coordination_artifact_path(run_id: str, name: str) -> Path:
    return get_coordination_dir(run_id) / name


def get_agentic_agent_dir(run_id: str, agent_name: str) -> Path:
    aliases = {
        "evidence_collector": "collector",
        "evidence_classification": "classification",
        "evidence_integrity": "integrity",
        "supervisor": "supervisor",
    }
    return get_run_dir(run_id) / aliases.get(agent_name, agent_name)


def get_agentic_agent_path(run_id: str, agent_name: str, name: str) -> Path:
    return get_agentic_agent_dir(run_id, agent_name) / name


def get_global_evidence_index_path() -> Path:
    return REGISTRY_DIR / "evidence_index.json"


def ensure_run_dir(run_id: str) -> Path:
    """Create and return the run directory."""
    run_dir = get_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
