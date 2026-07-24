"""Integrity artifact repository."""

from __future__ import annotations

from proofchain.core.paths import (
    get_evidence_bundles_path,
    get_evidence_gaps_path,
    get_integrity_findings_path,
    get_integrity_summary_path,
    get_run_dir,
)
from proofchain.repositories.json_artifact_repository import JsonArtifactRepository
from proofchain.schemas.common import ArtifactReference
from proofchain.schemas.integrity import (
    EvidenceBundle,
    EvidenceGap,
    IntegrityFinding,
    IntegritySummary,
)


class JsonFindingsRepository(JsonArtifactRepository):
    def save_all(
        self,
        run_id: str,
        bundles: list[EvidenceBundle],
        findings: list[IntegrityFinding],
        gaps: list[EvidenceGap],
        summaries: list[IntegritySummary],
        agent_run_id: str,
    ) -> ArtifactReference:
        self.store.write(get_evidence_bundles_path(run_id), bundles)
        self.store.write(get_integrity_findings_path(run_id), findings)
        self.store.write(get_evidence_gaps_path(run_id), gaps)
        self.store.write(get_integrity_summary_path(run_id), summaries)

        aggregate = {
            "bundles": bundles,
            "findings": findings,
            "gaps": gaps,
            "summaries": summaries,
        }
        aggregate_path = get_run_dir(run_id) / "integrity_result.json"
        digest = self.store.write(aggregate_path, aggregate)
        return ArtifactReference(
            stage_name="integrity",
            path=str(aggregate_path.resolve()),
            sha256=digest,
            record_count=len(findings) + len(gaps),
            agent_run_id=agent_run_id,
        )
