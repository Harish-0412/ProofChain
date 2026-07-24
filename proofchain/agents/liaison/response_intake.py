"""Task response intake specialist module."""

from __future__ import annotations

from proofchain.schemas.tasks import ResolutionTask, TaskResponse


class ResponseIntakeSpecialist:
    specialist_name = "response_intake"

    def run(self, tasks: list[ResolutionTask]) -> list[TaskResponse]:
        return [
            TaskResponse(
                response_id=f"RESP-{task.task_id}",
                task_id=task.task_id,
                responder_id=task.primary_owner_id,
                response_type="waiting_for_response",
                requires_agent_action=False,
            )
            for task in tasks
            if task.status == "active"
        ]
