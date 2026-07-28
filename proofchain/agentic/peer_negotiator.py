"""Convert legacy coordination messages into acceptance-tested peer contracts."""

from __future__ import annotations

from proofchain.schemas.agentic import CoordinationMessage
from proofchain.schemas.peer_contracts import AgentRequest


class PeerNegotiator:
    def normalize(self, message: CoordinationMessage) -> AgentRequest:
        conditions = list(message.payload.get("acceptance_conditions", []))
        if not conditions:
            conditions = [
                "A governed resolution status and explanation are recorded."
            ]
            if message.related_evidence_ids:
                conditions.append("Every related evidence ID is assessed.")
        return AgentRequest(
            request_id=message.message_id,
            run_id=message.run_id,
            source_agent=message.source_agent,
            target_agent=message.target_agent,
            goal_id=message.goal_id,
            requested_outcome=message.message_type,
            reason=message.reason,
            required_inputs=list(message.payload.get("required_inputs", [])),
            related_entities=list(message.related_evidence_ids),
            acceptance_conditions=conditions,
            priority=message.priority,
            blocking=message.message_type
            in {
                "additional_evidence_request",
                "verification_request",
                "conflict_notification",
            },
            status={
                "open": "OPEN",
                "accepted": "ACCEPTED",
                "in_progress": "IN_PROGRESS",
                "resolved": "RESOLVED",
                "rejected": "DECLINED",
                "expired": "EXPIRED",
            }[message.status],
        )


class AgentRequestLifecycle:
    """Enforce legal request transitions and acceptance-tested resolution."""

    _ALLOWED = {
        "OPEN": {"ACKNOWLEDGED", "DECLINED", "NEEDS_CLARIFICATION", "CANCELLED"},
        "ACKNOWLEDGED": {"ACCEPTED", "DECLINED", "NEEDS_CLARIFICATION", "EXPIRED"},
        "ACCEPTED": {"IN_PROGRESS", "CANCELLED", "EXPIRED"},
        "NEEDS_CLARIFICATION": {"OPEN", "CANCELLED", "EXPIRED"},
        "IN_PROGRESS": {"RESOLVED", "NEEDS_CLARIFICATION", "EXPIRED"},
        "DECLINED": set(),
        "RESOLVED": set(),
        "EXPIRED": set(),
        "CANCELLED": set(),
    }

    def transition(
        self,
        request: AgentRequest,
        status: str,
        *,
        satisfied_conditions: list[str] | None = None,
    ) -> AgentRequest:
        if status not in self._ALLOWED[request.status]:
            raise ValueError(
                f"Illegal peer request transition: {request.status} -> {status}."
            )
        updated = request.model_copy(
            update={
                "status": status,
                "satisfied_acceptance_conditions": list(
                    dict.fromkeys(
                        [
                            *request.satisfied_acceptance_conditions,
                            *(satisfied_conditions or []),
                        ]
                    )
                ),
            }
        )
        if status == "RESOLVED" and not updated.acceptance_satisfied():
            raise ValueError(
                "A peer request cannot resolve until every acceptance condition passes."
            )
        return updated
