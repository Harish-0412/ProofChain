"""PDF text and table extraction."""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from proofchain.core.enums import ExtractionStatus
from proofchain.schemas.classification import ExtractionResult
from proofchain.schemas.common import SourceReference


class PdfExtractor:
    def extract(self, path: Path, evidence_id: str) -> ExtractionResult:
        page_text: list[str] = []
        tables: list[dict] = []
        references: list[SourceReference] = []
        with pdfplumber.open(str(path)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                page_text.append(text)
                references.append(
                    SourceReference(
                        document=evidence_id,
                        page_number=page_number,
                        text_snippet=text[:240] or None,
                    )
                )
                for table in page.extract_tables() or []:
                    tables.append({"page_number": page_number, "rows": table})

        combined = "\n".join(page_text).strip()
        return ExtractionResult(
            extraction_status=ExtractionStatus.SUCCESS
            if combined
            else ExtractionStatus.PARTIAL,
            extractor_used="pdfplumber",
            text=combined or None,
            tables=tables,
            page_count=len(page_text),
            page_references=references,
            extraction_confidence=0.98 if combined else 0.45,
            warnings=[] if combined else ["PDF contains no extractable text."],
        )
