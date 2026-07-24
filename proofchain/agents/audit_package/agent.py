"""Goal-driven Audit Package Composer and Evidence Manifest Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from proofchain.agentic.base_goal_agent import BaseGoalAgent
from proofchain.agents.audit_package.evidence_orderer import EvidenceOrderingSpecialist
from proofchain.agents.audit_package.evidence_selector import EvidenceSelectionSpecialist
from proofchain.agents.audit_package.index_builder import IndexBuilderSpecialist
from proofchain.agents.audit_package.narrative_composer import NarrativeComposerSpecialist
from proofchain.agents.audit_package.package_assembler import PackageAssemblySpecialist
from proofchain.agents.audit_package.package_integrity import PackageIntegritySpecialist
from proofchain.agents.audit_package.privacy_redactor import PrivacyRedactionSpecialist
from proofchain.agents.audit_package.scope_resolver import PackageScopeSpecialist
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.repositories.json_lifecycle_repository import JsonLifecycleRepository
from proofchain.schemas.agentic import AgentPlan, CompletionDecision, PlanStep
from proofchain.schemas.packages import (
    AuditPackageAgentResult,
    AuditPackageInput,
    AuditPackageManifest,
)


class AuditPackageComposerAgent(
    BaseGoalAgent[AuditPackageInput, AuditPackageAgentResult]
):
    agent_name = "audit_package_composer"
    agent_version = "1.0.0"

    def __init__(self, *, repository=None, tracer=None):
        super().__init__(tracer=tracer)
        self.repository = repository or JsonLifecycleRepository()
        self.events = JsonEventRepository()
        self.scope = PackageScopeSpecialist()
        self.selector = EvidenceSelectionSpecialist()
        self.orderer = EvidenceOrderingSpecialist()
        self.narrative = NarrativeComposerSpecialist()
        self.index = IndexBuilderSpecialist()
        self.redactor = PrivacyRedactionSpecialist()
        self.assembler = PackageAssemblySpecialist()
        self.integrity = PackageIntegritySpecialist()
        self._state: dict = {}

    def validate_input(self, input_data):
        return None

    def execute(self, input_data):
        self._state = {}
        self._scope(input_data)
        self._select(input_data)
        self._order()
        self._compose(input_data)
        self._index(input_data)
        self._redact()
        self._assemble(input_data)
        return self._verify(input_data)

    def validate_output(self, output_data):
        return None

    def create_goal_plan(self, goal, input_data, revision):
        token = uuid4().hex[:8].upper()
        specs = [
            ("resolve_package_scope", "Freeze department, requirement, year, and claim scope."),
            ("select_package_evidence", "Select eligible current evidence and explain exclusions."),
            ("order_evidence", "Order evidence for reviewer usability."),
            ("compose_narrative", "Create grounded claim summaries."),
            ("build_cross_reference_index", "Build claim-to-evidence lineage."),
            ("apply_redaction_policy", "Record privacy policy without changing originals."),
            ("assemble_manifest", "Create reproducible package manifest hash."),
            ("verify_package_integrity", "Validate references, files, and lineage."),
        ]
        return AgentPlan(
            plan_id=f"PLAN-PACKAGE-{token}-R{revision}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            revision=revision,
            rationale="Generate a traceable draft audit package using only eligible evidence.",
            steps=[
                PlanStep(
                    step_id=f"STEP-{token}-{index:02d}",
                    sequence=index,
                    objective=objective,
                    proposed_tool=tool,
                    expected_observation=f"{tool} records package state.",
                    completion_condition="The package manifest remains reproducible.",
                )
                for index, (tool, objective) in enumerate(specs, 1)
            ],
            dependencies=goal.dependencies,
            expected_outputs=["audit_package_manifest.json"],
            status="approved",
        )

    def agentic_tools(self, input_data):
        return {
            "resolve_package_scope": lambda: self._scope(input_data),
            "select_package_evidence": lambda: self._select(input_data),
            "order_evidence": self._order,
            "compose_narrative": lambda: self._compose(input_data),
            "build_cross_reference_index": lambda: self._index(input_data),
            "apply_redaction_policy": self._redact,
            "assemble_manifest": lambda: self._assemble(input_data),
            "verify_package_integrity": lambda: self._verify(input_data),
        }

    def _scope(self, input_data):
        value = self.scope.run(input_data)
        self._state["scope"] = value
        return value

    def _select(self, input_data):
        eligible, excluded = self.selector.run(input_data.evidence_records)
        self._state.update(eligible=eligible, excluded=excluded)
        return {"eligible": len(eligible), "excluded": len(excluded)}

    def _order(self):
        self._state["eligible"] = self.orderer.run(self._state["eligible"])
        return self._state["eligible"]

    def _compose(self, input_data):
        value = self.narrative.run(input_data.claim_decisions)
        self._state["narrative"] = value
        return value

    def _index(self, input_data):
        value = self.index.run(input_data.claim_decisions)
        self._state["lineage"] = value
        return value

    def _redact(self):
        value = self.redactor.run(self._state["eligible"])
        self._state["eligible"] = value
        return value

    def _assemble(self, input_data):
        unresolved = [
            issue.issue_id
            for issue in input_data.canonical_issues
            if issue.status not in {"RESOLVED", "WAIVED_WITH_APPROVAL"}
        ]
        manifest = AuditPackageManifest(
            package_id=f"PKG-{input_data.workflow.run_id}",
            run_id=input_data.workflow.run_id,
            requirement_ids=self._state["scope"]["requirement_ids"],
            departments=self._state["scope"]["departments"],
            academic_year=self._state["scope"]["academic_year"],
            eligible_evidence=self._state["eligible"],
            excluded_evidence=self._state["excluded"],
            claim_ids=[decision.claim_id for decision in input_data.claim_decisions],
            unresolved_warning_issue_ids=unresolved,
            package_lineage=self._state["lineage"],
        )
        self._state["manifest"] = self.assembler.run(manifest)
        return self._state["manifest"]

    def _verify(self, input_data):
        started = datetime.now(tz=timezone.utc)
        errors = self.integrity.run(self._state["manifest"])
        warnings = [
            "Package contains unresolved warning disclosures."
        ] if self._state["manifest"].unresolved_warning_issue_ids else []
        result = AuditPackageAgentResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if warnings else "completed",
            input_count=len(input_data.evidence_records),
            success_count=len(self._state["manifest"].eligible_evidence),
            warning_count=len(warnings),
            failure_count=len(errors),
            manifest=self._state["manifest"],
            input_snapshot_hash=self.compute_input_hash(input_data),
            warnings=warnings,
            errors=[{"message": item} for item in errors],
            started_at=started,
        )
        artifact = self.repository.save_package(result)
        self.events.append(
            run_id=result.run_id,
            event_type="PackageGenerated",
            aggregate_type="audit_package",
            aggregate_id=result.manifest.package_id,
            actor=self.agent_name,
            payload={"package_hash": result.manifest.package_hash, "status": result.manifest.status},
        )
        result.output_reference = artifact.path
        result.output_snapshot_hash = artifact.sha256
        return result

    def evaluate_goal_completion(self, goal, output, observations):
        valid = bool(output) and output.failure_count == 0
        return CompletionDecision(
            decision_id=f"DEC-{uuid4().hex[:12].upper()}",
            run_id=goal.run_id,
            goal_id=goal.goal_id,
            agent_name=self.agent_name,
            goal_satisfied=valid,
            success_conditions_met=goal.success_conditions if valid else [],
            success_conditions_unmet=[] if valid else goal.success_conditions,
            blockers=[error["message"] for error in output.errors] if output else [],
            confidence=0.9 if valid else 0.0,
            final_status="completed_with_warnings" if output and output.warning_count else "completed" if valid else "failed",
            explanation=(
                f"Generated draft package manifest {output.manifest.package_id if output else 'none'} "
                "with reproducible hash and unresolved warnings disclosed."
            ),
            supporting_artifacts=[output.output_reference] if output and output.output_reference else [],
        )
