"""Deterministic schema compatibility and immutable artifact conversion."""

from __future__ import annotations

from copy import deepcopy

from proofchain.repositories.json_store import payload_sha256
from proofchain.schemas.institutional import ConvertedArtifact, SchemaArtifact


def analyze_compatibility(
    current_schema: dict, target_schema: dict
) -> tuple[str, list[str], list[str]]:
    current_required = set(current_schema.get("required", []))
    target_required = set(target_schema.get("required", []))
    current_properties = current_schema.get("properties", {})
    target_properties = target_schema.get("properties", {})
    breaking: list[str] = []
    steps: list[str] = []
    for field in sorted(current_required - set(target_properties)):
        breaking.append(f"Required field removed: {field}")
    for field in sorted(target_required - current_required):
        breaking.append(f"New required field: {field}")
        steps.append(f"Provide a mapping or default for {field}.")
    for field in sorted(set(current_properties) & set(target_properties)):
        old_type = current_properties[field].get("type")
        new_type = target_properties[field].get("type")
        if old_type and new_type and old_type != new_type:
            breaking.append(f"Field type changed: {field} ({old_type} -> {new_type})")
            steps.append(f"Convert {field} from {old_type} to {new_type}.")
    if not breaking:
        return "backward_compatible", [], []
    return "migration_required", breaking, steps


def convert_artifacts(
    artifacts: list[SchemaArtifact],
    target_version: str,
    field_mappings: dict[str, str],
    defaults: dict,
) -> list[ConvertedArtifact]:
    converted: list[ConvertedArtifact] = []
    for artifact in artifacts:
        original = deepcopy(artifact.payload)
        result = deepcopy(original)
        for old_field, new_field in field_mappings.items():
            if old_field in result and new_field not in result:
                result[new_field] = result.pop(old_field)
        for field, value in defaults.items():
            result.setdefault(field, deepcopy(value))
        converted.append(
            ConvertedArtifact(
                artifact_id=artifact.artifact_id,
                original_schema_version=artifact.schema_version,
                converted_schema_version=target_version,
                original_hash=payload_sha256(original),
                converted_hash=payload_sha256(result),
                converted_payload=result,
            )
        )
    return converted

