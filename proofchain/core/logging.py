"""
core/logging.py
Structured logging for ProofChain.

Produces both:
- Human-readable console output (via Python logging)
- Machine-readable JSON Lines trace entries (for audit and replay)

Usage:
    from proofchain.core.logging import get_logger, TraceLogger

    logger = get_logger(__name__)
    logger.info("Processing started")

    tracer = TraceLogger(run_id="RUN-001", trace_path=path)
    tracer.log(agent="collector", event="file_discovered", evidence_id="EVD-CSE-001")
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Standard Python Logger
# ---------------------------------------------------------------------------

LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a named logger with console output configured.
    Idempotent: calling this multiple times with the same name returns the same logger.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# JSON Lines Trace Logger
# ---------------------------------------------------------------------------

class TraceLogger:
    """
    Appends structured JSON Lines trace entries to a .jsonl file.

    Each entry records: timestamp, run_id, agent, event, and optional extra fields.
    The trace file is the canonical audit trail for a pipeline run.
    """

    def __init__(self, run_id: str, trace_path: Path):
        self.run_id = run_id
        self.trace_path = trace_path
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        agent: str,
        event: str,
        status: str | None = None,
        evidence_id: str | None = None,
        **extra: Any,
    ) -> None:
        """Append one trace entry to the JSONL file."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "run_id": self.run_id,
            "agent": agent,
            "event": event,
        }
        if status is not None:
            entry["status"] = status
        if evidence_id is not None:
            entry["evidence_id"] = evidence_id
        entry.update(extra)

        with self.trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def log_agent_start(self, agent: str, input_count: int) -> None:
        self.log(agent=agent, event="agent_started", status="running", input_count=input_count)

    def log_agent_end(self, agent: str, status: str, success_count: int, failure_count: int) -> None:
        self.log(
            agent=agent,
            event="agent_completed",
            status=status,
            success_count=success_count,
            failure_count=failure_count,
        )

    def log_rule_result(
        self,
        rule_id: str,
        passed: bool,
        finding_id: str | None = None,
        evidence_id: str | None = None,
    ) -> None:
        self.log(
            agent="integrity",
            event="rule_passed" if passed else "rule_failed",
            rule_id=rule_id,
            finding_id=finding_id,
            evidence_id=evidence_id,
        )

    def log_error(self, agent: str, error_code: str, message: str, evidence_id: str | None = None) -> None:
        self.log(
            agent=agent,
            event="error",
            status="error",
            error_code=error_code,
            message=message,
            evidence_id=evidence_id,
        )
