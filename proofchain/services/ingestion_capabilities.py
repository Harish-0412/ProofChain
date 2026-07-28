"""Deterministic file capability classification for governed ingestion."""

from __future__ import annotations

from pathlib import Path

from proofchain.schemas.ingestion import (
    IngestionCapabilityDecision,
    IngestionCapabilityReport,
)


NATIVE_EXTRACTORS = {
    ".pdf": "pdfplumber",
    ".xlsx": "openpyxl",
    ".csv": "csv",
    ".tsv": "csv",
    ".docx": "docx_xml",
    ".txt": "plain_text",
    ".md": "plain_text",
    ".json": "json",
    ".xml": "xml",
    ".html": "html_text",
    ".htm": "html_text",
}
METADATA_ONLY = {
    ".png": "image_metadata",
    ".jpg": "image_metadata",
    ".jpeg": "image_metadata",
}
REJECTED_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".jar",
    ".js",
    ".msi",
    ".ps1",
    ".scr",
    ".vbs",
}
ARCHIVE_EXTENSIONS = {".7z", ".gz", ".rar", ".tar", ".tgz", ".zip"}


class IngestionCapabilityService:
    """Classify a path before extraction without trusting its contents."""

    def assess(self, path: Path | str) -> IngestionCapabilityDecision:
        extension = Path(path).suffix.lower()
        if extension in NATIVE_EXTRACTORS:
            return IngestionCapabilityDecision(
                extension=extension,
                capability="native_extraction",
                extractor=NATIVE_EXTRACTORS[extension],
                reason="A bounded deterministic extractor is registered.",
                downstream_action="process",
                security_inspection_required=True,
            )
        if extension in METADATA_ONLY:
            return IngestionCapabilityDecision(
                extension=extension,
                capability="metadata_only",
                extractor=METADATA_ONLY[extension],
                reason=(
                    "The file is registered and its metadata is available; deterministic "
                    "OCR is not configured."
                ),
                downstream_action="process_with_warning",
                security_inspection_required=True,
            )
        if extension in REJECTED_EXTENSIONS:
            return IngestionCapabilityDecision(
                extension=extension,
                capability="rejected",
                reason="Executable or script content is outside the evidence boundary.",
                downstream_action="block",
                security_inspection_required=True,
            )
        if extension in ARCHIVE_EXTENSIONS:
            return IngestionCapabilityDecision(
                extension=extension,
                capability="unsupported",
                reason=(
                    "Archive content requires security inspection and an approved "
                    "conversion or extraction workflow."
                ),
                downstream_action="human_conversion_required",
                security_inspection_required=True,
            )
        return IngestionCapabilityDecision(
            extension=extension or "<none>",
            capability="unsupported",
            reason="No deterministic extractor is registered for this file type.",
            downstream_action="human_conversion_required",
            security_inspection_required=True,
        )

    def report(self, paths: list[Path | str] | None = None) -> IngestionCapabilityReport:
        return IngestionCapabilityReport(
            native_extensions=sorted(NATIVE_EXTRACTORS),
            metadata_only_extensions=sorted(METADATA_ONLY),
            rejected_extensions=sorted(REJECTED_EXTENSIONS),
            unknown_file_policy=(
                "Register identity and checksum, mark unsupported, exclude from positive "
                "evidence conclusions, and request governed conversion."
            ),
            decisions=[self.assess(path) for path in paths or []],
        )
