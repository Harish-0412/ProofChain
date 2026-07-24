"""
agents/base.py
Abstract BaseAgent class that all ProofChain agents must inherit.

Enforces the standard agent lifecycle:
    Validate Input
        ↓
    Create Agent Run Record
        ↓
    Execute Approved Tools
        ↓
    Validate Output
        ↓
    Persist Output
        ↓
    Return Structured Agent Result

The base handles:
- Logging (both console and structured trace)
- Timing
- Agent run ID generation
- Structured error wrapping
- Input/output hash computation for idempotency
- Safe partial-failure handling
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Generic, TypeVar

from proofchain.core.ids import generate_agent_run_id
from proofchain.core.logging import get_logger, TraceLogger
from proofchain.core.exceptions import ProofChainError

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


class BaseAgent(ABC, Generic[InputType, OutputType]):
    """
    Abstract base class for all ProofChain agents.

    Every concrete agent must implement:
        - validate_input(input_data)
        - execute(input_data)
        - validate_output(output_data)

    The run() method orchestrates the full lifecycle automatically.
    """

    agent_name: str = "base_agent"
    agent_version: str = "1.0.0"

    def __init__(self, tracer: TraceLogger | None = None):
        self.logger = get_logger(f"proofchain.agents.{self.agent_name}")
        self.tracer = tracer
        self._agent_run_id: str | None = None

    # ------------------------------------------------------------------
    # Abstract Interface
    # ------------------------------------------------------------------

    @abstractmethod
    def validate_input(self, input_data: InputType) -> None:
        """
        Validate input before execution begins.
        Raise a descriptive ProofChainError if the input is invalid.
        This method must not modify state.
        """
        ...

    @abstractmethod
    def execute(self, input_data: InputType) -> OutputType:
        """
        Core agent logic.
        Must return a structured output matching the OutputType contract.
        May raise RecoverableAgentError for partial failures.
        """
        ...

    @abstractmethod
    def validate_output(self, output_data: OutputType) -> None:
        """
        Validate the output before it is persisted and returned.
        Raise a SchemaValidationError if the output is malformed.
        """
        ...

    # ------------------------------------------------------------------
    # Lifecycle Orchestrator
    # ------------------------------------------------------------------

    def run(self, input_data: InputType) -> OutputType:
        """
        Execute the full agent lifecycle with timing, logging, and error wrapping.
        This method should NOT be overridden by subclasses.
        """
        run_id = getattr(getattr(input_data, "workflow", None), "run_id", "UNKNOWN")
        self._agent_run_id = generate_agent_run_id(self.agent_name, run_id)

        self.logger.info(
            f"[{self.agent_name}] Starting | agent_run_id={self._agent_run_id} | run={run_id}"
        )
        if self.tracer:
            self.tracer.log_agent_start(agent=self.agent_name, input_count=self._count_inputs(input_data))

        start_time = time.perf_counter()

        try:
            self.validate_input(input_data)
            output = self.execute(input_data)
            self.validate_output(output)

        except ProofChainError:
            # Re-raise structured errors as-is
            raise
        except Exception as exc:
            # Wrap unexpected errors with context
            self.logger.error(f"[{self.agent_name}] Unexpected error: {exc}", exc_info=True)
            raise ProofChainError(
                message=str(exc),
                error_code=f"{self.agent_name.upper()}_UNEXPECTED_ERROR",
            ) from exc

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        status = getattr(output, "status", "completed")

        self.logger.info(
            f"[{self.agent_name}] Completed | status={status} | duration={elapsed_ms}ms"
        )
        if self.tracer:
            self.tracer.log_agent_end(
                agent=self.agent_name,
                status=status,
                success_count=getattr(output, "success_count", 0),
                failure_count=getattr(output, "failure_count", 0),
            )

        # Attach timing to output if the field exists
        if hasattr(output, "duration_ms"):
            object.__setattr__(output, "duration_ms", elapsed_ms) if output.model_config.get("frozen") else setattr(output, "duration_ms", elapsed_ms)
        if hasattr(output, "completed_at"):
            ts = datetime.now(tz=timezone.utc)
            try:
                setattr(output, "completed_at", ts)
            except Exception:
                pass

        return output

    # ------------------------------------------------------------------
    # Idempotency Support
    # ------------------------------------------------------------------

    def compute_input_hash(self, input_data: InputType) -> str:
        """
        Compute a SHA-256 hash of the serialized input.
        Used for idempotency: skip re-processing if input hash + version unchanged.
        """
        try:
            serialized = json.dumps(
                input_data.model_dump() if hasattr(input_data, "model_dump") else str(input_data),
                sort_keys=True,
                default=str,
            )
            return hashlib.sha256(serialized.encode()).hexdigest()
        except Exception:
            return "hash_unavailable"

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _count_inputs(self, input_data: InputType) -> int:
        """Try to determine a meaningful input count for trace logging."""
        for attr in ("evidence_records", "classified_evidence", "source_directories"):
            value = getattr(input_data, attr, None)
            if isinstance(value, list):
                return len(value)
        return 1

    @property
    def agent_run_id(self) -> str | None:
        return self._agent_run_id
