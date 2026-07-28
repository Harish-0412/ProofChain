from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

from state_store import load_state, replace_pending_actions


DATA_DIR = Path(__file__).with_name("data")
DEFAULT_DATE = date(2026, 7, 28)


@dataclass(frozen=True)
class TimeBlock:
    start: datetime
    end: datetime
    title: str
    category: str
    source: str
    priority: str = "Fixed"
    reason: str = ""

    @property
    def minutes(self) -> int:
        return int((self.end - self.start).total_seconds() // 60)


@dataclass(frozen=True)
class WorkItem:
    id: str
    title: str
    category: str
    estimated_minutes: int
    deadline: Optional[datetime]
    importance: int
    source: str
    reason: str
    dependency: str = ""
    priority: str = "Medium"
    score: int = 0


def introduce_facultyflow() -> str:
    return (
        "FacultyFlow is a local-first academic work planning agent for teachers and staff. "
        "Right now I can read mock calendar events, mock email summaries, and mock tasks; "
        "detect overloaded days and schedule conflicts; build a prioritized daily plan; "
        "draft calendar/email proposals; and explain why each recommendation was made. "
        "No AWS, Bedrock, Gmail, Google Calendar, or Telegram write action is used in this "
        "local MVP unless you explicitly connect and approve it later."
    )


def build_daily_plan(request: str = "Plan my work for today.", requested_date: Optional[str] = None) -> dict[str, Any]:
    target_date = _parse_date(requested_date)
    preferences = _load_json("preferences.json")
    preferences.update(load_state().get("preferences", {}))
    fixed_blocks = _load_fixed_blocks(target_date)
    work_items = _prioritize_items(_build_work_items(target_date, preferences), target_date)
    free_slots = _free_slots(target_date, fixed_blocks, preferences)
    scheduled, unscheduled = _schedule_items(work_items, free_slots)
    conflicts = _detect_calendar_conflicts(fixed_blocks)
    risks = _deadline_risks(work_items, fixed_blocks, target_date, preferences)

    summary = _format_plan(
        target_date=target_date,
        request=request,
        fixed_blocks=fixed_blocks,
        scheduled=scheduled,
        unscheduled=unscheduled,
        conflicts=conflicts,
        risks=risks,
        preferences=preferences,
    )

    proposals = _build_action_proposals(scheduled, risks)
    stored_proposals = replace_pending_actions(proposals[:5])

    return {
        "mode": "local_mock_no_aws_spend",
        "request": request,
        "date": target_date.isoformat(),
        "summary": summary,
        "fixed_commitments": [_block_to_dict(block) for block in fixed_blocks],
        "scheduled_work": [_block_to_dict(block) for block in scheduled],
        "unscheduled_work": [_work_item_to_dict(item) for item in unscheduled],
        "conflicts": conflicts,
        "deadline_risks": risks,
        "draft_action_proposals": stored_proposals,
        "teacher_dashboard": _build_teacher_dashboard(fixed_blocks, scheduled, unscheduled, risks),
        "safety_note": "No external action has been taken. Calendar/email/Telegram actions are drafts only.",
    }


def get_calendar_for_day(requested_date: Optional[str] = None) -> list[dict[str, Any]]:
    target_date = _parse_date(requested_date)
    return [_block_to_dict(block) for block in _load_fixed_blocks(target_date)]


def get_pending_tasks(status: str = "Pending") -> list[dict[str, Any]]:
    wanted = status.lower()
    tasks = _load_json("mock_tasks.json") + load_state().get("tasks", [])
    return [task for task in tasks if task.get("status", "").lower() == wanted]


def get_actionable_emails() -> list[dict[str, Any]]:
    emails = _load_json("mock_emails.json") + load_state().get("email_summaries", [])
    safe_keys = {"id", "sender", "subject", "received_at", "summary", "due_by", "urgency", "action_required"}
    return [{key: email.get(key) for key in safe_keys if key in email} for email in emails if email.get("action_required")]


def build_event_proposal(title: str, start: str, end: str, reason: str) -> dict[str, Any]:
    return {
        "type": "calendar_event_proposal",
        "title": title,
        "start": start,
        "end": end,
        "reason": reason,
        "status": "awaiting_user_confirmation",
        "executed": False,
        "confirmation_required": True,
    }


def build_email_draft(to: str, subject: str, purpose: str, tone: str = "professional") -> dict[str, Any]:
    greeting = "Dear Sir/Madam" if tone == "formal" else "Hello"
    body = (
        f"{greeting},\n\n"
        f"{purpose.strip()}\n\n"
        "Regards,\n"
        "Faculty Member"
    )
    return {
        "type": "email_draft",
        "to": to,
        "subject": subject,
        "body": body,
        "status": "draft_only_awaiting_user_confirmation",
        "sent": False,
        "confirmation_required": True,
    }


def get_telegram_setup_requirements() -> dict[str, Any]:
    return {
        "safe_stage": "Not connected yet. Keep using local mock tools until the planner output is acceptable.",
        "needed_from_you_later": [
            "Telegram bot token from BotFather",
            "Your Telegram numeric chat ID or allowed user IDs",
            "Preferred commands to enable first, for example /today, /plan, /tasks, /help",
            "Whether the bot is personal-only or multi-user",
            "Preferred daily briefing time and timezone",
            "AWS region to deploy in, recommended ap-south-1 if your Bedrock model is available there",
            "Confirmation policy for writes, recommended: always ask before sending email or creating calendar events",
        ],
        "do_not_share_publicly": [
            "Telegram bot token",
            "OAuth client secret",
            "AWS access keys",
            "Gmail refresh tokens",
        ],
        "cost_guardrail": (
            "Telegram wiring can be developed with a local webhook simulator first. "
            "Do not deploy Lambda/API Gateway/AgentCore Runtime until you approve a costed deployment step."
        ),
    }


def _load_json(name: str) -> Any:
    with (DATA_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_date(value: Optional[str]) -> date:
    if not value:
        return DEFAULT_DATE
    normalized = value.strip().lower()
    if normalized in {"today", "now"}:
        return DEFAULT_DATE
    return date.fromisoformat(normalized)


def _parse_time_on_day(target_date: date, value: str) -> datetime:
    return datetime.combine(target_date, time.fromisoformat(value))


def _parse_optional_deadline(target_date: date, value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if "T" in value:
        return datetime.fromisoformat(value)
    return _parse_time_on_day(target_date, value)


def _load_fixed_blocks(target_date: date) -> list[TimeBlock]:
    events = []
    for event in _load_json("mock_calendar.json") + load_state().get("calendar_events", []):
        if event["date"] != target_date.isoformat():
            continue
        events.append(
            TimeBlock(
                start=_parse_time_on_day(target_date, event["start"]),
                end=_parse_time_on_day(target_date, event["end"]),
                title=event["title"],
                category=event["category"],
                source=event.get("source", "calendar"),
                reason=event.get("notes", ""),
            )
        )
    return sorted(events, key=lambda block: (block.start, block.end))


def _build_work_items(target_date: date, preferences: dict[str, Any]) -> list[WorkItem]:
    items: list[WorkItem] = []

    for event in _load_fixed_blocks(target_date):
        if event.category == "class":
            prep_minutes = int(preferences.get("default_class_prep_minutes", 30))
            items.append(
                WorkItem(
                    id=f"prep-{_slug(event.title)}",
                    title=f"Prepare for {event.title}",
                    category="Teaching",
                    estimated_minutes=prep_minutes,
                    deadline=event.start,
                    importance=5,
                    source="calendar",
                    reason=f"Class starts at {_fmt_time(event.start)}.",
                    dependency=event.title,
                )
            )

    for task in get_pending_tasks():
        if task.get("status") != "Pending":
            continue
        items.append(
            WorkItem(
                id=task["id"],
                title=task["title"],
                category=task.get("category", "General"),
                estimated_minutes=int(task["estimated_minutes"]),
                deadline=_parse_optional_deadline(target_date, task.get("deadline")),
                importance=int(task.get("importance", 3)),
                source=task.get("source", "tasks"),
                reason=task.get("reason", ""),
                dependency=task.get("dependency", ""),
            )
        )

    for email in get_actionable_emails():
        due = _parse_optional_deadline(target_date, email.get("due_by"))
        urgency = {"critical": 5, "high": 4, "medium": 3, "low": 2}.get(str(email.get("urgency", "")).lower(), 3)
        items.append(
            WorkItem(
                id=f"email-{email['id']}",
                title=f"Reply: {email['subject']}",
                category="Communication",
                estimated_minutes=15,
                deadline=due,
                importance=urgency,
                source=f"email:{email['sender']}",
                reason=email.get("summary", ""),
            )
        )
    return items


def _prioritize_items(items: Iterable[WorkItem], target_date: date) -> list[WorkItem]:
    now = datetime.combine(target_date, time(9, 0))
    prioritized = []
    for item in items:
        deadline_score = 0
        if item.deadline:
            hours = max((item.deadline - now).total_seconds() / 3600, 0)
            if hours <= 3:
                deadline_score = 50
            elif hours <= 8:
                deadline_score = 35
            elif item.deadline.date() == target_date:
                deadline_score = 25
            else:
                deadline_score = 10
        dependency_score = 15 if item.dependency else 0
        effort_score = 8 if item.estimated_minutes >= 75 else 4
        score = item.importance * 10 + deadline_score + dependency_score + effort_score
        priority = "Critical" if score >= 95 else "High" if score >= 75 else "Medium" if score >= 50 else "Low"
        prioritized.append(
            WorkItem(
                id=item.id,
                title=item.title,
                category=item.category,
                estimated_minutes=item.estimated_minutes,
                deadline=item.deadline,
                importance=item.importance,
                source=item.source,
                reason=item.reason,
                dependency=item.dependency,
                priority=priority,
                score=score,
            )
        )
    return sorted(prioritized, key=lambda item: (-item.score, item.deadline or datetime.max, -item.estimated_minutes))


def _free_slots(target_date: date, fixed_blocks: list[TimeBlock], preferences: dict[str, Any]) -> list[TimeBlock]:
    work_start = _parse_time_on_day(target_date, preferences.get("work_start", "09:00"))
    work_end = _parse_time_on_day(target_date, preferences.get("work_end", "17:30"))
    lunch_start = _parse_time_on_day(target_date, preferences.get("lunch_start", "13:30"))
    lunch_end = _parse_time_on_day(target_date, preferences.get("lunch_end", "14:00"))
    transition = timedelta(minutes=int(preferences.get("transition_buffer_minutes", 10)))

    busy = [TimeBlock(lunch_start, lunch_end, "Lunch", "break", "preference")]
    for block in fixed_blocks:
        busy.append(
            TimeBlock(
                start=max(work_start, block.start - transition),
                end=min(work_end, block.end + transition),
                title=block.title,
                category=block.category,
                source=block.source,
            )
        )

    busy = sorted(busy, key=lambda block: (block.start, block.end))
    merged: list[TimeBlock] = []
    for block in busy:
        if not merged or block.start > merged[-1].end:
            merged.append(block)
        else:
            previous = merged[-1]
            merged[-1] = TimeBlock(previous.start, max(previous.end, block.end), previous.title, previous.category, previous.source)

    slots = []
    cursor = work_start
    for block in merged:
        if cursor < block.start:
            slots.append(TimeBlock(cursor, block.start, "Available", "free", "computed"))
        cursor = max(cursor, block.end)
    if cursor < work_end:
        slots.append(TimeBlock(cursor, work_end, "Available", "free", "computed"))
    return [slot for slot in slots if slot.minutes >= 15]


def _schedule_items(items: list[WorkItem], slots: list[TimeBlock]) -> tuple[list[TimeBlock], list[WorkItem]]:
    remaining_slots = list(slots)
    scheduled: list[TimeBlock] = []
    unscheduled: list[WorkItem] = []

    for item in items:
        placed = False
        for index, slot in enumerate(remaining_slots):
            latest_end = min(slot.end, item.deadline) if item.deadline else slot.end
            if slot.start + timedelta(minutes=item.estimated_minutes) > latest_end:
                continue
            if item.category == "Teaching" and item.deadline:
                start = latest_end - timedelta(minutes=item.estimated_minutes)
            else:
                start = slot.start
            end = start + timedelta(minutes=item.estimated_minutes)
            scheduled.append(
                TimeBlock(
                    start=start,
                    end=end,
                    title=item.title,
                    category=item.category,
                    source=item.source,
                    priority=item.priority,
                    reason=_explain_item(item),
                )
            )
            remaining_slots.pop(index)
            replacement_slots = []
            if slot.start < start:
                replacement_slots.append(TimeBlock(slot.start, start, "Available", "free", "computed"))
            if end < slot.end:
                replacement_slots.append(TimeBlock(end, slot.end, "Available", "free", "computed"))
            for offset, replacement in enumerate(replacement_slots):
                remaining_slots.insert(index + offset, replacement)
            remaining_slots.sort(key=lambda block: (block.start, block.end))
            placed = True
            break
        if not placed:
            unscheduled.append(item)

    return sorted(scheduled, key=lambda block: block.start), unscheduled


def _detect_calendar_conflicts(blocks: list[TimeBlock]) -> list[dict[str, Any]]:
    conflicts = []
    ordered = sorted(blocks, key=lambda block: (block.start, block.end))
    for current, following in zip(ordered, ordered[1:]):
        if current.end > following.start:
            conflicts.append(
                {
                    "type": "calendar_overlap",
                    "items": [current.title, following.title],
                    "overlap": f"{_fmt_time(following.start)}-{_fmt_time(min(current.end, following.end))}",
                }
            )
    return conflicts


def _deadline_risks(
    items: list[WorkItem],
    fixed_blocks: list[TimeBlock],
    target_date: date,
    preferences: dict[str, Any],
) -> list[dict[str, Any]]:
    risks = []
    for item in items:
        if not item.deadline or item.deadline.date() != target_date:
            continue
        cutoff_slots = [slot for slot in _free_slots(target_date, fixed_blocks, preferences) if slot.start < item.deadline]
        available = sum(max(0, int((min(slot.end, item.deadline) - slot.start).total_seconds() // 60)) for slot in cutoff_slots)
        if available < item.estimated_minutes:
            risks.append(
                {
                    "task": item.title,
                    "deadline": _fmt_time(item.deadline),
                    "estimated_minutes": item.estimated_minutes,
                    "available_minutes_before_deadline": available,
                    "risk": "High",
                    "suggested_action": "Start immediately or postpone a lower-priority task.",
                }
            )
    return risks


def _build_action_proposals(scheduled: list[TimeBlock], risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proposals = []
    for block in scheduled:
        if block.category in {"Teaching", "Reports", "Communication"} and block.priority in {"Critical", "High"}:
            proposals.append(
                build_event_proposal(
                    title=block.title,
                    start=block.start.isoformat(timespec="minutes"),
                    end=block.end.isoformat(timespec="minutes"),
                    reason=block.reason,
                )
            )
    for risk in risks:
        proposals.append(
            {
                "type": "risk_alert_proposal",
                "message": f"{risk['task']} is at high risk before {risk['deadline']}.",
                "status": "draft_only_awaiting_user_confirmation",
                "executed": False,
                "confirmation_required": True,
            }
        )
    return proposals


def _build_teacher_dashboard(
    fixed_blocks: list[TimeBlock],
    scheduled: list[TimeBlock],
    unscheduled: list[WorkItem],
    risks: list[dict[str, Any]],
) -> dict[str, Any]:
    teaching = [block for block in fixed_blocks if block.category == "class"]
    communication = [block for block in scheduled if block.category == "Communication"]
    focus = [block for block in scheduled if block.minutes >= 45]
    return {
        "readiness_score": max(0, 100 - len(risks) * 25 - len(unscheduled) * 8),
        "classes_today": len(teaching),
        "important_replies": len(communication),
        "focus_blocks": [_block_to_dict(block) for block in focus],
        "at_risk_deadlines": len(risks),
        "automation_suggestions": [
            "Use /ingest each morning to paste timetable, task, and email summaries.",
            "Use /brief for a short Telegram-ready dashboard.",
            "Use /pending before approving calendar/email writes.",
        ],
    }


def _format_plan(
    target_date: date,
    request: str,
    fixed_blocks: list[TimeBlock],
    scheduled: list[TimeBlock],
    unscheduled: list[WorkItem],
    conflicts: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    preferences: dict[str, Any],
) -> str:
    total_fixed = sum(block.minutes for block in fixed_blocks)
    total_scheduled = sum(block.minutes for block in scheduled)
    total_unscheduled = sum(item.estimated_minutes for item in unscheduled)
    work_minutes = _workday_minutes(target_date, preferences)

    lines = [
        "FACULTYFLOW DAILY PLAN",
        f"Date: {target_date.isoformat()}",
        f"Request: {request}",
        "",
        "Today at a glance",
        f"- Fixed commitments: {_fmt_duration(total_fixed)}",
        f"- Planned flexible work: {_fmt_duration(total_scheduled)}",
        f"- Remaining unscheduled work: {_fmt_duration(total_unscheduled)}",
        f"- Workday capacity: {_fmt_duration(work_minutes)}",
        "",
        "Fixed commitments",
    ]
    lines.extend(_format_blocks(fixed_blocks) or ["- None"])

    critical = [block for block in scheduled if block.priority == "Critical"]
    high = [block for block in scheduled if block.priority == "High"]
    rest = [block for block in scheduled if block.priority not in {"Critical", "High"}]

    lines.extend(["", "Critical"])
    lines.extend(_format_blocks(critical, include_reason=True) or ["- None"])
    lines.extend(["", "High priority"])
    lines.extend(_format_blocks(high, include_reason=True) or ["- None"])
    lines.extend(["", "Other planned work"])
    lines.extend(_format_blocks(rest, include_reason=True) or ["- None"])

    if conflicts:
        lines.extend(["", "Conflicts detected"])
        lines.extend([f"- {conflict['items'][0]} overlaps {conflict['items'][1]} at {conflict['overlap']}." for conflict in conflicts])

    if risks:
        lines.extend(["", "Deadline risks"])
        for risk in risks:
            lines.append(
                f"- {risk['task']}: needs {risk['estimated_minutes']} minutes before "
                f"{risk['deadline']}, but only {risk['available_minutes_before_deadline']} minutes are free."
            )

    if unscheduled:
        lines.extend(["", "Recommended postponements"])
        for item in unscheduled:
            lines.append(f"- {item.title} ({_fmt_duration(item.estimated_minutes)}): {item.reason or 'No safe slot remains today.'}")

    lines.extend(
        [
            "",
            "External actions",
            "- No calendar event, email, Telegram message, or AWS action has been executed.",
            "- Any write action must be confirmed by the user before a real integration is connected.",
        ]
    )
    return "\n".join(lines)


def _format_blocks(blocks: list[TimeBlock], include_reason: bool = False) -> list[str]:
    lines = []
    for block in blocks:
        line = f"- {_fmt_time(block.start)}-{_fmt_time(block.end)}: {block.title}"
        if include_reason and block.reason:
            line += f" Reason: {block.reason}"
        lines.append(line)
    return lines


def _explain_item(item: WorkItem) -> str:
    parts = [item.reason] if item.reason else []
    if item.deadline:
        parts.append(f"Deadline: {_fmt_time(item.deadline)}.")
    if item.dependency:
        parts.append(f"Supports: {item.dependency}.")
    parts.append(f"Priority: {item.priority} based on urgency, importance, dependency, and effort.")
    return " ".join(parts)


def _workday_minutes(target_date: date, preferences: dict[str, Any]) -> int:
    start = _parse_time_on_day(target_date, preferences.get("work_start", "09:00"))
    end = _parse_time_on_day(target_date, preferences.get("work_end", "17:30"))
    lunch_start = _parse_time_on_day(target_date, preferences.get("lunch_start", "13:30"))
    lunch_end = _parse_time_on_day(target_date, preferences.get("lunch_end", "14:00"))
    return int((end - start - (lunch_end - lunch_start)).total_seconds() // 60)


def _block_to_dict(block: TimeBlock) -> dict[str, Any]:
    return {
        "start": block.start.isoformat(timespec="minutes"),
        "end": block.end.isoformat(timespec="minutes"),
        "title": block.title,
        "category": block.category,
        "source": block.source,
        "priority": block.priority,
        "reason": block.reason,
        "minutes": block.minutes,
    }


def _work_item_to_dict(item: WorkItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "estimated_minutes": item.estimated_minutes,
        "deadline": item.deadline.isoformat(timespec="minutes") if item.deadline else None,
        "source": item.source,
        "priority": item.priority,
        "score": item.score,
        "reason": item.reason,
    }


def _fmt_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def _fmt_duration(minutes: int) -> str:
    hours, remainder = divmod(minutes, 60)
    if hours and remainder:
        return f"{hours}h {remainder}m"
    if hours:
        return f"{hours}h"
    return f"{remainder}m"


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
