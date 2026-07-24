"""Specialist that decomposes explicit or evidence-derived institutional claims."""

from __future__ import annotations

import re

from proofchain.core.enums import DocumentType
from proofchain.schemas.claims import AtomicClaim, ClaimValidationInput, InstitutionalClaim
from proofchain.services.evidence_bundler import field_value


class ClaimDecompositionSpecialist:
    specialist_name = "claim_decomposition"
    goal = "Convert institutional statements into independently verifiable assertions."

    def run(self, input_data: ClaimValidationInput) -> list[InstitutionalClaim]:
        if input_data.institutional_claims:
            return [
                self._decompose_text(input_data, text, index)
                for index, text in enumerate(input_data.institutional_claims, 1)
            ]
        reports = [
            record
            for record in input_data.classified_evidence
            if record.document_type.primary_type == DocumentType.EVENT_REPORT
        ]
        return [
            self._derive_from_report(input_data, report, index)
            for index, report in enumerate(sorted(reports, key=lambda item: item.evidence_id), 1)
        ]

    def _decompose_text(
        self, input_data: ClaimValidationInput, text: str, index: int
    ) -> InstitutionalClaim:
        department = next(
            (
                item
                for item in input_data.workflow.department_scope
                if re.search(rf"\b{re.escape(item)}\b", text, re.IGNORECASE)
            ),
            input_data.workflow.department_scope[0],
        )
        academic_year = (
            re.search(r"\b20\d{2}-20\d{2}\b", text).group(0)
            if re.search(r"\b20\d{2}-20\d{2}\b", text)
            else input_data.workflow.academic_year
        )
        requirement_match = re.search(r"\bC\d+\.\d+\.\d+\b", text)
        requirement_id = (
            requirement_match.group(0)
            if requirement_match
            else input_data.workflow.requirement_scope[0]
        )
        claim_id = f"CLM-{requirement_id}-{index:03d}"
        atomic_values: list[tuple[str, str | int, dict[str, str]]] = [
            ("department", department, {}),
            ("academic_year", academic_year, {}),
        ]
        activity_type = self._activity_type(text)
        if activity_type:
            atomic_values.append(("activity_type", activity_type, {}))
        event_id = re.search(r"\bEVT-[A-Z]+-\d+\b", text, re.IGNORECASE)
        if event_id:
            atomic_values.append(
                ("event_id", event_id.group(0).upper(), {"event_id": event_id.group(0).upper()})
            )
        activity_count = re.search(
            r"\b(\d+)\s+(?:industry\s+)?(?:programmes?|programs?|activities|events)\b",
            text,
            re.IGNORECASE,
        )
        if activity_count:
            atomic_values.append(("activity_count", int(activity_count.group(1)), {}))
        participant_count = re.search(
            r"\b(\d+)\s+(?:unique\s+)?(?:students?|participants?|attendees?)\b",
            text,
            re.IGNORECASE,
        )
        if participant_count:
            atomic_values.append(
                ("participant_count", int(participant_count.group(1)), {})
            )
        atomic_claims = [
            AtomicClaim(
                atomic_claim_id=f"ACL-{claim_id}-{position:02d}",
                claim_id=claim_id,
                attribute=attribute,
                expected_value=value,
                qualifiers=qualifiers,
            )
            for position, (attribute, value, qualifiers) in enumerate(atomic_values, 1)
        ]
        return InstitutionalClaim(
            claim_id=claim_id,
            requirement_id=requirement_id,
            original_claim=text,
            department=department,
            academic_year=academic_year,
            atomic_claims=atomic_claims,
        )

    def _derive_from_report(
        self, input_data: ClaimValidationInput, report, index: int
    ) -> InstitutionalClaim:
        requirement_id = next(
            (
                mapping.requirement_id
                for mapping in report.requirement_mappings
                if mapping.requirement_id in input_data.workflow.requirement_scope
            ),
            input_data.workflow.requirement_scope[0],
        )
        event_id = str(field_value(report, "event_id") or report.evidence_id)
        title = str(field_value(report, "event_title") or "institutional activity")
        participant_count = field_value(report, "reported_participant_count")
        text = (
            f"{report.department} conducted {title} ({event_id}) during "
            f"{report.academic_year}"
        )
        if participant_count is not None:
            text += f" involving {participant_count} participants"
        text += "."
        claim = self._decompose_text(input_data, text, index)
        claim.source = "derived_from_evidence"
        claim.requirement_id = requirement_id
        return claim

    @staticmethod
    def _activity_type(text: str) -> str | None:
        lowered = text.casefold()
        for keyword, value in (
            ("industry", "industry_programme"),
            ("workshop", "workshop"),
            ("bootcamp", "bootcamp"),
            ("faculty development", "faculty_development"),
            ("outreach", "outreach"),
            ("value-added", "value_added_course"),
        ):
            if keyword in lowered:
                return value
        return None
