import json
import os
from typing import Any, List, Optional
from app.config import settings
from app.services.path_guard import PathGuard

class ArtifactReader:
    @staticmethod
    def read_json_artifact(run_id: str, filename: str) -> Optional[Any]:
        safe_run_id = PathGuard.validate_run_id(run_id)
        filepath = PathGuard.safe_join(settings.outputs_dir, safe_run_id, filename)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def read_jsonl_artifact(run_id: str, filename: str, limit: int = 100) -> List[Any]:
        safe_run_id = PathGuard.validate_run_id(run_id)
        filepath = PathGuard.safe_join(settings.outputs_dir, safe_run_id, filename)
        if not os.path.exists(filepath):
            return []
        items = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        items.append(json.loads(line))
                        if len(items) >= limit:
                            break
        except Exception:
            pass
        return items

    @staticmethod
    def list_runs() -> List[str]:
        if not os.path.exists(settings.outputs_dir):
            return []
        runs = []
        for entry in os.listdir(settings.outputs_dir):
            full_path = os.path.join(settings.outputs_dir, entry)
            if os.path.isdir(full_path) and not entry.startswith("."):
                runs.append(entry)
        return sorted(runs, reverse=True)
