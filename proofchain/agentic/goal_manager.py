"""Top-level goal interpretation, decomposition, and dependency scheduling."""

from __future__ import annotations

from proofchain.core.enums import RunMode
from proofchain.schemas.agentic import Goal
from proofchain.schemas.workflow import SupervisorRequest, WorkflowContext


class GoalManager:
    def create_top_level_goal(
        self, workflow: WorkflowContext, request: SupervisorRequest
    ) -> Goal:
        requirements = ", ".join(request.requirement_scope)
        departments = ", ".join(request.department_scope)
        objective = request.objective or (
            f"Determine whether {departments} requirements {requirements} for "
            f"{request.academic_year} are defensible using currently available evidence."
        )
        return Goal(
            goal_id=f"GOAL-{workflow.run_id}-TOP",
            run_id=workflow.run_id,
            assigned_agent="supervisor",
            objective=objective,
            goal_type="validate_requirement_defensibility",
            priority="critical",
            input_references=request.source_directories,
            constraints=[
                "Do not modify original evidence files.",
                f"Maximum supervisor rounds: {request.maximum_agent_rounds}.",
                f"Maximum replans per agent: {request.maximum_replans_per_agent}.",
            ],
            success_conditions=request.success_conditions
            or [
                "All mandatory evidence types are accounted for.",
                "Blocking integrity findings are resolved or formally disclosed.",
                "Every mapped document remains traceable to its source.",
                "A final defensibility decision is produced.",
            ],
            failure_conditions=[
                "No usable evidence can be acquired.",
                "A technical failure prevents deterministic validation.",
            ],
        )

    def decompose(
        self,
        top_goal: Goal,
        request: SupervisorRequest,
    ) -> list[Goal]:
        run_id = top_goal.run_id
        goals: list[Goal] = []
        collection_id = f"GOAL-{run_id}-COLLECT"
        classification_id = f"GOAL-{run_id}-CLASSIFY"
        integrity_id = f"GOAL-{run_id}-INTEGRITY"
        claim_id = f"GOAL-{run_id}-CLAIM"
        gap_id = f"GOAL-{run_id}-GAP"
        ownership_id = f"GOAL-{run_id}-OWNERSHIP"
        liaison_id = f"GOAL-{run_id}-LIAISON"
        closure_id = f"GOAL-{run_id}-CLOSURE"
        package_id = f"GOAL-{run_id}-PACKAGE"
        quality_id = f"GOAL-{run_id}-QUALITY"

        if request.run_mode in {RunMode.FULL, RunMode.COLLECT_ONLY, RunMode.RERUN}:
            goals.append(
                Goal(
                    goal_id=collection_id,
                    run_id=run_id,
                    parent_goal_id=top_goal.goal_id,
                    assigned_agent="evidence_collector",
                    objective="Acquire and register all available evidence in the approved source scope.",
                    goal_type="acquire_evidence",
                    priority="critical",
                    input_references=request.source_directories,
                    constraints=top_goal.constraints,
                    success_conditions=[
                        "Every discoverable supported file is registered or explicitly skipped.",
                        "Every registered file has a checksum and immutable source reference.",
                    ],
                    failure_conditions=["No readable evidence is available."],
                )
            )
        if request.run_mode in {
            RunMode.FULL,
            RunMode.CLASSIFY_ONLY,
            RunMode.RERUN,
        }:
            dependencies = [collection_id] if request.run_mode != RunMode.CLASSIFY_ONLY else []
            goals.append(
                Goal(
                    goal_id=classification_id,
                    run_id=run_id,
                    parent_goal_id=top_goal.goal_id,
                    assigned_agent="evidence_classification",
                    objective="Extract, classify, and map every registered evidence item.",
                    goal_type="understand_evidence",
                    priority="high",
                    constraints=top_goal.constraints,
                    success_conditions=[
                        "Every processable item has an extraction state and document type.",
                        "Every item has a requirement mapping or an explicit unresolved state.",
                    ],
                    failure_conditions=["No evidence item can be interpreted."],
                    dependencies=dependencies,
                )
            )
        if request.run_mode in {
            RunMode.FULL,
            RunMode.INTEGRITY_ONLY,
            RunMode.RERUN,
        }:
            dependencies = [classification_id] if request.run_mode != RunMode.INTEGRITY_ONLY else []
            goals.append(
                Goal(
                    goal_id=integrity_id,
                    run_id=run_id,
                    parent_goal_id=top_goal.goal_id,
                    assigned_agent="evidence_integrity",
                    objective="Verify evidence integrity, sufficiency, and requirement defensibility.",
                    goal_type="verify_defensibility",
                    priority="critical",
                    constraints=top_goal.constraints,
                    success_conditions=[
                        "All applicable deterministic rules are executed.",
                        "Blocking findings and evidence gaps are explicitly disclosed.",
                        "A defensibility state is produced.",
                    ],
                    failure_conditions=["Evidence cannot be bundled or checked."],
                    dependencies=dependencies,
                )
            )
            goals.extend(
                [
                    Goal(
                        goal_id=claim_id,
                        run_id=run_id,
                        parent_goal_id=top_goal.goal_id,
                        assigned_agent="claim_intelligence",
                        objective=(
                            "Validate institutional claims at atomic level using "
                            "supporting and counter-evidence."
                        ),
                        goal_type="validate_claim_defensibility",
                        priority="critical",
                        constraints=top_goal.constraints,
                        success_conditions=[
                            "Every atomic claim has a validation state and evidence references.",
                            "Contradictions are resolved or explicitly disclosed.",
                            "A defensible claim decision and lineage are produced.",
                        ],
                        failure_conditions=["No claim decision can be produced."],
                        dependencies=[integrity_id],
                    ),
                    Goal(
                        goal_id=gap_id,
                        run_id=run_id,
                        parent_goal_id=top_goal.goal_id,
                        assigned_agent="adaptive_gap_resolution",
                        objective=(
                            "Convert claim and integrity failures into a prioritized "
                            "resolution and readiness programme."
                        ),
                        goal_type="plan_gap_resolution",
                        priority="high",
                        constraints=top_goal.constraints,
                        success_conditions=[
                            "Every unresolved finding is represented by one normalized gap.",
                            "Every gap has strategies, closure evidence, and dependencies.",
                            "Readiness impact and priority are calculated.",
                        ],
                        failure_conditions=["Blocking gaps lack actionable resolution plans."],
                        dependencies=[claim_id],
                    ),
                    Goal(
                        goal_id=ownership_id,
                        run_id=run_id,
                        parent_goal_id=top_goal.goal_id,
                        assigned_agent="accountability_ownership",
                        objective=(
                            "Recommend authorized primary, backup, approval, and "
                            "escalation responsibility for every resolution gap."
                        ),
                        goal_type="resolve_evidence_ownership",
                        priority="high",
                        constraints=top_goal.constraints,
                        success_conditions=[
                            "Every gap has an assignment recommendation or formal unresolved state.",
                            "Permissions, workload, department, and conflicts are checked.",
                            "Human approval requirements and escalation paths are explicit.",
                        ],
                        failure_conditions=[
                            "A task is assigned without authorization or independent approval."
                        ],
                        dependencies=[gap_id],
                    ),
                    Goal(
                        goal_id=liaison_id,
                        run_id=run_id,
                        parent_goal_id=top_goal.goal_id,
                        assigned_agent="department_liaison",
                        objective=(
                            "Convert governed ownership and resolution recommendations "
                            "into policy-controlled tasks and communications."
                        ),
                        goal_type="coordinate_resolution_execution",
                        priority="high",
                        constraints=top_goal.constraints,
                        success_conditions=[
                            "Every canonical issue has a task decision.",
                            "Unapproved work remains paused.",
                            "Communication records use least-disclosure scope.",
                        ],
                        failure_conditions=[
                            "A task is activated without approval or an authorized owner."
                        ],
                        dependencies=[ownership_id],
                    ),
                    Goal(
                        goal_id=closure_id,
                        run_id=run_id,
                        parent_goal_id=top_goal.goal_id,
                        assigned_agent="closure_revalidation",
                        objective=(
                            "Evaluate submitted closure evidence through targeted "
                            "revalidation and issue lifecycle transitions."
                        ),
                        goal_type="revalidate_issue_closure",
                        priority="critical",
                        constraints=top_goal.constraints,
                        success_conditions=[
                            "Submitted evidence alone does not close any issue.",
                            "Closure decisions require registration, classification, integrity, claim, and policy checks.",
                            "Resolved, rejected, reopened, or waiting states are explicit.",
                        ],
                        failure_conditions=["A gap is marked resolved without closure evidence."],
                        dependencies=[liaison_id],
                    ),
                    Goal(
                        goal_id=package_id,
                        run_id=run_id,
                        parent_goal_id=top_goal.goal_id,
                        assigned_agent="audit_package_composer",
                        objective=(
                            "Generate a reproducible draft audit package manifest "
                            "with eligibility, lineage, exclusions, and warnings."
                        ),
                        goal_type="compose_audit_package",
                        priority="high",
                        constraints=top_goal.constraints,
                        success_conditions=[
                            "Package scope is frozen.",
                            "Only eligible evidence is included.",
                            "Manifest, checksums, lineage, exclusions, and unresolved warnings are present.",
                        ],
                        failure_conditions=["A package includes rejected or missing evidence."],
                        dependencies=[closure_id],
                    ),
                    Goal(
                        goal_id=quality_id,
                        run_id=run_id,
                        parent_goal_id=top_goal.goal_id,
                        assigned_agent="adversarial_quality_review",
                        objective=(
                            "Challenge the draft package as a skeptical internal auditor "
                            "before human approval."
                        ),
                        goal_type="challenge_audit_package",
                        priority="critical",
                        constraints=top_goal.constraints,
                        success_conditions=[
                            "Every material claim is challenged.",
                            "Package references are tested.",
                            "Omissions, reuse risks, and reviewer friction are scored.",
                            "A quality status and correction route are produced.",
                        ],
                        failure_conditions=["The package passes despite unsupported material claims."],
                        dependencies=[package_id],
                    ),
                ]
            )
        return goals

    @staticmethod
    def find_runnable_goals(
        goals: list[Goal], completed_goal_ids: set[str]
    ) -> list[Goal]:
        return [
            goal
            for goal in goals
            if goal.status == "created"
            and set(goal.dependencies).issubset(completed_goal_ids)
        ]
