from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from email.message import EmailMessage
import base64

from settings import APP_DIR, load_local_env, optional_env


READ_ONLY_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/gmail.metadata",
]

WRITE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.compose",
]


def google_status() -> dict[str, Any]:
    load_local_env()
    client_secret = optional_env("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
    token_file = optional_env("GOOGLE_OAUTH_TOKEN_FILE")
    token_scopes = get_token_scopes()
    desired_scopes = READ_ONLY_SCOPES + WRITE_SCOPES
    return {
        "configured": bool(client_secret and token_file and Path(token_file).exists()),
        "client_secret_file_set": bool(client_secret),
        "token_file_exists": bool(token_file and Path(token_file).exists()),
        "read_only_scopes": READ_ONLY_SCOPES,
        "write_scopes_after_confirmation": WRITE_SCOPES,
        "token_scopes": token_scopes,
        "missing_scopes": [scope for scope in desired_scopes if scope not in token_scopes],
        "note": (
            "Google access requires OAuth consent from the Google account owner. "
            "Telegram credentials alone cannot grant Gmail or Calendar access."
        ),
    }


def get_token_scopes() -> list[str]:
    load_local_env()
    token_file = optional_env("GOOGLE_OAUTH_TOKEN_FILE")
    if not token_file or not Path(token_file).exists():
        return []
    try:
        import json

        with Path(token_file).open("r", encoding="utf-8") as handle:
            token = json.load(handle)
        return token.get("scopes", [])
    except Exception:
        return []


def has_google_scope(scope: str) -> bool:
    return scope in get_token_scopes()


def list_google_calendar_events(hours: int = 24) -> list[dict[str, Any]]:
    service = _build_service("calendar", "v3")
    now = datetime.now(timezone.utc)
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=(now + timedelta(hours=hours)).isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        )
        .execute()
    )
    return events_result.get("items", [])


def list_google_calendar_events_between(start: datetime, end: datetime) -> list[dict[str, Any]]:
    service = _build_service("calendar", "v3")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start.astimezone(timezone.utc).isoformat(),
            timeMax=end.astimezone(timezone.utc).isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=30,
        )
        .execute()
    )
    return events_result.get("items", [])


def create_google_calendar_event(title: str, start: str, end: str, reason: str = "") -> dict[str, Any]:
    service = _build_service("calendar", "v3")
    event = {
        "summary": title,
        "description": f"Created by FacultyFlow after user confirmation.\n\nReason: {reason}",
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return {"id": created.get("id"), "htmlLink": created.get("htmlLink"), "status": created.get("status")}


def list_gmail_metadata(max_results: int = 10, label_ids: list[str] | None = None) -> list[dict[str, Any]]:
    service = _build_service("gmail", "v1")
    list_kwargs: dict[str, Any] = {"userId": "me", "maxResults": max_results}
    if label_ids:
        list_kwargs["labelIds"] = label_ids
    messages = service.users().messages().list(**list_kwargs).execute()
    results = []
    for item in messages.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )
        headers = {header["name"]: header["value"] for header in msg.get("payload", {}).get("headers", [])}
        results.append(
            {
                "id": msg["id"],
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "snippet": msg.get("snippet"),
                "labelIds": msg.get("labelIds", []),
            }
        )
    return results


def list_gmail_digest_messages(max_results: int = 15) -> list[dict[str, Any]]:
    try:
        messages = list_gmail_metadata(max_results=max_results, label_ids=["UNREAD", "IMPORTANT"])
        if messages:
            return messages
    except Exception:
        pass
    try:
        messages = list_gmail_metadata(max_results=max_results, label_ids=["UNREAD"])
        if messages:
            return messages
    except Exception:
        pass
    return list_gmail_metadata(max_results=max_results)


def send_gmail_message(to: str, subject: str, body: str) -> dict[str, Any]:
    service = _build_service("gmail", "v1")
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    sent = service.users().messages().send(userId="me", body={"raw": encoded}).execute()
    return {"id": sent.get("id"), "threadId": sent.get("threadId"), "labelIds": sent.get("labelIds", [])}


def create_gmail_draft(to: str, subject: str, body: str) -> dict[str, Any]:
    compose_scope = "https://www.googleapis.com/auth/gmail.compose"
    if not has_google_scope(compose_scope):
        return {
            "ok": False,
            "reason": "missing_scope",
            "missing_scope": compose_scope,
            "message": (
                "Gmail draft creation needs the gmail.compose OAuth scope. "
                "Please rerun: uv run python google_oauth.py, approve the updated scopes, then try again."
            ),
        }
    service = _build_service("gmail", "v1")
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft = service.users().drafts().create(userId="me", body={"message": {"raw": encoded}}).execute()
    return {
        "ok": True,
        "draft_id": draft.get("id"),
        "message_id": draft.get("message", {}).get("id"),
        "thread_id": draft.get("message", {}).get("threadId"),
        "status": "created_in_gmail_drafts",
    }


def _build_service(service_name: str, version: str) -> Any:
    load_local_env()
    try:
        from google.oauth2.credentials import Credentials
        import httplib2
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Google API dependencies are not installed. Run uv sync before enabling Google integrations.") from exc

    token_file = optional_env("GOOGLE_OAUTH_TOKEN_FILE")
    if not token_file or not Path(token_file).exists():
        raise RuntimeError(
            "Google OAuth is not configured. Complete OAuth consent first and set GOOGLE_OAUTH_TOKEN_FILE."
        )
    credentials = Credentials.from_authorized_user_file(token_file)
    http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=10))
    return build(service_name, version, http=http, cache_discovery=False)


def default_token_path() -> Path:
    return APP_DIR / "secrets" / "google_token.json"
