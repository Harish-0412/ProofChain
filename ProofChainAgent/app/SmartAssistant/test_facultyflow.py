from facultyflow import build_daily_plan, build_email_draft, get_telegram_setup_requirements
from bedrock_llm import ask_bedrock
from google_workspace import google_status
from telegram_bot import build_send_payload, handle_active_flow, normalize_command_text, route_message, should_send_working_note, start_draft_email_flow, working_note
from teacher_services import cancel_action, confirm_action, draft_focus_event, format_pending_actions
from ingestion import ingest_text
from state_store import add_image_ingestion, clear_state, get_telegram_flow, load_state


def test_daily_plan_is_local_and_draft_only() -> None:
    result = build_daily_plan("Plan my work for today.", "2026-07-28")

    assert result["mode"] == "local_mock_no_aws_spend"
    assert "Complete internal assessment report" in result["summary"]
    assert "No calendar event, email, Telegram message, or AWS action has been executed." in result["summary"]
    assert result["draft_action_proposals"]
    assert all(proposal["confirmation_required"] for proposal in result["draft_action_proposals"])


def test_email_draft_never_sends() -> None:
    draft = build_email_draft(
        to="hod@college.edu",
        subject="Internal Assessment Report",
        purpose="I will submit the completed report before the department review.",
    )

    assert draft["sent"] is False
    assert draft["confirmation_required"] is True


def test_telegram_requirements_do_not_request_public_secrets() -> None:
    requirements = get_telegram_setup_requirements()

    assert "Telegram bot token from BotFather" in requirements["needed_from_you_later"]
    assert "Telegram bot token" in requirements["do_not_share_publicly"]
    assert "Do not deploy" in requirements["cost_guardrail"]


def test_bedrock_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.setenv("FACULTYFLOW_ENABLE_BEDROCK", "false")

    result = ask_bedrock("hello")

    assert result["enabled"] is False
    assert "no model tokens were used" in result["text"]


def test_telegram_plan_command_uses_local_planner(monkeypatch) -> None:
    monkeypatch.setenv("FACULTYFLOW_ENABLE_BEDROCK", "false")

    response = route_message("/today")

    assert "FACULTYFLOW DAILY PLAN" in response
    assert "No calendar event, email, Telegram message, or AWS action has been executed." in response


def test_google_status_is_explicit_without_oauth(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE", "")
    monkeypatch.setenv("GOOGLE_OAUTH_TOKEN_FILE", "")

    status = google_status()

    assert status["configured"] is False
    assert "Telegram credentials alone cannot grant Gmail or Calendar access." in status["note"]


def test_ingestion_adds_teacher_workflow_items() -> None:
    clear_state()

    result = ingest_text(
        "\n".join(
            [
                "task: Finish accreditation note | deadline=2026-07-28T16:00:00 | minutes=40 | importance=4 | category=Reports",
                "event: AI lab | date=2026-07-28 | start=14:00 | end=15:00 | category=class",
                "email: coordinator@college.edu | subject=Rubric needed | due=13:00 | urgency=high | summary=Send project rubric",
                "pref: preferred_focus_minutes=45",
            ]
        ),
        default_date="2026-07-28",
    )

    state = load_state()
    assert result["created_count"] == 4
    assert len(state["tasks"]) == 1
    assert len(state["calendar_events"]) == 1
    assert len(state["email_summaries"]) == 1
    assert state["preferences"]["preferred_focus_minutes"] == "45"
    clear_state()


def test_telegram_brief_and_ingest_commands(monkeypatch) -> None:
    clear_state()
    monkeypatch.setenv("FACULTYFLOW_ENABLE_BEDROCK", "false")

    ingest_response = route_message("/addtask Prepare quiz | deadline=2026-07-28T15:00:00 | minutes=30 | importance=4")
    brief_response = route_message("/brief")

    assert "Ingested 1 item" in ingest_response
    assert "TEACHER BRIEF" in brief_response
    assert "Readiness score" in brief_response
    clear_state()


def test_advanced_teacher_commands_are_telegram_ready(monkeypatch) -> None:
    clear_state()
    monkeypatch.setenv("FACULTYFLOW_ENABLE_BEDROCK", "false")

    center = route_message("/center")
    radar = route_message("/radar")
    meetings = route_message("/meetings")
    automate = route_message("/automate")
    payload = build_send_payload("123", center)

    assert "FACULTYFLOW COMMAND CENTER" in center
    assert "DEADLINE RADAR" in radar
    assert "MEETING PREP" in meetings
    assert "AUTOMATION BLUEPRINT" in automate
    assert payload["reply_markup"]["keyboard"][0][0]["text"] == "Center - dashboard"
    assert "Morning - 6AM brief" in str(payload["reply_markup"]["keyboard"])
    assert normalize_command_text("Center - dashboard") == "/center"


def test_confirmation_flow_is_gated(monkeypatch) -> None:
    clear_state()
    monkeypatch.setenv("FACULTYFLOW_ENABLE_GOOGLE_WRITES", "false")

    action = draft_focus_event(
        "Prepare IA report",
        "2026-07-28T09:00:00",
        "2026-07-28T09:45:00",
        "High-priority report block.",
    )
    pending = format_pending_actions()
    result = confirm_action(action["id"])
    cancelled = cancel_action(action["id"])

    assert action["id"] in pending
    assert result["ok"] is False
    assert "Google writes are disabled" in result["message"]
    assert cancelled["ok"] is True
    clear_state()


def test_image_ingestion_creates_review_item() -> None:
    clear_state()

    item = add_image_ingestion("data/uploads/sample-timetable.jpg", caption="type=timetable")
    state = load_state()

    assert item["status"] == "awaiting_user_review"
    assert state["image_ingestions"][0]["caption"] == "type=timetable"
    assert state["pending_actions"][0]["type"] == "image_ingestion_review"
    clear_state()


def test_morning_and_image_commands_route(monkeypatch) -> None:
    monkeypatch.setattr("telegram_bot.morning_digest", lambda: "GOOD MORNING FACULTYFLOW BRIEF")

    assert "GOOD MORNING FACULTYFLOW BRIEF" in route_message("/morning")
    assert "IMAGE INGESTION" in route_message("/imagehelp")


def test_working_note_for_slow_commands() -> None:
    assert should_send_working_note("/emailplan", {}) is True
    assert "Checking important Gmail" in working_note("/emailplan", {})
    assert should_send_working_note("/center", {}) is False


def test_draft_email_conversation_flow(monkeypatch) -> None:
    clear_state()
    monkeypatch.setattr(
        "telegram_bot.create_ready_gmail_draft",
        lambda to, subject, purpose: {
            "ok": True,
            "to": to,
            "subject": subject,
            "body": purpose,
            "draft_id": "draft-123",
        },
    )

    start = start_draft_email_flow("chat-1")
    to_response = handle_active_flow("chat-1", "hod@college.edu")
    subject_response = handle_active_flow("chat-1", "IA report update")
    final_response = handle_active_flow("chat-1", "I will submit the IA report before 2 PM.")

    assert "recipient email address" in start
    assert "Now send the email subject" in to_response
    assert "short description" in subject_response
    assert "GMAIL DRAFT READY" in final_response
    assert get_telegram_flow("chat-1") is None
    clear_state()
