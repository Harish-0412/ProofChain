"""Classification artifact repository."""

from __future__ import annotations

from proofchain.core.paths import get_classified_evidence_path
from proofchain.repositories.json_artifact_repository import JsonArtifactRepository
from proofchain.schemas.classification import ClassifiedEvidence
from proofchain.schemas.common import ArtifactReference


class JsonClassificationRepository(JsonArtifactRepository):
    def save_records(
        self,
        run_id: str,
        records: list[ClassifiedEvidence],
        agent_run_id: str,
    ) -> ArtifactReference:
        return self.save(
            get_classified_evidence_path(run_id),
            records,
            stage_name="classification",
            record_count=len(records),
            agent_run_id=agent_run_id,
        )
