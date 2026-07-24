"""Goal-driven governed department liaison and task execution agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agents.liaison.approval_gate import ApprovalGateSpecialist
from proofchain.agents.liaison.communication_scope import CommunicationScopeSpecialist
from proofchain.agents.liaison.dispatcher import DispatchDeliverySpecialist
from proofchain.agents.liaison.message_drafter import MessageDraftingSpecialist
from proofchain.agents.liaison.response_intake import ResponseIntakeSpecialist
from proofchain.agents.liaison.sla_escalation import SlaEscalationSpecialist
from proofchain.agents.liaison.task_composer import TaskCompositionSpecialist
from proofchain.core.exceptions import SchemaValidationError
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_lifecycle_repository import JsonLifecycleRepository
from proofchain.schemas.agentic import AgentPlan, CompletionDecision, PlanStep
from proofchain.schemas.communications import CommunicationRecord
from proofchain.schemas.tasks import LiaisonAgentResult, LiaisonInput, ResolutionTask


class DepartmentLiaisonAgent(BaseGoalAgent[LiaisonInput, LiaisonAgentResult]):
    agent_name = "department_liaison"
    agent_version = "1.0.0"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or JsonLifecycleRepository()
        self.events = JsonEventRepository()
        self.scope = CommunicationScopeSpecialist()
        self.composer = TaskCompositionSpecialist()
        self.drafter = MessageDraftingSpecialist()
        self.gate = ApprovalGateSpecialist()
        self.dispatcher = DispatchDeliverySpecialist()
        self.response_intake = ResponseIntakeSpecialist()
        self.sla = SlaEscalationSpecialist()
        self._state: dict = {}

    def validate_input(self, input_data: LiaisonInput) -> None:
        if input_data.portfolio.gaps and not input_data.ownership.assignments:
            raise SchemaValidationError("Liaison requires ownership recommendations.")

    def execute(self, input_data):
        self._state = {}
        self._prepare_campaign(input_data)
        self._draft_messages()
        self._apply_approval_gate()
        self._dispatch()
        self._intake()
        return self._monitor(input_data)

    def validate_output(self, output_data):
        if output_data.input_count != len(output_data.tasks):
            raise SchemaValidationError("Every canonical issue requires a liaison task decision.")

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        specs = [
            ("prepare_task_campaign", "Compose least-disclosure tasks from approved recommendations."),
            ("draft_task_messages", "Create governed communication records."),
            ("apply_approval_gate", "Block unapproved or unauthorized task activation."),
            ("dispatch_allowed_tasks", "Record controlled in-app delivery only when allowed."),
            ("intake_responses", "Initialize response tracking for active tasks."),
            ("monitor_sla", "Record overdue or escalation conditions."),
        ]
        return AgentPlan(
            plan_id=f"PLAN-LIAISON-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale="Operationalize approved resolution work without changing evidence or claims.",
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=f"{tool} records governed task state.",
                    completion_condition="The task campaign remains auditable and policy bounded.",
                )
                for index, (tool, objective) in enumerate(specs, 1)
            ],
            dependencies=goal.dependencies,
            expected_outputs=["resolution_tasks_detailed.json", "communications.json"],
            status="approved",
        )

    def agentic_tools(self, input_data):
        return {
            "prepare_task_campaign": lambda: self._prepare_campaign(input_data),
            "draft_task_messages": self._draft_messages,
            "apply_approval_gate": self._apply_approval_gate,
            "dispatch_allowed_tasks": self._dispatch,
            "intake_responses": self._intake,
            "monitor_sla": lambda: self._monitor(input_data),
        }

    def _prepare_campaign(self, input_data: LiaisonInput) -> list[ResolutionTask]:
        issue_by_gap = {
            issue.root_entity_id: issue for issue in input_data.canonical_issues
        }
        issue_by_gap.update(
            {
                gap.gap_id: issue
                for issue in input_data.canonical_issues
                for gap in input_data.portfolio.gaps
                if gap.issue_id == issue.issue_id
            }
        )
        assignment_by_gap = {
            assignment.gap_id: assignment for assignment in input_data.ownership.assignments
        }
        plan_by_gap = {plan.gap_id: plan for plan in input_data.portfolio.plans}
        tasks: list[ResolutionTask] = []
        for gap in input_data.portfolio.gaps:
            issue = issue_by_gap.get(gap.gap_id)
            assignment = assignment_by_gap.get(gap.gap_id)
            plan = plan_by_gap.get(gap.gap_id)
            if not issue or not assignment or not plan:
                continue
            disclosure = self.scope.run(issue, assignment)
            task = self.composer.run(
                issue=issue,
                gap=gap,
                plan=plan,
                assignment=assignment,
                disclosure_scope=disclosure,
                approval_event_ids=input_data.approval_event_ids,
            )
            tasks.append(task)
        self._state["tasks"] = tasks
        return tasks

    def _draft_messages(self) -> list[CommunicationRecord]:
        communications = [self.drafter.run(task) for task in self._state["tasks"]]
        self._state["communications"] = communications
        return communications

    def _apply_approval_gate(self) -> list[str]:
        blockers = []
        for task, communication in zip(self._state["tasks"], self._state["communications"]):
            allowed, task_blockers = self.gate.run(task, communication)
            task.status = "active" if allowed else "approval_required"
            blockers.extend([f"{task.task_id}: {item}" for item in task_blockers])
        self._state["blockers"] = blockers
        return blockers

    def _dispatch(self) -> list[CommunicationRecord]:
        tasks = []
        communications = []
        for task, communication in zip(self._state["tasks"], self._state["communications"]):
            allowed = task.status == "active"
            updated_task, updated_communication = self.dispatcher.run(task, communication, allowed)
            tasks.append(updated_task)
            communications.append(updated_communication)
        self._state["tasks"] = tasks
        self._state["communications"] = communications
        return communications

    def _intake(self):
        responses = self.response_intake.run(self._state["tasks"])
        self._state["responses"] = responses
        return responses

    def _monitor(self, input_data: LiaisonInput) -> LiaisonAgentResult:
        started = datetime.now(tz=timezone.utc)
        overdue = self.sla.run(self._state["tasks"])
        tasks = self._state["tasks"]
        warnings = list(self._state.get("blockers", []))
        if overdue:
            warnings.append(f"{len(overdue)} tasks are overdue and need escalation review.")
        result = LiaisonAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if warnings else "completed",
            input_count=len(input_data.canonical_issues),
            success_count=sum(task.status == "active" for task in tasks),
            warning_count=len(warnings),
            failure_count=0,
            tasks=tasks,
            responses=self._state.get("responses", []),
            input_snapshot_hash=self.compute_input_hash(input_data),
            warnings=warnings,
            started_at=started,
        )
        artifact = self.repository.save_liaison(
            result.run_id, result, self._state["communications"]
        )
        for task in tasks:
            self.events.append(
                run_id=result.run_id,
                event_type="TaskActivated" if task.status == "active" else "ApprovalRequested",
                aggregate_type="task",
                aggregate_id=task.task_id,
                actor=self.agent_name,
                payload={
                    "issue_id": task.issue_id,
                    "gap_id": task.gap_id,
                    "status": task.status,
                    "original_artifacts_unchanged": True,
                },
            )
        result.output_reference = artifact.path
        result.output_snapshot_hash = artifact.sha256
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        complete = bool(output) and output.input_count == len(output.tasks)
        blockers = output.warnings if output else ["No liaison result was produced."]
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=complete,
            success_conditions_met=goal.success_conditions if complete else [],
            success_conditions_unmet=[] if complete else goal.success_conditions,
            blockers=[] if complete else blockers,
            unresolved_questions=blockers if output and output.warning_count else [],
            confidence=0.85 if complete else 0.0,
            final_status="completed_with_warnings" if output and output.warning_count else "completed" if complete else "failed",
            explanation=(
                f"Prepared {len(output.tasks) if output else 0} governed resolution tasks; "
                "unapproved tasks remain paused and original artifacts were not modified."
            ),
            supporting_artifacts=[output.output_reference] if output and output.output_reference else [],
        )
