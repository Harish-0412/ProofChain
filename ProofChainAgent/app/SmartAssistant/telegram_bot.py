from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, time as clock_time, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from bedrock_llm import ask_bedrock, is_bedrock_enabled
from facultyflow import (
    build_daily_plan,
    get_actionable_emails,
    get_calendar_for_day,
    get_pending_tasks,
    introduce_facultyflow,
)
from google_workspace import google_status, list_gmail_metadata, list_google_calendar_events
from ingestion import ingest_text, ingestion_help
from settings import env_bool, env_csv, env_int, load_local_env, optional_env
from state_store import add_image_ingestion, add_task, list_pending_actions, load_state, save_state
from state_store import clear_telegram_flow, get_telegram_flow, set_telegram_flow
from teacher_services import (
    automation_blueprint,
    cancel_action,
    command_center,
    confirm_action,
    deadline_radar,
    draft_focus_event,
    draft_reply,
    format_pending_actions,
    create_ready_gmail_draft,
    format_gmail_draft_result,
    email_followup_plan,
    live_google_snapshot,
    meeting_prep,
    morning_digest,
)


MAX_TELEGRAM_MESSAGE = 3900
IST = timezone(timedelta(hours=5, minutes=30))
SLOW_COMMANDS = {
    "/plan",
    "/today",
    "/live",
    "/morning",
    "/emailplan",
    "/google_calendar",
    "/gmail",
    "/draftemail",
}

COMMAND_ALIASES = {
    "center - dashboard": "/center",
    "brief - quick view": "/brief",
    "plan - full day": "/plan",
    "radar - risks": "/radar",
    "meetings - prep": "/meetings",
    "live - google": "/live",
    "morning - 6am brief": "/morning",
    "emailplan - followups": "/emailplan",
    "images - timetable": "/imagehelp",
    "ingest - add data": "/ingest",
    "pending - approvals": "/pending",
    "cost - safety": "/cost",
    "draftemail - gmail": "/draftemail",
    "draft email - gmail": "/draftemail",
}

BOT_COMMANDS = [
    {"command": "start", "description": "Open FacultyFlow menu and command buttons"},
    {"command": "center", "description": "Faculty command center with best next moves"},
    {"command": "brief", "description": "Short daily dashboard for a quick glance"},
    {"command": "plan", "description": "Detailed prioritized daily work plan"},
    {"command": "radar", "description": "Deadline risks and work to reschedule"},
    {"command": "meetings", "description": "Meeting and review preparation cards"},
    {"command": "live", "description": "Live Google Calendar and Gmail snapshot"},
    {"command": "morning", "description": "Run the 6 AM morning digest now"},
    {"command": "emailplan", "description": "Prepare Gmail follow-up calendar proposal"},
    {"command": "draftemail", "description": "Create a ready Gmail draft step by step"},
    {"command": "imagehelp", "description": "How to send timetable or meeting images"},
    {"command": "ingest", "description": "Add tasks, events, emails, or preferences"},
    {"command": "pending", "description": "Review confirmation-gated draft actions"},
    {"command": "cost", "description": "Show AWS and Bedrock cost guards"},
]


def main() -> None:
    load_local_env()
    token = optional_env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing in agentcore/.env.local")

    register_bot_commands(token)
    print("FacultyFlow Telegram polling started. Press Ctrl+C to stop.")
    offset: Optional[int] = None
    while True:
        try:
            updates = telegram_api(token, "getUpdates", {"timeout": 25, "offset": offset, "allowed_updates": ["message"]})
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                handle_update(token, update)
            maybe_send_morning_digest(token)
        except KeyboardInterrupt:
            print("Stopped.")
            return
        except Exception as exc:
            print(f"Polling error: {exc}")
            time.sleep(5)


