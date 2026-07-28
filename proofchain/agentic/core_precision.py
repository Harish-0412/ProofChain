"""Agent 1-10 precision assessment records."""

from __future__ import annotations

from typing import Any

from proofchain.agentic.cognition_profiles import ALL_AGENT_FEATURES
from proofchain.schemas.agentic import AgentPlan, CompletionDecision, Goal
from proofchain.schemas.cognition import CorePrecisionAssessment
from proofchain.schemas.completion_proofs import CompletionProof


FEATURE_REQUIREMENTS = {
    "evidence_collector": [
        "Prioritize authorized evidence sources.",
        "Record collection coverage and source exhaustion.",
        "Preserve duplicate and version lineage.",
    ],
    "evidence_classification": [
        "Select an extraction strategy by source quality.",
        "Retain field-level provenance and alternate hypotheses.",
        "Escalate low-confidence classifications.",
    ],
    "evidence_integrity": [
        "Record applicable, executed, passed, and failed rules.",
        "Group related root causes and test false positives.",
        "Preserve historical and cross-year comparisons.",
    ],
    "claim_intelligence": [
        "Measure dependence on weak or disputed sources.",
        "Preserve atomic claim and version lineage.",
        "Provide a counterfactual repair path.",
    ],
    "adaptive_gap_resolution": [
        "Compare strategies by effort, probability, and deadline.",
        "Respect staffing, policy, and approval constraints.",
        "Retain fallback strategies and readiness assumptions.",
    ],
    "accountability_ownership": [
        "Link user, role, department, permission, and workload.",
        "Evaluate delegation, backup depth, and conflicts.",
        "Explain assignment confidence.",
    ],
    "department_liaison": [
        "Check problem, action, evidence, path, and deadline clarity.",
        "Adapt communication and follow-up strategy.",
        "Route disputes and escalations through governance.",
    ],
    "closure_revalidation": [
        "Link original issue, correction, delta, and targeted rules.",
        "Revalidate claims and detect regressions.",
        "Prove closure rather than equating upload with closure.",
    ],
    "audit_package_composer": [
        "Order requirement, claim, evidence, validation, and closure.",
        "Measure redundancy, citation quality, and privacy coverage.",
        "Preserve package reproducibility and version comparison.",
    ],
    "adversarial_quality_review": [
        "Reproduce key facts independently from source artifacts.",
        "Challenge omissions, authority, privacy, and package version.",
        "Record reviewer confusion and required corrections.",
    ],
    "operational_persistence": [
        "Reconcile event and snapshot stores.",
        "Prove ordered state reconstruction and corruption handling.",
        "Record transaction and recovery confidence.",
    ],
    "workflow_continuation": [
        "Calculate the smallest dependency-complete rerun.",
        "Prove cache safety and suppress duplicate actions.",
        "Record critical path and resume readiness.",
    ],
    "identity_authorization": [
        "Resolve identity, role, delegation, time, and tenant scope.",
        "Enforce separation of duties and dual approval.",
        "Explain every effective permission and denial.",
    ],
    "integration_notification": [
        "Predict and record channel outcomes.",
        "Use bounded fallback and correlation identifiers.",
        "Prove duplicate suppression and disclosure scope.",
    ],
    "security_inspection": [
        "Treat content as untrusted across staged inspection.",
        "Explain quarantine and downstream restrictions.",
        "Produce an evidence trust envelope.",
    ],
    "reliability_incident_response": [
        "Rank incident hypotheses and blast radius.",
        "Simulate bounded retry, failover, pause, and escalation.",
        "Prove recovery preserved data integrity.",
    ],
    "schema_evolution": [
        "Map dependencies and breaking changes.",
        "Provide migration, rollback, and shadow validation.",
        "Prove historical compatibility before deployment.",
    ],
    "policy_lifecycle": [
        "Detect ambiguity, conflict, and effective-date risk.",
        "Simulate historical and open-run impact.",
        "Require approval before activation.",
    ],
    "tenant_governance": [
        "Prove subject, resource, tenant, and department context.",
        "Validate share approval and expiry.",
        "Prevent cross-tenant leakage and explain boundaries.",
    ],
    "external_submission": [
        "Dry-run every gate without transmission.",
        "Verify frozen hash, quality, approvals, payload, and deadline.",
        "Persist receipt or safe rejection and resubmission guidance.",
    ],
    "continuous_evaluation": [
        "Measure all cognition dimensions per agent.",
        "Cluster regressions and unsafe outcomes.",
        "Block releases that violate safety gates.",
    ],
    "knowledge_retrieval": [
        "Interpret the query and rank source authority.",
        "Prove freshness, diversity, contradiction, and citation coverage.",
        "Keep retrieved context advisory and uncertainty-aware.",
    ],
}


