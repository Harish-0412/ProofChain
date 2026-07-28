from __future__ import annotations

from typing import Any

from settings import env_bool, env_int, load_local_env, optional_env


SYSTEM_PROMPT = """You are FacultyFlow, a cautious academic work-planning assistant.
Use short, practical responses for Telegram. Never claim an external action was
completed unless a tool receipt confirms it. For Gmail, Calendar, and Telegram
write actions, produce a draft and ask for confirmation first."""


def is_bedrock_enabled() -> bool:
    load_local_env()
    return env_bool("FACULTYFLOW_ENABLE_BEDROCK", False)


def ask_bedrock(prompt: str, context: str = "") -> dict[str, Any]:
    load_local_env()
    if not is_bedrock_enabled():
        return {
            "enabled": False,
            "text": "Bedrock is disabled by FACULTYFLOW_ENABLE_BEDROCK=false, so no model tokens were used.",
        }

    import boto3

    region = optional_env("AWS_REGION") or "ap-south-1"
    model_id = optional_env("BEDROCK_MODEL_ID") or "amazon.nova-micro-v1:0"
    max_tokens = env_int("BEDROCK_MAX_TOKENS", 350)

    client = boto3.client("bedrock-runtime", region_name=region)
    response = client.converse(
        modelId=model_id,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[
            {
                "role": "user",
                "content": [{"text": f"Context:\n{context}\n\nUser request:\n{prompt}"}],
            }
        ],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
    )
    text = "".join(part.get("text", "") for part in response["output"]["message"]["content"])
    usage = response.get("usage", {})
    return {
        "enabled": True,
        "model_id": model_id,
        "region": region,
        "max_tokens": max_tokens,
        "text": text,
        "usage": usage,
    }
