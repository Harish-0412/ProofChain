from __future__ import annotations

import json
from pathlib import Path

from proofchain.services.run_projection import PRIMARY_AGENT_ORDER, RunProjectionService


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_projection_uses_persisted_truth_and_exposes_22_agents(tmp_path: Path):
    run_id = "RUN-PROJECTION"
    run_dir = tmp_path / run_id
    _write(
        run_dir / "run_manifest.json",
        {
            "status": "blocked",
            "workflow": {
                "department_scope": ["CSE"],
                "academic_year": "2025-2026",
            },
        },
    )
    _write(
        run_dir / "pipeline_result.json",
        {
            "run_id": run_id,
            "status": "blocked",
            "department_scope": ["CSE"],
            "academic_year": "2025-2026",
            "blocking_canonical_issues": 1,
        },
    )
    _write(
        run_dir / "gap_resolution_portfolio.json",
        {
            "portfolio": {
                "current_verified_readiness": 73,
                "projected_readiness": 96,
                "projection_type": "counterfactual",
                "projection_assumptions": ["All blocking gaps are resolved."],
            }
        },
    )
    _write(
        run_dir / "canonical_issues.json",
        {
            "issues": [
                {
                    "issue_id": "ISS-001",
                    "issue_type": "missing_required_document",
                    "severity": "high",
                    "blocking": True,
                    "status": "OPEN",
                    "canonical_key": "missing|required",
                    "affected_requirement_ids": ["C3.2.1"],
                    "source_gap_ids": [],
                }
            ]
        },
    )
    _write(
        run_dir / "component_registry.json",
        {
            "components": [
                {
                    "component_id": name,
                    "component_type": "goal_agent",
                    "description": "Primary governed goal agent.",
                }
                for name in PRIMARY_AGENT_ORDER
            ]
        },
    )

    projector = RunProjectionService(tmp_path)
    summary = projector.run_summary(run_id)
    agents = projector.agents(run_id)

    assert summary["status"] == "blocked"
    assert summary["verifiedReadiness"] == 73
    assert summary["projectedReadiness"] == 96
    assert summary["projectionType"] == "counterfactual"
    assert summary["blockingIssues"] == 1
    assert len(agents) == 22
    assert {item["name"] for item in agents}


def test_agent_detail_projects_cognition_and_governance(tmp_path: Path):
    run_id = "RUN-DETAIL"
    run_dir = tmp_path / run_id
    _write(run_dir / "run_manifest.json", {"status": "completed"})
    _write(
        run_dir / "component_registry.json",
        {
            "components": [
                {
                    "component_id": name,
                    "component_type": "goal_agent",
                    "description": "Primary ProofChain governed goal agent.",
                }
                for name in PRIMARY_AGENT_ORDER
            ]
        },
    )
    _write(
        run_dir / "collector" / "plans.json",
        [
            {
                "plan_id": "PLAN-1",
                "goal_id": "GOAL-1",
                "status": "completed",
                "steps": [
                    {
                        "step_id": "STEP-1",
                        "sequence": 1,
                        "objective": "Register evidence.",
                        "status": "completed",
                    }
                ],
            }
        ],
    )
    _write(
        run_dir / "collector" / "completion_decision.json",
        {
            "decision_id": "DEC-1",
            "final_status": "completed",
            "goal_satisfied": True,
            "success_conditions_met": ["Evidence registered."],
        },
    )

    projector = RunProjectionService(tmp_path)
    detail = projector.agent_detail(run_id, 1)

    assert detail is not None
    assert detail["agent"]["slug"] == "evidence_collector"
    assert detail["plan"]["steps"][0]["objective"] == "Register evidence."
    assert detail["completion"]["goalSatisfied"] is True
    assert detail["runtimeDirectory"] == "collector"