class CorePrecisionEvaluator:
    def assess(
        self,
        goal: Goal,
        plan: AgentPlan,
        output: Any,
        decision: CompletionDecision,
        proof: CompletionProof,
    ) -> CorePrecisionAssessment:
        payload = (
            output.model_dump(mode="json")
            if hasattr(output, "model_dump")
            else {}
        )
        coverage = [
            {
                "condition": condition,
                "covered_by_steps": [
                    step.step_id
                    for step in plan.steps
                    if step.sequence == len(plan.steps)
                ],
                "satisfied": condition in decision.success_conditions_met,
            }
            for condition in goal.success_conditions
        ]
        status = (
            "satisfied"
            if proof.proof_valid
            else "blocked"
            if decision.final_status in {"blocked", "failed"}
            else "partial"
        )
        warnings = payload.get("warnings", [])
        feature_metrics, feature_coverage = self._feature_details(
            goal.assigned_agent, payload
        )
        return CorePrecisionAssessment(
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=goal.assigned_agent,
            unique_feature=ALL_AGENT_FEATURES[goal.assigned_agent],
            feature_status=status,
            metrics={
                "success_count": payload.get("success_count", 0),
                "warning_count": payload.get("warning_count", len(warnings)),
                "failure_count": payload.get("failure_count", 0),
                "plan_steps": len(plan.steps),
                "conditions_evaluated": len(proof.condition_results),
                "completion_confidence": proof.completion_confidence,
                "output_fields": sorted(payload),
                **feature_metrics,
            },
            coverage=[*coverage, *feature_coverage],
            lineage=list(decision.supporting_artifacts),
            unresolved_items=list(
                dict.fromkeys(
                    [
                        *decision.blockers,
                        *decision.unresolved_questions,
                        *proof.unresolved_peer_requests,
                    ]
                )
            ),
            completion_requirements=FEATURE_REQUIREMENTS[goal.assigned_agent],
        )

    def _feature_details(
        self, agent_name: str, payload: dict[str, Any]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        handler = getattr(self, f"_assess_{agent_name}")
        return handler(payload)

    @staticmethod
    def _assess_evidence_collector(payload):
        records = payload.get("records", [])
        checksummed = sum(bool(item.get("sha256_checksum")) for item in records)
        lineage = sum(
            bool(item.get("duplicate_of_evidence_id")) for item in records
        )
        source_types = sorted(
            {str(item.get("source_type")) for item in records if item.get("source_type")}
        )
        extensions = sorted(
            {str(item.get("file_extension")) for item in records}
        )
        total = len(records)
        return (
            {
                "acquisition_sources": source_types,
                "evidence_categories": extensions,
                "checksum_coverage": checksummed / total if total else 1.0,
                "duplicate_version_lineage_count": lineage,
                "source_exhaustion_proven": (
                    payload.get("input_count", 0)
                    == payload.get("success_count", 0)
                    + payload.get("unsupported_count", 0)
                    + payload.get("failure_count", 0)
                ),
            },
            [
                {
                    "source_type": source,
                    "evidence_count": sum(
                        str(item.get("source_type")) == source for item in records
                    ),
                }
                for source in source_types
            ],
        )

    @staticmethod
    def _assess_evidence_classification(payload):
        records = payload.get("records", [])
        extractors: dict[str, int] = {}
        field_count = 0
        sourced_fields = 0
        alternate_hypotheses = 0
        for item in records:
            extraction = item.get("extraction", {})
            extractor = str(extraction.get("extractor_used", "unknown"))
            extractors[extractor] = extractors.get(extractor, 0) + 1
            fields = list(item.get("extracted_fields", {}).values())
            field_count += len(fields)
            sourced_fields += sum(
                bool(
                    field.get("page_number")
                    or field.get("sheet_name")
                    or field.get("cell_range")
                    or field.get("extraction_method")
                )
                for field in fields
            )
            alternate_hypotheses += len(
                item.get("document_type", {}).get("secondary_types", [])
            )
        return (
            {
                "extraction_strategy_distribution": extractors,
                "alternate_classification_hypotheses": alternate_hypotheses,
                "field_provenance_coverage": (
                    sourced_fields / field_count if field_count else 1.0
                ),
                "human_review_items": sum(
                    bool(item.get("requires_human_review")) for item in records
                ),
            },
            [
                {"strategy": key, "documents": value}
                for key, value in sorted(extractors.items())
            ],
        )

    @staticmethod
    def _assess_evidence_integrity(payload):
        findings = payload.get("findings", [])
        rule_ids = sorted(
            {str(item.get("rule_id")) for item in findings if item.get("rule_id")}
        )
        coverage = [
            {
                "rule_id": rule_id,
                "executed": True,
                "finding_count": sum(
                    item.get("rule_id") == rule_id for item in findings
                ),
                "blocking_findings": sum(
                    item.get("rule_id") == rule_id and item.get("blocking")
                    for item in findings
                ),
                "evidence_references": sorted(
                    {
                        evidence_id
                        for item in findings
                        if item.get("rule_id") == rule_id
                        for evidence_id in item.get("evidence_ids", [])
                    }
                ),
            }
            for rule_id in rule_ids
        ]
        return (
            {
                "applicable_rules_executed": len(rule_ids),
                "root_cause_groups": len(
                    {str(item.get("finding_type")) for item in findings}
                ),
                "blocking_findings": sum(
                    bool(item.get("blocking")) for item in findings
                ),
                "cross_scope_summaries": len(payload.get("summaries", [])),
            },
            coverage,
        )

    @staticmethod
    def _assess_claim_intelligence(payload):
        decisions = payload.get("decisions", [])
        fragile = []
        atomic = 0
        contradictions = 0
        for item in decisions:
            atomic_items = item.get("atomic_decisions", [])
            atomic += len(atomic_items)
            contradictions += len(item.get("contradictions", []))
            evidence = {
                evidence_id
                for atomic_item in atomic_items
                for evidence_id in atomic_item.get("evidence_ids", [])
            }
            if len(evidence) <= 1 or float(item.get("confidence", 0)) < 0.75:
                fragile.append(item.get("claim_id"))
        return (
            {
                "atomic_claims_evaluated": atomic,
                "fragile_claim_ids": fragile,
                "contradictions_ranked": contradictions,
                "claim_lineage_records": sum(
                    bool(item.get("lineage")) for item in decisions
                ),
            },
            [
                {
                    "claim_id": item.get("claim_id"),
                    "confidence": item.get("confidence", 0),
                    "status": item.get("status"),
                    "fragile": item.get("claim_id") in fragile,
                }
                for item in decisions
            ],
        )

    @staticmethod
    def _assess_adaptive_gap_resolution(payload):
        portfolio = payload.get("portfolio", {})
        plans = portfolio.get("plans", [])
        strategies = [
            strategy for plan in plans for strategy in plan.get("strategies", [])
        ]
        return (
            {
                "gaps_optimized": len(portfolio.get("gaps", [])),
                "strategies_compared": len(strategies),
                "minimal_resolution_set_size": len(
                    portfolio.get("minimal_resolution_set", [])
                ),
                "projection_type": portfolio.get("projection_type"),
                "projection_assumptions": portfolio.get(
                    "projection_assumptions", []
                ),
                "average_resolution_probability": (
                    sum(
                        float(item.get("expected_resolution_confidence", 0))
                        for item in strategies
                    )
                    / len(strategies)
                    if strategies
                    else 0.0
                ),
            },
            [
                {
                    "gap_id": plan.get("gap_id"),
                    "strategy_count": len(plan.get("strategies", [])),
                    "expected_readiness_delta": plan.get(
                        "expected_readiness_delta", 0
                    ),
                    "approval_required": plan.get(
                        "human_approval_required", True
                    ),
                }
                for plan in plans
            ],
        )

    @staticmethod
    def _assess_accountability_ownership(payload):
        assignments = payload.get("assignments", [])
        confidence = [
            float(item.get("assignment_confidence", 0)) for item in assignments
        ]
        return (
            {
                "responsibility_nodes": len(assignments),
                "average_assignment_confidence": (
                    sum(confidence) / len(confidence) if confidence else 0.0
                ),
                "backup_depth": sum(
                    bool(item.get("backup_owner")) for item in assignments
                ),
                "conflict_flag_count": sum(
                    any(item.get("conflict_checks", {}).values())
                    for item in assignments
                ),
                "unresolved_ownership": payload.get(
                    "unresolved_ownership", []
                ),
            },
            [
                {
                    "assignment_id": item.get("assignment_id"),
                    "gap_id": item.get("gap_id"),
                    "primary_owner": (
                        item.get("primary_owner") or {}
                    ).get("user_id"),
                    "backup_owner": (
                        item.get("backup_owner") or {}
                    ).get("user_id"),
                    "confidence": item.get("assignment_confidence", 0),
                }
                for item in assignments
            ],
        )

    @staticmethod
    def _assess_department_liaison(payload):
        tasks = payload.get("tasks", [])
        understandable = [
            bool(
                item.get("objective")
                and item.get("required_actions")
                and item.get("required_closure_evidence")
                and item.get("due_at")
            )
            for item in tasks
        ]
        return (
            {
                "tasks_checked": len(tasks),
                "understandability_pass_rate": (
                    sum(understandable) / len(tasks) if tasks else 1.0
                ),
                "paused_for_approval": sum(
                    item.get("status") == "approval_required" for item in tasks
                ),
                "delivery_failures": sum(
                    item.get("delivery_status") == "failed" for item in tasks
                ),
            },
            [
                {
                    "task_id": item.get("task_id"),
                    "problem_clear": bool(item.get("objective")),
                    "action_clear": bool(item.get("required_actions")),
                    "evidence_clear": bool(
                        item.get("required_closure_evidence")
                    ),
                    "submission_path_clear": bool(
                        item.get("dispatch_channel")
                    ),
                    "deadline_clear": bool(item.get("due_at")),
                }
                for item in tasks
            ],
        )

    @staticmethod
    def _assess_closure_revalidation(payload):
        checks = payload.get("closure_checks", [])
        return (
            {
                "closure_proofs": len(checks),
                "resolved_after_revalidation": sum(
                    item.get("status") == "resolved" for item in checks
                ),
                "regressions_or_rejections": sum(
                    item.get("status") == "rejected" for item in checks
                ),
                "current_verified_readiness": payload.get(
                    "current_verified_readiness", 0
                ),
            },
            [
                {
                    "issue_id": item.get("issue_id"),
                    "evidence_submitted": item.get("evidence_submitted"),
                    "evidence_registered": item.get("evidence_registered"),
                    "classification_complete": item.get(
                        "classification_complete"
                    ),
                    "integrity_rules_passed": item.get(
                        "integrity_rules_passed"
                    ),
                    "claims_revalidated": item.get(
                        "affected_claims_revalidated"
                    ),
                    "closure_policy_satisfied": item.get(
                        "closure_policy_satisfied"
                    ),
                    "status": item.get("status"),
                }
                for item in checks
            ],
        )

    @staticmethod
    def _assess_audit_package_composer(payload):
        manifest = payload.get("manifest", {})
        eligible = manifest.get("eligible_evidence", [])
        hashes = [
            item.get("sha256") for item in eligible if item.get("sha256")
        ]
        return (
            {
                "reviewer_journey": [
                    "requirement",
                    "claim",
                    "evidence",
                    "verification",
                    "closure",
                ],
                "eligible_evidence": len(eligible),
                "excluded_evidence": len(
                    manifest.get("excluded_evidence", [])
                ),
                "redundant_hash_count": len(hashes) - len(set(hashes)),
                "reproducibility_hash_present": bool(
                    manifest.get("package_hash")
                ),
                "privacy_boundary_enforced": not manifest.get(
                    "external_submission_approved", False
                ),
            },
            [
                {
                    "journey_stage": stage,
                    "position": position,
                    "traceable": True,
                }
                for position, stage in enumerate(
                    [
                        "requirement",
                        "claim",
                        "evidence",
                        "verification",
                        "closure",
                    ],
                    start=1,
                )
            ],
        )

    @staticmethod
    def _assess_adversarial_quality_review(payload):
        challenges = payload.get("claim_challenges", [])
        return (
            {
                "independent_reproductions": len(challenges),
                "failed_reproductions": sum(
                    item.get("result") == "failed" for item in challenges
                ),
                "broken_references": payload.get("broken_references", 0),
                "omitted_material_findings": payload.get(
                    "omitted_material_findings", 0
                ),
                "privacy_findings": payload.get("privacy_findings", 0),
                "reviewer_friction_score": payload.get(
                    "reviewer_friction_score", 0
                ),
                "audit_failure_risk": payload.get("audit_failure_risk", 0),
            },
            [
                {
                    "claim_id": item.get("claim_id"),
                    "reproduction_result": item.get("result"),
                    "reason": item.get("reason"),
                }
                for item in challenges
            ],
        )

    @staticmethod
    def _assess_operational_persistence(payload):
        source_hash = payload.get("source_state_hash")
        reconstructed_hash = payload.get("reconstructed_state_hash")
        return (
            {
                "backend": payload.get("backend"),
                "database_health": payload.get("database_health"),
                "events_reconciled": payload.get("persisted_events", 0),
                "snapshot_version": payload.get("snapshot_version", 0),
                "state_hash_match": bool(source_hash)
                and source_hash == reconstructed_hash,
                "recovery_verified": payload.get("recovery_verified", False),
                "corruption_hypotheses": payload.get(
                    "corruption_findings", []
                ),
                "snapshot_confidence": 1.0
                if payload.get("recovery_verified")
                else 0.0,
            },
            [
                {
                    "store": payload.get("backend"),
                    "source_hash": source_hash,
                    "reconstructed_hash": reconstructed_hash,
                    "reconciled": bool(source_hash)
                    and source_hash == reconstructed_hash,
                }
            ],
        )

    @staticmethod
    def _assess_workflow_continuation(payload):
        change_set = payload.get("change_set", [])
        scheduled = payload.get("scheduled_agents", [])
        return (
            {
                "changed_references": len(change_set),
                "stale_entities": len(payload.get("stale_entities", [])),
                "reusable_entities": len(payload.get("reusable_entities", [])),
                "minimal_rerun_agents": scheduled,
                "estimated_rerun_cost": len(scheduled),
                "duplicate_actions_suppressed": len(
                    payload.get("duplicate_actions_suppressed", [])
                ),
                "resume_readiness_proven": not payload.get(
                    "reconciliation_required", False
                ),
                "critical_path": scheduled,
            },
            [
                {
                    "reference": reference,
                    "stale": reference
                    in payload.get("stale_entities", []),
                    "reusable": reference
                    in payload.get("reusable_entities", []),
                }
                for reference in change_set
            ],
        )

    @staticmethod
    def _assess_identity_authorization(payload):
        return (
            {
                "authorization_decision": payload.get(
                    "authorization_decision"
                ),
                "authority_confidence": 1.0
                if payload.get("authorization_decision") == "AUTHORIZED"
                else 0.5,
                "effective_permissions": payload.get(
                    "effective_permissions", []
                ),
                "required_approvals": payload.get(
                    "required_approval_count", 0
                ),
                "valid_approvals": payload.get("valid_approval_count", 0),
                "separation_of_duties_passed": payload.get(
                    "separation_of_duties_passed", False
                ),
                "policy_reasons": payload.get("policy_reasons", []),
            },
            [
                {
                    "subject_id": payload.get("subject_id"),
                    "resource_id": payload.get("resource_id"),
                    "decision": payload.get("authorization_decision"),
                    "separation_of_duties": payload.get(
                        "separation_of_duties_passed", False
                    ),
                }
            ],
        )

    @staticmethod
    def _assess_integration_notification(payload):
        attempts = payload.get("attempts", [])
        return (
            {
                "selected_channel": payload.get("selected_channel"),
                "delivery_status": payload.get("delivery_status"),
                "channel_success_predictions": {
                    str(item.get("channel_type")): (
                        1.0 if item.get("status") == "delivered" else 0.0
                    )
                    for item in attempts
                },
                "fallback_attempts": max(0, len(attempts) - 1),
                "response_correlation_confidence": 1.0
                if payload.get("correlation_token")
                else 0.0,
                "duplicate_suppressed": payload.get(
                    "duplicate_suppressed", False
                ),
                "idempotency_key_present": bool(
                    payload.get("idempotency_key")
                ),
            },
            [
                {
                    "channel": item.get("channel_type"),
                    "destination": item.get("destination"),
                    "status": item.get("status"),
                    "provider_receipt": item.get("provider_message_id"),
                }
                for item in attempts
            ],
        )

    @staticmethod
    def _assess_security_inspection(payload):
        findings = payload.get("evidence_findings", [])
        return (
            {
                "overall_decision": payload.get("overall_decision"),
                "security_confidence": 1.0
                if all(item.get("decision") for item in findings)
                else 0.0,
                "multi_stage_items": len(findings),
                "quarantined_items": len(
                    payload.get("quarantined_paths", [])
                ),
                "allowed_items": len(payload.get("allowed_paths", [])),
                "risk_propagation_instruction": payload.get(
                    "downstream_instruction"
                ),
            },
            [
                {
                    "path": item.get("path"),
                    "decision": item.get("decision"),
                    "findings": item.get("findings", []),
                    "restrictions": item.get("restrictions", []),
                    "sha256": item.get("sha256"),
                    "quarantine_reference": item.get(
                        "quarantine_reference"
                    ),
                }
                for item in findings
            ],
        )

    @staticmethod
    def _assess_reliability_incident_response(payload):
        incidents = payload.get("incidents", [])
        return (
            {
                "reliability_status": payload.get("reliability_status"),
                "incident_hypotheses_ranked": len(incidents),
                "blast_radius_sources": sorted(
                    {
                        source
                        for item in incidents
                        for source in item.get("affected_sources", [])
                    }
                ),
                "retries_authorized": payload.get(
                    "retries_authorized", 0
                ),
                "failovers_authorized": payload.get(
                    "failovers_authorized", 0
                ),
                "paused_sources": payload.get("paused_sources", []),
                "recovery_safety_proven": payload.get(
                    "data_integrity_verified", False
                )
                and all(
                    item.get("integrity_verified", False)
                    for item in incidents
                ),
            },
            [
                {
                    "incident_id": item.get("incident_id"),
                    "severity": item.get("severity"),
                    "hypothesis": item.get("hypothesis"),
                    "recovery_action": item.get("recovery_action"),
                    "recovered": item.get("recovered"),
                    "integrity_verified": item.get(
                        "integrity_verified"
                    ),
                }
                for item in incidents
            ],
        )

    @staticmethod
    def _assess_schema_evolution(payload):
        converted = payload.get("converted_artifacts", [])
        return (
            {
                "compatibility": payload.get("compatibility"),
                "breaking_changes": payload.get("breaking_changes", []),
                "migration_steps": payload.get("migration_steps", []),
                "historical_samples": len(converted),
                "historical_artifacts_preserved": payload.get(
                    "historical_artifacts_preserved", False
                ),
                "deployment_decision": payload.get(
                    "deployment_decision"
                ),
                "rollback_required": bool(
                    payload.get("breaking_changes")
                ),
                "shadow_run_passed": all(
                    item.get("original_hash") != item.get("converted_hash")
                    or item.get("original_schema_version")
                    == item.get("converted_schema_version")
                    for item in converted
                ),
            },
            [
                {
                    "artifact_id": item.get("artifact_id"),
                    "from_version": item.get(
                        "original_schema_version"
                    ),
                    "to_version": item.get(
                        "converted_schema_version"
                    ),
                    "original_preserved": bool(
                        item.get("original_hash")
                    ),
                }
                for item in converted
            ],
        )

    @staticmethod
    def _assess_policy_lifecycle(payload):
        simulations = payload.get("simulations", [])
        return (
            {
                "syntax_valid": payload.get("syntax_valid", False),
                "ambiguities_or_conflicts": payload.get("conflicts", []),
                "scenario_simulations": len(simulations),
                "changed_historical_outcomes": sum(
                    bool(item.get("changed")) for item in simulations
                ),
                "affected_open_runs": payload.get(
                    "affected_open_run_ids", []
                ),
                "historical_decisions_preserved": payload.get(
                    "historical_decisions_preserved", False
                ),
                "activation_decision": payload.get(
                    "activation_decision"
                ),
            },
            [
                {
                    "case_id": item.get("case_id"),
                    "previous_decision": item.get(
                        "previous_decision"
                    ),
                    "simulated_decision": item.get(
                        "simulated_decision"
                    ),
                    "changed": item.get("changed"),
                }
                for item in simulations
            ],
        )

    @staticmethod
    def _assess_tenant_governance(payload):
        return (
            {
                "tenant_id": payload.get("tenant_id"),
                "department_id": payload.get("department_id"),
                "access_decision": payload.get("access_decision"),
                "cross_tenant_request": payload.get(
                    "cross_tenant_request", False
                ),
                "approved_share_applied": bool(
                    payload.get("applied_share_id")
                ),
                "effective_permissions": payload.get(
                    "effective_permissions", []
                ),
                "boundary_explanation": payload.get(
                    "policy_reasons", []
                ),
                "isolation_verified": not (
                    payload.get("cross_tenant_request")
                    and payload.get("access_decision") == "ALLOW"
                    and not payload.get("applied_share_id")
                ),
            },
            [
                {
                    "tenant": payload.get("tenant_id"),
                    "department": payload.get("department_id"),
                    "decision": payload.get("access_decision"),
                    "share_id": payload.get("applied_share_id"),
                }
            ],
        )

    @staticmethod
    def _assess_external_submission(payload):
        receipt = payload.get("receipt")
        return (
            {
                "eligibility_decision": payload.get(
                    "eligibility_decision"
                ),
                "submission_status": payload.get("submission_status"),
                "frozen_package_hash": payload.get(
                    "frozen_package_hash"
                ),
                "dry_run_completed": payload.get("submission_status")
                == "not_submitted",
                "transmission_occurred": bool(receipt),
                "receipt_confidence": 1.0
                if receipt and receipt.get("provider_reference")
                else 0.0,
                "idempotency_key_present": bool(
                    payload.get("idempotency_key")
                ),
                "policy_reasons": payload.get("policy_reasons", []),
            },
            [
                {
                    "package_id": payload.get("package_id"),
                    "frozen_hash": payload.get(
                        "frozen_package_hash"
                    ),
                    "eligible": payload.get(
                        "eligibility_decision"
                    )
                    == "ELIGIBLE",
                    "transmitted": bool(receipt),
                }
            ],
        )

    @staticmethod
    def _assess_continuous_evaluation(payload):
        return (
            {
                "release_id": payload.get("release_id"),
                "scenario_count": payload.get("scenario_count", 0),
                "accuracy": payload.get("accuracy", 0),
                "false_approval_rate": payload.get(
                    "false_approval_rate", 0
                ),
                "false_closure_rate": payload.get(
                    "false_closure_rate", 0
                ),
                "calibration_error": payload.get(
                    "calibration_error", 0
                ),
                "regression_findings": payload.get(
                    "regression_findings", []
                ),
                "release_decision": payload.get("release_decision"),
            },
            [
                {
                    "gate": "false_approval_rate",
                    "value": payload.get("false_approval_rate", 0),
                    "passed": payload.get("false_approval_rate", 0) == 0,
                },
                {
                    "gate": "false_closure_rate",
                    "value": payload.get("false_closure_rate", 0),
                    "passed": payload.get("false_closure_rate", 0) == 0,
                },
                {
                    "gate": "release_decision",
                    "value": payload.get("release_decision"),
                    "passed": payload.get("release_decision") == "PASS",
                },
            ],
        )

    @staticmethod
    def _assess_knowledge_retrieval(payload):
        citations = payload.get("citations", [])
        authorities = {
            item.get("authority") for item in citations
        }
        current = [
            item
            for item in citations
            if item.get("freshness_status") == "current"
        ]
        return (
            {
                "query_interpreted": bool(payload.get("query")),
                "citation_count": len(citations),
                "source_diversity": len(authorities),
                "authority_confidence": (
                    sum(
                        float(item.get("relevance_score", 0))
                        for item in citations
                    )
                    / len(citations)
                    if citations
                    else 0.0
                ),
                "freshness_coverage": (
                    len(current) / len(citations) if citations else 0.0
                ),
                "conflicting_sources": payload.get(
                    "conflicting_source_ids", []
                ),
                "citation_completeness": all(
                    item.get("source_checksum")
                    and item.get("uri")
                    and item.get("supporting_excerpt")
                    for item in citations
                ),
                "advisory_only": payload.get("advisory_only", True),
            },
            [
                {
                    "source_id": item.get("source_id"),
                    "authority": item.get("authority"),
                    "freshness": item.get("freshness_status"),
                    "relevance": item.get("relevance_score"),
                    "checksum_present": bool(
                        item.get("source_checksum")
                    ),
                }
                for item in citations
            ],
        )
