"""Agent 17: backward-compatible schema analysis and immutable migration planning."""

from __future__ import annotations

from proofchain.agents.production_base import ProductionGoalAgent
from proofchain.repositories.json_event_repository import JsonEventRepository
from proofchain.schemas.institutional import (
    SchemaEvolutionInput,
    SchemaEvolutionResult,
)
from proofchain.services.schema_evolution import (
    analyze_compatibility,
    convert_artifacts,
)


class SchemaEvolutionAgent(
    ProductionGoalAgent[SchemaEvolutionInput, SchemaEvolutionResult]
):
    agent_name = "schema_evolution"
    agent_version = "1.0.0"
    expected_artifact = "schema_evolution_report.json"
    tool_specs = (
        (
            "read_schema_registry",
            "Resolve current and target schema versions.",
            "Both schema contracts are available.",
        ),
        (
            "analyze_schema_compatibility",
            "Detect breaking field and type changes.",
            "Compatibility and migration requirements are explicit.",
        ),
        (
            "plan_immutable_migration",
            "Plan mappings and defaults without modifying originals.",
            "Historical artifacts remain immutable.",
        ),
        (
            "convert_artifact_copies",
            "Convert copies and calculate before-and-after hashes.",
            "Converted artifacts preserve original provenance.",
        ),
        (
            "evaluate_schema_deployment",
            "Gate deployment on compatibility and human approval.",
            "An explainable deployment decision is persisted.",
        ),
    )

    def execute(self, input_data):
        self._state = {}
        self._read(input_data)
        self._analyze(input_data)
        self._plan(input_data)
        self._convert(input_data)
        return self._complete(input_data)

    def agentic_tools(self, input_data):
        self._state = {}
        return {
            "read_schema_registry": lambda: self._read(input_data),
            "analyze_schema_compatibility": lambda: self._analyze(input_data),
            "plan_immutable_migration": lambda: self._plan(input_data),
            "convert_artifact_copies": lambda: self._convert(input_data),
            "evaluate_schema_deployment": lambda: self._complete(input_data),
        }

    def _read(self, input_data):
        return {
            "status": "completed",
            "schema": input_data.schema_name,
            "current": input_data.current_version,
            "target": input_data.target_version,
        }

    def _analyze(self, input_data):
        compatibility, breaking, steps = analyze_compatibility(
            input_data.current_schema, input_data.target_schema
        )
        self._state.update(
            compatibility=compatibility, breaking=breaking, steps=steps
        )
        return {
            "status": "completed_with_warnings" if breaking else "completed",
            "compatibility": compatibility,
            "breaking_changes": breaking,
        }

    def _plan(self, input_data):
        unresolved = []
        for change in self._state["breaking"]:
            if change.startswith("New required field: "):
                field = change.removeprefix("New required field: ")
                if field not in input_data.default_values and field not in input_data.field_mappings.values():
                    unresolved.append(field)
            if change.startswith("Field type changed: "):
                field = change.removeprefix("Field type changed: ").split(" ", 1)[0]
                if field not in input_data.field_mappings:
                    unresolved.append(field)
        self._state["unresolved"] = sorted(set(unresolved))
        return {
            "status": "completed_with_warnings" if unresolved else "completed",
            "unresolved": self._state["unresolved"],
        }

    def _convert(self, input_data):
        converted = convert_artifacts(
            input_data.artifacts,
            input_data.target_version,
            input_data.field_mappings,
            input_data.default_values,
        )
        self._state["converted"] = converted
        return {"status": "completed", "converted": len(converted)}

    def _complete(self, input_data):
        unresolved = self._state["unresolved"]
        compatibility = (
            "incompatible" if unresolved else self._state["compatibility"]
        )
        if unresolved:
            deployment = "BLOCK"
        elif input_data.deployment_requested and not input_data.human_approval_id:
            deployment = "NEEDS_HUMAN_APPROVAL"
        else:
            deployment = "PASS"
        warnings = [
            *self._state["breaking"],
            *[f"Unresolved migration field: {item}" for item in unresolved],
        ]
        result = SchemaEvolutionResult(
            run_id=input_data.workflow.run_id,
            agent_run_id=self.agent_run_id or "UNKNOWN",
            status="completed_with_warnings" if warnings else "completed",
            input_count=len(input_data.artifacts),
            success_count=len(self._state["converted"]),
            warning_count=len(warnings),
            warnings=warnings,
            schema_name=input_data.schema_name,
            compatibility=compatibility,
            breaking_changes=self._state["breaking"],
            migration_steps=self._state["steps"],
            converted_artifacts=self._state["converted"],
            historical_artifacts_preserved=True,
            deployment_decision=deployment,
        )
        result = self._persist(result)
        JsonEventRepository().append(
            run_id=result.run_id,
            event_type="SchemaEvolutionEvaluated",
            aggregate_type="schema",
            aggregate_id=input_data.schema_name,
            actor=self.agent_name,
            payload={
                "from_version": input_data.current_version,
                "to_version": input_data.target_version,
                "compatibility": compatibility,
                "deployment_decision": deployment,
            },
        )
        return result

