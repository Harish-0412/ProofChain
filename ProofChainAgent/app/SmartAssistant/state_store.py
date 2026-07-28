from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


STATE_FILE = Path(__file__).with_name("data") / "user_state.json"

DEFAULT_STATE: dict[str, Any] = {
    "calendar_events": [],
    "tasks": [],
    "email_summaries": [],
    "preferences": {},
    "pending_actions": [],
    "completed_items": [],
    "image_ingestions": [],
    "telegram_flows": {},
}


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        save_state(DEFAULT_STATE.copy())
    with STATE_FILE.open("r", encoding="utf-8") as handle:
        state = json.load(handle)
    for key, value in DEFAULT_STATE.items():
        state.setdefault(key, value.copy() if isinstance(value, list | dict) else value)
    return state


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def add_task(title: str, deadline: str | None = None, minutes: int = 45, importance: int = 3, category: str = "General") -> dict[str, Any]:
    state = load_state()
    task = {
        "id": f"user-task-{len(state['tasks']) + 1:04d}",
        "title": title,
        "description": title,
        "deadline": deadline,
        "estimated_minutes": minutes,
        "importance": importance,
        "status": "Pending",
        "source": "telegram_ingestion",
        "category": category,
        "reason": "Added by the user through FacultyFlow ingestion.",
    }
    state["tasks"].append(task)
    save_state(state)
    return task


def add_calendar_event(title: str, date: str, start: str, end: str, category: str = "meeting") -> dict[str, Any]:
    state = load_state()
    event = {
        "id": f"user-event-{len(state['calendar_events']) + 1:04d}",
        "date": date,
        "start": start,
        "end": end,
        "title": title,
        "category": category,
        "source": "telegram_ingestion",
        "notes": "Added by the user through FacultyFlow ingestion.",
    }
    state["calendar_events"].append(event)
    save_state(state)
    return event


def add_email_summary(sender: str, subject: str, summary: str, due_by: str | None = None, urgency: str = "medium") -> dict[str, Any]:
    state = load_state()
    email = {
        "id": f"user-email-{len(state['email_summaries']) + 1:04d}",
        "sender": sender,
        "subject": subject,
        "received_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "due_by": due_by,
        "urgency": urgency,
        "action_required": True,
    }
    state["email_summaries"].append(email)
    save_state(state)
    return email


def add_image_ingestion(file_path: str, caption: str = "", source: str = "telegram_photo") -> dict[str, Any]:
    state = load_state()
    item = {
        "id": f"image-{len(state['image_ingestions']) + 1:04d}",
        "file_path": file_path,
        "caption": caption,
        "source": source,
        "status": "awaiting_user_review",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_note": (
            "Image saved. Please confirm the timetable/meeting details in text, or send a caption "
            "using the /ingest format so FacultyFlow can insert it safely."
        ),
    }
    state["image_ingestions"].append(item)
    state["pending_actions"].append(
        {
            "id": f"pending-image-{len(state['image_ingestions']):04d}",
            "type": "image_ingestion_review",
            "image_id": item["id"],
            "file_path": file_path,
            "caption": caption,
            "status": "awaiting_confirmation",
            "created_at": item["created_at"],
            "message": "Review uploaded timetable/meeting image before inserting schedule data.",
            "confirmation_required": True,
        }
    )
    save_state(state)
    return item


def set_preference(key: str, value: str) -> dict[str, str]:
    state = load_state()
    state["preferences"][key] = value
    save_state(state)
    return {"key": key, "value": value}


def list_pending_actions() -> list[dict[str, Any]]:
    return load_state()["pending_actions"]


def remember_pending_action(action: dict[str, Any]) -> dict[str, Any]:
    state = load_state()
    action = dict(action)
    action.setdefault("id", f"pending-{len(state['pending_actions']) + 1:04d}")
    action.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
    action.setdefault("status", "awaiting_confirmation")
    state["pending_actions"].append(action)
    save_state(state)
    return action


def replace_pending_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state = load_state()
    stored = []
    for index, action in enumerate(actions, start=1):
        action = dict(action)
        action["id"] = f"pending-{index:04d}"
        action["created_at"] = datetime.now().isoformat(timespec="seconds")
        action["status"] = "awaiting_confirmation"
        stored.append(action)
    state["pending_actions"] = stored
    save_state(state)
    return stored


def clear_state() -> None:
    save_state(DEFAULT_STATE.copy())


def set_telegram_flow(chat_id: str, flow: dict[str, Any]) -> None:
    state = load_state()
    state["telegram_flows"][chat_id] = flow
    save_state(state)


def get_telegram_flow(chat_id: str) -> dict[str, Any] | None:
    return load_state().get("telegram_flows", {}).get(chat_id)


def clear_telegram_flow(chat_id: str) -> None:
    state = load_state()
    state.get("telegram_flows", {}).pop(chat_id, None)
    save_state(state)
