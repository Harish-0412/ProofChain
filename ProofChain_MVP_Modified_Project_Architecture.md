# ProofChain MVP
## Modified Project Architecture and Build Blueprint

**Project Name:** ProofChain  
**MVP Focus:** Accreditation evidence ingestion, verification, gap detection, task generation, notification, and audit package generation  
**Primary Users:** IQAC coordinators, accreditation coordinators, HoDs, department evidence coordinators, reviewers  
**Primary Goal:** Demonstrate one complete accreditation evidence workflow using realistic sample institutional documents.

---

# 1. MVP Positioning

ProofChain should be built first as an evidence-governance MVP, not as a broad AI document chatbot.

The first version must clearly prove this chain:

```text
Accreditation Requirement
-> Institutional Claim
-> Supporting Evidence
-> Extraction
-> Mapping
-> Integrity Verification
-> Gap Detection
-> Task Assignment
-> Department Response
-> Human Approval
-> Audit-Ready Package
```

The system should show that an institution can move from scattered files to defensible proof with traceability.

---

# 2. Modified MVP Objective

The MVP should demonstrate that ProofChain can:

1. Ingest evidence from a folder or Google Drive source.
2. Register each file with a unique evidence ID.
3. Extract useful fields from PDFs and spreadsheets.
4. Map evidence to accreditation requirements.
5. Detect missing, duplicate, and contradictory evidence.
6. Generate corrective tasks.
7. Prepare department notifications.
8. Track department response status.
9. Calculate dashboard impact metrics.
10. Generate an audit-ready package.

---

# 3. MVP Dataset Scope

Use a synthetic but realistic dataset.

## 3.1 Departments

Use four department folders:

- CSE
- AIML
- AIDS
- Mechanical

## 3.2 Accreditation Requirements

Use five sample accreditation requirements:

| Requirement ID | Requirement Name | Example Evidence Needed |
|---|---|---|
| C3.2.1 | Industry interaction activities | Event reports, attendance sheets, approvals, photos |
| C5.1.3 | Student enrichment programmes | Certificates, reports, participant lists |
| C6.3.2 | Faculty development activities | FDP certificates, approval letters, faculty profiles |
| C7.1.1 | Extension and outreach activities | Activity reports, photos, beneficiary lists |
| C1.2.1 | Value-added courses | Course reports, attendance sheets, completion certificates |

## 3.3 Sample Evidence Files

Approximate sample set:

- 20 to 30 sample event reports
- 5 department folders
- 5 accreditation requirements
- 5 attendance spreadsheets
- 10 approval documents
- A few event photographs or placeholder image evidence records
- A few deliberately incorrect, missing, or duplicated files

## 3.4 Deliberately Injected Errors

The demo dataset should include:

- Participant count mismatch
- Missing approval document
- Missing signature in approval letter
- Duplicate event report
- Duplicate student rows in attendance spreadsheet
- Wrong academic year
- Incorrect department name
- Event report mapped to the wrong requirement
- Same evidence reused for unrelated claims
- Missing participant list

---

# 4. Ingestion Strategy

ProofChain should support two ingestion modes in the MVP design.

## 4.1 Manual Folder Upload

Manual upload is the simplest and most reliable MVP path.

The user uploads a local folder or selected files containing:

- PDF event reports
- PDF approval documents
- Excel attendance sheets
- Certificates
- Photographs

The system then registers, extracts, maps, and verifies the documents.

## 4.2 Google Drive Ingestion

Google Drive ingestion is doable and should be included in the implementation architecture.

However, it should be added as a connector source beside manual upload, not as the only ingestion path.

Recommended design:

```text
Google Drive Folder
-> Drive Connector
-> Evidence Intake Queue
-> Evidence Registry
-> Document Extraction
-> Evidence Mapping
-> Integrity Checks
-> Gap and Task Generation
```

## 4.3 Why Google Drive Should Be Optional For MVP

Google Drive requires:

- Google Cloud project setup
- OAuth consent configuration
- Drive API enablement
- Client ID and client secret
- User authorization flow
- Token storage
- Permission handling
- Folder access validation

