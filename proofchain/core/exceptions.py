"""
core/exceptions.py
Structured exception hierarchy for ProofChain.
All exceptions are recoverable or unrecoverable, and always carry an error_code.
"""


class ProofChainError(Exception):
    """Root exception for all ProofChain errors."""

    error_code: str = "PROOFCHAIN_ERROR"
    recoverable: bool = False

    def __init__(self, message: str, error_code: str | None = None, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        if error_code:
            self.error_code = error_code


# ---------------------------------------------------------------------------
# Collector Exceptions
# ---------------------------------------------------------------------------

class CollectorError(ProofChainError):
    """Base error for the Evidence Collector Agent."""
    error_code = "COLLECTOR_ERROR"


class DirectoryNotFoundError(CollectorError):
    """A configured source directory does not exist."""
    error_code = "COLLECTOR_DIRECTORY_NOT_FOUND"
    recoverable = True


class UnsupportedFileTypeError(CollectorError):
    """A file with an unsupported extension was encountered."""
    error_code = "COLLECTOR_UNSUPPORTED_FILE"
    recoverable = True


class ChecksumError(CollectorError):
    """Failed to compute file checksum."""
    error_code = "COLLECTOR_CHECKSUM_FAILED"
    recoverable = True


class RegistryError(CollectorError):
    """Failed to write or read the evidence registry."""
    error_code = "COLLECTOR_REGISTRY_FAILED"
    recoverable = False


# ---------------------------------------------------------------------------
# Classification Exceptions
# ---------------------------------------------------------------------------

class ClassificationError(ProofChainError):
    """Base error for the Evidence Classification Agent."""
    error_code = "CLASSIFIER_ERROR"


class ExtractionError(ClassificationError):
    """Document extraction (PDF/XLSX) failed."""
    error_code = "CLASSIFIER_EXTRACTION_FAILED"
    recoverable = True


class DocumentTypeUnresolvedError(ClassificationError):
    """Could not determine the document type with sufficient confidence."""
    error_code = "CLASSIFIER_DOCUMENT_TYPE_UNRESOLVED"
    recoverable = True


class MappingLowConfidenceError(ClassificationError):
    """Requirement mapping confidence is below the minimum threshold."""
    error_code = "CLASSIFIER_MAPPING_LOW_CONFIDENCE"
    recoverable = True


# ---------------------------------------------------------------------------
# Integrity Exceptions
# ---------------------------------------------------------------------------

class IntegrityError(ProofChainError):
    """Base error for the Evidence Integrity Agent."""
    error_code = "INTEGRITY_ERROR"


class RuleExecutionError(IntegrityError):
    """A deterministic rule failed to execute (not a rule failure — an execution error)."""
    error_code = "INTEGRITY_RULE_EXECUTION_FAILED"
    recoverable = True


class BundleUnresolvedError(IntegrityError):
    """Evidence could not be grouped into a coherent bundle."""
    error_code = "INTEGRITY_BUNDLE_UNRESOLVED"
    recoverable = True


# ---------------------------------------------------------------------------
# Supervisor Exceptions
# ---------------------------------------------------------------------------

class SupervisorError(ProofChainError):
    """Base error for the Supervisor Agent."""
    error_code = "SUPERVISOR_ERROR"


class StageGateError(SupervisorError):
    """A stage gate condition was not met, blocking the next stage."""
    error_code = "SUPERVISOR_STAGE_GATE_FAILED"
    recoverable = False


class RecoverableAgentError(SupervisorError):
    """
    Wraps a recoverable error from any agent so the Supervisor can decide
    whether to continue processing the remaining evidence.
    """
    error_code = "SUPERVISOR_RECOVERABLE_AGENT_ERROR"
    recoverable = True

    def __init__(self, message: str, agent_name: str, original_error: Exception):
        super().__init__(message)
        self.agent_name = agent_name
        self.original_error = original_error


# ---------------------------------------------------------------------------
# Schema / Validation Exceptions
# ---------------------------------------------------------------------------

class SchemaValidationError(ProofChainError):
    """Output from an agent did not match the required Pydantic schema."""
    error_code = "SCHEMA_VALIDATION_FAILED"
    recoverable = False


class ConfigurationError(ProofChainError):
    """Application configuration is missing or invalid."""
    error_code = "CONFIGURATION_ERROR"
    recoverable = False
