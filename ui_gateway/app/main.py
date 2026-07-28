"""ProofChain artifact projection and governed command gateway."""

from __future__ import annotations

import os

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.services.command_executor import CommandExecutor
from app.services.event_streamer import EventStreamer
from proofchain.services.ingestion_capabilities import IngestionCapabilityService
from proofchain.services.platform_health import PlatformHealthService
from proofchain.services.run_projection import RunProjectionService


projector = RunProjectionService()
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="ProofChain artifact projections and governed CLI sidecar.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/ui-api/health")
def health_check(run_id: str | None = None):
    result = PlatformHealthService().inspect(run_id)
    result.update(
        service=settings.app_name,
        version=settings.version,
        outputs_dir=settings.outputs_dir,
        outputs_dir_exists=os.path.exists(settings.outputs_dir),
    )
    return result


@app.get("/ui-api/runs")
def get_runs():
    return projector.list_runs()


@app.get("/ui-api/runs/{run_id}")
def get_run_detail(run_id: str):
    _require_run(run_id)
    return projector.run_summary(run_id)


@app.get("/ui-api/runs/{run_id}/metrics")
def get_run_metrics(run_id: str):
    _require_run(run_id)
    return projector.dashboard_metrics(run_id)


@app.get("/ui-api/runs/{run_id}/workflow-status")
def get_workflow_status(run_id: str):
    _require_run(run_id)
    return projector.workflow_status(run_id)


@app.get("/ui-api/runs/{run_id}/agents")
def get_run_agents(run_id: str):
    _require_run(run_id)
    return projector.agents(run_id)


@app.get("/ui-api/runs/{run_id}/agents/{agent_id}")
def get_run_agent(run_id: str, agent_id: int):
    _require_run(run_id)
    item = projector.agent_detail(run_id, agent_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} was not found.")
    return item


@app.get("/ui-api/runs/{run_id}/goals")
def get_run_goals(run_id: str):
    _require_run(run_id)
    return projector.goals(run_id)


@app.get("/ui-api/runs/{run_id}/events")
def get_run_events(run_id: str, limit: int = 100, offset: int = 0):
    _require_run(run_id)
    return projector.events(run_id, limit=limit, offset=offset)


@app.get("/ui-api/runs/{run_id}/events/stream")
async def stream_run_events(run_id: str):
    _require_run(run_id)
    return StreamingResponse(
        EventStreamer.stream_events(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/ui-api/runs/{run_id}/messages")
def get_run_messages(run_id: str):
    _require_run(run_id)
    return projector.messages(run_id)


@app.get("/ui-api/runs/{run_id}/evidence")
def get_run_evidence(run_id: str):
    _require_run(run_id)
    return projector.evidence(run_id)


@app.get("/ui-api/runs/{run_id}/claims")
def get_run_claims(run_id: str):
    _require_run(run_id)
    return projector.claims(run_id)


@app.get("/ui-api/runs/{run_id}/issues")
def get_run_issues(run_id: str):
    _require_run(run_id)
    return projector.issues(run_id)


@app.get("/ui-api/runs/{run_id}/tasks")
def get_run_tasks(run_id: str):
    _require_run(run_id)
    return projector.tasks(run_id)


@app.get("/ui-api/runs/{run_id}/approvals")
def get_run_approvals(run_id: str):
    _require_run(run_id)
    return projector.approvals(run_id)


@app.get("/ui-api/runs/{run_id}/package")
def get_run_package(run_id: str):
    _require_run(run_id)
    return projector.package(run_id)


@app.get("/ui-api/runs/{run_id}/governance")
def get_run_governance(run_id: str):
    _require_run(run_id)
    return projector.governance(run_id)


@app.get("/ui-api/ingestion/capabilities")
def get_ingestion_capabilities():
    return IngestionCapabilityService().report().model_dump(mode="json")


@app.post("/ui-api/ingestion/inspect")
def inspect_ingestion(payload: dict = Body(...)):
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        raise HTTPException(status_code=400, detail="'paths' must be a list.")
    return IngestionCapabilityService().report(paths).model_dump(mode="json")


@app.post("/ui-api/commands/{command_name}")
def execute_command(command_name: str, payload: dict = Body(...)):
    result = CommandExecutor.execute_command(
        command_name,
        payload=payload,
        rationale=payload.get("rationale", ""),
    )
    if not result.get("success", True):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/ui-api/jobs/{job_id}")
def get_job_status(job_id: str):
    result = CommandExecutor.get_job(job_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' was not found.")
    return result


def _require_run(run_id: str) -> None:
    try:
        available = projector.run_exists(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not available:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' was not found.")
