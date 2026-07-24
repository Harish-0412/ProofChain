"""Specialist that retrieves both supporting and counter-evidence."""

from __future__ import annotations

from collections import defaultdict

from proofchain.schemas.claims import (
    ClaimValidationInput,
    EvidenceSupportLink,
    InstitutionalClaim,
)
from proofchain.services.evidence_bundler import field_value


AUTHORITY = {
    "attendance_sheet": 0.98,
    "approval_document": 0.95,
    "event_report": 0.82,
    "certificate": 0.72,
    "photograph": 0.55,
    "unknown": 0.30,
}


class EvidenceRetrievalSpecialist:
    specialist_name = "claim_evidence_retrieval"
    goal = "Retrieve authoritative support and deliberate counter-evidence."

    field_aliases = {
        "participant_count": ["unique_student_count", "reported_participant_count"],
        "department": ["department"],
        "academic_year": ["academic_year"],
        "event_id": ["event_id"],
        "event_title": ["event_title"],
    }

    def run(
        self,
        input_data: ClaimValidationInput,
        claims: list[InstitutionalClaim],
    ) -> list[EvidenceSupportLink]:
        links: list[EvidenceSupportLink] = []
        by_event: dict[str, list] = defaultdict(list)
        for record in input_data.classified_evidence:
            by_event[str(field_value(record, "event_id") or "")].append(record)

        for claim in claims:
            scoped_candidates = [
                record
                for record in input_data.classified_evidence
                if record.department == claim.department
                and record.academic_year == claim.academic_year
                and any(
                    mapping.requirement_id == claim.requirement_id
                    for mapping in record.requirement_mappings
                )
            ]
            event_atomic = next(
                (item for item in claim.atomic_claims if item.attribute == "event_id"),
                None,
            )
            candidates = scoped_candidates
            if event_atomic:
                candidates = [
                    record
                    for record in by_event.get(str(event_atomic.expected_value), [])
                    if record in scoped_candidates
                ]
            for atomic in claim.atomic_claims:
                if atomic.attribute == "activity_count":
                    unique_events = {
                        str(field_value(record, "event_id"))
                        for record in scoped_candidates
                        if field_value(record, "event_id")
                    }
                    observed = len(unique_events)
                    evidence = next(
                        (
                            record
                            for record in candidates
                            if record.document_type.primary_type.value == "event_report"
                        ),
                        None,
                    )
                    if evidence:
                        links.append(
                            self._link(
                                atomic.atomic_claim_id,
                                evidence,
                                "activity_count",
                                observed,
                                atomic.expected_value,
                            )
                        )
                    continue
                if atomic.attribute == "activity_type":
                    evidence = next(
                        (
                            record
                            for record in candidates
                            if record.document_type.primary_type.value == "event_report"
                        ),
                        None,
                    )
                    if evidence:
                        links.append(
                            EvidenceSupportLink(
                                atomic_claim_id=atomic.atomic_claim_id,
                                evidence_id=evidence.evidence_id,
                                relation="partially_supports",
                                strength=0.72,
                                observed_value=atomic.expected_value,
                                authority="event_report",
                                reason="The activity type is supported by title and requirement context.",
                            )
                        )
                    continue
                for record in candidates:
                    for field_name in self.field_aliases.get(atomic.attribute, []):
                        observed = field_value(record, field_name)
                        if observed is None:
                            continue
                        links.append(
                            self._link(
                                atomic.atomic_claim_id,
                                record,
                                field_name,
                                observed,
                                atomic.expected_value,
                            )
                        )
        return links

    @staticmethod
    def _link(atomic_id, record, field_name, observed, expected) -> EvidenceSupportLink:
        equal = str(observed).casefold() == str(expected).casefold()
        authority = record.document_type.primary_type.value
        strength = AUTHORITY.get(authority, 0.4)
        return EvidenceSupportLink(
            atomic_claim_id=atomic_id,
            evidence_id=record.evidence_id,
            extracted_field_id=field_name,
            relation="supports" if equal else "contradicts",
            strength=strength,
            observed_value=observed,
            authority=authority,
            reason=(
                f"{field_name}={observed!r} "
                f"{'matches' if equal else 'conflicts with'} expected {expected!r}."
            ),
        )
