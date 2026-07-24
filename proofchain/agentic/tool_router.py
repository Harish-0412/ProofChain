"""Strict permission boundary between agent decisions and deterministic tools."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.schemas.agentic import ActionProposal, ToolResult


class ToolPermissionError(PermissionError):
    pass


@dataclass
class RoutedToolExecution:
    output: Any
    audit: ToolResult


class ToolRouter:
    def __init__(self, coordination: JsonCoordinationRepository):
        self.coordination = coordination
        self._tools: dict[str, tuple[str, Callable[..., Any]]] = {}
        self._permissions: dict[str, set[str]] = {}

    def register(
        self,
        *,
        name: str,
        agent_name: str,
        function: Callable[..., Any],
        version: str = "1.0.0",
    ) -> None:
        self._tools[name] = (version, function)
        self._permissions.setdefault(agent_name, set()).add(name)

    def execute(self, action: ActionProposal) -> RoutedToolExecution:
        if action.selected_tool not in self._permissions.get(action.agent_name, set()):
            raise ToolPermissionError(
                f"{action.agent_name} is not allowed to execute {action.selected_tool}."
            )
        version, function = self._tools[action.selected_tool]
        started = time.perf_counter()
        try:
            output = function(**action.tool_arguments)
        except Exception as exc:
            audit = ToolResult(
                tool_name=action.selected_tool,
                tool_version=version,
                status="failed",
                errors=[str(exc)],
                execution_time_ms=int((time.perf_counter() - started) * 1000),
            )
            self.coordination.append_tool_result(action.run_id, audit)
            raise

        status = getattr(output, "status", "completed")
        audit = ToolResult(
            tool_name=action.selected_tool,
            tool_version=version,
            status="failed"
            if status == "failed"
            else "partial"
            if status == "completed_with_warnings"
            else "success",
            output={
                "result_type": type(output).__name__,
                "status": status,
                "success_count": getattr(output, "success_count", 0),
                "warning_count": getattr(output, "warning_count", 0),
                "failure_count": getattr(output, "failure_count", 0),
                "output_reference": getattr(output, "output_reference", None),
                "output_snapshot_hash": getattr(output, "output_snapshot_hash", None),
            },
            source_references=[
                reference
                for reference in [getattr(output, "output_reference", None)]
                if reference
            ],
            warnings=list(getattr(output, "warnings", [])),
            errors=[
                getattr(error, "message", str(error))
                for error in getattr(output, "errors", [])
            ],
            execution_time_ms=int((time.perf_counter() - started) * 1000),
        )
        self.coordination.append_tool_result(action.run_id, audit)
        return RoutedToolExecution(output=output, audit=audit)
