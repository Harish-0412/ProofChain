"""Construct and enforce machine-readable completion proofs."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.agentic import CompletionDecision, Goal
from proofchain.schemas.completion_proofs import (
    CompletionConditionResult,
    CompletionProof,
)
from proofchain.schemas.input_validation import InputValidationResult
from proofchain.schemas.peer_contracts import AgentRequest


class CompletionProver:
    def prove(
        self,
        goal: Goal,
        decision: CompletionDecision,
        inputs: InputValidationResult,
        *,
        output_schema_valid: bool,
        peer_requests: list[AgentRequest],
        policy_conflicts: list[str],
    ) -> CompletionProof:
        met = set(decision.success_conditions_met)
        unmet = set(decision.success_conditions_unmet)
        results = [
            CompletionConditionResult(
                condition=condition,
                evaluated=condition in met or condition in unmet,
                satisfied=condition in met,
                evidence=list(decision.supporting_artifacts),
                explanation=(
                    "Condition is reported as satisfied by the governed completion decision."
                    if condition in met
                    else "Condition remains unmet or was not demonstrated."
                ),
            )
            for condition in goal.success_conditions
        ]
        unresolved_peers = [
            item.request_id
            for item in peer_requests
            if item.blocking
            and (item.status != "RESOLVED" or not item.acceptance_satisfied())
        ]
        all_evaluated = all(item.evaluated for item in results)
        all_satisfied = all(item.satisfied for item in results)
        positive = decision.final_status in {"completed", "completed_with_warnings"}
        common_positive_gates = (
            inputs.valid
            and inputs.complete
            and inputs.authorized
            and inputs.current
            and output_schema_valid
            and not decision.blockers
            and not unresolved_peers
            and not policy_conflicts
        )
        refusal_basis = bool(
            decision.blockers
            or decision.success_conditions_unmet
            or decision.unresolved_questions
            or unresolved_peers
            or policy_conflicts
            or not inputs.valid
            or not output_schema_valid
        )
        proof_valid = (
            all_evaluated
            and (
                all_satisfied and common_positive_gates
                if positive
                else refusal_basis
            )
        )
        final_status = decision.final_status
        if positive and not proof_valid:
            final_status = (
                "needs_human_review"
                if unresolved_peers or policy_conflicts
                else "blocked"
            )
        return CompletionProof(
            proof_id=f"PRF-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=goal.assigned_agent,
            all_success_conditions_evaluated=all_evaluated,
            condition_results=results,
            mandatory_inputs_valid=inputs.valid and inputs.complete,
            output_schema_valid=output_schema_valid,
            unresolved_blockers=list(decision.blockers),
            unresolved_peer_requests=unresolved_peers,
            policy_conflicts=policy_conflicts,
            artifact_references=list(decision.supporting_artifacts),
            evidence_references=list(decision.supporting_artifacts),
            rule_references=["AGENT-BUDGET-001", "COMPLETION-POLICY-001"],
            completion_confidence=decision.confidence if proof_valid else 0.0,
            proof_valid=proof_valid,
            final_status=final_status,
            proof_metadata={
                "reported_decision_id": decision.decision_id,
                "positive_decision_requested": positive,
            },
        )

    @staticmethod
    def enforce(
        decision: CompletionDecision, proof: CompletionProof
    ) -> CompletionDecision:
        if proof.final_status == decision.final_status:
            return decision
        return decision.model_copy(
            update={
                "goal_satisfied": False,
                "success_conditions_unmet": list(
                    dict.fromkeys(
                        [
                            *decision.success_conditions_unmet,
                            *[
                                item.condition
                                for item in proof.condition_results
                                if not item.satisfied
                            ],
                        ]
                    )
                ),
                "blockers": list(
                    dict.fromkeys(
                        [
                            *decision.blockers,
                            *proof.unresolved_peer_requests,
                            *proof.policy_conflicts,
                            "Completion proof did not satisfy every mandatory gate.",
                        ]
                    )
                ),
                "confidence": 0.0,
                "final_status": proof.final_status,
                "explanation": (
                    f"{decision.explanation} The advanced completion proof prevented "
                    "an unsupported positive decision."
                ),
            }
        )
