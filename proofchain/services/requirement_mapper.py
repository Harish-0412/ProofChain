"""Deterministic requirement mapping and event-consensus propagation."""

from __future__ import annotations

from collections import defaultdict

from proofchain.core.config import get_requirement_mapping
from proofchain.core.enums import MappingType
from proofchain.schemas.classification import ClassifiedEvidence, RequirementMapping
from proofchain.schemas.common import SourceReference
from proofchain.schemas.evidence import EvidenceRecord


class RequirementMapper:
    def __init__(self, config: dict | None = None):
        self.config = config or get_requirement_mapping()

    def map(
        self,
        evidence: EvidenceRecord,
        text: str,
        fields: dict,
        requirement_scope: list[str],
    ) -> list[RequirementMapping]:
        configured = self.config.get("requirements", {})
        scope = requirement_scope or list(configured)
        candidates: dict[str, tuple[float, MappingType, str]] = {}
        source = SourceReference(document=evidence.evidence_id, text_snippet=(text or "")[:200] or None)

        for field_name in ("mapped_requirement_id", "requirement_id"):
            field = fields.get(field_name)
            value = str(field.normalized_value) if field else ""
            if value in scope and value in configured:
                candidates[value] = (
                    0.99,
                    MappingType.EXTRACTED_FIELD,
                    f"Exact requirement ID extracted from {field_name}.",
                )

        filename = evidence.original_filename.casefold()
        for requirement_id in scope:
            definition = configured.get(requirement_id)
            if not definition:
                continue
            if any(pattern.casefold() in filename for pattern in definition.get("filename_patterns", [])):
                current = candidates.get(requirement_id, (0.0, MappingType.FILENAME, ""))
                if current[0] < 0.96:
                    candidates[requirement_id] = (
                        0.96,
                        MappingType.FILENAME,
                        "Requirement ID matched the filename.",
                    )
            keyword_hits = [
                keyword
                for keyword in definition.get("keywords", [])
                if keyword.casefold() in (text or "").casefold()
            ]
            if keyword_hits and candidates.get(requirement_id, (0.0, None, ""))[0] < 0.75:
                candidates[requirement_id] = (
                    min(0.88, 0.68 + 0.05 * len(keyword_hits)),
                    MappingType.KEYWORD,
                    f"Requirement keywords matched: {', '.join(keyword_hits[:3])}.",
                )

        ranked = [
            RequirementMapping(
                requirement_id=requirement_id,
                mapping_type=method,
                confidence=confidence,
                reason=reason,
                source_references=[source],
            )
            for requirement_id, (confidence, method, reason) in sorted(
                candidates.items(), key=lambda item: (-item[1][0], item[0])
            )
        ]
        if not ranked:
            return []
        best_confidence = ranked[0].confidence
        if best_confidence >= 0.9:
            return [mapping for mapping in ranked if mapping.confidence >= 0.9]
        return ranked[:1]

    def propagate_event_consensus(self, records: list[ClassifiedEvidence]) -> None:
        consensus: dict[tuple[str, str], list[str]] = defaultdict(list)
        for record in records:
            event_field = record.extracted_fields.get("event_id")
            if not event_field:
                continue
            event_id = str(event_field.normalized_value)
            key = (record.department.casefold(), event_id.casefold())
            for mapping in record.requirement_mappings:
                if mapping.confidence >= 0.9:
                    consensus[key].append(mapping.requirement_id)

        for record in records:
            if record.requirement_mappings:
                continue
            event_field = record.extracted_fields.get("event_id")
            if not event_field:
                continue
            event_id = str(event_field.normalized_value)
            values = consensus.get((record.department.casefold(), event_id.casefold()), [])
            unique_values = set(values)
            if len(unique_values) == 1:
                requirement_id = next(iter(unique_values))
                record.requirement_mappings = [
                    RequirementMapping(
                        requirement_id=requirement_id,
                        mapping_type=MappingType.EXTRACTED_FIELD,
                        confidence=0.9,
                        reason="Inherited from unanimous same-department event ID consensus.",
                        source_references=[
                            SourceReference(document=record.evidence_id, text_snippet=event_id)
                        ],
                    )
                ]
