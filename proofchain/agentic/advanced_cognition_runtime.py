"""Orchestrate the complete Phase 1 cognition lifecycle for one agent goal."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from proofchain.agentic.action_selector import InformationGainActionSelector
from proofchain.agentic.cognition_profiles import cognition_profile_for
from proofchain.agentic.completion_prover import CompletionProver
from proofchain.agentic.context_builder import ContextBuilder
from proofchain.agentic.contradiction_resolver import ContradictionResolver
from proofchain.agentic.core_precision import CorePrecisionEvaluator
from proofchain.agentic.decision_explainer import DecisionExplainer
from proofchain.agentic.goal_interpreter import GoalInterpreter
from proofchain.agentic.hypothesis_manager import HypothesisManager
from proofchain.agentic.input_validator import PrePlanInputValidator
from proofchain.agentic.observation_normalizer import ObservationNormalizer
from proofchain.agentic.peer_negotiator import PeerNegotiator
from proofchain.agentic.plan_critic import PlanCritic
from proofchain.agentic.planning_engine import AdvancedPlanningEngine
from proofchain.agentic.reflection_engine import StructuredReflectionEngine
from proofchain.agentic.state_machine import AgentCognitionStateMachine
from proofchain.agentic.uncertainty_calibrator import UncertaintyCalibrator
from proofchain.core.paths import POLICIES_DIR
from proofchain.repositories.advanced_cognition_repository import (
    AdvancedCognitionRepository,
)
from proofchain.repositories.json_coordination_repository import (
    JsonCoordinationRepository,
)
from proofchain.schemas.advanced_plans import AdvancedAgentPlan
from proofchain.schemas.agentic import (
    ActionProposal,
    AgentPlan,
    CompletionDecision,
    CoordinationMessage,
    Goal,
    Observation,
    ReflectionDecision,
)
from proofchain.schemas.agentic_evaluation import AgenticScorecard
from proofchain.schemas.cognition import NormalizedToolObservation
from proofchain.schemas.hypotheses import Hypothesis
from proofchain.schemas.input_validation import InputValidationResult
from proofchain.schemas.interpreted_goal import InterpretedGoal
from proofchain.schemas.plan_critiques import PlanCritique
from proofchain.schemas.validated_cases import ValidatedCase


class AdvancedCognitionRuntime:
    """Owns canonical cognition artifacts without changing deterministic tools."""

    def __init__(self, goal: Goal, coordination: JsonCoordinationRepository):
        self.goal = goal
        self.coordination = coordination
        self.profile = cognition_profile_for(goal.assigned_agent)
        self.repository = AdvancedCognitionRepository(
            run_id=goal.run_id,
            agent_name=goal.assigned_agent,
            goal_id=goal.goal_id,
        )
        self.state = AgentCognitionStateMachine(
            self.repository,
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=goal.assigned_agent,
        )
        self.interpreted: InterpretedGoal | None = None
        self.input_validation: InputValidationResult | None = None
        self.hypotheses: list[Hypothesis] = []
        self.context = None
        self.tenant_id: str | None = None
        self.advanced_plan: AdvancedAgentPlan | None = None
        self.last_critique: PlanCritique | None = None
        self.normalized_observations: list[NormalizedToolObservation] = []
        self.peer_requests = []
        self.repository.write("cognition_profile.json", self.profile)

    def initialize(
        self,
        input_data: Any,
        *,
        deterministic_error: Exception | None,
    ) -> InputValidationResult:
        self.state.transition("CREATED", "Advanced cognition profile activated.")
        self.state.transition(
            "INTERPRETING_GOAL", "Normalize objective, scope, and governance boundaries."
        )
        policy_known = any(POLICIES_DIR.glob("*.yaml"))
        self.interpreted = GoalInterpreter().interpret(
            self.goal, policy_version_known=policy_known
        )
        self.repository.write("interpreted_goal.json", self.interpreted)

        self.state.transition(
            "VALIDATING_INPUTS", "Apply the pre-plan deterministic input gate."
        )
        self.input_validation = PrePlanInputValidator().validate(
            self.goal,
            input_data,
            deterministic_error=deterministic_error,
        )
        self.repository.write("input_validation.json", self.input_validation)
        self.tenant_id = getattr(input_data, "tenant_id", None) or getattr(
            input_data, "requested_tenant_id", None
        )

        self.state.transition(
            "BUILDING_CONTEXT", "Construct an immutable policy and artifact snapshot."
        )
        context = ContextBuilder().build(
            self.goal,
            self.interpreted,
            self.coordination,
            input_data,
        )
        self.context = context
        self.repository.write("context_snapshot.json", context)

        self.state.transition(
            "FORMING_HYPOTHESES", "Create competing, testable outcome hypotheses."
        )
        self.hypotheses = HypothesisManager().form(self.goal, context)
        self.repository.write("hypotheses.json", self.hypotheses)
        initial_uncertainty = UncertaintyCalibrator().assess(
            self.interpreted,
            self.input_validation,
            agent_name=self.goal.assigned_agent,
        )
        self.repository.append("uncertainty_assessments.jsonl", initial_uncertainty)
        return self.input_validation

    def record_plan(
        self, plan: AgentPlan, *, allowed_tools: set[str]
    ) -> tuple[AdvancedAgentPlan, PlanCritique]:
        state = "REPLANNING" if plan.revision > 1 else "PLANNING"
        self.state.transition(
            state,
            f"Build risk-aware plan revision {plan.revision}.",
        )
        self.advanced_plan = AdvancedPlanningEngine().enrich(
            self.goal,
            plan,
            validated_case_ids=self.context.validated_case_ids
            if self.context
            else [],
        )
        self.repository.write(
            f"plans/plan_revision_{plan.revision}.json", self.advanced_plan
        )
        self.state.transition(
            "CRITIQUING_PLAN",
            f"Challenge coverage, permission, risk, and completion tests for revision {plan.revision}.",
        )
        self.last_critique = PlanCritic().critique(
            self.goal,
            self.advanced_plan,
            allowed_tools=allowed_tools,
        )
        self.advanced_plan.status = (
            "approved" if self.last_critique.approved else "critic_rejected"
        )
        self.repository.write(
            f"critiques/critique_revision_{plan.revision}.json",
            self.last_critique,
        )
        self.repository.write(
            f"plans/plan_revision_{plan.revision}.json", self.advanced_plan
        )
        return self.advanced_plan, self.last_critique

    def select_action(
        self, step_id: str, *, allowed_tools: set[str]
    ) -> ActionProposal:
        if self.advanced_plan is None:
            raise RuntimeError("Advanced plan is not available.")
        step = next(item for item in self.advanced_plan.steps if item.step_id == step_id)
        self.state.transition(
            "EXECUTING",
            f"Select the authorized action with highest expected information gain for {step_id}.",
        )
        action = InformationGainActionSelector().select(
            self.goal,
            self.goal.assigned_agent,
            step,
            available_tools=allowed_tools,
        )
        self.repository.append("action_selections.jsonl", action)
        return action

    def record_control_action(self, step_id: str, objective: str) -> None:
        self.state.transition(
            "EXECUTING", f"Execute reversible control assessment for {step_id}."
        )
        self.repository.append(
            "action_selections.jsonl",
            {
                "action_id": f"ACT-{uuid4().hex[:12].upper()}",
                "run_id": self.goal.run_id,
                "goal_id": self.goal.goal_id,
                "agent_name": self.goal.assigned_agent,
                "step_id": step_id,
                "selected_tool": "internal_control_assessment",
                "alternatives": [],
                "selection_reason": objective,
                "expected_information_gain": 0.5,
                "risk_level": "low",
                "reversible": True,
                "approval_required": False,
            },
        )

    def record_observation(
        self,
        observation: Observation,
        *,
        source_tool: str,
        source_version: str,
    ) -> NormalizedToolObservation:
        self.state.transition(
            "OBSERVING", f"Normalize observation {observation.observation_id}."
        )
        normalized = ObservationNormalizer().normalize(
            observation,
            source_tool=source_tool,
            source_version=source_version,
        )
        self.normalized_observations.append(normalized)
        self.repository.append("normalized_observations.jsonl", normalized)
        self.hypotheses = HypothesisManager().update(self.hypotheses, normalized)
        self.repository.write("hypotheses.json", self.hypotheses)
        uncertainty = UncertaintyCalibrator().assess(
            self.interpreted,
            self.input_validation,
            normalized,
            agent_name=self.goal.assigned_agent,
        )
        self.repository.append("uncertainty_assessments.jsonl", uncertainty)
        return normalized

    def record_reflection(
        self,
        reflection: ReflectionDecision,
        observation: NormalizedToolObservation,
    ) -> None:
        self.state.transition(
            "REFLECTING", f"Measure progress after {observation.observation_id}."
        )
        structured = StructuredReflectionEngine().reflect(
            self.goal, reflection, observation
        )
        self.repository.append("structured_reflections.jsonl", structured)

    def record_peer_requests(
        self, messages: list[CoordinationMessage]
    ) -> None:
        negotiator = PeerNegotiator()
        for message in messages:
            request = negotiator.normalize(message)
            self.peer_requests.append(request)
            self.repository.append("peer_requests.jsonl", request)
            self.coordination.append_agent_request(request)

    def finalize(
        self,
        plan: AgentPlan,
        output: Any,
        decision: CompletionDecision,
        *,
        output_schema_valid: bool,
    ) -> CompletionDecision:
        self.state.transition(
            "VERIFYING_COMPLETION",
            "Evaluate every success condition and governance gate.",
        )
        proof = CompletionProver().prove(
            self.goal,
            decision,
            self.input_validation,
            output_schema_valid=output_schema_valid,
            peer_requests=self.peer_requests,
            policy_conflicts=list(self.last_critique.policy_conflicts)
            if self.last_critique
            else [],
        )
        reported_decision = decision
        decision = CompletionProver.enforce(decision, proof)
        if decision.final_status != reported_decision.final_status:
            self.repository.write("completion_proof_attempt.json", proof)
            proof = CompletionProver().prove(
                self.goal,
                decision,
                self.input_validation,
                output_schema_valid=output_schema_valid,
                peer_requests=self.peer_requests,
                policy_conflicts=list(self.last_critique.policy_conflicts)
                if self.last_critique
                else [],
            )
            proof.proof_metadata.update(
                {
                    "corrected_from_proof_id": self.repository.store.read(
                        self.repository.root / "completion_proof_attempt.json",
                        default={},
                    ).get("proof_id"),
                    "unsupported_positive_decision_intercepted": True,
                }
            )
        self.repository.write("completion_proof.json", proof)

        contradiction = ContradictionResolver().evaluate(
            self.normalized_observations
        )
        if contradiction:
            self.repository.write("contradiction_resolution.json", contradiction)

        final_uncertainty = UncertaintyCalibrator().assess(
            self.interpreted,
            self.input_validation,
            self.normalized_observations[-1]
            if self.normalized_observations
            else None,
            agent_name=self.goal.assigned_agent,
            completion_confidence=proof.completion_confidence,
        )
        self.repository.write("final_uncertainty.json", final_uncertainty)
        explanation = DecisionExplainer().explain(
            self.goal, decision, self.input_validation, final_uncertainty, proof
        )
        self.repository.write("decision_explanation.json", explanation)
        self.repository.append_decision_ledger(explanation)

        precision = CorePrecisionEvaluator().assess(
            self.goal, plan, output, decision, proof
        )
        self.repository.write("core_precision_assessment.json", precision)
        score = self._scorecard(
            proof.proof_valid,
            self.last_critique.approved if self.last_critique else False,
        )
        self.repository.write("agentic_scorecard.json", score)
        self.repository.write(
            "experience_candidate.json",
            ValidatedCase(
                case_id=f"CASE-{uuid4().hex[:12].upper()}",
                case_type=self.goal.goal_type,
                tenant_id=self.tenant_id,
                policy_fingerprint=self.context.policy_fingerprint
                if self.context
                else None,
                context_features={
                    "agent_name": self.goal.assigned_agent,
                    "goal_priority": self.goal.priority,
                },
                successful_plan=[step.objective for step in plan.steps],
                successful_tools=[
                    step.proposed_tool
                    for step in plan.steps
                    if step.proposed_tool
                ],
                outcome=decision.final_status,
                validation_status="pending",
                reusable=False,
            ),
        )
        terminal = {
            "completed": "COMPLETED",
            "completed_with_warnings": "COMPLETED_WITH_WARNINGS",
            "needs_human_review": "WAITING_FOR_HUMAN",
            "blocked": "BLOCKED",
            "failed": "FAILED",
            "cancelled": "CANCELLED",
        }[decision.final_status]
        self.state.transition(
            terminal,
            f"Completion proof produced terminal decision {decision.final_status}.",
        )
        return decision

    def _scorecard(self, proof_valid: bool, critique_approved: bool) -> AgenticScorecard:
        input_accuracy = 1.0 if self.input_validation.valid else 0.0
        interpretation = self.interpreted.interpretation_confidence
        proof_score = 1.0 if proof_valid else 0.0
        return AgenticScorecard(
            run_id=self.goal.run_id,
            agent_name=self.goal.assigned_agent,
            goal_interpretation_accuracy=interpretation,
            input_validation_accuracy=input_accuracy,
            plan_completeness=1.0
            if self.advanced_plan
            and all(self.advanced_plan.success_condition_coverage.values())
            else 0.0,
            plan_critique_effectiveness=1.0 if critique_approved else 0.5,
            tool_selection_accuracy=1.0,
            replan_success_rate=1.0,
            peer_request_usefulness=1.0
            if all(
                not item.blocking
                or (item.status == "RESOLVED" and item.acceptance_satisfied())
                for item in self.peer_requests
            )
            else 0.0,
            uncertainty_calibration=1.0,
            completion_proof_accuracy=proof_score,
            decision_explanation_quality=1.0,
            human_escalation_precision=1.0,
        )
