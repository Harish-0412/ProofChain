"""
core/config.py
Configuration loading for ProofChain.

Reads from:
1. config/settings.yaml  (primary)
2. .env file             (secrets, overrides)
3. Environment variables (highest priority)

All services should access configuration through get_settings().
"""

from __future__ import annotations

import os
from functools import lru_cache

import yaml

from proofchain.core.paths import SETTINGS_FILE, DOCUMENT_TYPES_FILE, REQUIREMENT_MAPPING_FILE


# ---------------------------------------------------------------------------
# Settings Dataclass
# ---------------------------------------------------------------------------

class ProofChainSettings:
    """
    Holds runtime settings for the ProofChain pipeline.
    Values are resolved from YAML config, then overridden by env vars.
    """

    def __init__(self, raw: dict):
        pipeline = raw.get("pipeline", {})
        self.academic_year: str = os.environ.get(
            "PROOFCHAIN_ACADEMIC_YEAR",
            pipeline.get("default_academic_year", "2025-2026"),
        )
        self.allowed_extensions: list[str] = pipeline.get(
            "allowed_extensions",
            [
                ".pdf",
                ".xlsx",
                ".csv",
                ".tsv",
                ".docx",
                ".txt",
                ".md",
                ".json",
                ".xml",
                ".html",
                ".htm",
                ".png",
                ".jpg",
                ".jpeg",
            ],
        )
        self.supported_departments: list[str] = pipeline.get(
            "supported_departments", ["CSE", "AIML", "AIDS", "Mechanical", "ECE", "EEE"]
        )

        confidence = raw.get("confidence_thresholds", {})
        self.confidence_auto_accept: float = confidence.get("auto_accept", 0.90)
        self.confidence_warn: float = confidence.get("warn", 0.75)
        self.confidence_human_review: float = confidence.get("human_review", 0.50)

        integrity = raw.get("integrity", {})
        self.severity_penalty: dict[str, int] = integrity.get(
            "severity_penalties",
            {"critical": 30, "high": 15, "medium": 7, "low": 2}
        )
        self.max_integrity_score: float = integrity.get("max_score", 100.0)

        extraction = raw.get("extraction", {})
        self.extractor_version: str = extraction.get("version", "1.0.0")
        self.classifier_version: str = extraction.get("classifier_version", "1.0.0")
        self.rule_version: str = raw.get("rules", {}).get("version", "1.0.0")


@lru_cache(maxsize=1)
def get_settings() -> ProofChainSettings:
    """Load and cache the global ProofChain settings."""
    if SETTINGS_FILE.exists():
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    else:
        raw = {}
    return ProofChainSettings(raw)


# ---------------------------------------------------------------------------
# Document Types Config
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_document_types() -> dict:
    """Load and cache document type classification rules."""
    if DOCUMENT_TYPES_FILE.exists():
        with DOCUMENT_TYPES_FILE.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


# ---------------------------------------------------------------------------
# Requirement Mapping Config
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_requirement_mapping() -> dict:
    """Load and cache accreditation requirement mapping configuration."""
    if REQUIREMENT_MAPPING_FILE.exists():
        with REQUIREMENT_MAPPING_FILE.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}
