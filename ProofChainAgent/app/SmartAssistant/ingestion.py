from __future__ import annotations

from datetime import date
from typing import Any

from state_store import add_calendar_event, add_email_summary, add_task, set_preference


def ingest_text(payload: str, default_date: str | None = None) -> dict[str, Any]:
    target_date = default_date or date.today().isoformat()
    created: list[dict[str, Any]] = []
    errors: list[str] = []

    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            created.append(_ingest_line(line, target_date))
        except ValueError as exc:
            errors.append(f"{line}: {exc}")

    return {
        "created_count": len(created),
        "created": created,
        "errors": errors,
        "help": ingestion_help(),
    }


def ingestion_help() -> str:
    return (
        "Send /ingest followed by one item per line:\n"
        "task: Finish lab manual | deadline=2026-07-28T16:00:00 | minutes=45 | importance=4 | category=Reports\n"
        "event: DBMS class | date=2026-07-28 | start=10:00 | end=11:00 | category=class\n"
        "email: hod@college.edu | subject=Report needed | due=14:00 | urgency=critical | summary=Submit IA report\n"
        "pref: preferred_focus_minutes=45"
    )


def _ingest_line(line: str, target_date: str) -> dict[str, Any]:
    kind, _, body = line.partition(":")
    if not body:
        raise ValueError("Missing ':' after item type.")
    kind = kind.strip().lower()
    title_or_first, fields = _parse_fields(body)

    if kind == "task":
        return {"type": "task", "item": add_task(
            title=title_or_first,
            deadline=fields.get("deadline") or fields.get("due"),
            minutes=int(fields.get("minutes", fields.get("estimated_minutes", 45))),
            importance=int(fields.get("importance", 3)),
            category=fields.get("category", "General"),
        )}
    if kind == "event":
        start = fields.get("start")
        end = fields.get("end")
        if not start or not end:
            raise ValueError("Events require start and end.")
        return {"type": "event", "item": add_calendar_event(
            title=title_or_first,
            date=fields.get("date", target_date),
            start=start,
            end=end,
            category=fields.get("category", "meeting"),
        )}
    if kind == "email":
        return {"type": "email", "item": add_email_summary(
            sender=title_or_first,
            subject=fields.get("subject", "Action required"),
            summary=fields.get("summary", fields.get("subject", "Action required")),
            due_by=fields.get("due") or fields.get("deadline"),
            urgency=fields.get("urgency", "medium"),
        )}
    if kind in {"pref", "preference"}:
        key, _, value = title_or_first.partition("=")
        if not value:
            raise ValueError("Preferences must look like pref: key=value.")
        return {"type": "preference", "item": set_preference(key.strip(), value.strip())}

    raise ValueError("Supported types are task, event, email, and pref.")


def _parse_fields(body: str) -> tuple[str, dict[str, str]]:
    chunks = [chunk.strip() for chunk in body.split("|") if chunk.strip()]
    if not chunks:
        raise ValueError("Missing item content.")
    fields: dict[str, str] = {}
    for chunk in chunks[1:]:
        key, _, value = chunk.partition("=")
        if not value:
            raise ValueError(f"Invalid field '{chunk}'. Use key=value.")
        fields[key.strip().lower()] = value.strip()
    return chunks[0], fields
