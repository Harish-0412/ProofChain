"""
core/enums.py
Shared enumeration types for ProofChain.
All agents and services must use these enums instead of raw strings.
"""

from enum import Enum


# ---------------------------------------------------------------------------
# Evidence & File
# ---------------------------------------------------------------------------

class IngestionStatus(str, Enum):
    REGISTERED = "registered"
    DUPLICATE_DETECTED = "duplicate_detected"
    UNSUPPORTED = "unsupported"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    CORRUPTED = "corrupted"
    SKIPPED = "skipped"


class DuplicateStatus(str, Enum):
    UNIQUE = "unique"
    EXACT_DUPLICATE = "exact_duplicate"
    NEAR_DUPLICATE = "near_duplicate"


class SourceType(str, Enum):
    DEPARTMENT_FOLDER = "department_folder"
    MANUAL_UPLOAD = "manual_upload"
    GOOGLE_DRIVE = "google_drive"


# ---------------------------------------------------------------------------
# Document Classification
# ---------------------------------------------------------------------------

class DocumentType(str, Enum):
    EVENT_REPORT = "event_report"
    ATTENDANCE_SHEET = "attendance_sheet"
    APPROVAL_DOCUMENT = "approval_document"
    CERTIFICATE = "certificate"
    PHOTOGRAPH = "photograph"
    PARTICIPANT_LIST = "participant_list"
    FACULTY_PROFILE = "faculty_profile"
    FEEDBACK_FORM = "feedback_form"
    TRAINER_PROFILE = "trainer_profile"
    COURSE_REPORT = "course_report"
    UNKNOWN = "unknown"


class ClassificationMethod(str, Enum):
    FILENAME_RULE = "filename_rule"
    FOLDER_RULE = "folder_rule"
    KEYWORD_RULE = "keyword_rule"
    STRUCTURE_RULE = "structure_rule"
    EMBEDDING = "embedding"
    LLM = "llm"
    MANUAL = "manual"


class MappingType(str, Enum):
    FILENAME = "filename"
    FOLDER = "folder"
    EXTRACTED_FIELD = "extracted_field"
    KEYWORD = "keyword"
    MANUAL_OVERRIDE = "manual_override"


# ---------------------------------------------------------------------------
# Processing Status
# ---------------------------------------------------------------------------

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    UNRESOLVED = "unresolved"
    SKIPPED = "skipped"


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


# ---------------------------------------------------------------------------
# Integrity & Findings
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    ACCEPTED_RISK = "accepted_risk"
    UNDER_REVIEW = "under_review"


class FindingType(str, Enum):
    PARTICIPANT_COUNT_MISMATCH = "participant_count_mismatch"
    DUPLICATE_FILE = "duplicate_file"
    DUPLICATE_STUDENT_ROW = "duplicate_student_row"
    MISSING_SIGNATURE = "missing_signature"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    ACADEMIC_YEAR_MISMATCH = "academic_year_mismatch"
    DEPARTMENT_MISMATCH = "department_mismatch"
    WEAK_MAPPING = "weak_mapping"
    EVIDENCE_REUSE = "evidence_reuse"
    DATE_INCONSISTENCY = "date_inconsistency"
    EMPTY_DOCUMENT = "empty_document"
    EXTRACTION_FAILED = "extraction_failed"


class GapType(str, Enum):
    MISSING_REQUIRED_DOCUMENT = "missing_required_document"
    CONTRADICTION = "contradiction"
    WEAK_EVIDENCE = "weak_evidence"
    UNRESOLVED_MAPPING = "unresolved_mapping"
    COUNT_DISCREPANCY = "count_discrepancy"


# ---------------------------------------------------------------------------
# Workflow & Supervisor
# ---------------------------------------------------------------------------

class WorkflowStage(str, Enum):
    CREATED = "CREATED"
    COLLECTING = "COLLECTING"
    COLLECTION_COMPLETED = "COLLECTION_COMPLETED"
    COLLECTION_PARTIAL = "COLLECTION_PARTIAL"
    CLASSIFYING = "CLASSIFYING"
    CLASSIFICATION_COMPLETED = "CLASSIFICATION_COMPLETED"
    CLASSIFICATION_PARTIAL = "CLASSIFICATION_PARTIAL"
    VALIDATING_INTEGRITY = "VALIDATING_INTEGRITY"
    INTEGRITY_COMPLETED = "INTEGRITY_COMPLETED"
    INTEGRITY_PARTIAL = "INTEGRITY_PARTIAL"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    WAITING_FOR_TASK_ACKNOWLEDGEMENT = "WAITING_FOR_TASK_ACKNOWLEDGEMENT"
    WAITING_FOR_EVIDENCE_SUBMISSION = "WAITING_FOR_EVIDENCE_SUBMISSION"
    WAITING_FOR_HUMAN_REVIEW = "WAITING_FOR_HUMAN_REVIEW"
    WAITING_FOR_EXTERNAL_SYSTEM = "WAITING_FOR_EXTERNAL_SYSTEM"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class RunMode(str, Enum):
    FULL = "full"
    COLLECT_ONLY = "collect_only"
    CLASSIFY_ONLY = "classify_only"
    INTEGRITY_ONLY = "integrity_only"
    RERUN = "rerun"


# ---------------------------------------------------------------------------
# Confidence Routing Thresholds
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, Enum):
    HIGH = "high"       # 0.90 - 1.00 → Accept automatically
    MEDIUM = "medium"   # 0.75 - 0.89 → Accept with warning
    LOW = "low"         # 0.50 - 0.74 → Require human review
    VERY_LOW = "very_low"  # < 0.50 → Mark unresolved


def classify_confidence(score: float) -> ConfidenceLevel:
    """Map a float confidence score to a ConfidenceLevel enum."""
    if score >= 0.90:
        return ConfidenceLevel.HIGH
    elif score >= 0.75:
        return ConfidenceLevel.MEDIUM
    elif score >= 0.50:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.VERY_LOW
