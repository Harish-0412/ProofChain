"""Persistence for claim, gap, ownership, and consolidated decision artifacts."""

from __future__ import annotations

from proofchain.core.paths import (
    get_claim_decisions_path,
    get_extended_pipeline_report_path,
    get_gap_resolution_path,
    get_ownership_assignments_path,
)
from proofchain.repositories.json_artifact_repository import JsonArtifactRepository
from proofchain.schemas.claims import ClaimAgentResult
from proofchain.schemas.common import ArtifactReference
from proofchain.schemas.gaps import GapAgentResult
from proofchain.schemas.ownership import OwnershipAgentResult
from proofchain.schemas.readiness import ExtendedAgentPipelineReport


class JsonDecisionRepository(JsonArtifactRepository):
    def save_claims(
        self, run_id: str, result: ClaimAgentResult, agent_run_id: str
    ) -> ArtifactReference:
        return self.save(
            get_claim_decisions_path(run_id),
            result.model_dump(exclude={"output_reference", "output_snapshot_hash"}),
            stage_name="claim_intelligence",
            record_count=len(result.decisions),
            agent_run_id=agent_run_id,
        )

    def save_gaps(
        self, run_id: str, result: GapAgentResult, agent_run_id: str
    ) -> ArtifactReference:
        return self.save(
            get_gap_resolution_path(run_id),
            result.model_dump(exclude={"output_reference", "output_snapshot_hash"}),
            stage_name="gap_resolution",
            record_count=len(result.portfolio.gaps),
            agent_run_id=agent_run_id,
        )

    def save_ownership(
        self, run_id: str, result: OwnershipAgentResult, agent_run_id: str
    ) -> ArtifactReference:
        return self.save(
            get_ownership_assignments_path(run_id),
            result.model_dump(exclude={"output_reference", "output_snapshot_hash"}),
            stage_name="ownership",
            record_count=len(result.assignments),
            agent_run_id=agent_run_id,
        )

    def save_report(self, report: ExtendedAgentPipelineReport) -> ArtifactReference:
        return self.save(
            get_extended_pipeline_report_path(report.run_id),
            report,
            stage_name="claim_resolution_ownership_report",
            record_count=len(report.resolution_portfolio),
            agent_run_id=None,
        )
