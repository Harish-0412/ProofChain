from __future__ import annotations

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from google_workspace import READ_ONLY_SCOPES, WRITE_SCOPES, default_token_path, google_status
from settings import ENV_FILE, env_int, load_local_env, optional_env


def main() -> None:
    load_local_env()
    client_secret_file = optional_env("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
    if not client_secret_file:
        raise SystemExit("GOOGLE_OAUTH_CLIENT_SECRET_FILE is missing in agentcore/.env.local")
    client_secret_path = Path(client_secret_file)
    if not client_secret_path.exists():
        raise SystemExit(f"Google OAuth client secret file was not found: {client_secret_path}")

    token_path = Path(optional_env("GOOGLE_OAUTH_TOKEN_FILE") or default_token_path())
    token_path.parent.mkdir(parents=True, exist_ok=True)

    scopes = READ_ONLY_SCOPES + WRITE_SCOPES
    port = env_int("GOOGLE_OAUTH_LOCAL_PORT", 8765)
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), scopes=scopes)
    credentials = flow.run_local_server(host="localhost", port=port, prompt="consent")
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    _upsert_env("GOOGLE_OAUTH_TOKEN_FILE", str(token_path))

    print(json.dumps({"token_file": str(token_path), "status": google_status()}, indent=2))


def _upsert_env(key: str, value: str) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    replaced = False
    updated = []
    for line in lines:
        if line.startswith(f"{key}="):
            updated.append(f"{key}={value}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
