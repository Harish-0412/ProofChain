"""Streaming content checksums."""

from __future__ import annotations

import hashlib
from pathlib import Path


class ChecksumService:
    def sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