Because this can slow down the first working version, the MVP should work with manual upload first, while the code architecture should keep Drive ingestion ready to plug in.

## 4.4 Google Drive Connector Responsibilities

The Google Drive connector should:

- Accept a Google Drive folder link or folder ID.
- Authenticate the authorized institutional user.
- List supported files inside the selected folder.
- Read file metadata.
- Download or stream supported files.
- Preserve original file names.
- Store Google Drive file ID.
- Store source URL.
- Store last modified timestamp.
- Detect whether a file was already ingested.
- Queue new or changed files for processing.

## 4.5 Supported Drive File Types

The MVP should support:

- PDF
- XLSX
- CSV
- DOCX, optional
- PNG/JPG, optional for photo evidence

Google Docs, Sheets, and Slides can be exported later as:

- Google Docs -> PDF or DOCX
- Google Sheets -> XLSX or CSV
- Google Slides -> PDF

---

# 5. MVP System Architecture

Use a simple but expandable architecture.

```text
User Interface
-> Ingestion Source
   -> Manual Upload
   -> Google Drive Connector
-> Evidence Intake Service
-> Evidence Registry
-> Document Extraction Service
-> Evidence Mapping Service
-> Integrity Rule Engine
-> Gap and Task Service
-> Notification Service
-> Dashboard Metrics Service
-> Audit Package Generator
```

For the MVP, PostgreSQL or SQLite can be used for structured data. Object storage can be local storage first, then MinIO or S3 later.

Qdrant and Neo4j should be postponed until after the first complete workflow is working.

---

# 6. MVP Agent Model

Instead of starting with ten fully autonomous agents, the first build should use a controlled workflow with agent-like modules.

## 6.1 Required MVP Agents

| Agent | MVP Responsibility |
|---|---|
| Supervisor Agent | Orchestrates the workflow and records trace |
| Evidence Intake Agent | Registers files and assigns evidence IDs |
| Document Understanding Agent | Extracts fields from PDF and spreadsheet files |
| Evidence Mapping Agent | Maps evidence to accreditation requirements |
| Evidence Integrity Agent | Runs deterministic checks |
| Gap Analysis Agent | Creates gaps and corrective tasks |
| Department Liaison Agent | Drafts or sends department notifications |
| Audit Package Agent | Generates final audit package |

## 6.2 Deferred Agents

The following can be added after MVP:

- Quality Review Agent
- Ownership and Responsibility Agent
- Advanced Claim Validation Agent
- RAG-based Accreditation Advisor
- Evidence Graph Agent

---

# 7. Evidence Processing Workflow

## 7.1 Step-by-Step Flow

1. User selects an accreditation requirement.
2. User uploads a folder or connects a Google Drive folder.
3. Evidence Intake Agent registers each file.
4. System calculates checksum and detects exact duplicates.
5. Document Understanding Agent extracts text, tables, dates, counts, departments, and signatures.
6. Evidence Mapping Agent maps each file to one or more requirements.
7. Integrity Agent runs deterministic rules.
8. Gap Analysis Agent identifies missing or inconsistent evidence.
9. System creates corrective tasks for departments.
10. Department Liaison Agent prepares notification messages.
11. Dashboard updates impact metrics.
12. User reviews and approves resolved evidence.
13. Audit Package Agent generates a package.
14. System records complete trace.

## 7.2 Demo Flow

The demonstration should show:

- Uploading a folder of documents
- Automatic extraction
- Evidence mapping
- Detection of missing and inconsistent evidence
- Automatic task generation
- Department notification
- Generation of an audit-ready package

---

# 8. Deterministic Integrity Rules

The MVP should prioritize deterministic verification rules.

## 8.1 Required Rules

