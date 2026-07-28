"""Authority-ranked, cited, advisory-only local knowledge retrieval."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from proofchain.schemas.institutional import KnowledgeCitation, KnowledgeSource


AUTHORITY_WEIGHT = {
    "official_framework": 1.0,
    "institutional_policy": 0.9,
    "approved_procedure": 0.8,
    "historical_package": 0.6,
    "advisory_example": 0.4,
}


def retrieve_sources(
    query: str,
    sources: list[KnowledgeSource],
    maximum_results: int,
    require_current: bool,
) -> tuple[list[KnowledgeCitation], list[str]]:
    query_terms = set(_terms(query))
    now = datetime.now(tz=timezone.utc)
    ranked: list[tuple[float, KnowledgeSource, str]] = []
    conflicts: list[str] = []
    for source in sources:
        if not source.approved:
            continue
        freshness = (
            "expired"
            if source.valid_until and source.valid_until < now
            else "current"
            if source.published_at or source.valid_until
            else "undated"
        )
        if require_current and freshness == "expired":
            continue
        source_terms = set(_terms(f"{source.title} {source.content}"))
        lexical = len(query_terms & source_terms) / max(len(query_terms), 1)
        score = min(1.0, lexical * 0.75 + AUTHORITY_WEIGHT[source.authority] * 0.25)
        if score <= 0.25:
            continue
        ranked.append((score, source, freshness))
        lowered = source.content.lower()
        if any(marker in lowered for marker in ("conflicts with", "supersedes", "contradicts")):
            conflicts.append(source.source_id)
    ranked.sort(key=lambda item: (-item[0], -AUTHORITY_WEIGHT[item[1].authority], item[1].source_id))
    citations = [
        KnowledgeCitation(
            source_id=source.source_id,
            title=source.title,
            uri=source.uri,
            authority=source.authority,
            source_checksum=source.checksum
            or hashlib.sha256(source.content.encode("utf-8")).hexdigest(),
            relevance_score=round(score, 4),
            freshness_status=freshness,
            supporting_excerpt=_excerpt(source.content, query_terms),
        )
        for score, source, freshness in ranked[:maximum_results]
    ]
    return citations, sorted(set(conflicts))


def _terms(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9.]+", text.lower())
        if len(token) > 2
    ]


def _excerpt(content: str, query_terms: set[str], limit: int = 240) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())
    sentence = max(
        sentences or [content],
        key=lambda item: len(query_terms & set(_terms(item))),
    )
    return sentence[:limit].strip()

