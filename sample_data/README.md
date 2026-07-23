# Sample Dataset Structure

This folder defines the synthetic dataset plan for the ProofChain MVP.

The dataset should be realistic enough to test ingestion, extraction, mapping, verification, task generation, and audit package generation.

## Folder Structure

```text
sample_data/
  departments/
    CSE/
      event_reports/
      attendance_sheets/
      approval_documents/
      certificates/
      photos/
    ECE/
      event_reports/
      attendance_sheets/
      approval_documents/
      certificates/
      photos/
    EEE/
      event_reports/
      attendance_sheets/
      approval_documents/
      certificates/
      photos/
    Mechanical/
      event_reports/
      attendance_sheets/
      approval_documents/
      certificates/
      photos/
    Civil/
      event_reports/
      attendance_sheets/
      approval_documents/
      certificates/
      photos/
  requirements/
    C3.2.1/
    C5.1.3/
    C6.3.2/
    C7.1.1/
    C1.2.1/
  injected_errors/
```

## Target Counts

- 20 to 30 sample event reports; current generated set has 27 event report PDFs including deliberate duplicates and wrong-field variants
- 5 department folders
- 5 accreditation requirements
- 5 attendance spreadsheets
- 10 approval documents
- 12 certificate PDFs
- 10 photo evidence records
- A few deliberately incorrect or duplicated files

## Generated Manifests

- `dataset_manifest.json`
- `injected_errors/injected_errors_manifest.json`
- `extraction_outputs/expected_extraction_results.json`
- `extraction_outputs/extracted_fields.json`

## Injected Errors

Include examples of:

- Participant count mismatch
- Missing approval document
- Missing signature
- Duplicate event report
- Duplicate student rows
- Wrong academic year
- Wrong department
- Incorrect requirement mapping

## First Demo Dataset

The first demo should focus on:

```text
Department: CSE
Requirement: C3.2.1
Claim: 120 students attended an industry workshop
Expected issue: attendance sheet contains fewer unique students and approval letter is unsigned
```
