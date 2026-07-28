# ProofChain Three-Department Mock Institution

This deterministic, fully synthetic ProofChain fixture represents academic
year `2025-2026`.

| Code | Department | Students | Female | Male | Events |
|---|---|---:|---:|---:|---:|
| AIML | Artificial Intelligence and Machine Learning | 30 | 15 | 15 | 5 |
| AIDS | Artificial Intelligence and Data Science | 30 | 15 | 15 | 5 |
| CSE | Computer Science and Engineering | 30 | 15 | 15 | 5 |
| **Total** |  | **90** | **45** | **45** | **15** |

All names, events, approvals, signatures, emails, and evidence are fictional.
Email addresses use the reserved `example.invalid` domain.

## Dataset Layout

```text
mock_institution/
  student_master/
    AIML_students.json
    AIDS_students.xml
    CSE_students.csv
    all_students.xlsx
  departments/
    AIML/
    AIDS/
    CSE/
      event_reports/
      attendance_sheets/
      approval_documents/
      certificates/
      photos/
  dataset_manifest.json
  expected_outcomes.json
  validation_report.json
```

`student_master` is reference data and deliberately sits outside the evidence
source root. This prevents student rosters from being misclassified as
accreditation evidence. Attendance files use exactly the same identities.

## Evidence Design

Each department has one complete event for every configured requirement:

- `C3.2.1` - industry interaction
- `C5.1.3` - student enrichment
- `C6.3.2` - faculty development
- `C7.1.1` - extension and outreach
- `C1.2.1` - value-added courses

Every event contains an event report, a 30-student attendance register, a
signed approval document, a completion certificate register, and a synthetic
PNG photo record. The same event identity and institutional fields are used
across each bundle.

## Supported Formats

The corpus exercises PDF, XLSX, CSV, TSV, DOCX, TXT, Markdown, JSON, XML,
HTML, and PNG metadata-only evidence. The manifest records each artifact with
its relative path, byte size, and SHA-256 checksum.

## Validate The Fixture

```powershell
python scripts\validate_three_department_mock_data.py
```

The validator checks department scope, balanced student counts, identity
uniqueness, checksums, event identity, attendance reconciliation, evidence
bundle shape, and native format coverage.

## Run All 22 Agents

```powershell
python -m proofchain.cli run-complete `
  --source "sample_data\mock_institution\departments" `
  --departments AIML AIDS CSE `
  --academic-year 2025-2026 `
  --requirements C3.2.1 C5.1.3 C6.3.2 C7.1.1 C1.2.1 `
  --requested-by mock-data-validation `
  --objective "Validate the complete three-department synthetic accreditation dataset"
```

Use `dataset_manifest.json` as the source-of-truth inventory and
`expected_outcomes.json` as the acceptance contract.

## Verified Baseline

The complete lifecycle was executed against this fixture as
`RUN-20260728-B4AE`.

- 22 primary agents executed and persistence synchronized.
- 75 files were registered and classified.
- 0 documents were unresolved.
- 0 integrity findings and 0 evidence gaps were produced.
- 15 of 15 derived claims were supported.
- 0 canonical issues and 0 resolution gaps were created.
- Package quality returned `pass_for_human_approval`.
- Standard and agentic validators passed.
- Platform health passed all 8 checks.
- Agent 21 passed all 10 golden scenarios with `1.0` accuracy.

External submission remains `NOT_ELIGIBLE` by design until a human reviewer
records an independent approval bound to the final package hash.

The persisted machine-readable result is located at
`outputs/runs/RUN-20260728-B4AE/complete_run_summary.json`.
