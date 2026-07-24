"""Run manifest, checkpoint, and final result persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from proofchain.core.exceptions import StageGateError
from proofchain.core.paths import (
    ensure_run_dir,
    get_pipeline_result_path,
    get_run_manifest_path,
    get_synchronization_path,
)
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.repositories.json_store import file_sha256
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.common import ArtifactReference, StageCheckpoint
from proofchain.schemas.workflow import PipelineResult, WorkflowContext


class JsonRunRepository:
    def __init__(self, store: AtomicJsonStore | None = None):
        self.store = store or AtomicJsonStore()

    def create(self, workflow: WorkflowContext, run_mode: str) -> None:
        ensure_run_dir(workflow.run_id)
        manifest = {
            "schema_version": "1.0.0",
            "run_id": workflow.run_id,
            "run_mode": run_mode,
            "workflow": workflow,
            "status": "running",
            "created_at": datetime.now(tz=timezone.utc),
            "updated_at": datetime.now(tz=timezone.utc),
            "checkpoints": [],
        }
        self.store.write(get_run_manifest_path(workflow.run_id), manifest)
        self.store.write(get_synchronization_path(workflow.run_id), [])

    def register_checkpoint(
        self,
        workflow: WorkflowContext,
        *,
        stage_name: str,
        status: str,
        input_sha256: str,
        output: ArtifactReference,
        upstream_sha256: str | None,
        started_at: datetime,
        completed_at: datetime,
    ) -> StageCheckpoint:
        if upstream_sha256 and workflow.upstream_artifact_hash != upstream_sha256:
            raise StageGateError(
                f"Synchronization mismatch for {stage_name}: "
                f"context={workflow.upstream_artifact_hash}, expected={upstream_sha256}"
            )
        checkpoint = StageCheckpoint(
            run_id=workflow.run_id,
            stage_name=stage_name,
            status=status,
            input_sha256=input_sha256,
            output=output,
            upstream_sha256=upstream_sha256,
            started_at=started_at,
            completed_at=completed_at,
        )
        sync_path = get_synchronization_path(workflow.run_id)
        checkpoints = self.store.read(sync_path, default=[])
        checkpoints.append(checkpoint)
        self.store.write(sync_path, checkpoints)

        manifest_path = get_run_manifest_path(workflow.run_id)
        manifest = self.store.read(manifest_path, default={})
        manifest["checkpoints"] = checkpoints
        manifest["updated_at"] = datetime.now(tz=timezone.utc)
        self.store.write(manifest_path, manifest)
        return checkpoint

    def complete(self, result: PipelineResult) -> None:
        self.store.write(get_pipeline_result_path(result.run_id), result)
        manifest_path = get_run_manifest_path(result.run_id)
        manifest = self.store.read(manifest_path, default={})
        manifest["status"] = result.status
        manifest["updated_at"] = datetime.now(tz=timezone.utc)
        manifest["pipeline_result_path"] = str(get_pipeline_result_path(result.run_id).resolve())
        manifest["top_level_goal_id"] = result.top_level_goal_id
        manifest["goal_graph_path"] = result.goal_graph_path
        manifest["coordination_state_path"] = result.coordination_state_path
        manifest["final_decision_path"] = result.final_decision_path
        manifest["supervisor_rounds"] = result.supervisor_rounds
        manifest["claim_output_path"] = result.claim_output_path
        manifest["gap_resolution_output_path"] = result.gap_resolution_output_path
        manifest["ownership_output_path"] = result.ownership_output_path
        manifest["extended_report_path"] = result.extended_report_path
        manifest["canonical_issues_path"] = result.canonical_issues_path
        manifest["liaison_tasks_path"] = result.liaison_tasks_path
        manifest["communications_path"] = result.communications_path
        manifest["closure_output_path"] = result.closure_output_path
        manifest["audit_package_output_path"] = result.audit_package_output_path
        manifest["quality_review_output_path"] = result.quality_review_output_path
        manifest["workflow_events_path"] = result.workflow_events_path
        manifest["component_registry_path"] = result.component_registry_path
        manifest["policy_manifest_path"] = result.policy_manifest_path
        manifest["model_governance_manifest_path"] = (
            result.model_governance_manifest_path
        )
        manifest["supervisor_rounds_path"] = result.supervisor_rounds_path
        manifest["observability_metrics_path"] = result.observability_metrics_path
        manifest["audit_package_bundle_path"] = result.audit_package_bundle_path
        self.store.write(manifest_path, manifest)

    def load_manifest(self, run_id: str) -> dict[str, Any]:
        return self.store.read(get_run_manifest_path(run_id), default={})

    def validate(self, run_id: str) -> list[str]:
        manifest = self.load_manifest(run_id)
        errors: list[str] = []
        if not manifest:
            return [f"Run manifest not found for {run_id}"]
        checkpoints = manifest.get("checkpoints", [])
        previous_hash: str | None = None
        for index, checkpoint in enumerate(checkpoints):
            upstream = checkpoint.get("upstream_sha256")
            if index > 0 and upstream is not None and upstream != previous_hash:
                errors.append(
                    f"{checkpoint.get('stage_name')} upstream hash does not match prior output"
                )
            artifact = checkpoint.get("output", {})
            path = Path(artifact.get("path", ""))
            if not path.exists():
                errors.append(f"Artifact missing: {path}")
            elif artifact.get("sha256") != file_sha256(path):
                errors.append(f"Artifact checksum mismatch: {path}")
            previous_hash = artifact.get("sha256")
        for label in (
            "goal_graph_path",
            "coordination_state_path",
            "final_decision_path",
            "claim_output_path",
            "gap_resolution_output_path",
            "ownership_output_path",
            "extended_report_path",
            "canonical_issues_path",
            "liaison_tasks_path",
            "communications_path",
            "closure_output_path",
            "audit_package_output_path",
            "quality_review_output_path",
            "workflow_events_path",
            "component_registry_path",
            "policy_manifest_path",
            "model_governance_manifest_path",
            "supervisor_rounds_path",
            "observability_metrics_path",
            "audit_package_bundle_path",
        ):
            artifact_path = manifest.get(label)
            if artifact_path and not Path(artifact_path).exists():
                errors.append(f"Agentic artifact missing: {artifact_path}")
        errors.extend(JsonEventRepository.validate_chain(run_id))
        return errors
