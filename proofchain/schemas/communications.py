"""Communication records for least-disclosure task coordination."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CommunicationRecord(BaseModel):
    communication_id: str
    task_id: str
    message_type: str
    recipient_ids: list[str]
    channel: str
    template_version: str = "1.0.0"
    content_hash: str
    disclosure_fields: list[str] = Field(default_factory=list)
    approval_event_id: str | None = None
    delivery_status: str = "not_sent"
    sent_at: datetime | None = None
