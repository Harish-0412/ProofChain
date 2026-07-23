# Phase 0: Project Foundation

## Goal

Create a clear project base before implementation begins.

Phase 0 is complete when the team understands the MVP scope, all core entities are defined, the build order is clear, and no major feature ambiguity remains.

---

# 1. Foundation Decisions

## 1.1 Use One Complete Workflow First

The MVP should not try to cover all accreditation scenarios at once.

The first workflow should be:

```text
CSE event evidence
-> requirement C3.2.1
-> event report + attendance sheet + approval document
-> extraction
-> count mismatch and missing signature detection
-> gap creation
-> task assignment
-> notification draft
-> approval
-> audit package
```

## 1.2 Use Manual Upload First

Manual upload is the fastest path to a working MVP.

Google Drive should be included in the architecture, but not allowed to block the first working version.

## 1.3 Keep Google Drive As Optional Connector

Google Drive ingestion will use the same Evidence Intake pipeline as manual upload.

```text
Manual upload -> Evidence Intake
Google Drive -> Evidence Intake
```

Both sources should create the same evidence record shape.

## 1.4 Use Deterministic Rules First

The first version should prioritize rules that are easy to verify:

- Exact duplicate detection
- Missing required documents
- Participant count mismatch
- Academic year mismatch
- Department mismatch
- Missing approval signature

AI should help with extraction and explanation later, but core verification should be rule-driven.

## 1.5 Postpone Qdrant and Neo4j

For the MVP, structured database records are enough.

Postpone:

- Qdrant for semantic search and RAG
- Neo4j for evidence graph traversal

Add them only after the first workflow is working.

---

# 2. Core Entities

These entities form the base of ProofChain:

| Entity | Purpose |
|---|---|
| Department | Institutional unit that owns evidence |
| Accreditation Requirement | Requirement or criterion that needs proof |
| Claim | Statement made by a department or institution |
| Evidence | File or record used to support a claim |
| Ingestion Source | Manual upload or connected Drive folder |
| Extracted Field | Structured value extracted from evidence |
| Evidence Mapping | Link between evidence and requirement |
| Integrity Finding | Rule result or issue found in evidence |
| Gap | Missing or weak proof needing correction |
| Task | Action assigned to a department/user |
| Notification | Message draft or sent communication |
| Approval | Human decision for sensitive workflow steps |
| Audit Package | Final packaged proof for review |
| Audit Log | Trace of important system actions |

---

# 3. Deliverables

## 3.1 Project README

Status: Complete.

Location:

```text
README.md
```

## 3.2 MVP Architecture Document

Status: Complete.

Location:

```text
ProofChain_MVP_Modified_Project_Architecture.md
```

## 3.3 Build Phases Document

Status: Complete.

Location:

```text
docs/ProofChain_MVP_Phases_and_Workflow.md
```

## 3.4 Sample Dataset Structure

Status: Complete as a planned folder structure.

Location:

```text
sample_data/
```

## 3.5 Initial Data Schema Draft

Status: Complete as a planning draft.

Location:

```text
docs/Initial_Data_Schema_Draft.md
```

---

# 4. Done Criteria

Phase 0 is done when:

- Team understands the MVP scope.
- Manual ingestion is the first build path.
- Google Drive is planned but optional.
- Deterministic rules are the first validation layer.
- Qdrant and Neo4j are postponed.
- All core entities are defined.
- Build order is clear.
- Initial schema exists.
- Sample dataset structure exists.
- No major feature ambiguity remains.

---

# 5. Phase 0 Completion Status

Phase 0 is ready for review.

The next implementation phase is:

```text
Phase 1: Evidence Registry and Ingestion
```