def handle_update(token: str, update: dict[str, Any]) -> None:
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    text = (message.get("text") or "").strip()

    if not is_allowed_chat(chat_id):
        return

    try:
        telegram_api(token, "sendChatAction", {"chat_id": chat_id, "action": "typing"})
        if should_send_working_note(text, message):
            telegram_api(token, "sendMessage", {"chat_id": chat_id, "text": working_note(text, message)})
        if message.get("photo"):
            response = handle_photo_message(token, message)
        elif get_telegram_flow(chat_id):
            response = handle_active_flow(chat_id, text)
        elif normalize_command_text(text).lower().strip() in {"/draftemail", "/draft_email", "draft email"}:
            response = start_draft_email_flow(chat_id)
        else:
            response = route_message(text)
    except Exception as exc:
        response = (
            "I received your message, but the backend hit an error while processing it.\n\n"
            f"Problem: {exc}\n\n"
            "Please try /center or /help again. If this repeats, check the Telegram worker log."
        )
    for chunk in chunk_message(response):
        telegram_api(token, "sendMessage", build_send_payload(chat_id, chunk))


def route_message(text: str) -> str:
    command_text = normalize_command_text(text)
    lowered = command_text.lower().strip()
    if lowered in {"", "/start", "/help"}:
        return (
            "FacultyFlow is ready.\n\n"
            "The buttons below now include short meanings.\n\n"
            "Fast choices:\n"
            "- /center: command center with next moves.\n"
            "- /brief: quick view for a busy morning.\n"
            "- /plan: detailed schedule with reasons.\n"
            "- /morning: Gmail + Calendar morning digest.\n"
            "- /emailplan: convert important emails into a review-block proposal.\n"
            "- /draftemail: create a ready Gmail draft step by step.\n"
            "- /imagehelp: send timetable or meeting images safely.\n\n"
            "For slower Gmail/Calendar work I will show typing and send a working note first. "
            "Writes stay draft-only unless you confirm them."
        )
    if lowered == "/intro":
        return introduce_facultyflow()
    if lowered == "/center":
        return command_center()
    if lowered in {"/today", "/plan"}:
        return build_daily_plan(command_text or "Plan my work for today.")["summary"]
    if lowered == "/brief":
        return format_brief(build_daily_plan("Create my teacher morning brief."))
    if lowered == "/radar":
        return deadline_radar()
    if lowered == "/meetings":
        return meeting_prep()
    if lowered == "/live":
        try:
            return live_google_snapshot()
        except Exception as exc:
            return f"Live Google snapshot failed: {exc}"
    if lowered == "/morning":
        try:
            return morning_digest()
        except Exception as exc:
            return f"Morning digest failed: {exc}"
    if lowered == "/emailplan":
        try:
            return email_followup_plan()
        except Exception as exc:
            return friendly_google_error("Email follow-up planning failed", exc)
    if lowered in {"/draftemail", "/draft_email", "draft email"}:
        return start_draft_email_flow()
    if lowered == "/imagehelp":
        return image_help()
    if lowered == "/automate":
        return automation_blueprint()
    if lowered == "/ingest":
        return ingestion_help()
    if lowered.startswith("/ingest "):
        result = ingest_text(command_text[len("/ingest "):], default_date="2026-07-28")
        return format_ingestion_result(result)
    if lowered.startswith("/addtask "):
        result = ingest_text("task: " + command_text[len("/addtask "):], default_date="2026-07-28")
        return format_ingestion_result(result)
    if lowered == "/calendar":
        return json.dumps(get_calendar_for_day(), indent=2)
    if lowered == "/emails":
        return json.dumps(get_actionable_emails(), indent=2)
    if lowered == "/tasks":
        return json.dumps(get_pending_tasks(), indent=2)
    if lowered == "/pending":
        return format_pending_actions()
    if lowered.startswith("/confirm "):
        return json.dumps(confirm_action(command_text.split(maxsplit=1)[1].strip()), indent=2)
    if lowered.startswith("/cancel "):
        return json.dumps(cancel_action(command_text.split(maxsplit=1)[1].strip()), indent=2)
    if lowered.startswith("/draftmail "):
        parts = [part.strip() for part in command_text[len("/draftmail "):].split("|")]
        if len(parts) < 3:
            return "Use: /draftmail recipient@example.com | Subject | Purpose text"
        return format_gmail_draft_result(create_ready_gmail_draft(parts[0], parts[1], parts[2]))
    if lowered.startswith("/focusdraft "):
        parts = [part.strip() for part in command_text[len("/focusdraft "):].split("|")]
        if len(parts) < 4:
            return "Use: /focusdraft Title | 2026-07-28T10:00:00 | 2026-07-28T10:45:00 | Reason"
        return json.dumps(draft_focus_event(parts[0], parts[1], parts[2], parts[3]), indent=2)
    if lowered == "/state":
        state = load_state()
        return json.dumps(
            {
                "user_tasks": len(state["tasks"]),
                "user_calendar_events": len(state["calendar_events"]),
                "user_email_summaries": len(state["email_summaries"]),
                "preferences": state["preferences"],
                "pending_actions": len(state["pending_actions"]),
            },
            indent=2,
        )
    if lowered == "/google":
        return json.dumps(google_status(), indent=2)
    if lowered == "/google_calendar":
        try:
            return json.dumps(list_google_calendar_events(), indent=2)[:MAX_TELEGRAM_MESSAGE]
        except Exception as exc:
            return f"Google Calendar read failed: {exc}"
    if lowered == "/gmail":
        try:
            return json.dumps(list_gmail_metadata(), indent=2)[:MAX_TELEGRAM_MESSAGE]
        except Exception as exc:
            return friendly_google_error("Gmail metadata read failed", exc)
    if lowered == "/cost":
        return (
            f"Bedrock enabled: {is_bedrock_enabled()}\n"
            "Default model: amazon.nova-micro-v1:0\n"
            "Token cap: BEDROCK_MAX_TOKENS, currently defaults to 350\n"
            "AgentCore/AWS deployment is not free; deploy only after explicit cost approval."
        )
    if is_bedrock_enabled():
        plan = build_daily_plan(command_text)["summary"]
        result = ask_bedrock(command_text, context=plan)
        return result["text"]
    if "plan" in lowered:
        return build_daily_plan(command_text or "Plan my work for today.")["summary"]
    return (
        "I can handle /center, /today, /brief, /radar, /meetings, /live, /morning, /emailplan, /ingest, /addtask, /pending, /google, and /cost right now. "
        "Bedrock is disabled, so no model tokens were used."
    )


