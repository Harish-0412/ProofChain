"""Submission intake specialist module."""

from __future__ import annotations

from proofchain.schemas.tasks import ResolutionTask


class SubmissionIntakeSpecialist:
    specialist_name = "submission_intake"

    def run(self, tasks: list[ResolutionTask]) -> dict[str, bool]:
        return {
            task.task_id: task.status == "evidence_submitted"
            for task in tasks
        }
