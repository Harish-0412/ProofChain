"""Shared component, model, policy, and observability registration."""

from __future__ import annotations

from proofchain.core.paths import (
    get_component_registry_path,
    get_model_governance_manifest_path,
    get_observability_metrics_path,
    get_policy_manifest_path,
)
from proofchain.repositories.json_store import AtomicJsonStore
from proofchain.schemas.components import ComponentDeclaration, ComponentRegistry
from proofchain.schemas.runtime_governance import (
    AgentExecutionProfile,
    ModelGovernanceManifest,
)
from proofchain.services.policy_loader import GovernancePolicyCatalog


def register_governed_agents(
    *,
    run_id: str,
    agents: dict[str, list[str]],
    description: str,
    store: AtomicJsonStore | None = None,
) -> ComponentRegistry:
    store = store or AtomicJsonStore()
    payload = store.read(
        get_component_registry_path(run_id),
        default={"run_id": run_id, "components": []},
    )
    registry = ComponentRegistry.model_validate(payload)
    existing = {item.component_id for item in registry.components}
    for agent_name, specialists in agents.items():
        if agent_name not in existing:
            registry.components.append(
                ComponentDeclaration(
                    component_id=agent_name,
                    component_type="goal_agent",
                    has_independent_goal=True,
                    has_plan=True,
                    has_memory=True,
                    can_replan=True,
                    description=description,
                )
            )
            existing.add(agent_name)
        for specialist in specialists:
            if specialist in existing:
                continue
            registry.components.append(
                ComponentDeclaration(
                    component_id=specialist,
                    component_type="deterministic_specialist_module",
                    parent_agent=agent_name,
                    description="Deterministic specialist executed by its parent goal agent.",
                )
            )
            existing.add(specialist)
    store.write(get_component_registry_path(run_id), registry)

    catalog = GovernancePolicyCatalog.load()
    store.write(get_policy_manifest_path(run_id), catalog.manifest(run_id))
    model_payload = store.read(get_model_governance_manifest_path(run_id), default=None)
    profiles = (
        ModelGovernanceManifest.model_validate(model_payload).profiles
        if model_payload
        else []
    )
    profile_names = {profile.agent_name for profile in profiles}
    profiles.extend(
        AgentExecutionProfile(
            agent_name=agent_name,
            execution_mode="deterministic",
            external_model_calls=0,
            high_impact_actions_require_approval=True,
            fallback_behavior="deterministic_only",
        )
        for agent_name in agents
        if agent_name not in profile_names
    )
    store.write(
        get_model_governance_manifest_path(run_id),
        ModelGovernanceManifest(
            run_id=run_id,
            policy_fingerprint=catalog.fingerprint,
            profiles=profiles,
            total_external_model_calls=sum(
                profile.external_model_calls for profile in profiles
            ),
        ),
    )
    observability = store.read(get_observability_metrics_path(run_id), default={})
    if observability:
        observability["primary_agent_count"] = sum(
            item.component_type == "goal_agent" for item in registry.components
        )
        observability["specialist_module_count"] = sum(
            item.component_type == "deterministic_specialist_module"
            for item in registry.components
        )
        store.write(get_observability_metrics_path(run_id), observability)
    return registry