def image_help() -> str:
    return (
        "IMAGE INGESTION\n"
        "Send a timetable, meeting notice, circular, or task screenshot as a photo.\n\n"
        "Best caption format:\n"
        "type=timetable date=2026-07-29 note=Please extract class slots\n\n"
        "I will save the image, create a pending review item, and politely ask you to confirm "
        "what should be inserted before anything is added to your schedule."
    )


def start_draft_email_flow(chat_id: str | None = None) -> str:
    if chat_id:
        set_telegram_flow(chat_id, {"type": "draft_email", "step": "to"})
    return (
        "EMAIL DRAFT ASSISTANT\n\n"
        "Please send the recipient email address.\n\n"
        "Example: hod@college.edu\n\n"
        "You can type /cancel anytime to stop."
    )


def friendly_google_error(prefix: str, exc: Exception) -> str:
    text = str(exc)
    if "invalid_scope" in text:
        return (
            f"{prefix}.\n\n"
            "Google rejected the OAuth scope for this action.\n\n"
            "Fix:\n"
            "1. Run: uv run python google_oauth.py\n"
            "2. Approve the updated Gmail permissions.\n"
            "3. Try the Telegram command again.\n\n"
            "No Gmail or Calendar changes were made."
        )
    return f"{prefix}: {text}"


def handle_active_flow(chat_id: str, text: str) -> str:
    flow = get_telegram_flow(chat_id)
    if not flow:
        return route_message(text)
    if text.strip().lower() in {"/cancel", "cancel"}:
        clear_telegram_flow(chat_id)
        return "Cancelled the current draft flow."
    if flow.get("type") == "draft_email":
        return handle_draft_email_flow(chat_id, text, flow)
    clear_telegram_flow(chat_id)
    return "I cleared an unknown flow. Please try /draftemail again."


