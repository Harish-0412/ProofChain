"""Build immutable context snapshots for advanced planning."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from proofchain.agentic.experience_memory import ExperienceMemory
from proofchain.core.paths import POLICIES_DIR
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.schemas.agent_context import AgentContext
from proofchain.schemas.agentic import Goal
from proofchain.schemas.interpreted_goal import InterpretedGoal


class ContextBuilder:
    def build(
        self,
        goal: Goal,
        interpreted: InterpretedGoal,
        coordination: JsonCoordinationRepository,
        input_data: Any | None = None,
    ) -> AgentContext:
        policies = sorted(str(path.resolve()) for path in POLICIES_DIR.glob("*.yaml"))
        fingerprint = hashlib.sha256(
            "|".join(
                f"{path}:{Path(path).stat().st_mtime_ns}" for path in policies
            ).encode("utf-8")
        ).hexdigest()
        try:
            messages = coordination.get_open_messages(goal.run_id)
            open_requests = [
                item.message_id
                for item in messages
                if item.target_agent == goal.assigned_agent
                or item.source_agent == goal.assigned_agent
            ]
        except FileNotFoundError:
            open_requests = []
        completeness = 1.0
        unresolved = list(interpreted.ambiguity_flags)
        if unresolved:
            completeness = max(0.0, 1.0 - 0.15 * len(unresolved))
        tenant_id = getattr(input_data, "tenant_id", None)
        if tenant_id is None:
            tenant_id = getattr(input_data, "requested_tenant_id", None)
        validated_cases = ExperienceMemory().eligible(
            case_type=goal.goal_type,
            tenant_id=tenant_id,
            policy_fingerprint=fingerprint,
        )
        return AgentContext(
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=goal.assigned_agent,
            goal=interpreted,
            relevant_entities=interpreted.subject_entities,
            artifacts=goal.input_references,
            applicable_policies=policies,
            applicable_rules=["AGENT-BUDGET-001", "COMPLETION-POLICY-001"],
            open_peer_requests=open_requests,
            blockers=[],
            validated_case_ids=[case.case_id for case in validated_cases],
            context_completeness=completeness,
            unresolved_questions=unresolved,
            policy_fingerprint=fingerprint,
        )
