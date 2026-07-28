import asyncio
import json
import os
from typing import AsyncGenerator
from app.config import settings
from app.services.path_guard import PathGuard

class EventStreamer:
    @staticmethod
    async def stream_events(run_id: str) -> AsyncGenerator[str, None]:
        safe_run_id = PathGuard.validate_run_id(run_id)
        filepath = PathGuard.safe_join(settings.outputs_dir, safe_run_id, "workflow_events.jsonl")

        last_pos = 0
        while True:
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        f.seek(last_pos)
                        lines = f.readlines()
                        last_pos = f.tell()

                        for line in lines:
                            line = line.strip()
                            if line:
                                try:
                                    event_data = json.loads(line)
                                    yield f"data: {json.dumps(event_data)}\n\n"
                                except json.JSONDecodeError:
                                    pass
                except Exception:
                    pass
            else:
                # If file doesn't exist yet, yield a heartbeat comment
                yield ": heartbeat\n\n"

            await asyncio.sleep(2.0)