def handle_draft_email_flow(chat_id: str, text: str, flow: dict[str, Any]) -> str:
    value = text.strip()
    step = flow.get("step")
    if step == "to":
        if "@" not in value or "." not in value:
            return "Please send a valid recipient email address, for example hod@college.edu."
        flow["to"] = value
        flow["step"] = "subject"
        set_telegram_flow(chat_id, flow)
        return "Got it. Now send the email subject."
    if step == "subject":
        if len(value) < 3:
            return "Please send a slightly clearer subject."
        flow["subject"] = value
        flow["step"] = "purpose"
        set_telegram_flow(chat_id, flow)
        return (
            "Thanks. Now send a short description of what this email is about.\n\n"
            "Example: Tell the HOD that I will submit the IA report before 2 PM."
        )
    if step == "purpose":
        if len(value) < 8:
            return "Please add a little more context so the draft is useful."
        result = create_ready_gmail_draft(flow["to"], flow["subject"], value)
        clear_telegram_flow(chat_id)
        return format_gmail_draft_result(result)
    clear_telegram_flow(chat_id)
    return "The draft flow got out of sync. Please start again with /draftemail."


def normalize_command_text(text: str) -> str:
    cleaned = text.strip()
    lowered = cleaned.lower()
    if lowered in COMMAND_ALIASES:
        return COMMAND_ALIASES[lowered]
    for suffix in ("@SmartAssistant12Bot", "@smartassistant12bot"):
        if lowered.startswith("/") and suffix.lower() in lowered:
            return cleaned.replace(suffix, "")
    return cleaned


def should_send_working_note(text: str, message: dict[str, Any]) -> bool:
    if message.get("photo"):
        return True
    if not text.strip():
        return False
    command = normalize_command_text(text).split(maxsplit=1)[0].lower()
    return command in SLOW_COMMANDS


def working_note(text: str, message: dict[str, Any]) -> str:
    if message.get("photo"):
        return "Received the image. I am saving it and preparing a review request now."
    command = normalize_command_text(text).split(maxsplit=1)[0].lower() if text.strip() else ""
    notes = {
        "/plan": "Building your full day plan. This should take a few seconds.",
        "/today": "Building your full day plan. This should take a few seconds.",
        "/live": "Reading Calendar and Gmail metadata now. No writes will be made.",
        "/morning": "Preparing your morning brief from Calendar, Gmail, and your task plan.",
        "/emailplan": "Checking important Gmail messages and preparing a draft follow-up block.",
        "/google_calendar": "Reading Google Calendar events now.",
        "/gmail": "Reading Gmail metadata now. I will not read full private bodies.",
        "/draftemail": "Opening the email draft assistant. I will ask for recipient, subject, and purpose.",
    }
    return notes.get(command, "Working on it. I will reply shortly.")


def handle_photo_message(token: str, message: dict[str, Any]) -> str:
    photos = message.get("photo") or []
    caption = (message.get("caption") or "").strip()
    if not photos:
        return image_help()
    largest = photos[-1]
    file_id = largest["file_id"]
    file_info = telegram_api(token, "getFile", {"file_id": file_id})
    file_path = file_info.get("result", {}).get("file_path")
    if not file_path:
        return "I received the image, but Telegram did not provide a downloadable file path. Please try again."

    saved_path = download_telegram_file(token, file_path)
    item = add_image_ingestion(str(saved_path), caption=caption)
    return (
        "Thank you. I received the image and saved it for review.\n\n"
        f"Image ID: {item['id']}\n"
        f"Caption: {caption or '(no caption provided)'}\n\n"
        "Before I insert anything into your timetable or task list, please confirm the details in text. "
        "For example:\n"
        "/ingest event: DBMS class | date=2026-07-29 | start=10:00 | end=11:00 | category=class\n\n"
        "No calendar or task changes have been made yet."
    )


