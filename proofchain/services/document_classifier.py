"""Deterministic document type classification."""

from __future__ import annotations

from pathlib import Path

from proofchain.core.config import get_document_types
from proofchain.core.enums import ClassificationMethod, DocumentType
from proofchain.schemas.classification import (
    ClassificationCandidate,
    DocumentTypePrediction,
    ExtractionResult,
)
from proofchain.schemas.evidence import EvidenceRecord


class DocumentClassifier:
    def __init__(self, config: dict | None = None):
        self.config = config or get_document_types()

    def classify(
        self,
        evidence: EvidenceRecord,
        extraction: ExtractionResult,
    ) -> DocumentTypePrediction:
        path = Path(evidence.absolute_path)
        text = (extraction.text or "").casefold()
        filename = path.name.casefold()
        parent_parts = {part.casefold() for part in path.parts}
        scores: dict[DocumentType, float] = {}
        reasons: dict[DocumentType, list[str]] = {}
        strongest_method: dict[DocumentType, ClassificationMethod] = {}

        for type_name, rules in self.config.get("document_types", {}).items():
            try:
                document_type = DocumentType(type_name)
            except ValueError:
                continue
            score = 0.0
            type_reasons: list[str] = []
            method = ClassificationMethod.KEYWORD_RULE

            extensions = {item.casefold() for item in rules.get("file_extensions", [])}
            if path.suffix.casefold() in extensions:
                score += 1.0
                type_reasons.append(f"Extension {path.suffix} is configured for {type_name}.")
                method = ClassificationMethod.STRUCTURE_RULE

            if any(hint.casefold() in parent_parts for hint in rules.get("folder_hints", [])):
                score += 0.45
                type_reasons.append("Parent folder matched.")
                method = ClassificationMethod.FOLDER_RULE

            if any(pattern.casefold() in filename for pattern in rules.get("filename_patterns", [])):
                score += 0.45
                type_reasons.append("Filename pattern matched.")
                method = ClassificationMethod.FILENAME_RULE

            keyword_hits = [
                keyword for keyword in rules.get("keywords", []) if keyword.casefold() in text
            ]
            if keyword_hits:
                score += min(0.3, 0.12 + (len(keyword_hits) - 1) * 0.06)
                type_reasons.append(f"Content keywords matched: {', '.join(keyword_hits[:3])}.")

            if type_name == "attendance_sheet" and extraction.tables:
                flattened = str(extraction.tables[:1]).casefold()
                if "roll number" in flattened or "student" in flattened:
                    score += 0.35
                    type_reasons.append("Spreadsheet structure matched attendance data.")
                    method = ClassificationMethod.STRUCTURE_RULE

            scores[document_type] = min(score, 1.0)
            reasons[document_type] = type_reasons
            strongest_method[document_type] = method

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0].value))
        if not ranked or ranked[0][1] < 0.5:
            return DocumentTypePrediction(
                primary_type=DocumentType.UNKNOWN,
                confidence=ranked[0][1] if ranked else 0.0,
                reasons=["No deterministic document-type rule reached the acceptance floor."],
                requires_human_review=True,
            )

        primary, confidence = ranked[0]
        secondary = [
            ClassificationCandidate(
                document_type=document_type,
                confidence=score,
                reason="; ".join(reasons[document_type]),
            )
            for document_type, score in ranked[1:3]
            if score > 0
        ]
        return DocumentTypePrediction(
            primary_type=primary,
            confidence=confidence,
            secondary_types=secondary,
            classification_method=strongest_method[primary],
            reasons=reasons[primary],
        )
