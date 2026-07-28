"""Idempotent notification adapters for local, SMTP, and webhook delivery."""

from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol
from urllib.request import Request, urlopen
from uuid import uuid4

from proofchain.core.paths import get_run_dir
from proofchain.schemas.production import DeliveryAttempt, DeliveryChannel, NotificationInput


class NotificationAdapter(Protocol):
    def deliver(self, request: NotificationInput, channel: DeliveryChannel) -> DeliveryAttempt: ...


class RecordingNotificationAdapter:
    """Safe local adapter that records a delivery envelope without network access."""

    def deliver(self, request: NotificationInput, channel: DeliveryChannel) -> DeliveryAttempt:
        path = get_run_dir(request.workflow.run_id) / "notification_outbox.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        message_id = f"LOCAL-{uuid4().hex[:12].upper()}"
        envelope = {
            "message_id": message_id,
            "task_id": request.task_id,
            "recipient_id": request.recipient_id,
            "destination": channel.destination,
            "subject": request.subject,
            "message": request.message,
            "correlation_token": request.correlation_token,
            "idempotency_key": request.idempotency_key,
        }
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(envelope, ensure_ascii=True, sort_keys=True) + "\n")
        return DeliveryAttempt(
            channel_type=channel.channel_type,
            destination=channel.destination,
            status="delivered",
            provider_message_id=message_id,
        )


class SmtpNotificationAdapter:
    def deliver(self, request: NotificationInput, channel: DeliveryChannel) -> DeliveryAttempt:
        host = os.getenv("PROOFCHAIN_SMTP_HOST")
        sender = os.getenv("PROOFCHAIN_SMTP_FROM")
        if not host or not sender:
            raise RuntimeError("SMTP requires PROOFCHAIN_SMTP_HOST and PROOFCHAIN_SMTP_FROM.")
        port = int(os.getenv("PROOFCHAIN_SMTP_PORT", "465"))
        message = EmailMessage()
        message["From"] = sender
        message["To"] = channel.destination
        message["Subject"] = request.subject
        message["X-ProofChain-Correlation"] = request.correlation_token
        message.set_content(request.message)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as smtp:
            username = os.getenv("PROOFCHAIN_SMTP_USERNAME")
            password = os.getenv("PROOFCHAIN_SMTP_PASSWORD")
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
        return DeliveryAttempt(
            channel_type="email",
            destination=channel.destination,
            status="delivered",
            provider_message_id=message["Message-ID"] or request.idempotency_key,
        )


class WebhookNotificationAdapter:
    def deliver(self, request: NotificationInput, channel: DeliveryChannel) -> DeliveryAttempt:
        if not channel.destination.startswith("https://"):
            raise ValueError("Webhook destinations must use HTTPS.")
        body = json.dumps(
            {
                "text": request.message,
                "subject": request.subject,
                "task_id": request.task_id,
                "correlation_token": request.correlation_token,
                "idempotency_key": request.idempotency_key,
            }
        ).encode("utf-8")
        outbound = Request(
            channel.destination,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Idempotency-Key": request.idempotency_key,
            },
            method="POST",
        )
        with urlopen(outbound, timeout=15) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Webhook returned HTTP {response.status}.")
            provider_id = response.headers.get("X-Request-ID", request.idempotency_key)
        return DeliveryAttempt(
            channel_type=channel.channel_type,
            destination=channel.destination,
            status="delivered",
            provider_message_id=provider_id,
        )


def adapter_for(channel_type: str) -> NotificationAdapter:
    if channel_type == "recording":
        return RecordingNotificationAdapter()
    if channel_type == "email":
        return SmtpNotificationAdapter()
    if channel_type in {"teams", "slack", "webhook"}:
        return WebhookNotificationAdapter()
    raise ValueError(f"Unsupported notification channel: {channel_type}")


def idempotency_ledger_path(run_id: str) -> Path:
    return get_run_dir(run_id) / "notification_idempotency.json"

