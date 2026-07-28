from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import Any

from facultyflow import build_daily_plan, build_email_draft, build_event_proposal
from google_workspace import (
    create_google_calendar_event,
    create_gmail_draft,
    list_gmail_digest_messages,
    list_gmail_metadata,
    list_google_calendar_events,
    list_google_calendar_events_between,
    send_gmail_message,
)
from settings import env_bool, load_local_env
from state_store import list_pending_actions, load_state, save_state


IST = timezone(timedelta(hours=5, minutes=30))


def command_center() -> str:
    plan = build_daily_plan("Create the faculty command center brief.")
    dashboard = plan["teacher_dashboard"]
    lines = [
        "FACULTYFLOW COMMAND CENTER",
        f"Readiness: {dashboard['readiness_score']}/100",
        f"Classes: {dashboard['classes_today']} | Replies: {dashboard['important_replies']} | Risks: {dashboard['at_risk_deadlines']}",
        "",
        "Best next moves",
    ]
    scheduled = plan["scheduled_work"][:4]
    lines.extend([f"- {item['start'][11:16]}-{item['end'][11:16]} {item['title']} ({item['priority']})" for item in scheduled] or ["- No planned work yet."])
    lines.extend(
        [
            "",
            "Use /radar for deadlines, /meetings for prep, /live for Google snapshot, /ingest to add data.",
        ]
    )
    return "\n".join(lines)


def deadline_radar() -> str:
    plan = build_daily_plan("Find deadline risks and urgent work.")
    lines = ["DEADLINE RADAR"]
    if plan["deadline_risks"]:
        for risk in plan["deadline_risks"]:
            lines.append(
                f"- HIGH: {risk['task']} by {risk['deadline']} needs {risk['estimated_minutes']}m; "
                f"{risk['available_minutes_before_deadline']}m free."
            )
    else:
        lines.append("- No high-risk deadline detected from current data.")
    if plan["unscheduled_work"]:
        lines.append("")
        lines.append("Postpone or reschedule")
        for item in plan["unscheduled_work"][:5]:
            lines.append(f"- {item['title']} ({item['priority']}, {item['estimated_minutes']}m)")
    return "\n".join(lines)


def meeting_prep() -> str:
    plan = build_daily_plan("Prepare me for today's meetings.")
    fixed = [item for item in plan["fixed_commitments"] if item["category"] in {"meeting", "review"}]
    lines = ["MEETING PREP"]
    if not fixed:
        return "MEETING PREP\n- No meetings or reviews found today."
    for event in fixed:
        lines.extend(
            [
                f"- {event['start'][11:16]} {event['title']}",
                "  Bring: report status, unresolved blockers, next actions.",
                "  Ask: what decision is needed and who owns the follow-up?",
            ]
        )
    return "\n".join(lines)


def live_google_snapshot() -> str:
    calendar_events = list_google_calendar_events(24)
    gmail_messages = list_gmail_metadata(2)
    lines = ["LIVE GOOGLE SNAPSHOT", "", f"Calendar events in next 24h: {len(calendar_events)}"]
    for event in calendar_events[:5]:
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date") or "unknown"
        lines.append(f"- {start}: {event.get('summary', '(no title)')}")
    lines.extend(["", f"Recent Gmail metadata: {len(gmail_messages)}"])
    for email in gmail_messages[:5]:
        lines.append(f"- {email.get('from')}: {email.get('subject')}")
    return "\n".join(lines)


