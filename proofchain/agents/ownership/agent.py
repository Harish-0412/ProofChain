"""Goal-driven compound Accountability and Evidence Ownership Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agents.ownership.assignment_validator import (
    AssignmentValidationSpecialist,
)
from proofchain.agents.ownership.escalation_planner import (
    EscalationPlanningSpecialist,
)
from proofchain.agents.ownership.provenance_resolver import (
    EvidenceProvenanceSpecialist,
)
from proofchain.agents.ownership.responsibility_matcher import (
    ResponsibilityMatchingSpecialist,
)
from proofchain.agents.ownership.workload_balancer import (
    WorkloadBalancingSpecialist,
)
from proofchain.core.exceptions import SchemaValidationError
from proofchain.repositories.json_decision_repository import JsonDecisionRepository
from proofchain.schemas.agentic import (
    AgentPlan,
    CompletionDecision,
    CoordinationMessage,
    PlanStep,
)
from proofchain.schemas.ownership import OwnershipAgentResult, OwnershipInput


class AccountabilityOwnershipAgent(
    BaseGoalAgent[OwnershipInput, OwnershipAgentResult]
):
    agent_name = "accountability_ownership"
    agent_version = "1.0.0"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or JsonDecisionRepository()
        self.provenance = EvidenceProvenanceSpecialist()
        self.matcher = ResponsibilityMatchingSpecialist()
        self.balancer = WorkloadBalancingSpecialist()
        self.escalation = EscalationPlanningSpecialist()
        self.validator = AssignmentValidationSpecialist()
        self._state: dict = {}

    def validate_input(self, input_data: OwnershipInput) -> None:
        if input_data.portfolio.gaps and not input_data.portfolio.plans:
            raise SchemaValidationError("Ownership requires planned resolution gaps.")

    def execute(self, input_data):
        self._state = {}
        self._trace(input_data)
        self._match(input_data)
        self._balance()
        self._escalate(input_data)
        return self._validate(input_data)

    def validate_output(self, output_data):
        if output_data.input_count != len(output_data.assignments):
            raise SchemaValidationError("Every gap requires an assignment decision.")
        for assignment in output_data.assignments:
            if not assignment.escalation_plan:
                raise SchemaValidationError("Every assignment needs an escalation plan.")

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        specs = [
            ("trace_evidence_provenance", "Resolve department and provenance candidates."),
            ("match_responsibility", "Map gaps to eligible roles and permissions."),
            ("balance_workload", "Select primary, backup, and approver candidates."),
            ("build_escalation_plan", "Recommend a controlled escalation path."),
            ("validate_assignments", "Check authorization, independence, privacy, and workload."),
        ]
        return AgentPlan(
            plan_id=f"PLAN-OWNER-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale="Resolve accountable roles through provenance, authority, workload, and conflict checks.",
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=f"{tool} returns a bounded assignment artifact.",
                    completion_condition="The specialist records a traceable ownership decision.",
                )
                for index, (tool, objective) in enumerate(specs, 1)
            ],
            dependencies=goal.dependencies,
            expected_outputs=["ownership_assignments.json"],
            status="approved",
        )

    def agentic_tools(self, input_data):
        return {
            "trace_evidence_provenance": lambda: self._trace(input_data),
            "match_responsibility": lambda: self._match(input_data),
            "balance_workload": self._balance,
            "build_escalation_plan": lambda: self._escalate(input_data),
            "validate_assignments": lambda: self._validate(input_data),
        }

    def _trace(self, input_data):
        members = self.provenance.load_members(
            input_data.workflow.department_scope,
            input_data.organisation_members,
        )
        value = self.provenance.run(
            input_data.portfolio,
            members,
            input_data.workflow.department_scope[0],
        )
        self._state.update(members=members, provenance=value)
        return value

    def _match(self, input_data):
        value = self.matcher.run(input_data.portfolio)
        self._state["responsibility"] = value
        return value

    def _balance(self):
        value = self.balancer.run(
            self._state["provenance"],
            self._state["responsibility"],
            self._state["members"],
        )
        self._state["balanced"] = value
        return value

    def _escalate(self, input_data):
        value = self.escalation.run(input_data.portfolio)
        self._state["escalation"] = value
        return value

    def _validate(self, input_data):
        started = datetime.now(tz=timezone.utc)
        assignments = self.validator.run(
            input_data.portfolio,
            self._state["provenance"],
            self._state["responsibility"],
            self._state["balanced"],
            self._state["escalation"],
        )
        unresolved = [
            item.gap_id for item in assignments if item.status == "unresolved"
        ]
        result = OwnershipAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if unresolved else "completed",
            input_count=len(input_data.portfolio.gaps),
            success_count=len(assignments) - len(unresolved),
            warning_count=len(unresolved),
            failure_count=0,
            assignments=assignments,
            unresolved_ownership=unresolved,
            input_snapshot_hash=self.compute_input_hash(input_data),
            warnings=[
                f"Ownership is formally unresolved for {gap_id}."
                for gap_id in unresolved
            ],
            started_at=started,
        )
        artifact = self.repository.save_ownership(
            result.run_id, result, result.agent_run_id
        )
        result.output_reference = artifact.path
        result.output_snapshot_hash = artifact.sha256
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        complete = bool(output) and output.input_count == len(output.assignments)
        unresolved = output.unresolved_ownership if output else []
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=complete,
            success_conditions_met=goal.success_conditions if complete else [],
            success_conditions_unmet=[] if complete else goal.success_conditions,
            unresolved_questions=unresolved,
            confidence=min(
                (item.assignment_confidence for item in output.assignments),
                default=0.0,
            )
            if output
            else 0.0,
            final_status=(
                "completed_with_warnings"
                if complete and unresolved
                else "completed"
                if complete
                else "failed"
            ),
            explanation=(
                f"Produced {len(output.assignments) if output else 0} assignment "
                f"recommendations; {len(unresolved)} remain formally unresolved. "
                "No task was assigned or messaged without human approval."
            ),
            supporting_artifacts=[output.output_reference]
            if output and output.output_reference
            else [],
        )

    def create_peer_requests(self, goal, output):
        if output is None or not output.unresolved_ownership:
            return []
        return [
            CoordinationMessage(
                message_id=f"MSG-{uuid4().hex[:12].upper()}",
                run_id=goal.run_id,
                goal_id=goal.goal_id,
                source_agent=self.agent_name,
                target_agent="supervisor",
                message_type="information_request",
                reason="No authorized owner could be established; human assignment is required.",
                payload={"gap_ids": output.unresolved_ownership},
                priority="critical",
            )
        ]
