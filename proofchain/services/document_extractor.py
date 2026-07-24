"""Extractor dispatch with a strict ExtractionResult contract."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from proofchain.core.enums import ExtractionStatus
from proofchain.schemas.classification import ExtractionResult
from proofchain.schemas.common import SourceReference
from proofchain.services.pdf_extractor import PdfExtractor
from proofchain.services.spreadsheet_extractor import SpreadsheetExtractor


class DocumentExtractionService:
    def __init__(
        self,
        pdf_extractor: PdfExtractor | None = None,
        spreadsheet_extractor: SpreadsheetExtractor | None = None,
    ):
        self.pdf_extractor = pdf_extractor or PdfExtractor()
        self.spreadsheet_extractor = spreadsheet_extractor or SpreadsheetExtractor()

    def extract(self, path: Path, evidence_id: str) -> ExtractionResult:
        extension = path.suffix.lower()
        if extension == ".pdf":
            return self.pdf_extractor.extract(path, evidence_id)
        if extension == ".xlsx":
            return self.spreadsheet_extractor.extract_xlsx(path, evidence_id)
        if extension == ".csv":
            return self.spreadsheet_extractor.extract_csv(path, evidence_id)
        if extension == ".docx":
            return self._extract_docx(path, evidence_id)
        if extension in {".png", ".jpg", ".jpeg"}:
            return ExtractionResult(
                extraction_status=ExtractionStatus.SUCCESS,
                extractor_used="image_metadata",
                extraction_confidence=1.0,
                warnings=["Image OCR is outside the deterministic MVP boundary."],
            )
        return ExtractionResult(
            extraction_status=ExtractionStatus.UNSUPPORTED,
            extractor_used="none",
            extraction_confidence=0.0,
            warnings=[f"No extractor is registered for {extension}."],
        )

    @staticmethod
    def _extract_docx(path: Path, evidence_id: str) -> ExtractionResult:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        text = " ".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
        text = re.sub(r"\s+", " ", text).strip()
        return ExtractionResult(
            extraction_status=ExtractionStatus.SUCCESS
            if text
            else ExtractionStatus.PARTIAL,
            extractor_used="docx_xml",
            text=text or None,
            page_references=[
                SourceReference(document=evidence_id, text_snippet=text[:240] or None)
            ],
            extraction_confidence=0.9 if text else 0.4,
        )
