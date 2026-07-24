"""Persistence for canonical issues, tasks, closure, package, and quality artifacts."""

from __future__ import annotations

from proofchain.core.paths import (
    get_audit_package_manifest_path,
    get_access_decision_log_path,
    get_canonical_issues_path,
    get_closure_report_path,
    get_communications_path,
    get_component_registry_path,
    get_liaison_tasks_path,
    get_quality_review_path,
    get_security_scan_path,
    get_prompt_injection_findings_path,
    get_pii_redaction_manifest_path,
    get_policy_manifest_path,
    get_model_governance_manifest_path,
    get_supervisor_rounds_path,
    get_observability_metrics_path,
)
from proofchain.repositories.json_artifact_repository import JsonArtifactRepository
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.closure import ClosureAgentResult
from proofchain.schemas.common import ArtifactReference
from proofchain.schemas.components import ComponentRegistry
from proofchain.schemas.communications import CommunicationRecord
from proofchain.schemas.issues import IssueLedger
from proofchain.schemas.packages import AuditPackageAgentResult
from proofchain.schemas.quality import QualityReviewAgentResult
from proofchain.schemas.tasks import LiaisonAgentResult
from proofchain.schemas.runtime_governance import (
    GovernancePolicyManifest,
    ModelGovernanceManifest,
    RunObservabilitySnapshot,
    SupervisorRoundRecord,
)


class JsonLifecycleRepository(JsonArtifactRepository):
    def __init__(self, store: AtomicJsonStore | None = None):
        super().__init__(store or AtomicJsonStore())

    def save_issues(self, ledger: IssueLedger) -> ArtifactReference:
        return self.save(
            get_canonical_issues_path(ledger.run_id),
            ledger,
            stage_name="canonical_issues",
            record_count=len(ledger.issues),
            agent_run_id=None,
        )

    def save_liaison(
        self,
        run_id: str,
        result: LiaisonAgentResult,
        communications: list[CommunicationRecord],
    ) -> ArtifactReference:
        self.store.write(get_communications_path(run_id), communications)
        return self.save(
            get_liaison_tasks_path(run_id),
            result.model_dump(exclude={"output_reference", "output_snapshot_hash"}),
            stage_name="department_liaison",
            record_count=len(result.tasks),
            agent_run_id=result.agent_run_id,
        )

    def save_closure(self, result: ClosureAgentResult) -> ArtifactReference:
        return self.save(
            get_closure_report_path(result.run_id),
            result.model_dump(exclude={"output_reference", "output_snapshot_hash"}),
            stage_name="closure_revalidation",
            record_count=len(result.closure_checks),
            agent_run_id=result.agent_run_id,
        )

    def save_package(self, result: AuditPackageAgentResult) -> ArtifactReference:
        return self.save(
            get_audit_package_manifest_path(result.run_id),
            result.model_dump(exclude={"output_reference", "output_snapshot_hash"}),
            stage_name="audit_package_composer",
            record_count=len(result.manifest.eligible_evidence),
            agent_run_id=result.agent_run_id,
        )

    def save_quality(self, result: QualityReviewAgentResult) -> ArtifactReference:
        return self.save(
            get_quality_review_path(result.run_id),
            result.model_dump(exclude={"output_reference", "output_snapshot_hash"}),
            stage_name="adversarial_quality_review",
            record_count=len(result.claim_challenges),
            agent_run_id=result.agent_run_id,
        )

    def save_component_registry(self, registry: ComponentRegistry) -> None:
        self.store.write(get_component_registry_path(registry.run_id), registry)

    def save_policy_manifest(self, manifest: GovernancePolicyManifest) -> None:
        self.store.write(get_policy_manifest_path(manifest.run_id), manifest)

    def save_model_governance(self, manifest: ModelGovernanceManifest) -> None:
        self.store.write(
            get_model_governance_manifest_path(manifest.run_id),
            manifest,
        )

    def save_scheduler_round(self, record: SupervisorRoundRecord) -> None:
        path = get_supervisor_rounds_path(record.run_id)
        records = self.store.read(path, default=[])
        records.append(record)
        self.store.write(path, records)

    def save_observability(self, snapshot: RunObservabilitySnapshot) -> None:
        self.store.write(get_observability_metrics_path(snapshot.run_id), snapshot)

    def save_prompt_injection_findings(
        self,
        run_id: str,
        findings: list[dict],
    ) -> None:
        self.store.write(get_prompt_injection_findings_path(run_id), findings)

    def save_security_exports(self, run_id: str) -> None:
        self.store.write(
            get_security_scan_path(run_id),
            {
                "run_id": run_id,
                "status": "baseline_controls_recorded",
                "controls": [
                    "path_traversal_checked_by_source_scope",
                    "unsupported_files_skipped",
                    "extracted_text_treated_as_untrusted_data",
                    "formula_cells_not_executed",
                ],
            },
        )
        self.store.write(get_prompt_injection_findings_path(run_id), [])
        self.store.write(
            get_pii_redaction_manifest_path(run_id),
            {"run_id": run_id, "redactions": [], "original_evidence_unchanged": True},
        )
        access_log = get_access_decision_log_path(run_id)
        access_log.parent.mkdir(parents=True, exist_ok=True)
        access_log.touch(exist_ok=True)
