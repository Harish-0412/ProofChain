from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from bedrock_llm import ask_bedrock, is_bedrock_enabled
from facultyflow import (
    build_daily_plan,
    build_email_draft,
    build_event_proposal,
    get_actionable_emails,
    get_calendar_for_day,
    get_pending_tasks,
    get_telegram_setup_requirements,
    introduce_facultyflow,
)
from google_workspace import google_status
from ingestion import ingest_text, ingestion_help
from state_store import list_pending_actions, load_state
from teacher_services import (
    automation_blueprint,
    cancel_action,
    command_center,
    confirm_action,
    deadline_radar,
    format_pending_actions,
    live_google_snapshot,
    meeting_prep,
    morning_digest,
    email_followup_plan,
)

mcp = FastMCP("FacultyFlow", host="0.0.0.0", stateless_http=True)


@mcp.tool()
def introduce() -> str:
    """Introduce FacultyFlow and explain the currently enabled safe local features."""
    return introduce_facultyflow()


@mcp.tool()
def plan_my_day(request: str = "Plan my work for today.", date: Optional[str] = None) -> dict[str, Any]:
    """Create a realistic daily faculty work plan using mock calendar, email, and task data."""
    return build_daily_plan(request=request, requested_date=date)


@mcp.tool()
def get_today_schedule(date: Optional[str] = None) -> list[dict[str, Any]]:
    """Return mock fixed calendar events for the requested day."""
    return get_calendar_for_day(requested_date=date)


@mcp.tool()
def get_tasks(status: str = "Pending") -> list[dict[str, Any]]:
    """Return mock faculty tasks filtered by status."""
    return get_pending_tasks(status=status)


@mcp.tool()
def list_actionable_emails() -> list[dict[str, Any]]:
    """Return actionable mock email summaries without exposing full email bodies."""
    return get_actionable_emails()


@mcp.tool()
def propose_calendar_event(title: str, start: str, end: str, reason: str) -> dict[str, Any]:
    """Create a draft calendar event proposal. This never writes to a real calendar."""
    return build_event_proposal(title=title, start=start, end=end, reason=reason)


@mcp.tool()
def draft_email(to: str, subject: str, purpose: str, tone: str = "professional") -> dict[str, Any]:
    """Create a draft email. This never sends email."""
    return build_email_draft(to=to, subject=subject, purpose=purpose, tone=tone)


@mcp.tool()
def telegram_setup_requirements() -> dict[str, Any]:
    """List the information needed later to connect Telegram safely."""
    return get_telegram_setup_requirements()


@mcp.tool()
def google_workspace_status() -> dict[str, Any]:
    """Show whether Gmail and Google Calendar OAuth are configured."""
    return google_status()


@mcp.tool()
def bedrock_status() -> dict[str, Any]:
    """Show Bedrock configuration without making a model call."""
    return {
        "enabled": is_bedrock_enabled(),
        "default_model": "amazon.nova-micro-v1:0",
        "cost_guardrail": "No model call is made by this status tool.",
    }


@mcp.tool()
def ask_bedrock_guarded(prompt: str, context: str = "") -> dict[str, Any]:
    """Ask Bedrock only if FACULTYFLOW_ENABLE_BEDROCK=true."""
    return ask_bedrock(prompt=prompt, context=context)


@mcp.tool()
def ingest_faculty_data(payload: str, default_date: str = "2026-07-28") -> dict[str, Any]:
    """Ingest tasks, events, email summaries, and preferences from simple text lines."""
    return ingest_text(payload=payload, default_date=default_date)


@mcp.tool()
def ingestion_format_help() -> str:
    """Show the supported text ingestion format."""
    return ingestion_help()


@mcp.tool()
def pending_action_proposals() -> list[dict[str, Any]]:
    """List draft actions awaiting user confirmation."""
    return list_pending_actions()


@mcp.tool()
def local_faculty_state() -> dict[str, Any]:
    """Show counts of local user-ingested data without exposing secrets."""
    state = load_state()
    return {
        "user_tasks": len(state["tasks"]),
        "user_calendar_events": len(state["calendar_events"]),
        "user_email_summaries": len(state["email_summaries"]),
        "preferences": state["preferences"],
        "pending_actions": len(state["pending_actions"]),
    }


@mcp.tool()
def faculty_command_center() -> str:
    """Return a compact faculty operations dashboard."""
    return command_center()


@mcp.tool()
def deadline_risk_radar() -> str:
    """Return urgent deadlines, risks, and rescheduling suggestions."""
    return deadline_radar()


@mcp.tool()
def meeting_preparation_cards() -> str:
    """Return meeting and review preparation cards for today."""
    return meeting_prep()


@mcp.tool()
def live_google_snapshot_tool() -> str:
    """Return live Google Calendar and Gmail metadata summaries."""
    return live_google_snapshot()


@mcp.tool()
def automation_blueprint_tool() -> str:
    """Return the recommended FacultyFlow automation blueprint."""
    return automation_blueprint()


@mcp.tool()
def morning_digest_tool() -> str:
    """Return the Telegram-ready 6 AM FacultyFlow morning digest."""
    return morning_digest()


@mcp.tool()
def email_followup_plan_tool() -> str:
    """Read Gmail metadata and prepare confirmation-gated email follow-up proposals."""
    return email_followup_plan()


@mcp.tool()
def pending_actions_text() -> str:
    """Return pending confirmation actions as Telegram-ready text."""
    return format_pending_actions()


@mcp.tool()
def confirm_pending_action(action_id: str) -> dict[str, Any]:
    """Confirm a pending action. Google writes must be separately enabled."""
    return confirm_action(action_id)


@mcp.tool()
def cancel_pending_action(action_id: str) -> dict[str, Any]:
    """Cancel a pending action proposal."""
    return cancel_action(action_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