def download_telegram_file(token: str, file_path: str) -> Path:
    uploads = Path(__file__).with_name("data") / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    suffix = Path(file_path).suffix or ".jpg"
    target = uploads / f"telegram-{datetime.now().strftime('%Y%m%d-%H%M%S')}{suffix}"
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    with urllib.request.urlopen(url, timeout=35) as response:
        target.write_bytes(response.read())
    return target


def maybe_send_morning_digest(token: str) -> None:
    if not env_bool("TELEGRAM_MORNING_DIGEST_ENABLED", True):
        return
    allowed = env_csv("TELEGRAM_ALLOWED_CHAT_IDS")
    if not allowed:
        return

    now = datetime.now(IST)
    scheduled = clock_time(
        env_int("TELEGRAM_MORNING_DIGEST_HOUR", 6),
        env_int("TELEGRAM_MORNING_DIGEST_MINUTE", 0),
    )
    if now.time() < scheduled:
        return

    state = load_state()
    sent_key = "last_morning_digest_date"
    if state.get(sent_key) == now.date().isoformat():
        return

    text = morning_digest(now)
    for chat_id in sorted(allowed):
        for chunk in chunk_message(text):
            telegram_api(token, "sendMessage", build_send_payload(chat_id, chunk))
    state[sent_key] = now.date().isoformat()
    save_state(state)


def build_send_payload(chat_id: str, text: str) -> dict[str, Any]:
    return {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "keyboard": [
                [{"text": "Center - dashboard"}, {"text": "Brief - quick view"}],
                [{"text": "Plan - full day"}, {"text": "Radar - risks"}],
                [{"text": "Meetings - prep"}, {"text": "Live - Google"}],
                [{"text": "Morning - 6AM brief"}, {"text": "EmailPlan - followups"}],
                [{"text": "DraftEmail - gmail"}, {"text": "Images - timetable"}],
                [{"text": "Ingest - add data"}, {"text": "Pending - approvals"}],
                [{"text": "Cost - safety"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        },
    }


def register_bot_commands(token: str) -> None:
    telegram_api(token, "setMyCommands", {"commands": BOT_COMMANDS})


def format_brief(plan: dict[str, Any]) -> str:
    dashboard = plan["teacher_dashboard"]
    return (
        "TEACHER BRIEF\n"
        f"Readiness score: {dashboard['readiness_score']}/100\n"
        f"Classes today: {dashboard['classes_today']}\n"
        f"Important replies: {dashboard['important_replies']}\n"
        f"At-risk deadlines: {dashboard['at_risk_deadlines']}\n\n"
        "Top plan:\n"
        + "\n".join(plan["summary"].splitlines()[12:22])
        + "\n\nUse /plan for the full schedule or /pending for draft actions."
    )


def format_ingestion_result(result: dict[str, Any]) -> str:
    lines = [f"Ingested {result['created_count']} item(s)."]
    for created in result["created"]:
        item = created["item"]
        lines.append(f"- {created['type']}: {item.get('title') or item.get('subject') or item.get('key')}")
    if result["errors"]:
        lines.append("\nErrors:")
        lines.extend(f"- {error}" for error in result["errors"])
    lines.append("\nRun /plan to include this new data.")
    return "\n".join(lines)


def is_allowed_chat(chat_id: str) -> bool:
    allowed = env_csv("TELEGRAM_ALLOWED_CHAT_IDS")
    if not allowed:
        return env_bool("TELEGRAM_ALLOW_ALL_CHATS", False)
    return chat_id in allowed


def telegram_api(token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
    encoded_payload = {
        key: json.dumps(value) if isinstance(value, (list, dict)) else value
        for key, value in payload.items()
        if value is not None
    }
    data = urllib.parse.urlencode(encoded_payload).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram API {method} failed: {exc.code} {detail}") from exc


def chunk_message(text: str) -> list[str]:
    if len(text) <= MAX_TELEGRAM_MESSAGE:
        return [text]
    chunks = []
    remaining = text
    while remaining:
        chunks.append(remaining[:MAX_TELEGRAM_MESSAGE])
        remaining = remaining[MAX_TELEGRAM_MESSAGE:]
    return chunks


if __name__ == "__main__":
    main()
