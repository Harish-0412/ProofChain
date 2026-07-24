"""Deterministic grouping of classified evidence into event bundles."""

from __future__ import annotations

import re
from collections import defaultdict

from proofchain.core.ids import generate_bundle_id
from proofchain.schemas.classification import ClassifiedEvidence
from proofchain.schemas.integrity import EvidenceBundle


def field_value(record: ClassifiedEvidence, name: str):
    field = record.extracted_fields.get(name)
    return field.normalized_value if field else None


class EvidenceBundler:
    def bundle(
        self,
        records: list[ClassifiedEvidence],
        run_id: str,
    ) -> tuple[list[EvidenceBundle], list[str]]:
        grouped: dict[tuple[str, str], list[ClassifiedEvidence]] = defaultdict(list)
        methods: dict[tuple[str, str], tuple[str, float]] = {}
        warnings: list[str] = []

        for record in records:
            event_id = field_value(record, "event_id")
            event_title = field_value(record, "event_title")
            event_date = field_value(record, "event_date")
            if event_id:
                event_key = str(event_id).upper()
                method = ("event_id", 1.0)
            elif event_title:
                normalized_title = re.sub(r"[^A-Za-z0-9]+", "-", str(event_title)).strip("-")
                event_key = f"{normalized_title}-{event_date or 'undated'}"
                method = ("event_title_date", 0.78)
                warnings.append(
                    f"{record.evidence_id} was bundled without an explicit event ID."
                )
            else:
                event_key = f"UNRESOLVED-{record.evidence_id}"
                method = ("singleton_unresolved", 0.35)
                warnings.append(
                    f"{record.evidence_id} could not be synchronized to an event bundle."
                )
            key = (record.department.casefold(), event_key.casefold())
            grouped[key].append(record)
            methods[key] = method

        bundles: list[EvidenceBundle] = []
        for key in sorted(grouped):
            items = sorted(grouped[key], key=lambda item: item.evidence_id)
            method, confidence = methods[key]
            event_id = field_value(items[0], "event_id")
            event_title = next(
                (field_value(item, "event_title") for item in items if field_value(item, "event_title")),
                None,
            )
            event_key = str(event_id or event_title or items[0].evidence_id)
            bundles.append(
                EvidenceBundle(
                    bundle_id=generate_bundle_id(items[0].department, event_key),
                    event_id=str(event_id) if event_id else None,
                    event_title=str(event_title) if event_title else None,
                    department=items[0].department,
                    academic_year=items[0].academic_year,
                    evidence_ids=[item.evidence_id for item in items],
                    document_types_present=sorted(
                        {
                            item.document_type.primary_type.value
                            for item in items
                        }
                    ),
                    grouping_method=method,
                    grouping_confidence=confidence,
                    run_id=run_id,
                )
            )
        return bundles, warnings
