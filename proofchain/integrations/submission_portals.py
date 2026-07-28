"""Human-gated local and HTTPS package submission adapters."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from urllib.request import Request, urlopen
from uuid import uuid4

from proofchain.core.paths import get_run_dir
from proofchain.schemas.institutional import SubmissionInput, SubmissionReceipt


class SubmissionPortal(Protocol):
    def submit(self, request: SubmissionInput, package_hash: str) -> SubmissionReceipt: ...


class RecordingSubmissionPortal:
    def submit(self, request: SubmissionInput, package_hash: str) -> SubmissionReceipt:
        source = Path(request.package_path).resolve()
        package_dir = get_run_dir(request.workflow.run_id) / "submission_outbox"
        package_dir.mkdir(parents=True, exist_ok=True)
        retained_package = package_dir / f"{package_hash}{source.suffix.lower()}"
        if not retained_package.exists():
            shutil.copy2(source, retained_package)
        receipt = SubmissionReceipt(
            receipt_id=f"REC-{uuid4().hex[:12].upper()}",
            package_id=request.package_id,
            package_hash=package_hash,
            portal_type="recording",
            destination=request.portal_destination,
            submitted_at=datetime.now(tz=timezone.utc),
            provider_reference=str(retained_package.resolve()),
        )
        path = get_run_dir(request.workflow.run_id) / "submission_outbox.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(receipt.model_dump_json() + "\n")
        return receipt


class HttpsSubmissionPortal:
    def submit(self, request: SubmissionInput, package_hash: str) -> SubmissionReceipt:
        if not request.portal_destination.startswith("https://"):
            raise ValueError("External submission portals must use HTTPS.")
        package_path = Path(request.package_path).resolve()
        payload = package_path.read_bytes()
        outbound = Request(
            request.portal_destination,
            data=payload,
            headers={
                "Content-Type": "application/zip",
                "Idempotency-Key": request.idempotency_key,
                "X-ProofChain-Package-ID": request.package_id,
                "X-ProofChain-Package-Hash": package_hash,
                "X-ProofChain-Package-Name": package_path.name,
            },
            method="POST",
        )
        with urlopen(outbound, timeout=30) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Submission portal returned HTTP {response.status}.")
            provider_reference = response.headers.get(
                "X-Receipt-ID", request.idempotency_key
            )
        return SubmissionReceipt(
            receipt_id=f"REC-{uuid4().hex[:12].upper()}",
            package_id=request.package_id,
            package_hash=package_hash,
            portal_type="https",
            destination=request.portal_destination,
            submitted_at=datetime.now(tz=timezone.utc),
            provider_reference=provider_reference,
        )


def portal_for(portal_type: str) -> SubmissionPortal:
    if portal_type == "recording":
        return RecordingSubmissionPortal()
    if portal_type == "https":
        return HttpsSubmissionPortal()
    raise ValueError(f"Unsupported submission portal: {portal_type}")
