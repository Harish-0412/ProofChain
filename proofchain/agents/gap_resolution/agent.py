"""Goal-driven compound Adaptive Gap Resolution Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agents.gap_resolution.gap_detector import GapDetectionSpecialist
from proofchain.agents.gap_resolution.gap_prioritizer import (
    GapPrioritizationSpecialist,
)
from proofchain.agents.gap_resolution.readiness_simulator import (
    ReadinessSimulationSpecialist,
)
from proofchain.agents.gap_resolution.resolution_planner import (
    ResolutionPlanningSpecialist,
)
from proofchain.agents.gap_resolution.root_cause_analyzer import (
    RootCauseAnalysisSpecialist,
)
from proofchain.core.exceptions import SchemaValidationError
from proofchain.repositories.json_decision_repository import JsonDecisionRepository
from proofchain.schemas.agentic import (
    AgentPlan,
    CompletionDecision,
    CoordinationMessage,
    PlanStep,
)
from proofchain.schemas.gaps import (
    GapAgentResult,
    GapResolutionInput,
    ResolutionPortfolio,
)


class AdaptiveGapResolutionAgent(BaseGoalAgent[GapResolutionInput, GapAgentResult]):
    agent_name = "adaptive_gap_resolution"
    agent_version = "1.0.0"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or JsonDecisionRepository()
        self.detector = GapDetectionSpecialist()
        self.root_cause = RootCauseAnalysisSpecialist()
        self.planner = ResolutionPlanningSpecialist()
        self.simulator = ReadinessSimulationSpecialist()
        self.prioritizer = GapPrioritizationSpecialist()
        self._state: dict = {}

    def validate_input(self, input_data: GapResolutionInput) -> None:
        if not input_data.integrity_findings and not input_data.integrity_gaps:
            if all(item.status == "supported" for item in input_data.claim_decisions):
                return
        if not input_data.claim_decisions:
            raise SchemaValidationError("Gap resolution requires claim decisions.")

    def execute(self, input_data):
        self._state = {}
        self._detect(input_data)
        self._analyze()
        self._plan()
        self._simulate(input_data)
        return self._prioritize(input_data)

    def validate_output(self, output_data):
        if len(output_data.portfolio.gaps) != len(output_data.portfolio.plans):
            raise SchemaValidationError("Every normalized gap requires one resolution plan.")
        if any(not plan.required_completion_evidence for plan in output_data.portfolio.plans):
            raise SchemaValidationError("Resolution plans require explicit closure evidence.")

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        specs = [
            ("detect_gaps", "Normalize findings and unsupported claim components."),
            ("analyze_root_causes", "Generate evidence-backed root-cause hypotheses."),
            ("generate_resolution_options", "Create alternative governed strategies."),
            ("simulate_readiness", "Estimate readiness deltas without closing gaps."),
            ("prioritize_gaps", "Build the ordered resolution portfolio."),
        ]
        return AgentPlan(
            plan_id=f"PLAN-GAP-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale="Turn every disclosed failure into a unique, actionable, measurable plan.",
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=f"{tool} returns typed gap-planning state.",
                    completion_condition="The specialist output covers every open gap.",
                )
                for index, (tool, objective) in enumerate(specs, 1)
            ],
            dependencies=goal.dependencies,
            expected_outputs=["gap_resolution_portfolio.json"],
            status="approved",
        )

    def agentic_tools(self, input_data):
        return {
            "detect_gaps": lambda: self._detect(input_data),
            "analyze_root_causes": self._analyze,
            "generate_resolution_options": self._plan,
            "simulate_readiness": lambda: self._simulate(input_data),
            "prioritize_gaps": lambda: self._prioritize(input_data),
        }

    def _detect(self, input_data):
        value = self.detector.run(input_data)
        self._state["gaps"] = value
        return value

    def _analyze(self):
        value = self.root_cause.run(self._state["gaps"])
        self._state["gaps"] = value
        return value

    def _plan(self):
        value = self.planner.run(self._state["gaps"])
        self._state["plans"] = value
        return value

    def _simulate(self, input_data):
        scores = [item.integrity_score for item in input_data.integrity_summaries]
        current = round(sum(scores) / len(scores), 2) if scores else 100.0
        gaps, plans, simulation = self.simulator.run(
            self._state["gaps"], self._state["plans"], current
        )
        self._state.update(gaps=gaps, plans=plans, simulation=simulation)
        return simulation

    def _prioritize(self, input_data):
        started = datetime.now(tz=timezone.utc)
        priorities = self.prioritizer.run(
            self._state["gaps"], self._state["plans"]
        )
        blocking = sum(gap.blocking for gap in self._state["gaps"])
        debt = min(
            100.0,
            round(
                sum(
                    priority.priority_score * (1.15 if gap.blocking else 0.65)
                    for priority in priorities
                    for gap in self._state["gaps"]
                    if gap.gap_id == priority.gap_id
                )
                / max(1, len(priorities)),
                2,
            ),
        )
        dependency_graph = {
            plan.gap_id: plan.dependencies for plan in self._state["plans"]
        }
        minimal = [
            item.gap_id
            for item in priorities
            if next(
                gap for gap in self._state["gaps"] if gap.gap_id == item.gap_id
            ).blocking
        ]
        portfolio = ResolutionPortfolio(
            portfolio_id=f"PORT-{input_data.workflow.run_id}",
            run_id=input_data.workflow.run_id,
            current_readiness=self._state["simulation"].current_readiness,
            current_verified_readiness=self._state["simulation"].current_readiness,
            projected_readiness=self._state["simulation"].projected_readiness,
            projection_type=self._state["simulation"].projection_type,
            projection_confidence=self._state["simulation"].projection_confidence,
            projection_assumptions=self._state["simulation"].assumptions,
            projection_unresolved_dependencies=self._state[
                "simulation"
            ].unresolved_dependencies,
            scenario_bands=self._state["simulation"].scenario_bands,
            not_an_approval=True,
            evidence_debt_score=debt,
            gaps=self._state["gaps"],
            plans=self._state["plans"],
            priorities=priorities,
            minimal_resolution_set=minimal,
            dependency_graph=dependency_graph,
        )
        result = GapAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if blocking else "completed",
            input_count=len(input_data.integrity_findings)
            + len(input_data.integrity_gaps),
            success_count=len(portfolio.gaps),
            warning_count=blocking,
            failure_count=0,
            portfolio=portfolio,
            input_snapshot_hash=self.compute_input_hash(input_data),
            warnings=[
                f"{blocking} blocking gaps require approved resolution."
            ]
            if blocking
            else [],
            started_at=started,
        )
        artifact = self.repository.save_gaps(
            result.run_id, result, result.agent_run_id
        )
        result.output_reference = artifact.path
        result.output_snapshot_hash = artifact.sha256
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        valid = bool(output) and all(
            plan.strategies and plan.required_completion_evidence
            for plan in output.portfolio.plans
        )
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=valid,
            success_conditions_met=goal.success_conditions if valid else [],
            success_conditions_unmet=[] if valid else goal.success_conditions,
            confidence=1.0 if valid else 0.0,
            final_status=(
                "completed_with_warnings"
                if valid and output.portfolio.minimal_resolution_set
                else "completed"
                if valid
                else "failed"
            ),
            explanation=(
                f"Planned {len(output.portfolio.gaps) if output else 0} unique gaps "
                "with priorities, dependencies, closure evidence, and readiness impact."
            ),
            supporting_artifacts=[output.output_reference]
            if output and output.output_reference
            else [],
        )

    def create_peer_requests(self, goal, output):
        if output is None or not output.portfolio.gaps:
            return []
        requests = [
            CoordinationMessage(
                message_id=f"MSG-{uuid4().hex[:12].upper()}",
                run_id=goal.run_id,
                goal_id=goal.goal_id,
                source_agent=self.agent_name,
                target_agent="accountability_ownership",
                message_type="information_request",
                reason="Resolution tasks require authorized primary, backup, and approval owners.",
                payload={"portfolio_id": output.portfolio.portfolio_id},
                priority="critical",
            )
        ]
        for plan in output.portfolio.plans:
            strategy = next(
                item
                for item in plan.strategies
                if item.strategy_id == plan.recommended_strategy_id
            )
            if strategy.requires_new_evidence:
                requests.append(
                    CoordinationMessage(
                        message_id=f"MSG-{uuid4().hex[:12].upper()}",
                        run_id=goal.run_id,
                        goal_id=goal.goal_id,
                        source_agent=self.agent_name,
                        target_agent="evidence_collector",
                        message_type="additional_evidence_request",
                        reason=strategy.title,
                        payload={"gap_id": plan.gap_id},
                        priority="high",
                    )
                )
            elif strategy.requires_claim_revision:
                requests.append(
                    CoordinationMessage(
                        message_id=f"MSG-{uuid4().hex[:12].upper()}",
                        run_id=goal.run_id,
                        goal_id=goal.goal_id,
                        source_agent=self.agent_name,
                        target_agent="claim_intelligence",
                        message_type="verification_request",
                        reason=strategy.title,
                        payload={"gap_id": plan.gap_id},
                        priority="high",
                    )
                )
        return requests