def morning_digest(now: datetime | None = None) -> str:
    local_now = now or datetime.now(IST)
    digest_end = datetime.combine(local_now.date(), time(6, 0), tzinfo=IST)
    if local_now < digest_end:
        digest_end = local_now
    digest_start = digest_end - timedelta(days=1)

    try:
        emails = list_gmail_digest_messages(10)
    except Exception as exc:
        emails = []
        email_error = str(exc)
    else:
        email_error = ""

    try:
        events = list_google_calendar_events_between(
            datetime.combine(local_now.date(), time(0, 0), tzinfo=IST),
            datetime.combine(local_now.date(), time(23, 59), tzinfo=IST),
        )
    except Exception as exc:
        events = []
        calendar_error = str(exc)
    else:
        calendar_error = ""

    plan = build_daily_plan("Create my 6 AM faculty morning digest.")
    lines = [
        "GOOD MORNING FACULTYFLOW BRIEF",
        f"Window: {digest_start.strftime('%d %b %I:%M %p')} to {digest_end.strftime('%d %b %I:%M %p')}",
        "",
        f"Today's calendar items: {len(events)}",
    ]
    for event in events[:6]:
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date") or "unknown"
        lines.append(f"- {start}: {event.get('summary', '(no title)')}")
    if calendar_error:
        lines.append(f"- Calendar read note: {calendar_error}")

    lines.extend(["", f"Unread/important Gmail items: {len(emails)}"])
    for email in emails[:8]:
        labels = ", ".join(email.get("labelIds", [])[:3])
        lines.append(f"- {email.get('from')}: {email.get('subject')} [{labels}]")
        if email.get("snippet"):
            lines.append(f"  {email['snippet'][:140]}")
    if email_error:
        lines.append(f"- Gmail read note: {email_error}")

    lines.extend(
        [
            "",
            "Suggested day focus",
            f"- Readiness score: {plan['teacher_dashboard']['readiness_score']}/100",
            "- Use /plan for the detailed schedule.",
            "- Use /emailplan to create review blocks from important emails.",
        ]
    )
    return "\n".join(lines)


def email_followup_plan() -> str:
    emails = list_gmail_digest_messages(4)
    if not emails:
        return "EMAIL FOLLOW-UP PLAN\n- No Gmail messages were available from the current read."
    state = load_state()
    now = datetime.now(IST)
    proposed_start = datetime.combine(now.date(), time(8, 30), tzinfo=IST)
    if now >= proposed_start:
        proposed_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    proposed_end = proposed_start + timedelta(minutes=30)
    subjects = [email.get("subject") or "No subject" for email in emails[:4]]
    action = {
        "id": f"pending-email-review-{len(state['pending_actions']) + 1:04d}",
        "type": "calendar_event_proposal",
        "title": "Review important unread emails",
        "start": proposed_start.isoformat(timespec="minutes"),
        "end": proposed_end.isoformat(timespec="minutes"),
        "reason": "Review important/unread Gmail messages: " + "; ".join(subjects),
        "source_email_ids": [email.get("id") for email in emails[:4]],
        "status": "awaiting_confirmation",
        "confirmation_required": True,
    }
    state["pending_actions"].append(action)
    save_state(state)
    lines = [
        "EMAIL FOLLOW-UP PLAN",
        "",
        "What I found",
    ]
    for index, email in enumerate(emails[:4], start=1):
        subject = shorten(email.get("subject") or "No subject", 72)
        sender = shorten(email.get("from") or "Unknown sender", 54)
        snippet = shorten(email.get("snippet") or "", 95)
        labels = ", ".join(email.get("labelIds", [])[:2])
        lines.extend(
            [
                f"{index}. {subject}",
                f"   From: {sender}",
                f"   Tags: {labels or 'none'}",
            ]
        )
        if snippet:
            lines.append(f"   Note: {snippet}")
        lines.append("")
    lines.extend(
        [
            "Prepared action",
            f"- {action['id']}: Review these emails",
            f"- Time: {action['start']} to {action['end']}",
            "",
            "Nothing was added to Calendar yet.",
            "Use /confirm " + action["id"] + " only if this review block looks correct.",
        ]
    )
    return "\n".join(lines)


def create_ready_gmail_draft(to: str, subject: str, purpose: str) -> dict[str, Any]:
    body = compose_email_body(purpose)
    result = create_gmail_draft(to=to, subject=subject, body=body)
    return {
        **result,
        "to": to,
        "subject": subject,
        "body": body,
    }


def compose_email_body(purpose: str) -> str:
    return (
        "Dear Sir/Madam,\n\n"
        f"{purpose.strip()}\n\n"
        "Regards,\n"
        "Harish"
    )


