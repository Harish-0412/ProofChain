"""Goal-driven Evidence Closure and Continuous Revalidation Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agents.closure.closure_verifier import ClosureVerifierSpecialist
from proofchain.agents.closure.evidence_difference import EvidenceDifferenceSpecialist
from proofchain.agents.closure.issue_state_decider import IssueStateDecisionSpecialist
from proofchain.agents.closure.regression_detector import RegressionDetectorSpecialist
from proofchain.agents.closure.submission_intake import SubmissionIntakeSpecialist
from proofchain.agents.closure.targeted_revalidation import TargetedRevalidationSpecialist
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_lifecycle_repository import JsonLifecycleRepository
from proofchain.schemas.agentic import AgentPlan, CompletionDecision, PlanStep
from proofchain.schemas.closure import ClosureAgentResult, ClosureInput


class ClosureRevalidationAgent(BaseGoalAgent[ClosureInput, ClosureAgentResult]):
    agent_name = "closure_revalidation"
    agent_version = "1.0.0"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or JsonLifecycleRepository()
        self.events = JsonEventRepository()
        self.intake = SubmissionIntakeSpecialist()
        self.diff = EvidenceDifferenceSpecialist()
        self.revalidation = TargetedRevalidationSpecialist()
        self.verifier = ClosureVerifierSpecialist()
        self.regression = RegressionDetectorSpecialist()
        self.decider = IssueStateDecisionSpecialist()
        self._state: dict = {}

    def validate_input(self, input_data):
        return None

    def execute(self, input_data):
        self._state = {}
        self._intake(input_data)
        self._diff(input_data)
        self._revalidate(input_data)
        self._verify(input_data)
        self._detect_regressions()
        return self._decide(input_data)

    def validate_output(self, output_data):
        return None

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        specs = [
            ("intake_submissions", "Check whether closure evidence was submitted."),
            ("compare_evidence_versions", "Detect registered and classifiable evidence state."),
            ("run_targeted_revalidation", "Evaluate affected integrity blockers."),
            ("verify_closure_conditions", "Apply closure policy to each issue."),
            ("detect_regressions", "Detect new or remaining contradictions."),
            ("decide_issue_states", "Produce formal issue lifecycle transitions."),
        ]
        return AgentPlan(
            plan_id=f"PLAN-CLOSURE-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale="A gap closes only after submitted evidence passes targeted revalidation.",
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=f"{tool} returns closure lifecycle state.",
                    completion_condition="Closure state remains evidence backed.",
                )
                for index, (tool, objective) in enumerate(specs, 1)
            ],
            dependencies=goal.dependencies,
            expected_outputs=["closure_revalidation_report.json"],
            status="approved",
        )

    def agentic_tools(self, input_data):
        return {
            "intake_submissions": lambda: self._intake(input_data),
            "compare_evidence_versions": lambda: self._diff(input_data),
            "run_targeted_revalidation": lambda: self._revalidate(input_data),
            "verify_closure_conditions": lambda: self._verify(input_data),
            "detect_regressions": self._detect_regressions,
            "decide_issue_states": lambda: self._decide(input_data),
        }

    def _intake(self, input_data):
        value = self.intake.run(input_data.tasks)
        self._state["submitted"] = value
        return value

    def _diff(self, input_data):
        value = self.diff.run(input_data.classified_evidence)
        self._state["registered"] = bool(value)
        return value

    def _revalidate(self, input_data):
        value = self.revalidation.run(input_data.canonical_issues, input_data.integrity_findings)
        self._state["integrity"] = value
        return value

    def _verify(self, input_data):
        task_by_issue = {task.issue_id: task for task in input_data.tasks}
        checks = []
        for issue in input_data.canonical_issues:
            task = task_by_issue.get(issue.issue_id)
            submitted = self._state["submitted"].get(task.task_id, False) if task else False
            checks.append(
                self.verifier.run(
                    issue=issue,
                    task=task,
                    submitted=submitted,
                    registered=self._state["registered"],
                    integrity_passed=self._state["integrity"].get(issue.issue_id, False),
                    claim_decisions=input_data.claim_decisions,
                )
            )
        self._state["checks"] = checks
        return checks

    def _detect_regressions(self):
        value = self.regression.run(self._state["checks"])
        self._state["regressions"] = value
        return value

    def _decide(self, input_data):
        started = datetime.now(tz=timezone.utc)
        updated, transitions = self.decider.run(
            input_data.canonical_issues, self._state["checks"]
        )
        resolved = sum(issue.status == "RESOLVED" for issue in updated)
        blocking_open = sum(issue.blocking and issue.status != "RESOLVED" for issue in updated)
        readiness = input_data.portfolio.current_verified_readiness if input_data.portfolio else 100.0
        result = ClosureAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if blocking_open else "completed",
            input_count=len(input_data.canonical_issues),
            success_count=resolved,
            warning_count=blocking_open,
            failure_count=0,
            closure_checks=self._state["checks"],
            issue_transitions=transitions,
            updated_issues=updated,
            current_verified_readiness=readiness or 0.0,
            input_snapshot_hash=self.compute_input_hash(input_data),
            warnings=[
                f"{blocking_open} blocking issues remain unresolved after targeted revalidation."
            ] if blocking_open else [],
            started_at=started,
        )
        artifact = self.repository.save_closure(result)
        for transition in transitions:
            self.events.append(
                run_id=result.run_id,
                event_type="GapResolved" if transition.to_status == "RESOLVED" else "ClosureRejected",
                aggregate_type="issue",
                aggregate_id=transition.issue_id,
                actor=self.agent_name,
                payload=transition.model_dump(),
            )
        result.output_reference = artifact.path
        result.output_snapshot_hash = artifact.sha256
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        complete = output is not None
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=complete,
            success_conditions_met=goal.success_conditions if complete else [],
            success_conditions_unmet=[] if complete else goal.success_conditions,
            blockers=output.warnings if output and output.warning_count else [],
            confidence=0.88 if complete else 0.0,
            final_status="completed_with_warnings" if output and output.warning_count else "completed" if complete else "failed",
            explanation=(
                f"Evaluated closure for {len(output.closure_checks) if output else 0} issues; "
                "evidence submission alone did not close any issue."
            ),
            supporting_artifacts=[output.output_reference] if output and output.output_reference else [],
        )
