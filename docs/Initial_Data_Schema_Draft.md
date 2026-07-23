# Initial Data Schema Draft

## Purpose

This draft defines the first data model for ProofChain MVP.

The schema is designed for Phase 0 and Phase 1, with enough structure to support later extraction, mapping, validation, tasks, approvals, and audit packages.

---

# 1. departments

Stores institutional departments.

| Field | Type | Notes |
|---|---|---|
| id | string | Internal ID |
| code | string | CSE, ECE, EEE, MECH, CIVIL |
| name | string | Full department name |
| coordinator_name | string | Optional for MVP |
| coordinator_email | string | Optional for MVP |
| active | boolean | Whether department is active |
| created_at | datetime | Creation time |

---

# 2. accreditation_requirements

Stores the five MVP requirements.

| Field | Type | Notes |
|---|---|---|
| id | string | C3.2.1, C5.1.3, etc. |
| title | string | Requirement title |
| description | text | Requirement description |
| required_document_types | json | Checklist for evidence |
| active | boolean | Whether requirement is active |
| created_at | datetime | Creation time |

---

# 3. claims

Stores institutional or department claims.

| Field | Type | Notes |
|---|---|---|
| id | string | Claim ID |
| requirement_id | string | Linked requirement |
| department_id | string | Linked department |
| academic_year | string | Example: 2025-2026 |
| claim_text | text | Human-readable claim |
| structured_claim | json | Extracted claim values |
| status | string | draft, under_review, partially_supported, verified |
| created_by | string | User ID |
| approved_by | string | User ID, nullable |
| created_at | datetime | Creation time |

---

# 4. ingestion_sources

Tracks where files come from.

| Field | Type | Notes |
|---|---|---|
| id | string | Source ID |
| source_type | string | manual_upload or google_drive |
| display_name | string | User-facing name |
| external_folder_id | string | Drive folder ID, nullable |
| source_url | text | Drive URL, nullable |
| sync_status | string | not_connected, connected, syncing, failed |
| last_synced_at | datetime | Nullable |
| created_by | string | User ID |
| created_at | datetime | Creation time |

---

# 5. ingestion_batches

Groups one upload or sync operation.

| Field | Type | Notes |
|---|---|---|
| id | string | Batch ID |
| source_id | string | Linked ingestion source |
| department_id | string | Selected department |
| requirement_id | string | Selected requirement |
| academic_year | string | Selected academic year |
| uploaded_count | integer | Total files received |
| registered_count | integer | Successfully registered |
| duplicate_count | integer | Duplicates detected |
| unsupported_count | integer | Unsupported files |
| status | string | started, completed, failed |
| started_at | datetime | Start time |
| completed_at | datetime | End time |

---

# 6. evidence

Stores the main evidence records.

| Field | Type | Notes |
|---|---|---|
| id | string | Evidence ID |
| ingestion_batch_id | string | Linked batch |
| original_filename | string | Original uploaded name |
| stored_filename | string | Internal stored name |
| storage_path | text | Local or object storage path |
| department_id | string | Linked department |
| requirement_id | string | Linked requirement |
| academic_year | string | Academic year |
| source_type | string | manual_upload or google_drive |
| source_reference | text | Drive link or local reference |
| mime_type | string | File MIME type |
| file_size_bytes | integer | File size |
| checksum_sha256 | string | SHA-256 checksum |
| status | string | registered, duplicate_detected, unsupported, etc. |
| duplicate_of | string | Original evidence ID, nullable |
| uploaded_by | string | User ID |
| uploaded_at | datetime | Upload time |

---

# 7. evidence_versions

Stores future corrected or updated evidence versions.

| Field | Type | Notes |
|---|---|---|
| id | string | Version ID |
| evidence_id | string | Linked evidence |
| version_number | integer | Starts at 1 |
| original_filename | string | Original filename |
| storage_path | text | Version file path |
| checksum_sha256 | string | Version checksum |
| uploaded_by | string | User ID |
| uploaded_at | datetime | Upload time |

---

# 8. extracted_fields

Reserved for Phase 3.

| Field | Type | Notes |
|---|---|---|
| id | string | Field ID |
| evidence_id | string | Linked evidence |
| field_name | string | event_date, participant_count, etc. |
| field_value | text | Extracted value |
| field_value_json | json | Structured value, optional |
| source_reference | string | Page, row, or sheet reference |
| confidence | decimal | Extraction confidence |
| extraction_method | string | parser, ocr, ai, manual |
| created_at | datetime | Creation time |

---

# 9. integrity_findings

Reserved for Phase 5.

| Field | Type | Notes |
|---|---|---|
| id | string | Finding ID |
| evidence_id | string | Linked evidence |
| requirement_id | string | Linked requirement |
| rule_id | string | Rule that created finding |
| finding_type | string | count_mismatch, missing_signature, etc. |
| severity | string | low, medium, high, critical |
| description | text | Human-readable finding |
| expected_value | text | Nullable |
| observed_value | text | Nullable |
| status | string | open, resolved, accepted_risk |
| created_at | datetime | Creation time |

---

# 10. gaps

Reserved for Phase 6.

| Field | Type | Notes |
|---|---|---|
| id | string | Gap ID |
| requirement_id | string | Linked requirement |
| department_id | string | Linked department |
| evidence_id | string | Nullable |
| finding_id | string | Nullable |
| gap_type | string | missing_document, contradiction, weak_evidence |
| severity | string | low, medium, high, critical |
| description | text | Gap description |
| status | string | open, assigned, resolved |
| created_at | datetime | Creation time |

---

# 11. tasks

Reserved for Phase 6.

| Field | Type | Notes |
|---|---|---|
| id | string | Task ID |
| gap_id | string | Linked gap |
| assigned_department_id | string | Department |
| assigned_to | string | User ID, nullable |
| title | string | Task title |
| description | text | Task details |
| priority | string | low, medium, high |
| due_date | date | Due date |
| status | string | open, awaiting_response, submitted, resolved |
| created_at | datetime | Creation time |

---

# 12. notifications

Reserved for Phase 7.

| Field | Type | Notes |
|---|---|---|
| id | string | Notification ID |
| task_id | string | Linked task |
| department_id | string | Linked department |
| channel | string | draft, email, teams, etc. |
| subject | string | Message subject |
| body | text | Message body |
| status | string | draft, pending_approval, sent, rejected |
| approved_by | string | User ID, nullable |
| sent_at | datetime | Nullable |

---

# 13. approvals

Stores human decisions.

| Field | Type | Notes |
|---|---|---|
| id | string | Approval ID |
| object_type | string | evidence, task, notification, package |
| object_id | string | Related object |
| requested_from | string | User ID |
| decision | string | pending, approved, rejected |
| comments | text | Optional |
| decided_at | datetime | Nullable |
| created_at | datetime | Creation time |

---

# 14. audit_logs

Stores traceability events.

| Field | Type | Notes |
|---|---|---|
| id | string | Log ID |
| actor_type | string | user, agent, system |
| actor_id | string | Actor ID |
| action | string | evidence.registered, etc. |
| entity_type | string | evidence, task, approval |
| entity_id | string | Entity ID |
| previous_state | json | Nullable |
| new_state | json | Nullable |
| timestamp | datetime | Event time |

---

# 15. Phase 1 Minimum Schema

For Phase 1 implementation, only these are required:

- departments
- accreditation_requirements
- ingestion_sources
- ingestion_batches
- evidence
- evidence_versions
- audit_logs

Everything else can be added in later phases.

