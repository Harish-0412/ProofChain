import os
import re
from fastapi import HTTPException, status

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{1,64}$")

class PathGuard:
    @staticmethod
    def validate_run_id(run_id: str) -> str:
        if not RUN_ID_PATTERN.match(run_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid run_id format: '{run_id}'. Must be alphanumeric with hyphens/underscores.",
            )
        return run_id

    @staticmethod
    def safe_join(base_dir: str, *paths: str) -> str:
        resolved_base = os.path.abspath(base_dir)
        target_path = os.path.abspath(os.path.join(resolved_base, *paths))
        if not target_path.startswith(resolved_base):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Path traversal attempt detected.",
            )
        return target_path