| Rule ID | Rule Name | Purpose |
|---|---|---|
| DUP-001 | Exact duplicate detection | Detect same file using checksum |
| CNT-001 | Participant count reconciliation | Compare event report count with attendance count |
| DATE-001 | Academic year validation | Ensure event date belongs to selected academic year |
| DOC-001 | Required evidence checklist | Detect missing required document types |
| SIGN-001 | Approval signature check | Detect missing signature or approval marker |
| DEPT-001 | Department consistency check | Compare department in file with selected department |
| MAP-001 | Requirement mapping confidence | Flag weak or incorrect evidence mapping |

## 8.2 Example Rule Result

```json
{
  "rule_id": "CNT-001",
  "severity": "high",
  "status": "failed",
  "finding": "Event report claims 120 participants, but attendance sheet contains 108 unique students.",
  "expected_value": 120,
  "observed_value": 108,
  "recommended_action": "Request corrected attendance sheet or revise claim."
}
```

---

# 9. Evidence Mapping

Evidence mapping should initially combine:

- File name patterns
- Folder name
- Extracted document type
- Extracted keywords
- Requirement checklist
- Optional LLM classification later

For MVP, mapping does not need advanced RAG. It only needs to be good enough to demonstrate that evidence can be connected to requirements.

Example:

```text
AI_Workshop_Report_CSE_2025.pdf
-> document_type: event_report
-> department: CSE
-> likely_requirement: C3.2.1
-> mapping_confidence: 0.88
```

---

# 10. Task Generation

When gaps are found, ProofChain should automatically create tasks.

## 10.1 Task Examples

| Gap | Task |
|---|---|
| Missing approval letter | Upload signed approval letter |
| Count mismatch | Verify participant count and upload corrected sheet |
| Duplicate evidence | Confirm correct evidence file |
| Wrong academic year | Upload evidence from correct academic year |
| Missing signature | Upload signed document or approval proof |

## 10.2 Task Fields

Each task should include:

- Task ID
- Requirement ID
- Evidence ID, if available
- Department
- Assigned owner
- Priority
- Due date
- Status
- Gap reason
- Required correction
- Notification status

---

# 11. Department Notification

For MVP, notifications can be shown as generated message drafts.

Actual email, Google Chat, Slack, Teams, or WhatsApp delivery can be added later.

## 11.1 MVP Notification Behavior

The system should:

- Generate a department-specific message.
- List unresolved evidence gaps.
- Include due date.
- Include responsible coordinator.
- Require human approval before sending.
- Mark department as awaiting response.

## 11.2 Example Notification

```text
Subject: Evidence correction required for C3.2.1 - CSE

Dear CSE Coordinator,

ProofChain found the following issues in the submitted evidence:

1. Event report states 120 participants, but attendance sheet contains 108 unique students.
2. Approval document is missing HoD signature.
3. One event photograph appears duplicated from another activity.

Please upload corrected evidence by 30 July 2026.
```

---

# 12. Dashboard Metrics

The dashboard should display the impact metrics requested for the MVP.

## 12.1 Required Metrics

| Metric | Meaning |
|---|---|
| Evidence completeness percentage | Percentage of required evidence documents available |
| Number of unresolved evidence gaps | Open issues requiring correction |
| Contradictions detected | Count of failed consistency checks |
| Duplicate evidence detected | Number of duplicate or reused evidence files |
| Departments awaiting response | Departments with pending corrective tasks |
| Average verification time | Average time taken to verify each evidence item |
| Estimated manual hours saved | Estimated manual review time avoided |
| Audit readiness score | Combined score showing package readiness |

## 12.2 Suggested MVP Formulas

```text
Evidence Completeness =
available_required_documents / total_required_documents * 100
```

```text
Audit Readiness Score =
0.30 * Evidence Completeness
+ 0.25 * Integrity Pass Rate
+ 0.20 * Gap Resolution Rate
+ 0.15 * Approval Completion
+ 0.10 * Package Completion
```

```text
Estimated Manual Hours Saved =
processed_documents * average_manual_review_minutes_per_document / 60
```

Recommended MVP assumption:

```text
average_manual_review_minutes_per_document = 8
```

---

# 13. Audit Package Generation

The MVP should generate an audit-ready package containing:

