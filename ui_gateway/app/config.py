import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ProofChain UI Gateway"
    version: str = "0.2.0"
    project_root: str = os.getenv(
        "PROOFCHAIN_PROJECT_ROOT",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
    )
    outputs_dir: str = os.getenv(
        "PROOFCHAIN_RUNS_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../outputs/runs")),
    )
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    allowlisted_commands: set[str] = {
        "run-pipeline",
        "run-complete",
        "validate-run",
        "validate-agentic-run",
        "approve-decision",
        "activate-resolution-task",
        "record-task-response",
        "revalidate-closure",
        "build-audit-package",
        "review-audit-package",
        "resume-run",
        "replay-run",
        "health-check",
    }

settings = Settings()
