from __future__ import annotations

import json
import sys

from settings import load_local_env, optional_env
from telegram_bot import telegram_api


def main() -> None:
    load_local_env()
    token = optional_env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing in agentcore/.env.local")

    command = sys.argv[1] if len(sys.argv) > 1 else "get-me"
    if command == "get-me":
        print(json.dumps(telegram_api(token, "getMe", {}), indent=2))
        return
    if command == "chat-ids":
        updates = telegram_api(token, "getUpdates", {"timeout": 1, "allowed_updates": ["message"]})
        chats = []
        for update in updates.get("result", []):
            message = update.get("message") or {}
            chat = message.get("chat") or {}
            if chat:
                chats.append(
                    {
                        "chat_id": chat.get("id"),
                        "type": chat.get("type"),
                        "username": chat.get("username"),
                        "first_name": chat.get("first_name"),
                    }
                )
        print(json.dumps(chats, indent=2))
        return
    if command == "webhook-info":
        print(json.dumps(telegram_api(token, "getWebhookInfo", {}), indent=2))
        return
    if command == "delete-webhook":
        print(json.dumps(telegram_api(token, "deleteWebhook", {"drop_pending_updates": False}), indent=2))
        return

    raise SystemExit("Usage: python telegram_admin.py [get-me|chat-ids|webhook-info|delete-webhook]")


if __name__ == "__main__":
    main()
