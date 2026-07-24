"""Deterministic completion policies that validate agent completion claims."""

from __future__ import annotations

from uuid import uuid4

from proofchain.schemas.agentic import CompletionDecision, Goal, Observation
from proofchain.schemas.classification import ClassificationAgentResult
from proofchain.schemas.evidence import CollectorAgentResult
from proofchain.schemas.integrity import IntegrityAgentResult


def _artifacts(observations: list[Observation]) -> list[str]:
    return list(
        dict.fromkeys(
            reference
            for observation in observations
            for reference in observation.source_references
        )
    )


def evaluate_collector(
    goal: Goal,
    output: CollectorAgentResult | None,
    observations: list[Observation],
) -> CompletionDecision:
    if output is None or not output.records:
        return _decision(
            goal,
            "evidence_collector",
            status="failed",
            satisfied=False,
            confidence=0.0,
            unmet=goal.success_conditions,
            blockers=["No readable evidence was registered."],
            explanation="The acquisition goal cannot proceed without registered evidence.",
            artifacts=_artifacts(observations),
        )
    warnings = [*output.warnings, *(error.message for error in output.errors)]
    status = "completed_with_warnings" if warnings else "completed"
    return _decision(
        goal,
        "evidence_collector",
        status=status,
        satisfied=True,
        confidence=0.9 if warnings else 1.0,
        met=goal.success_conditions,
        questions=warnings,
        explanation=(
            f"Registered {len(output.records)} evidence records with checksums. "
            f"{len(warnings)} acquisition warnings remain disclosed."
        ),
        artifacts=_artifacts(observations),
    )


def evaluate_classification(
    goal: Goal,
    output: ClassificationAgentResult | None,
    observations: list[Observation],
) -> CompletionDecision:
    if output is None or output.status == "failed":
        return _decision(
            goal,
            "evidence_classification",
            status="failed",
            satisfied=False,
            confidence=0.0,
            unmet=goal.success_conditions,
            blockers=["No eligible classification result was produced."],
            explanation="The understanding goal failed deterministic validation.",
            artifacts=_artifacts(observations),
        )
    unresolved = [
        record.evidence_id
        for record in output.records
        if record.requires_human_review or not record.requirement_mappings
    ]
    if unresolved:
        return _decision(
            goal,
            "evidence_classification",
            status="needs_human_review",
            satisfied=False,
            confidence=0.5,
            met=goal.success_conditions[:1],
            unmet=goal.success_conditions[1:],
            questions=[
                f"Resolve classification or mapping ambiguity for {evidence_id}"
                for evidence_id in unresolved
            ],
            explanation=(
                f"Processed {len(output.records)} items, but {len(unresolved)} items "
                "remain too ambiguous for an autonomous positive completion claim."
            ),
            artifacts=_artifacts(observations),
        )
    status = (
        "completed_with_warnings"
        if output.warning_count or output.warnings
        else "completed"
    )
    return _decision(
        goal,
        "evidence_classification",
        status=status,
        satisfied=True,
        confidence=0.9 if status == "completed_with_warnings" else 1.0,
        met=goal.success_conditions,
        questions=output.warnings,
        explanation=(
            f"Every one of {len(output.records)} evidence records has an explicit "
            "extraction, classification, and mapping state."
        ),
        artifacts=_artifacts(observations),
    )


def evaluate_integrity(
    goal: Goal,
    output: IntegrityAgentResult | None,
    observations: list[Observation],
) -> CompletionDecision:
    if output is None or output.status == "failed":
        return _decision(
            goal,
            "evidence_integrity",
            status="failed",
            satisfied=False,
            confidence=0.0,
            unmet=goal.success_conditions,
            blockers=["Integrity tools did not produce a defensibility result."],
            explanation="The verification goal failed before a defensible decision was possible.",
            artifacts=_artifacts(observations),
        )
    blockers = [
        f"{finding.rule_id}: {finding.title}"
        for finding in output.findings
        if finding.blocking
    ]
    blockers.extend(
        f"{gap.requirement_id}: {gap.description}"
        for gap in output.gaps
        if gap.blocking
    )
    if blockers:
        return _decision(
            goal,
            "evidence_integrity",
            status="blocked",
            satisfied=False,
            confidence=1.0,
            met=goal.success_conditions,
            blockers=blockers,
            explanation=(
                "All applicable checks ran and produced a not-yet-defensible decision "
                f"with {len(blockers)} disclosed blocking issues."
            ),
            artifacts=_artifacts(observations),
        )
    status = (
        "completed_with_warnings"
        if output.findings or output.gaps or output.warnings
        else "completed"
    )
    return _decision(
        goal,
        "evidence_integrity",
        status=status,
        satisfied=True,
        confidence=1.0,
        met=goal.success_conditions,
        questions=[
            *(finding.title for finding in output.findings),
            *(gap.description for gap in output.gaps),
        ],
        explanation=(
            f"Integrity evaluated {len(output.bundles)} bundles and found no "
            "undisclosed blocking condition."
        ),
        artifacts=_artifacts(observations),
    )


def _decision(
    goal: Goal,
    agent_name: str,
    *,
    status: str,
    satisfied: bool,
    confidence: float,
    explanation: str,
    met: list[str] | None = None,
    unmet: list[str] | None = None,
    blockers: list[str] | None = None,
    questions: list[str] | None = None,
    artifacts: list[str] | None = None,
) -> CompletionDecision:
    return CompletionDecision(
        decision_id=f"DEC-{uuid4().hex[:12].upper()}",
        run_id=goal.run_id,
        goal_id=goal.goal_id,
        agent_name=agent_name,
        goal_satisfied=satisfied,
        success_conditions_met=met or [],
        success_conditions_unmet=unmet or [],
        blockers=blockers or [],
        unresolved_questions=questions or [],
        confidence=confidence,
        final_status=status,
        explanation=explanation,
        supporting_artifacts=artifacts or [],
    )
