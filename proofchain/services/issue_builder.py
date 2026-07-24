"""Build canonical issue identities from findings, gaps, and claim failures."""

from __future__ import annotations

from proofchain.schemas.claims import ClaimDecision
from proofchain.schemas.gaps import ResolutionPortfolio
from proofchain.schemas.integrity import EvidenceGap, IntegrityFinding
from proofchain.schemas.issues import CanonicalIssue, IssueLedger


def build_issue_ledger(
    *,
    run_id: str,
    findings: list[IntegrityFinding],
    evidence_gaps: list[EvidenceGap],
    claim_decisions: list[ClaimDecision],
    portfolio: ResolutionPortfolio,
) -> IssueLedger:
    issues: dict[str, CanonicalIssue] = {}
    for gap in portfolio.gaps:
        key = "|".join(
            [
                gap.gap_type,
                ",".join(sorted(gap.affected_requirements)),
                ",".join(sorted(gap.affected_claims)),
                gap.description.casefold(),
            ]
        )
        source_finding_ids = [
            source_id for source_id in gap.source_ids if source_id.startswith("FND-")
        ]
        source_gap_ids = [
            source_id for source_id in gap.source_ids if source_id.startswith("GAP-")
        ]
        source_claim_ids = [
            source_id
            for source_id in [*gap.source_ids, *gap.affected_claims]
            if source_id.startswith("CLM-")
        ]
        issue = CanonicalIssue(
            issue_id=f"ISS-{len(issues) + 1:04d}",
            run_id=run_id,
            issue_type=gap.gap_type,
            root_entity_type=gap.source_type,
            root_entity_id=gap.source_ids[0] if gap.source_ids else gap.gap_id,
            source_finding_ids=source_finding_ids,
            source_gap_ids=source_gap_ids,
            source_claim_ids=list(dict.fromkeys(source_claim_ids)),
            affected_requirement_ids=gap.affected_requirements,
            affected_evidence_ids=[],
            severity=gap.severity,
            blocking=gap.blocking,
            status="PLANNED",
            root_cause_id=f"ROOT-{gap.gap_id}" if gap.root_cause else None,
            canonical_key=key,
        )
        issues[key] = issue
        gap.issue_id = issue.issue_id
    claim_failures = [
        decision for decision in claim_decisions if decision.status != "supported"
    ]
    return IssueLedger(
        run_id=run_id,
        raw_findings=len(findings),
        claim_failures=len(claim_failures),
        raw_gaps=len(evidence_gaps),
        canonical_issues=len(issues),
        blocking_canonical_issues=sum(issue.blocking for issue in issues.values()),
        resolution_tasks=0,
        issues=list(issues.values()),
    )
