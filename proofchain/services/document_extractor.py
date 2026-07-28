"""Extractor dispatch with a strict ExtractionResult contract."""

from __future__ import annotations

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from proofchain.core.enums import ExtractionStatus
from proofchain.schemas.classification import ExtractionResult
from proofchain.schemas.common import SourceReference
from proofchain.services.pdf_extractor import PdfExtractor
from proofchain.services.spreadsheet_extractor import SpreadsheetExtractor


class DocumentExtractionService:
    max_text_characters = 2_000_000

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
        if extension == ".tsv":
            return self.spreadsheet_extractor.extract_tsv(path, evidence_id)
        if extension == ".docx":
            return self._extract_docx(path, evidence_id)
        if extension in {".txt", ".md"}:
            return self._extract_text(path, evidence_id, "plain_text")
        if extension == ".json":
            return self._extract_json(path, evidence_id)
        if extension == ".xml":
            return self._extract_xml(path, evidence_id)
        if extension in {".html", ".htm"}:
            return self._extract_html(path, evidence_id)
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

    def _bounded_text(self, text: str) -> tuple[str, list[str]]:
        normalized = "\n".join(
            line
            for line in (
                re.sub(r"[^\S\r\n]+", " ", raw_line).strip()
                for raw_line in text.splitlines()
            )
            if line
        )
        if len(normalized) <= self.max_text_characters:
            return normalized, []
        return (
            normalized[: self.max_text_characters],
            [
                "Extracted text was truncated at the deterministic character limit; "
                "human review is required for omitted content."
            ],
        )

    def _text_result(
        self,
        text: str,
        evidence_id: str,
        extractor: str,
    ) -> ExtractionResult:
        bounded, warnings = self._bounded_text(text)
        return ExtractionResult(
            extraction_status=(
                ExtractionStatus.PARTIAL
                if warnings or not bounded
                else ExtractionStatus.SUCCESS
            ),
            extractor_used=extractor,
            text=bounded or None,
            page_references=[
                SourceReference(
                    document=evidence_id,
                    text_snippet=bounded[:240] or None,
                )
            ],
            extraction_confidence=0.95 if bounded and not warnings else 0.7 if bounded else 0.0,
            warnings=warnings,
        )

    def _extract_text(
        self,
        path: Path,
        evidence_id: str,
        extractor: str,
    ) -> ExtractionResult:
        return self._text_result(
            path.read_text(encoding="utf-8-sig"),
            evidence_id,
            extractor,
        )

    def _extract_json(self, path: Path, evidence_id: str) -> ExtractionResult:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            text = "\n".join(
                f"{key} | {value}"
                for key, value in payload.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            )
        else:
            text = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return self._text_result(text, evidence_id, "json")

    def _extract_xml(self, path: Path, evidence_id: str) -> ExtractionResult:
        root = ElementTree.fromstring(path.read_text(encoding="utf-8-sig"))
        fields = [
            f"{self._display_label(node.tag)} | {node.text.strip()}"
            for node in root
            if node.text and node.text.strip()
        ]
        text = "\n".join(fields) if fields else "\n".join(
            item.strip() for item in root.itertext() if item.strip()
        )
        return self._text_result(text, evidence_id, "xml")

    def _extract_html(self, path: Path, evidence_id: str) -> ExtractionResult:
        parser = _HTMLTextExtractor()
        parser.feed(path.read_text(encoding="utf-8-sig"))
        return self._text_result("\n".join(parser.parts), evidence_id, "html_text")

    @staticmethod
    def _extract_docx(path: Path, evidence_id: str) -> ExtractionResult:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        paragraphs = []
        for paragraph in (node for node in root.iter() if node.tag.endswith("}p")):
            value = "".join(
                node.text or "" for node in paragraph.iter() if node.tag.endswith("}t")
            ).strip()
            if value:
                paragraphs.append(value)
        text = "\n".join(paragraphs)
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

    @staticmethod
    def _display_label(tag: str) -> str:
        local_name = tag.rsplit("}", 1)[-1]
        return local_name.replace("_", " ").strip().title()


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())
