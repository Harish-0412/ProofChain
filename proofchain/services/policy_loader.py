"""Load, validate, and fingerprint ProofChain's machine-readable policies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from proofchain.core.paths import POLICIES_DIR
from proofchain.repositories.json_store import file_sha256, payload_sha256
from proofchain.schemas.runtime_governance import (
    GovernancePolicyManifest,
    PolicyFileRecord,
)


REQUIRED_POLICY_FILES = (
    "agent_permissions.yaml",
    "approval_policy.yaml",
    "communication_policy.yaml",
    "closure_policy.yaml",
    "package_policy.yaml",
    "security_policy.yaml",
    "retention_policy.yaml",
)


@dataclass(frozen=True)
class ApprovalActor:
    actor_id: str
    role: str
    scopes: list[str]
    permissions: list[str]


class GovernancePolicyCatalog:
    def __init__(self, policies: dict[str, dict[str, Any]], records: list[PolicyFileRecord]):
        self.policies = policies
        self.records = records
        self.fingerprint = payload_sha256(
            [{"policy_id": item.policy_id, "sha256": item.sha256} for item in records]
        )

    @classmethod
    def load(cls, directory: Path = POLICIES_DIR) -> "GovernancePolicyCatalog":
        policies: dict[str, dict[str, Any]] = {}
        records: list[PolicyFileRecord] = []
        for name in REQUIRED_POLICY_FILES:
            path = directory / name
            if not path.is_file():
                raise FileNotFoundError(f"Required governance policy is missing: {path}")
            with path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
            policy_id = str(payload.get("policy_id", "")).strip()
            schema_version = str(payload.get("schema_version", "")).strip()
            if not policy_id or not schema_version:
                raise ValueError(f"Policy {path} requires policy_id and schema_version.")
            policies[policy_id] = payload
            records.append(
                PolicyFileRecord(
                    policy_id=policy_id,
                    path=str(path.resolve()),
                    sha256=file_sha256(path),
                    schema_version=schema_version,
                )
            )
        return cls(policies, records)

    def manifest(self, run_id: str) -> GovernancePolicyManifest:
        return GovernancePolicyManifest(
            run_id=run_id,
            policy_fingerprint=self.fingerprint,
            policies=self.records,
        )

    def approval_actor(self, actor_id: str) -> ApprovalActor | None:
        policy = self.policies["approval-authorization"]
        actors = policy.get("actors", {})
        configured_id = next(
            (key for key in actors if key.casefold() == actor_id.strip().casefold()),
            None,
        )
        if configured_id is None:
            return None
        actor = actors[configured_id]
        return ApprovalActor(
            actor_id=configured_id,
            role=str(actor["role"]),
            scopes=[str(item) for item in actor.get("scopes", [])],
            permissions=[str(item) for item in actor.get("permissions", [])],
        )

    def required_approval_permission(self, approval_type: str) -> str | None:
        mapping = self.policies["approval-authorization"].get(
            "approval_permissions", {}
        )
        value = mapping.get(approval_type)
        return str(value) if value else None

    def security_policy(self) -> dict[str, Any]:
        return self.policies["untrusted-content-security"]
