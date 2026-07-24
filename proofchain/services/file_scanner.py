"""Read-only evidence source discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileCandidate:
    path: Path
    source_directory: Path
    department: str
    supported: bool


class FileScanner:
    def scan(
        self,
        source_directories: list[str],
        *,
        allowed_extensions: list[str],
        department_scope: list[str],
        recursive: bool,
    ) -> tuple[list[FileCandidate], list[Path]]:
        allowed = {extension.lower() for extension in allowed_extensions}
        department_lookup = {item.casefold(): item for item in department_scope}
        candidates: list[FileCandidate] = []
        missing: list[Path] = []

        for source_text in source_directories:
            source = Path(source_text).expanduser().resolve()
            if not source.is_dir():
                missing.append(source)
                continue
            iterator = source.rglob("*") if recursive else source.glob("*")
            for path in iterator:
                if not path.is_file():
                    continue
                department = self._infer_department(path, source, department_lookup)
                if department_scope and not department:
                    continue
                candidates.append(
                    FileCandidate(
                        path=path.resolve(),
                        source_directory=source,
                        department=department or source.name,
                        supported=path.suffix.lower() in allowed,
                    )
                )

        candidates.sort(key=lambda item: str(item.path).casefold())
        return candidates, missing

    @staticmethod
    def _infer_department(
        path: Path,
        source: Path,
        department_lookup: dict[str, str],
    ) -> str | None:
        for part in path.parts:
            match = department_lookup.get(part.casefold())
            if match:
                return match
        return department_lookup.get(source.name.casefold())
