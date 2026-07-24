"""Versioned deterministic integrity rule execution."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from proofchain.core.config import get_settings
from proofchain.core.enums import FindingType, GapType, Severity
from proofchain.core.ids import generate_finding_id, generate_gap_id
from proofchain.core.paths import (
    ACADEMIC_YEAR_RULES_FILE,
    COMMON_RULES_FILE,
    EVENT_EVIDENCE_RULES_FILE,
    REQUIRED_DOCUMENT_RULES_FILE,
)
from proofchain.schemas.classification import ClassifiedEvidence
from proofchain.schemas.common import SourceReference
from proofchain.schemas.integrity import (
    EvidenceBundle,
    EvidenceGap,
    IntegrityFinding,
    IntegritySummary,
)
from proofchain.services.evidence_bundler import field_value
from proofchain.services.duplicate_detector import DuplicateDetector


class RuleCatalog:
    def __init__(self, paths: list[Path] | None = None):
        self.paths = paths or [
            COMMON_RULES_FILE,
            EVENT_EVIDENCE_RULES_FILE,
            ACADEMIC_YEAR_RULES_FILE,
            REQUIRED_DOCUMENT_RULES_FILE,
        ]
        self.rules: dict[str, dict[str, Any]] = {}
        self.required_documents: dict[str, dict[str, list[str]]] = {}
        self._load()

    def _load(self) -> None:
        for path in self.paths:
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
            for rule in payload.get("rules", []):
                self.rules[rule["id"]] = rule
            if "requirements" in payload:
                self.required_documents.update(payload["requirements"])

    def definition(self, rule_id: str) -> dict[str, Any]:
        return self.rules.get(rule_id, {"id": rule_id, "version": "1.0.0"})


class RuleEngine:
    def __init__(
        self,
        catalog: RuleCatalog | None = None,
        duplicate_detector: DuplicateDetector | None = None,
        tracer=None,
    ):
        self.catalog = catalog or RuleCatalog()
        self.duplicate_detector = duplicate_detector or DuplicateDetector()
        self.tracer = tracer
        self.settings = get_settings()
        self._finding_sequence = 0
        self._gap_sequence = 0

    def evaluate(
        self,
        *,
        run_id: str,
        academic_year: str,
        requirement_scope: list[str],
        records: list[ClassifiedEvidence],
        bundles: list[EvidenceBundle],
    ) -> tuple[list[IntegrityFinding], list[EvidenceGap], list[IntegritySummary]]:
        self._finding_sequence = 0
        self._gap_sequence = 0
        findings: list[IntegrityFinding] = []
        gaps: list[EvidenceGap] = []
        by_id = {record.evidence_id: record for record in records}

        findings.extend(self._duplicates(run_id, records))
        findings.extend(self._file_rules(run_id, academic_year, records))
        for bundle in bundles:
            items = [by_id[evidence_id] for evidence_id in bundle.evidence_ids]
            bundle_findings, bundle_gaps = self._bundle_rules(
                run_id, academic_year, requirement_scope, bundle, items
            )
            findings.extend(bundle_findings)
            gaps.extend(bundle_gaps)
        findings.extend(self._reuse_rules(run_id, records))
        gaps.extend(self._unresolved_mapping_gaps(run_id, records))
        summaries = self._summaries(requirement_scope, records, findings, gaps)
        return findings, gaps, summaries

    def _new_finding(
        self,
        run_id: str,
        rule_id: str,
        finding_type: FindingType,
        evidence_ids: list[str],
        title: str,
        description: str,
        *,
        bundle_id: str | None = None,
        requirement_id: str | None = None,
        expected_value=None,
        observed_value=None,
        source_references: list[SourceReference] | None = None,
    ) -> IntegrityFinding:
        self._finding_sequence += 1
        definition = self.catalog.definition(rule_id)
        severity = Severity(definition.get("severity", "medium"))
        finding = IntegrityFinding(
            finding_id=generate_finding_id(run_id, self._finding_sequence),
            run_id=run_id,
            rule_id=rule_id,
            rule_version=str(definition.get("version", self.settings.rule_version)),
            finding_type=finding_type,
            severity=severity,
            evidence_ids=evidence_ids,
            bundle_id=bundle_id,
            requirement_id=requirement_id,
            title=title,
            description=description,
            expected_value=expected_value,
            observed_value=observed_value,
            source_references=source_references or [],
            blocking=bool(definition.get("blocking", False)),
            recommended_action=definition.get("on_failure", {}).get(
                "recommended_action", ""
            ),
        )
        if self.tracer:
            self.tracer.log_rule_result(
                rule_id=rule_id,
                passed=False,
                finding_id=finding.finding_id,
                evidence_id=evidence_ids[0] if evidence_ids else None,
            )
        return finding

    def _new_gap(
        self,
        run_id: str,
        requirement_id: str,
        gap_type: GapType,
        description: str,
        *,
        bundle_id: str | None = None,
        department: str | None = None,
        missing_evidence_type: str | None = None,
        blocking: bool = False,
        related_findings: list[str] | None = None,
    ) -> EvidenceGap:
        self._gap_sequence += 1
        return EvidenceGap(
            gap_id=generate_gap_id(run_id, self._gap_sequence),
            run_id=run_id,
            requirement_id=requirement_id,
            bundle_id=bundle_id,
            department=department,
            gap_type=gap_type,
            severity=Severity.HIGH if blocking else Severity.MEDIUM,
            missing_evidence_type=missing_evidence_type,
            related_findings=related_findings or [],
            description=description,
            recommended_action="Upload or correct the evidence, then rerun integrity validation.",
            blocking=blocking,
        )

    def _duplicates(
        self, run_id: str, records: list[ClassifiedEvidence]
    ) -> list[IntegrityFinding]:
        findings = []
        duplicate_groups = self.duplicate_detector.exact_groups(records)
        for ordered in duplicate_groups:
            checksum = ordered[0].sha256_checksum
            findings.append(
                self._new_finding(
                    run_id,
                    "DUP-001",
                    FindingType.DUPLICATE_FILE,
                    [item.evidence_id for item in ordered],
                    "Exact duplicate evidence detected",
                    f"{len(ordered)} evidence records have SHA-256 {checksum}.",
                    observed_value=len(ordered),
                )
            )
        if not duplicate_groups:
            self._trace_pass("DUP-001")
        return findings

    def _file_rules(
        self,
        run_id: str,
        academic_year: str,
        records: list[ClassifiedEvidence],
    ) -> list[IntegrityFinding]:
        findings: list[IntegrityFinding] = []
        for record in records:
            document_type = record.document_type.primary_type.value
            if (
                document_type in {"event_report", "approval_document", "attendance_sheet"}
                and record.extraction.extraction_confidence < 0.5
            ):
                findings.append(
                    self._new_finding(
                        run_id,
                        "FILE-EMPTY-001",
                        FindingType.EMPTY_DOCUMENT,
                        [record.evidence_id],
                        "Document has no reliable extractable content",
                        f"{record.original_filename} could not be read reliably.",
                    )
                )
            elif document_type in {"event_report", "approval_document", "attendance_sheet"}:
                self._trace_pass("FILE-EMPTY-001", record.evidence_id)

            if document_type == "approval_document":
                signature = str(field_value(record, "signature_present") or "").casefold()
                if signature not in {"yes", "true", "present", "signed"}:
                    findings.append(
                        self._new_finding(
                            run_id,
                            "SIGN-001",
                            FindingType.MISSING_SIGNATURE,
                            [record.evidence_id],
                            "Approval signature is missing",
                            f"{record.original_filename} does not contain an affirmative signature marker.",
                            expected_value="Yes",
                            observed_value=field_value(record, "signature_present"),
                        )
                    )
                else:
                    self._trace_pass("SIGN-001", record.evidence_id)

            if document_type == "event_report":
                event_date = field_value(record, "event_date")
                if event_date and not self._date_in_academic_year(str(event_date), academic_year):
                    findings.append(
                        self._new_finding(
                            run_id,
                            "DATE-001",
                            FindingType.ACADEMIC_YEAR_MISMATCH,
                            [record.evidence_id],
                            "Event date is outside the selected academic year",
                            f"Event date {event_date} is not within {academic_year}.",
                            expected_value=academic_year,
                            observed_value=str(event_date),
                        )
                    )
                elif event_date:
                    self._trace_pass("DATE-001", record.evidence_id)

            duplicates = str(field_value(record, "duplicate_roll_numbers") or "").strip()
            if document_type == "attendance_sheet" and duplicates:
                findings.append(
                    self._new_finding(
                        run_id,
                        "DUP-STUDENT-001",
                        FindingType.DUPLICATE_STUDENT_ROW,
                        [record.evidence_id],
                        "Duplicate attendance rows detected",
                        f"Repeated roll numbers: {duplicates}.",
                        observed_value=duplicates,
                    )
                )
        return findings

    def _bundle_rules(
        self,
        run_id: str,
        academic_year: str,
        requirement_scope: list[str],
        bundle: EvidenceBundle,
        records: list[ClassifiedEvidence],
    ) -> tuple[list[IntegrityFinding], list[EvidenceGap]]:
        findings: list[IntegrityFinding] = []
        gaps: list[EvidenceGap] = []
        by_type: dict[str, list[ClassifiedEvidence]] = defaultdict(list)
        for record in records:
            by_type[record.document_type.primary_type.value].append(record)

        report = next(iter(by_type.get("event_report", [])), None)
        attendance = next(iter(by_type.get("attendance_sheet", [])), None)
        if report and attendance:
            reported = field_value(report, "reported_participant_count")
            observed = field_value(attendance, "unique_student_count")
            if reported is not None and observed is not None and int(reported) != int(observed):
                findings.append(
                    self._new_finding(
                        run_id,
                        "EVT-COUNT-001",
                        FindingType.PARTICIPANT_COUNT_MISMATCH,
                        [report.evidence_id, attendance.evidence_id],
                        "Participant count does not reconcile",
                        f"Event report claims {reported}; attendance contains {observed} unique students.",
                        bundle_id=bundle.bundle_id,
                        expected_value=reported,
                        observed_value=observed,
                    )
                )
            elif reported is not None and observed is not None:
                self._trace_pass("EVT-COUNT-001", report.evidence_id)

        extracted_departments = {
            str(field_value(record, "department"))
            for record in records
            if field_value(record, "department")
        }
        if len(extracted_departments) > 1 or (
            extracted_departments
            and bundle.department.casefold()
            not in {value.casefold() for value in extracted_departments}
        ):
            findings.append(
                self._new_finding(
                    run_id,
                    "EVT-DEPT-CONSISTENCY-001",
                    FindingType.DEPARTMENT_MISMATCH,
                    [record.evidence_id for record in records],
                    "Department values conflict within the event bundle",
                    f"Collector department is {bundle.department}; extracted values are "
                    f"{sorted(extracted_departments)}.",
                    bundle_id=bundle.bundle_id,
                    expected_value=bundle.department,
                    observed_value=", ".join(sorted(extracted_departments)),
                )
            )
        else:
            self._trace_pass(
                "EVT-DEPT-CONSISTENCY-001",
                records[0].evidence_id if records else None,
            )

        requirement_ids = sorted(
            {
                mapping.requirement_id
                for record in records
                for mapping in record.requirement_mappings
                if mapping.requirement_id in requirement_scope
            }
        )
        for requirement_id in requirement_ids:
            required = self.catalog.required_documents.get(requirement_id, {}).get("required", [])
            missing = [item for item in required if item not in by_type]
            for document_type in missing:
                finding = self._new_finding(
                    run_id,
                    "DOC-001",
                    FindingType.MISSING_REQUIRED_FIELD,
                    [record.evidence_id for record in records],
                    "Required evidence document is missing",
                    f"{document_type} is required for {requirement_id}.",
                    bundle_id=bundle.bundle_id,
                    requirement_id=requirement_id,
                    expected_value=document_type,
                )
                findings.append(finding)
                gaps.append(
                    self._new_gap(
                        run_id,
                        requirement_id,
                        GapType.MISSING_REQUIRED_DOCUMENT,
                        f"Bundle {bundle.bundle_id} is missing {document_type}.",
                        bundle_id=bundle.bundle_id,
                        department=bundle.department,
                        missing_evidence_type=document_type,
                        blocking=True,
                        related_findings=[finding.finding_id],
                    )
                )
            if not missing:
                self._trace_pass(
                    "DOC-001",
                    records[0].evidence_id if records else None,
                )
        return findings, gaps

    def _reuse_rules(
        self, run_id: str, records: list[ClassifiedEvidence]
    ) -> list[IntegrityFinding]:
        findings: list[IntegrityFinding] = []
        for record in records:
            requirements = {mapping.requirement_id for mapping in record.requirement_mappings}
            if len(requirements) > 1:
                findings.append(
                    self._new_finding(
                        run_id,
                        "REUSE-001",
                        FindingType.EVIDENCE_REUSE,
                        [record.evidence_id],
                        "Evidence is reused across multiple claims",
                        f"Mapped requirements: {', '.join(sorted(requirements))}.",
                        observed_value=", ".join(sorted(requirements)),
                    )
                )
            else:
                self._trace_pass("REUSE-001", record.evidence_id)
        return findings

    def _trace_pass(self, rule_id: str, evidence_id: str | None = None) -> None:
        if self.tracer:
            self.tracer.log_rule_result(
                rule_id=rule_id,
                passed=True,
                evidence_id=evidence_id,
            )

    def _unresolved_mapping_gaps(
        self, run_id: str, records: list[ClassifiedEvidence]
    ) -> list[EvidenceGap]:
        return [
            self._new_gap(
                run_id,
                "UNRESOLVED",
                GapType.UNRESOLVED_MAPPING,
                f"{record.evidence_id} has no accepted requirement mapping.",
                department=record.department,
                blocking=False,
            )
            for record in records
            if not record.requirement_mappings
        ]

    def _summaries(
        self,
        requirement_scope: list[str],
        records: list[ClassifiedEvidence],
        findings: list[IntegrityFinding],
        gaps: list[EvidenceGap],
    ) -> list[IntegritySummary]:
        departments = sorted({record.department for record in records})
        summaries: list[IntegritySummary] = []
        for department in departments:
            for requirement_id in requirement_scope:
                evidence_ids = {
                    record.evidence_id
                    for record in records
                    if record.department == department
                    and any(
                        mapping.requirement_id == requirement_id
                        for mapping in record.requirement_mappings
                    )
                }
                scoped_findings = [
                    finding
                    for finding in findings
                    if finding.requirement_id == requirement_id
                    or bool(evidence_ids.intersection(finding.evidence_ids))
                ]
                scoped_gaps = [
                    gap
                    for gap in gaps
                    if gap.department == department and gap.requirement_id == requirement_id
                ]
                severity_counts = Counter(finding.severity for finding in scoped_findings)
                penalty = sum(
                    self.settings.severity_penalty.get(finding.severity.value, 0)
                    for finding in scoped_findings
                )
                summaries.append(
                    IntegritySummary(
                        scope_type="department_requirement",
                        scope_id=f"{department}:{requirement_id}",
                        integrity_score=max(
                            0.0, self.settings.max_integrity_score - penalty
                        ),
                        total_findings=len(scoped_findings),
                        critical_findings=severity_counts[Severity.CRITICAL],
                        high_findings=severity_counts[Severity.HIGH],
                        medium_findings=severity_counts[Severity.MEDIUM],
                        low_findings=severity_counts[Severity.LOW],
                        blocking_findings=sum(
                            finding.blocking for finding in scoped_findings
                        ),
                        total_gaps=len(scoped_gaps),
                        status="requires_correction"
                        if scoped_findings or scoped_gaps
                        else "verified_by_automated_checks",
                    )
                )
        return summaries

    @staticmethod
    def _date_in_academic_year(value: str, academic_year: str) -> bool:
        try:
            event_date = date.fromisoformat(value[:10])
            start_year, end_year = [int(item) for item in academic_year.split("-", 1)]
            start = date(start_year, 7, 1)
            end = date(end_year, 6, 30)
            return start <= event_date <= end
        except (ValueError, TypeError):
            return False