def format_gmail_draft_result(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return (
            "GMAIL DRAFT NOT CREATED\n\n"
            f"Reason: {result.get('message', result.get('reason', 'Unknown issue'))}\n\n"
            "The draft text is ready locally, but Gmail needs updated OAuth permission before I can place it in Drafts."
        )
    return (
        "GMAIL DRAFT READY\n\n"
        f"To: {result['to']}\n"
        f"Subject: {result['subject']}\n"
        f"Draft ID: {result['draft_id']}\n\n"
        "It is saved in your Gmail Drafts folder. Please review it in Gmail before sending."
    )


def shorten(value: str, limit: int) -> str:
    clean = " ".join(str(value).split())
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 3)] + "..."


def automation_blueprint() -> str:
    return (
        "AUTOMATION BLUEPRINT\n"
        "1. Morning: /brief sends teaching plan and risks.\n"
        "2. Before class: reminder proposal from calendar events.\n"
        "3. Midday: /radar checks deadline risk.\n"
        "4. End of day: pending work becomes tomorrow's ingest draft.\n"
        "5. Writes: /confirm <id> only after reviewing exact calendar/email draft.\n\n"
        "AWS deployment can host this later, but local Telegram polling is the lowest-cost first automation."
    )


def draft_reply(to: str, subject: str, purpose: str) -> dict[str, Any]:
    draft = build_email_draft(to=to, subject=subject, purpose=purpose)
    return _replace_or_add_pending(draft)


def draft_focus_event(title: str, start: str, end: str, reason: str) -> dict[str, Any]:
    proposal = build_event_proposal(title=title, start=start, end=end, reason=reason)
    return _replace_or_add_pending(proposal)


def confirm_action(action_id: str) -> dict[str, Any]:
    load_local_env()
    state = load_state()
    actions = state["pending_actions"]
    action = next((item for item in actions if item.get("id") == action_id), None)
    if not action:
        return {"ok": False, "message": f"No pending action found for {action_id}."}
    if not env_bool("FACULTYFLOW_ENABLE_GOOGLE_WRITES", False):
        return {
            "ok": False,
            "message": "Google writes are disabled. Set FACULTYFLOW_ENABLE_GOOGLE_WRITES=true only after you are ready.",
            "action": action,
        }
    if action.get("type") == "calendar_event_proposal":
        receipt = create_google_calendar_event(action["title"], action["start"], action["end"], action.get("reason", ""))
    elif action.get("type") == "email_draft":
        receipt = send_gmail_message(action["to"], action["subject"], action["body"])
    else:
        return {"ok": False, "message": f"Action type {action.get('type')} is not executable.", "action": action}
    action["status"] = "executed"
    action["executed_at"] = datetime.now().isoformat(timespec="seconds")
    action["receipt"] = receipt
    save_state(state)
    return {"ok": True, "message": f"Executed {action_id}.", "receipt": receipt}


def cancel_action(action_id: str) -> dict[str, Any]:
    state = load_state()
    before = len(state["pending_actions"])
    state["pending_actions"] = [item for item in state["pending_actions"] if item.get("id") != action_id]
    save_state(state)
    return {"ok": len(state["pending_actions"]) < before, "message": f"Cancelled {action_id}."}


def _replace_or_add_pending(action: dict[str, Any]) -> dict[str, Any]:
    state = load_state()
    action = dict(action)
    action["id"] = f"pending-{len(state['pending_actions']) + 1:04d}"
    action["created_at"] = datetime.now().isoformat(timespec="seconds")
    action["status"] = "awaiting_confirmation"
    state["pending_actions"].append(action)
    save_state(state)
    return action


def format_pending_actions() -> str:
    actions = list_pending_actions()
    if not actions:
        return "No pending actions. Run /plan, /draftmail, or /focusdraft to create proposals."
    lines = ["PENDING ACTIONS"]
    for action in actions:
        label = action.get("title") or action.get("subject") or action.get("message") or action.get("type")
        lines.append(f"- {action['id']}: {label} [{action.get('type')}]")
    lines.append("\nUse /confirm <id> or /cancel <id>.")
    return "\n".join(lines)
