"""Fingerprinting and dependency impact analysis for partial re-execution."""

from __future__ import annotations

import hashlib
from pathlib import Path

from proofchain.schemas.production import FingerprintRecord


AGENT_IMPACT = {
    "evidence": [
        "evidence_classification",
        "evidence_integrity",
        "claim_intelligence",
        "adaptive_gap_resolution",
        "closure_revalidation",
        "audit_package_composer",
        "adversarial_quality_review",
    ],
    "approval": [
        "accountability_ownership",
        "department_liaison",
        "closure_revalidation",
    ],
    "policy": [
        "evidence_integrity",
        "claim_intelligence",
        "closure_revalidation",
        "audit_package_composer",
        "adversarial_quality_review",
    ],
}


def fingerprint_references(references: list[str]) -> list[FingerprintRecord]:
    records: list[FingerprintRecord] = []
    for reference in references:
        path = Path(reference).resolve()
        if not path.is_file():
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        lowered = path.name.lower()
        entity_type = "policy" if "policy" in lowered else "approval" if "approval" in lowered else "evidence"
        records.append(
            FingerprintRecord(
                reference=str(path),
                sha256=digest.hexdigest(),
                entity_type=entity_type,
            )
        )
    return records


def calculate_impact(
    previous: list[FingerprintRecord],
    current: list[FingerprintRecord],
    dependency_graph: dict[str, list[str]],
) -> tuple[list[str], list[str], list[str], list[str]]:
    old = {item.reference: item for item in previous}
    new = {item.reference: item for item in current}
    changed = sorted(
        reference
        for reference in set(old) | set(new)
        if reference not in old
        or reference not in new
        or old[reference].sha256 != new[reference].sha256
    )
    stale: set[str] = set()
    agents: set[str] = set()
    frontier = list(changed)
    while frontier:
        entity = frontier.pop()
        for dependent in dependency_graph.get(entity, []):
            if dependent not in stale:
                stale.add(dependent)
                frontier.append(dependent)
        entity_type = (new.get(entity) or old.get(entity))
        if entity_type:
            agents.update(AGENT_IMPACT.get(entity_type.entity_type, []))
    reusable = sorted(set(dependency_graph) - set(changed) - stale)
    return changed, sorted(stale), reusable, sorted(agents)

