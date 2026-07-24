"""Filesystem metadata normalization."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class FileMetadata:
    mime_type: str
    file_size_bytes: int
    created_at: datetime
    modified_at: datetime


class MetadataService:
    def inspect(self, path: Path) -> FileMetadata:
        stat = path.stat()
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return FileMetadata(
            mime_type=mime_type,
            file_size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )
