"""Phase 1 cognition profiles and agent-specific precision capabilities."""

from __future__ import annotations

from proofchain.schemas.cognition import CognitionProfile


CORE_AGENT_FEATURES = {
    "evidence_collector": "Evidence Acquisition Strategy",
    "evidence_classification": "Extraction Strategy Planner",
    "evidence_integrity": "Verification Coverage Matrix",
    "claim_intelligence": "Claim Fragility",
    "adaptive_gap_resolution": "Resolution Portfolio Optimizer",
    "accountability_ownership": "Explainable Responsibility Graph",
    "department_liaison": "Task Understandability Check",
    "closure_revalidation": "Closure Proof Bundle",
    "audit_package_composer": "Reviewer Journey Planner",
    "adversarial_quality_review": "Independent Reproduction",
}

PLATFORM_AGENT_FEATURES = {
    "operational_persistence": "State Reconstruction Proof",
    "workflow_continuation": "Minimal Safe Rerun Proof",
    "identity_authorization": "Authorization Explanation Graph",
    "integration_notification": "Delivery Correlation Proof",
    "security_inspection": "Evidence Trust Envelope",
    "reliability_incident_response": "Recovery Safety Proof",
    "schema_evolution": "Migration Compatibility Proof",
    "policy_lifecycle": "Policy Counterfactual Simulator",
    "tenant_governance": "Tenant Boundary Proof",
    "external_submission": "Submission Dry-Run Proof",
    "continuous_evaluation": "Agentic Release Gate",
    "knowledge_retrieval": "Retrieval Provenance Proof",
}

ALL_AGENT_FEATURES = {**CORE_AGENT_FEATURES, **PLATFORM_AGENT_FEATURES}

ADVANCED_PROFILE = CognitionProfile(
    profile_version="phase2-2.0.0",
    profile_name="advanced-cognition-platform",
    goal_interpretation_required=True,
    input_gate_required=True,
    context_required=True,
    hypotheses_required=True,
    plan_critique_required=True,
    normalized_observations_required=True,
    structured_reflection_required=True,
    uncertainty_proof_required=True,
    completion_proof_required=True,
    decision_explanation_required=True,
)

LEGACY_PROFILE = CognitionProfile(
    profile_version="phase1-compat-1.0.0",
    profile_name="legacy-compatible",
    goal_interpretation_required=False,
    input_gate_required=False,
    context_required=False,
    hypotheses_required=False,
    plan_critique_required=False,
    normalized_observations_required=False,
    structured_reflection_required=False,
    uncertainty_proof_required=False,
    completion_proof_required=False,
    decision_explanation_required=False,
)


def cognition_profile_for(agent_name: str) -> CognitionProfile:
    """All 22 primary agents use the mature profile after Phase 2 migration."""
    return ADVANCED_PROFILE if agent_name in ALL_AGENT_FEATURES else LEGACY_PROFILE
