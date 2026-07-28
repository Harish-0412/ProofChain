from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_three_department_mock_data import validate


ROOT = Path("sample_data/mock_institution")


def test_three_department_fixture_contract() -> None:
    report = validate(ROOT)

    assert report["valid"], report["errors"]
    assert report["summary"] == {
        "departments": 3,
        "students": 90,
        "events": 15,
        "evidence_files": 75,
        "checks_passed": 11,
        "checks_total": 11,
    }


def test_manifest_declares_balanced_departments_and_formats() -> None:
    manifest = json.loads((ROOT / "dataset_manifest.json").read_text(encoding="utf-8"))

    assert set(manifest["departments"]) == {"AIML", "AIDS", "CSE"}
    assert all(
        department["student_count"] == 30
        and department["female_count"] == 15
        and department["male_count"] == 15
        for department in manifest["departments"].values()
    )
    assert {
        ".pdf",
        ".xlsx",
        ".csv",
        ".tsv",
        ".docx",
        ".txt",
        ".md",
        ".json",
        ".xml",
        ".html",
        ".png",
    }.issubset(manifest["supported_format_inventory"])
