"""ProofChain UI Gateway — security: audit log.

Every inbound HTTP request and every command dispatch is written to an
append-only JSONL audit log.  The file is flushed after every write to
ensure durability even if the process is killed mid-request.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Thread-safety lock so concurrent requests don't interleave log lines.
_lock = threading.Lock()

# File handle opened once at module import time (lazy-opened on first write).
_fh: Optional[Any] = None


def _get_fh():
    """Return (and lazily open) the audit log file handle."""
    global _fh
    if _fh is None:
        log_path: Path = settings.ui_gateway_audit_log_file
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            _fh = open(log_path, "a", encoding="utf-8", buffering=1)  # line-buffered
        except OSError as exc:
            logger.error("audit_log: cannot open %s: %s", log_path, exc)
    return _fh


def _write(record: Dict[str, Any]) -> None:
    """Serialize *record* to the audit log, thread-safely."""
    fh = _get_fh()
    if fh is None:
        return
    line = json.dumps(record, default=str)
    with _lock:
        try:
            fh.write(line + "\n")
            fh.flush()
        except OSError as exc:
            logger.error("audit_log: write error: %s", exc)


# ------------------------------------------------------------------ #
# Public helpers
# ------------------------------------------------------------------ #

def log_request(
    *,
    method: str,
    path: str,
    client_host: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Write a request audit record."""
    record: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "request",
        "method": method,
        "path": path,
        "client": client_host,
        "status": status_code,
        "duration_ms": duration_ms,
    }
    if extra:
        record.update(extra)
    _write(record)


def log_command(
    *,
    slug: str,
    args: Dict[str, Any],
    job_id: str,
    client_host: Optional[str] = None,
) -> None:
    """Write a command-dispatch audit record."""
    record: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "command",
        "slug": slug,
        "args": args,
        "job_id": job_id,
        "client": client_host,
    }
    _write(record)


def log_command_result(
    *,
    job_id: str,
    exit_code: int,
    duration_ms: float,
) -> None:
    """Write a command-completion audit record."""
    record: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "command_result",
        "job_id": job_id,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
    }
    _write(record)
