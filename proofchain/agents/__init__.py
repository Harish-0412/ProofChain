"""
ProofChain Agents Module
Houses all agent classes that participate in the evidence governance pipeline.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "EvidenceCollectorAgent",
    "EvidenceClassificationAgent",
    "EvidenceIntegrityAgent",
    "Supervisor",
    "ClaimIntelligenceAgent",
    "AdaptiveGapResolutionAgent",
    "AccountabilityOwnershipAgent",
    "DepartmentLiaisonAgent",
    "ClosureRevalidationAgent",
    "AuditPackageComposerAgent",
    "AdversarialQualityReviewAgent",
]

_EXPORTS = {
    "EvidenceCollectorAgent": (
        "proofchain.agents.evidence_collector",
        "EvidenceCollectorAgent",
    ),
    "EvidenceClassificationAgent": (
        "proofchain.agents.evidence_classification",
        "EvidenceClassificationAgent",
    ),
    "EvidenceIntegrityAgent": (
        "proofchain.agents.evidence_integrity",
        "EvidenceIntegrityAgent",
    ),
    "Supervisor": ("proofchain.agents.supervisor", "Supervisor"),
    "ClaimIntelligenceAgent": (
        "proofchain.agents.claim_validation.agent",
        "ClaimIntelligenceAgent",
    ),
    "AdaptiveGapResolutionAgent": (
        "proofchain.agents.gap_resolution.agent",
        "AdaptiveGapResolutionAgent",
    ),
    "AccountabilityOwnershipAgent": (
        "proofchain.agents.ownership.agent",
        "AccountabilityOwnershipAgent",
    ),
    "DepartmentLiaisonAgent": (
        "proofchain.agents.liaison.agent",
        "DepartmentLiaisonAgent",
    ),
    "ClosureRevalidationAgent": (
        "proofchain.agents.closure.agent",
        "ClosureRevalidationAgent",
    ),
    "AuditPackageComposerAgent": (
        "proofchain.agents.audit_package.agent",
        "AuditPackageComposerAgent",
    ),
    "AdversarialQualityReviewAgent": (
        "proofchain.agents.quality_review.agent",
        "AdversarialQualityReviewAgent",
    ),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
