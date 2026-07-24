"""
core/ids.py
Stable, deterministic ID generation for ProofChain entities.

Key design decisions:
- Evidence IDs are deterministic (based on department + year + sequence) NOT random UUIDs.
- Run IDs are timestamp-based for uniqueness and human readability.
- Version IDs embed their parent evidence ID.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Evidence ID
# ---------------------------------------------------------------------------

def generate_evidence_id(department: str, academic_year: str, sequence: int) -> str:
    """
    Generate a stable, human-readable evidence ID.

    Format: EVD-{DEPT}-{YEAR_START}-{YEAR_END}-{SEQ:05d}
    Example: EVD-CSE-2025-2026-00017
    """
    year_part = academic_year.replace("-", "-")   # already "2025-2026"
    seq_part = str(sequence).zfill(5)
    dept_upper = department.strip().upper()
    return f"EVD-{dept_upper}-{year_part}-{seq_part}"


# ---------------------------------------------------------------------------
# Version ID
# ---------------------------------------------------------------------------

def generate_version_id(evidence_id: str, version_number: int) -> str:
    """
    Generate a version ID tied to a parent evidence record.

    Format: VER-{SEQ}-{VERSION:02d}
    Example: VER-00017-01
    """
    # Extract sequence number from EVD-CSE-2025-2026-00017 -> 00017
    parts = evidence_id.split("-")
    seq_part = parts[-1] if parts else "00000"
    return f"VER-{seq_part}-{str(version_number).zfill(2)}"


# ---------------------------------------------------------------------------
# Run ID
# ---------------------------------------------------------------------------

def generate_run_id() -> str:
    """
    Generate a unique pipeline run ID.

    Format: RUN-{YYYYMMDD}-{SEQUENCE_SUFFIX}
    Example: RUN-20260724-A3F2
    Uses a short random suffix to avoid collisions within the same day.
    """
    today = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:4].upper()
    return f"RUN-{today}-{suffix}"


# ---------------------------------------------------------------------------
# Finding ID
# ---------------------------------------------------------------------------

def generate_finding_id(run_id: str, sequence: int) -> str:
    """
    Generate a unique integrity finding ID.

    Format: FND-{RUN_SUFFIX}-{SEQ:06d}
    Example: FND-A3F2-000142
    """
    run_suffix = run_id.split("-")[-1] if "-" in run_id else run_id[:4]
    return f"FND-{run_suffix}-{str(sequence).zfill(6)}"


# ---------------------------------------------------------------------------
# Gap ID
# ---------------------------------------------------------------------------

def generate_gap_id(run_id: str, sequence: int) -> str:
    """
    Generate a unique gap ID.

    Format: GAP-{RUN_SUFFIX}-{SEQ:05d}
    Example: GAP-A3F2-00038
    """
    run_suffix = run_id.split("-")[-1] if "-" in run_id else run_id[:4]
    return f"GAP-{run_suffix}-{str(sequence).zfill(5)}"


# ---------------------------------------------------------------------------
# Bundle ID
# ---------------------------------------------------------------------------

def generate_bundle_id(department: str, event_key: str) -> str:
    """
    Generate a deterministic bundle ID based on department and event key.

    Format: BUNDLE-{DEPT}-{SLUG}
    Example: BUNDLE-CSE-AIWORKSHOP-20260214
    """
    dept_upper = department.strip().upper()
    slug = event_key.strip().upper().replace(" ", "")[:20]
    return f"BUNDLE-{dept_upper}-{slug}"


# ---------------------------------------------------------------------------
# Agent Run ID
# ---------------------------------------------------------------------------

def generate_agent_run_id(agent_name: str, run_id: str) -> str:
    """
    Generate a unique agent execution ID.

    Format: AGNT-{AGENT_PREFIX}-{RUN_SUFFIX}-{SHORT_UUID}
    Example: AGNT-COLL-A3F2-7B2E
    """
    prefix = agent_name[:4].upper()
    run_suffix = run_id.split("-")[-1] if "-" in run_id else run_id[:4]
    short_id = uuid.uuid4().hex[:4].upper()
    return f"AGNT-{prefix}-{run_suffix}-{short_id}"


# ---------------------------------------------------------------------------
# Correlation ID
# ---------------------------------------------------------------------------

def generate_correlation_id() -> str:
    """Generate a UUID4 correlation ID for distributed tracing."""
    return str(uuid.uuid4())