```text
audit_package/
  manifest.json
  evidence_index.xlsx
  requirement_summary.pdf
  findings_report.pdf
  traceability_report.pdf
  C3.2.1/
    event_reports/
    attendance_sheets/
    approval_documents/
    certificates/
    photos/
```

## 13.1 Package Manifest

The manifest should record:

- Package ID
- Requirement IDs
- Departments included
- Academic year
- Evidence IDs
- File names
- Checksums
- Verification status
- Approval status
- Generated timestamp

---

# 14. Human Approval

Human approval should be mandatory for:

- Marking a claim as verified
- Sending department notifications
- Accepting corrected evidence
- Generating final audit package
- Overriding failed integrity checks

The MVP can simulate approvals in the interface, but the architecture should record approvals as formal workflow events.

---

# 15. Recommended MVP Data Model

Use these core tables or equivalent structured records:

- users
- departments
- accreditation_requirements
- evidence
- evidence_versions
- extracted_fields
- evidence_mappings
- integrity_findings
- gaps
- tasks
- notifications
- approvals
- audit_packages
- agent_runs
- audit_logs
- ingestion_sources

## 15.1 Ingestion Source Record

```json
{
  "id": "SRC-001",
  "source_type": "google_drive",
  "display_name": "CSE Accreditation Evidence Folder",
  "external_folder_id": "google-drive-folder-id",
  "sync_status": "connected",
  "last_synced_at": "2026-07-23T18:30:00Z"
}
```

## 15.2 Evidence Record

```json
{
  "evidence_id": "EVD-CSE-2026-00014",
  "source_type": "google_drive",
  "source_file_id": "drive-file-id",
  "original_filename": "AI_Workshop_Report.pdf",
  "checksum": "sha256-value",
  "department": "CSE",
  "academic_year": "2025-2026",
  "document_type": "event_report",
  "status": "requires_correction"
}
```

---

# 16. Recommended Build Order

Build the MVP in this order:

1. Define sample dataset and folder structure.
2. Create evidence registry.
3. Implement manual folder upload.
4. Add Google Drive connector interface.
5. Add PDF and spreadsheet extraction.
6. Add evidence mapping.
7. Add deterministic integrity rules.
8. Add gap and task generation.
9. Add notification draft workflow.
10. Add dashboard metrics.
11. Add human approval workflow.
12. Add audit package generation.
13. Add complete traceability view.

---

# 17. Google Drive Implementation Plan

Google Drive should be implemented after manual ingestion works.

## 17.1 Required Setup

1. Create a Google Cloud project.
2. Enable Google Drive API.
3. Configure OAuth consent screen.
4. Create OAuth client credentials.
5. Store client ID and client secret securely.
6. Add redirect URI for the ProofChain app.
7. Request only the minimum required Drive scopes.

## 17.2 Recommended OAuth Scope

For safest MVP behavior:

```text
https://www.googleapis.com/auth/drive.readonly
```

This allows ProofChain to read files selected by the user without modifying Drive content.

## 17.3 Drive Sync Rules

The connector should:

- Read only approved folders.
- Never delete Drive files.
- Never modify original Drive files.
- Store only controlled copies or references.
- Track Drive file ID and checksum.
- Reprocess only changed files.
- Log every sync action.

---

# 18. MVP Success Definition

The MVP is successful when a user can:

1. Select an accreditation requirement.
2. Upload or connect a folder of evidence.
3. See files automatically registered.
4. See extracted values from PDFs and spreadsheets.
5. See evidence mapped to requirements.
6. See contradictions and duplicates detected.
7. See missing evidence converted into tasks.
8. See department notification drafts.
9. See dashboard impact metrics.
10. Generate an audit-ready package.
11. Open a trace showing why each decision was made.

---

# 19. Final MVP Recommendation

Build the first version around manual folder upload plus a Google Drive-ready ingestion architecture.

The immediate product should prove the complete accreditation workflow without being blocked by OAuth setup.

Once the local/manual workflow is working, Google Drive ingestion can be connected to the same intake queue and processing pipeline.

This keeps the MVP fast to build, easy to demonstrate, and ready for institutional use cases.

