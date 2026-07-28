"""ProofChain UI Gateway — security: command allowlist.

Only declared CLI commands may be dispatched through the gateway.
Any other command name will be rejected with HTTP 400 before it
ever reaches the subprocess layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional


# ------------------------------------------------------------------ #
# Allowlisted command descriptors
# ------------------------------------------------------------------ #

@dataclass(frozen=True)
class AllowedCommand:
    """Metadata for a single allowlisted command."""

    # CLI subcommand token, e.g. "run-pipeline"
    cli_name: str

    # URL path segment, e.g. "run-pipeline"  → POST /ui-api/commands/run-pipeline
    route_slug: str

    # Human-readable description (shown in /ui-api/health)
    description: str

    # Which JSON body keys may be forwarded as CLI arguments.
    # Values are validated as non-empty strings before shell-escaping.
    allowed_body_keys: FrozenSet[str] = field(default_factory=frozenset)

    # Body keys that are required (subset of allowed_body_keys).
    required_body_keys: FrozenSet[str] = field(default_factory=frozenset)

    # Body keys whose values are treated as repeatable flags (--key value
    # passed multiple times when the JSON value is a list).
    list_body_keys: FrozenSet[str] = field(default_factory=frozenset)

    # Body keys emitted positionally before optional CLI flags.
    positional_body_keys: tuple[str, ...] = ()


ALLOWED_COMMANDS: List[AllowedCommand] = [
    AllowedCommand(
        cli_name="run-complete",
        route_slug="run-complete",
        description="Run and validate the complete 22-agent governed lifecycle.",
        allowed_body_keys=frozenset({
            "source", "departments", "academic_year", "requirements",
            "requested_by", "claim", "objective", "max_agent_rounds",
            "max_replans", "require_human_approval", "backend", "database_url",
            "tenant_id", "department_id", "query",
        }),
        required_body_keys=frozenset({"source", "departments"}),
        list_body_keys=frozenset({"source", "departments", "requirements", "claim"}),
    ),
    AllowedCommand(
        cli_name="run-pipeline",
        route_slug="run-pipeline",
        description="Run collection, classification, and integrity pipeline.",
        allowed_body_keys=frozenset({
            "source", "departments", "academic_year", "requirements",
            "requested_by", "claim", "objective", "max_agent_rounds",
            "max_replans", "require_human_approval",
        }),
        required_body_keys=frozenset({"departments"}),
        list_body_keys=frozenset({"source", "departments", "requirements", "claim"}),
    ),
    AllowedCommand(
        cli_name="validate-run",
        route_slug="validate-run",
        description="Validate artifact presence, hashes, and synchronization links.",
        allowed_body_keys=frozenset({"run_id"}),
        required_body_keys=frozenset({"run_id"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="validate-agentic-run",
        route_slug="validate-agentic-run",
        description="Validate cognition, proof, state, and decision-ledger artifacts.",
        allowed_body_keys=frozenset({"run_id"}),
        required_body_keys=frozenset({"run_id"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="approve-decision",
        route_slug="approve-decision",
        description="Record an explicit human approval or rejection.",
        allowed_body_keys=frozenset({
            "run_id", "type", "target", "decision", "decided_by", "reason", "evidence",
        }),
        required_body_keys=frozenset({"run_id", "type", "target", "decision", "decided_by", "reason"}),
        list_body_keys=frozenset({"evidence"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="activate-resolution-task",
        route_slug="activate-resolution-task",
        description="Activate an approved resolution task.",
        allowed_body_keys=frozenset({"run_id", "gap"}),
        required_body_keys=frozenset({"run_id", "gap"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="record-task-response",
        route_slug="record-task-response",
        description="Record an append-only department task response event.",
        allowed_body_keys=frozenset({"run_id", "task", "response", "artifact", "message", "responder"}),
        required_body_keys=frozenset({"run_id", "task", "response"}),
        list_body_keys=frozenset({"artifact"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="revalidate-closure",
        route_slug="revalidate-closure",
        description="Report the current closure revalidation artifact for a task.",
        allowed_body_keys=frozenset({"run_id", "task"}),
        required_body_keys=frozenset({"run_id", "task"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="build-audit-package",
        route_slug="build-audit-package",
        description="Report the current generated audit package manifest.",
        allowed_body_keys=frozenset({"run_id", "requirement"}),
        required_body_keys=frozenset({"run_id", "requirement"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="review-audit-package",
        route_slug="review-audit-package",
        description="Report the current adversarial quality review artifact.",
        allowed_body_keys=frozenset({"run_id", "package"}),
        required_body_keys=frozenset({"run_id", "package"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="resume-run",
        route_slug="resume-run",
        description="Record a run-resume event for replayable coordination.",
        allowed_body_keys=frozenset({"run_id"}),
        required_body_keys=frozenset({"run_id"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="replay-run",
        route_slug="replay-run",
        description="List replayable workflow events for a run.",
        allowed_body_keys=frozenset({"run_id"}),
        required_body_keys=frozenset({"run_id"}),
        positional_body_keys=("run_id",),
    ),
    AllowedCommand(
        cli_name="health-check",
        route_slug="health-check",
        description="Inspect proof, event, database, and adapter health.",
        allowed_body_keys=frozenset({"run_id"}),
    ),
]

# ------------------------------------------------------------------ #
# Fast-lookup index by route slug
# ------------------------------------------------------------------ #

COMMAND_BY_SLUG: Dict[str, AllowedCommand] = {
    cmd.route_slug: cmd for cmd in ALLOWED_COMMANDS
}

ALLOWED_SLUGS: FrozenSet[str] = frozenset(COMMAND_BY_SLUG.keys())


def get_command(slug: str) -> Optional[AllowedCommand]:
    """Return the AllowedCommand for *slug*, or None if not allowlisted."""
    return COMMAND_BY_SLUG.get(slug)


def is_allowed(slug: str) -> bool:
    """Return True if *slug* maps to an allowlisted command."""
    return slug in COMMAND_BY_SLUG
