"""Build standard concise decision explanations."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.agentic import CompletionDecision, Goal
from proofchain.schemas.completion_proofs import CompletionProof
from proofchain.schemas.decision_explanations import DecisionExplanation
from proofchain.schemas.input_validation import InputValidationResult
from proofchain.schemas.uncertainty import UncertaintyAssessment


class DecisionExplainer:
    def explain(
        self,
        goal: Goal,
        decision: CompletionDecision,
        inputs: InputValidationResult,
        uncertainty: UncertaintyAssessment,
        proof: CompletionProof,
    ) -> DecisionExplanation:
        return DecisionExplanation(
            explanation_id=f"EXP-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=goal.assigned_agent,
            decision=decision.final_status,
            goal=goal.objective,
            inputs_considered=[
                check.reference or check.check_name for check in inputs.checks
            ],
            evidence_considered=list(decision.supporting_artifacts),
            rules_applied=list(proof.rule_references),
            policies_applied=["advanced-cognition-core", "completion-proof-gate"],
            alternatives_considered=[
                "completed",
                "completed_with_warnings",
                "needs_human_review",
                "blocked",
                "failed",
            ],
            uncertainty=list(
                dict.fromkeys(
                    [*uncertainty.reasons, *decision.unresolved_questions]
                )
            ),
            reason=decision.explanation,
            next_action=(
                None
                if decision.final_status in {"completed", "completed_with_warnings"}
                else "Resolve blockers and rerun targeted validation."
            ),
            human_approval_required=decision.final_status == "needs_human_review",
            completion_proof_id=proof.proof_id,
        )
