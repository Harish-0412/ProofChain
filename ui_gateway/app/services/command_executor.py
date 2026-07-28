"""Asynchronous, allowlisted ProofChain CLI execution."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.security.command_allowlist import get_command


JOBS_DB: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()


class CommandExecutor:
    @staticmethod
    def execute_command(
        command_name: str,
        payload: dict[str, Any] | None = None,
        rationale: str = "",
    ) -> dict[str, Any]:
        descriptor = get_command(command_name)
        if command_name not in settings.allowlisted_commands or descriptor is None:
            return {
                "success": False,
                "error": f"Command '{command_name}' is not in the governed allowlist.",
            }
        payload = dict(payload or {})
        payload.pop("rationale", None)
        unknown = set(payload) - descriptor.allowed_body_keys
        if unknown:
            return {
                "success": False,
                "error": f"Unsupported command fields: {', '.join(sorted(unknown))}.",
            }
        missing = [
            key
            for key in descriptor.required_body_keys
            if key not in payload or CommandExecutor._is_empty(payload[key])
        ]
        if missing:
            return {
                "success": False,
                "error": f"Missing required command fields: {', '.join(sorted(missing))}.",
            }
        try:
            argv = CommandExecutor._build_argv(descriptor, payload)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        with JOBS_LOCK:
            JOBS_DB[job_id] = {
                "id": job_id,
                "success": True,
                "command": command_name,
                "rationale": rationale,
                "status": "queued",
                "argv": argv[3:],
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "exit_code": None,
                "stdout": "",
                "stderr": "",
            }
        threading.Thread(
            target=CommandExecutor._run,
            args=(job_id, argv),
            daemon=True,
        ).start()
        return CommandExecutor.get_job(job_id)

    @staticmethod
    def get_job(job_id: str) -> dict[str, Any]:
        with JOBS_LOCK:
            return dict(JOBS_DB.get(job_id, {"id": job_id, "status": "not_found"}))

    @staticmethod
    def _build_argv(descriptor, payload: dict[str, Any]) -> list[str]:
        argv = [sys.executable, "-m", "proofchain.cli", descriptor.cli_name]
        consumed = set()
        for key in descriptor.positional_body_keys:
            argv.append(CommandExecutor._safe_scalar(payload.get(key), key))
            consumed.add(key)
        for key in sorted(payload):
            if key in consumed:
                continue
            value = payload[key]
            flag = f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    argv.append(flag)
                continue
            if key in descriptor.list_body_keys:
                values = value if isinstance(value, list) else [value]
                if key in {"departments", "requirements"}:
                    argv.append(flag)
                    argv.extend(
                        CommandExecutor._safe_scalar(item, key) for item in values
                    )
                else:
                    for item in values:
                        argv.extend(
                            [flag, CommandExecutor._safe_scalar(item, key)]
                        )
                continue
            argv.extend([flag, CommandExecutor._safe_scalar(value, key)])
        return argv

    @staticmethod
    def _safe_scalar(value: Any, key: str) -> str:
        if not isinstance(value, (str, int, float)):
            raise ValueError(f"Field '{key}' must contain scalar values.")
        text = str(value)
        if not text or "\x00" in text or "\r" in text or "\n" in text:
            raise ValueError(f"Field '{key}' contains an invalid value.")
        return text

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value is None or value == "" or value == () or value == []

    @staticmethod
    def _run(job_id: str, argv: list[str]) -> None:
        with JOBS_LOCK:
            JOBS_DB[job_id]["status"] = "running"
            JOBS_DB[job_id]["started_at"] = datetime.now(tz=timezone.utc).isoformat()
        try:
            completed = subprocess.run(
                argv,
                cwd=settings.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=1800,
                shell=False,
                check=False,
            )
            stdout = completed.stdout[-200_000:]
            parsed = None
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError:
                pass
            with JOBS_LOCK:
                JOBS_DB[job_id].update(
                    status="completed" if completed.returncode == 0 else "failed",
                    exit_code=completed.returncode,
                    stdout=stdout,
                    stderr=completed.stderr[-50_000:],
                    result=parsed,
                    completed_at=datetime.now(tz=timezone.utc).isoformat(),
                )
        except (OSError, subprocess.SubprocessError) as exc:
            with JOBS_LOCK:
                JOBS_DB[job_id].update(
                    status="failed",
                    exit_code=None,
                    stderr=str(exc),
                    completed_at=datetime.now(tz=timezone.utc).isoformat(),
                )
