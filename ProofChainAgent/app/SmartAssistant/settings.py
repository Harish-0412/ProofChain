from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parents[1]
ENV_FILE = PROJECT_DIR / "agentcore" / ".env.local"


def load_local_env(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_csv(name: str) -> set[str]:
    value = os.getenv(name, "")
    return {part.strip() for part in value.split(",") if part.strip()}


def optional_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()
