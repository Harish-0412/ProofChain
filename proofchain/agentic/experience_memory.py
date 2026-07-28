"""Governed experience memory that only returns validated reusable cases."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from proofchain.core.paths import OUTPUTS_DIR
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.validated_cases import ValidatedCase


class ExperienceMemory:
    def __init__(
        self,
        path: Path | None = None,
        store: AtomicJsonStore | None = None,
    ):
        self.path = path or OUTPUTS_DIR / "validated_cases.json"
        self.store = store or AtomicJsonStore()

    def eligible(
        self,
        *,
        case_type: str,
        tenant_id: str | None,
        policy_fingerprint: str | None,
    ) -> list[ValidatedCase]:
        payload = self.store.read(self.path, default=[])
        return [
            case
            for item in payload
            if (case := ValidatedCase.model_validate(item)).case_type == case_type
            and case.validation_status == "validated"
            and case.reusable
            and case.tenant_id == tenant_id
            and case.policy_fingerprint == policy_fingerprint
            and (
                case.expires_at is None
                or case.expires_at > datetime.now(tz=timezone.utc)
            )
        ]

    def record_candidate(self, case: ValidatedCase) -> None:
        payload = self.store.read(self.path, default=[])
        payload.append(case)
        self.store.write(self.path, payload)

    def approve(
        self,
        candidate: ValidatedCase,
        *,
        approved_by: str,
        tenant_id: str | None,
        policy_fingerprint: str,
    ) -> ValidatedCase:
        if candidate.outcome not in {"completed", "completed_with_warnings"}:
            raise ValueError("Only successful terminal cases may become reusable.")
        if not approved_by.strip():
            raise ValueError("Validated experience requires an explicit approver.")
        validated = candidate.model_copy(
            update={
                "tenant_id": tenant_id,
                "policy_fingerprint": policy_fingerprint,
                "validation_status": "validated",
                "approved_by": approved_by,
                "reusable": True,
            }
        )
        self.record_candidate(validated)
        return validated
