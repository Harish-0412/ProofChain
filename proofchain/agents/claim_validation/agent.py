"""Goal-driven compound Claim Intelligence and Defensibility Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.repositories.json_decision_repository import JsonDecisionRepository
from proofchain.schemas.agentic import (
    AgentPlan,
    CompletionDecision,
    CoordinationMessage,
    PlanStep,
)
from proofchain.schemas.claims import ClaimAgentResult, ClaimValidationInput
from proofchain.core.exceptions import SchemaValidationError
from proofchain.agents.claim_validation.claim_decomposer import (
    ClaimDecompositionSpecialist,
)
from proofchain.agents.claim_validation.contradiction_investigator import (
    ContradictionInvestigationSpecialist,
)
from proofchain.agents.claim_validation.defensibility_judge import (
    DefensibilityDecisionSpecialist,
)
from proofchain.agents.claim_validation.evidence_retriever import (
    EvidenceRetrievalSpecialist,
)
from proofchain.agents.claim_validation.sufficiency_evaluator import (
    SufficiencyEvaluationSpecialist,
)


class ClaimIntelligenceAgent(BaseGoalAgent[ClaimValidationInput, ClaimAgentResult]):
    agent_name = "claim_intelligence"
    agent_version = "1.0.0"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or JsonDecisionRepository()
        self.decomposer = ClaimDecompositionSpecialist()
        self.retriever = EvidenceRetrievalSpecialist()
        self.investigator = ContradictionInvestigationSpecialist()
        self.sufficiency = SufficiencyEvaluationSpecialist()
        self.judge = DefensibilityDecisionSpecialist()
        self._state: dict = {}

    def validate_input(self, input_data: ClaimValidationInput) -> None:
        if not input_data.classified_evidence:
            raise SchemaValidationError("Claim intelligence requires classified evidence.")
        if not input_data.bundles:
            raise SchemaValidationError("Claim intelligence requires integrity bundles.")

    def execute(self, input_data: ClaimValidationInput) -> ClaimAgentResult:
        self._state = {}
        self._decompose(input_data)
        self._retrieve(input_data)
        self._investigate()
        self._evaluate_sufficiency()
        return self._decide(input_data)

    def validate_output(self, output_data: ClaimAgentResult) -> None:
        if not output_data.decisions:
            raise SchemaValidationError("Every claim run must produce a claim decision.")
        if any(not item.atomic_decisions for item in output_data.decisions):
            raise SchemaValidationError("Claim decisions must include atomic decisions.")

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        specs = [
            ("decompose_claim", "Decompose claims into atomic assertions."),
            ("retrieve_claim_evidence", "Retrieve supporting and counter-evidence."),
            ("investigate_contradictions", "Explain material value contradictions."),
            ("evaluate_claim_sufficiency", "Score coverage, authority, consistency, and independence."),
            ("judge_claim_defensibility", "Produce claim decisions, repair proposals, and lineage."),
        ]
        return AgentPlan(
            plan_id=f"PLAN-CLAIM-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale="Validate atomic claims using two-sided evidence and explicit specialist boundaries.",
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=f"{tool} returns a typed, auditable result.",
                    completion_condition="The specialist output is persisted in working memory.",
                )
                for index, (tool, objective) in enumerate(specs, 1)
            ],
            dependencies=goal.dependencies,
            expected_outputs=["claim_decisions.json", "claim lineage"],
            status="approved",
        )

    def agentic_tools(self, input_data):
        return {
            "decompose_claim": lambda: self._decompose(input_data),
            "retrieve_claim_evidence": lambda: self._retrieve(input_data),
            "investigate_contradictions": self._investigate,
            "evaluate_claim_sufficiency": self._evaluate_sufficiency,
            "judge_claim_defensibility": lambda: self._decide(input_data),
        }

    def _decompose(self, input_data):
        value = self.decomposer.run(input_data)
        self._state["claims"] = value
        return value

    def _retrieve(self, input_data):
        value = self.retriever.run(input_data, self._state["claims"])
        self._state["links"] = value
        return value

    def _investigate(self):
        value = self.investigator.run(self._state["links"])
        self._state["contradictions"] = value
        return value

    def _evaluate_sufficiency(self):
        value = self.sufficiency.run(
            self._state["claims"],
            self._state["links"],
            self._state["contradictions"],
        )
        self._state["sufficiency"] = value
        return value

    def _decide(self, input_data):
        started = datetime.now(tz=timezone.utc)
        decisions = self.judge.run(
            self._state["claims"],
            self._state["links"],
            self._state["contradictions"],
            self._state["sufficiency"],
        )
        warnings = [
            f"{item.claim_id} requires human review."
            for item in decisions
            if item.requires_human_review
        ]
        result = ClaimAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if warnings else "completed",
            input_count=len(self._state["claims"]),
            success_count=len(decisions),
            warning_count=len(warnings),
            claims=self._state["claims"],
            support_links=self._state["links"],
            sufficiency_assessments=self._state["sufficiency"],
            decisions=decisions,
            input_snapshot_hash=self.compute_input_hash(input_data),
            warnings=warnings,
            started_at=started,
        )
        artifact = self.repository.save_claims(
            result.run_id, result, result.agent_run_id
        )
        result.output_reference = artifact.path
        result.output_snapshot_hash = artifact.sha256
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        if output is None or not output.decisions:
            return self._completion(goal, False, "failed", 0.0, "No claim decisions were produced.")
        unresolved = [
            item.claim_id for item in output.decisions if item.requires_human_review
        ]
        status = "completed_with_warnings" if unresolved else "completed"
        return self._completion(
            goal,
            True,
            status,
            min((item.confidence for item in output.decisions), default=0.0),
            (
                f"Validated {len(output.decisions)} claims at atomic level; "
                f"{len(unresolved)} require governed human review."
            ),
            questions=unresolved,
            artifacts=[output.output_reference] if output.output_reference else [],
        )

    def create_peer_requests(self, goal, output):
        if output is None:
            return []
        requests = []
        for decision in output.decisions:
            if decision.status == "insufficient_evidence":
                requests.append(
                    self._message(
                        goal,
                        "evidence_collector",
                        "additional_evidence_request",
                        f"Claim {decision.claim_id} lacks mandatory evidence.",
                        decision.supporting_evidence,
                    )
                )
            if decision.contradictions:
                requests.append(
                    self._message(
                        goal,
                        "evidence_integrity",
                        "verification_request",
                        f"Claim {decision.claim_id} contains material contradictions.",
                        decision.counter_evidence,
                    )
                )
        return requests

    def _completion(
        self, goal, satisfied, status, confidence, explanation, questions=None, artifacts=None
    ):
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=satisfied,
            success_conditions_met=goal.success_conditions if satisfied else [],
            success_conditions_unmet=[] if satisfied else goal.success_conditions,
            unresolved_questions=questions or [],
            confidence=confidence,
            final_status=status,
            explanation=explanation,
            supporting_artifacts=artifacts or [],
        )

    def _message(self, goal, target, message_type, reason, evidence_ids):
        return CoordinationMessage(
            message_id=f"MSG-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            source_agent=self.agent_name,
            target_agent=target,
            message_type=message_type,
            reason=reason,
            related_evidence_ids=evidence_ids,
            priority="high",
        )
