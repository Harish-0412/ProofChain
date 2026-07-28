"""Submission eligibility, package freezing, and approval validation."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from proofchain.schemas.institutional import SubmissionInput


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate_submission(
    request: SubmissionInput,
) -> tuple[str, str | None, list[str]]:
    reasons: list[str] = []
    path = Path(request.package_path).resolve()
    if not path.is_file():
        return "NOT_ELIGIBLE", None, ["Approved package file is missing."]
    package_hash = file_sha256(path)
    if package_hash != request.expected_package_hash:
        reasons.append("Package hash differs from the approved package version.")
    if request.quality_status not in {"pass_for_human_approval", "pass_with_warnings"}:
        reasons.append("Package quality status is not eligible for submission.")
    approved = [
        item
        for item in request.approvals
        if item.decision == "approved"
        and item.independent
        and item.package_hash == package_hash
    ]
    rejected = [item for item in request.approvals if item.decision == "rejected"]
    if rejected:
        reasons.append("A final package approval was rejected.")
    if not approved:
        reasons.append("An independent approval for the frozen package hash is required.")
    if request.submission_deadline and request.submission_deadline < datetime.now(
        tz=timezone.utc
    ):
        reasons.append("The submission deadline has passed.")
    if reasons:
        return "NOT_ELIGIBLE", package_hash, reasons
    if not request.final_confirmation:
        return (
            "NEEDS_FINAL_CONFIRMATION",
            package_hash,
            ["Final human submission confirmation is required."],
        )
    return "ELIGIBLE", package_hash, ["All submission gates passed."]

