"""
tests/unit/test_base_infrastructure.py
Unit tests for the ProofChain base infrastructure:
- ID generation
- Enums and confidence routing
- Exception hierarchy
- TraceLogger
- BaseAgent lifecycle
"""

import json
from pathlib import Path

import pytest

from proofchain.core.ids import (
    generate_evidence_id,
    generate_version_id,
    generate_run_id,
    generate_finding_id,
    generate_bundle_id,
)
from proofchain.core.enums import (
    ConfidenceLevel,
    classify_confidence,
    Severity,
    DocumentType,
    WorkflowStage,
)
from proofchain.core.exceptions import (
    ProofChainError,
    CollectorError,
    DirectoryNotFoundError,
    ExtractionError,
    StageGateError,
    RecoverableAgentError,
)
from proofchain.core.logging import TraceLogger


# ===========================================================================
# ID Generation Tests
# ===========================================================================

class TestEvidenceIDGeneration:

    def test_generates_correct_format(self):
        eid = generate_evidence_id("CSE", "2025-2026", 17)
        assert eid == "EVD-CSE-2025-2026-00017"

    def test_department_is_uppercased(self):
        eid = generate_evidence_id("cse", "2025-2026", 1)
        assert eid.startswith("EVD-CSE-")

    def test_sequence_is_zero_padded(self):
        eid = generate_evidence_id("CSE", "2025-2026", 1)
        assert eid.endswith("-00001")

    def test_different_departments_produce_different_ids(self):
        id1 = generate_evidence_id("CSE", "2025-2026", 1)
        id2 = generate_evidence_id("ECE", "2025-2026", 1)
        assert id1 != id2

    def test_same_args_produce_same_id(self):
        id1 = generate_evidence_id("CSE", "2025-2026", 5)
        id2 = generate_evidence_id("CSE", "2025-2026", 5)
        assert id1 == id2


class TestVersionIDGeneration:

    def test_generates_correct_format(self):
        vid = generate_version_id("EVD-CSE-2025-2026-00017", 1)
        assert vid == "VER-00017-01"

    def test_version_number_is_padded(self):
        vid = generate_version_id("EVD-CSE-2025-2026-00017", 2)
        assert vid.endswith("-02")


class TestRunIDGeneration:

    def test_run_id_starts_with_RUN(self):
        rid = generate_run_id()
        assert rid.startswith("RUN-")

    def test_run_id_is_unique(self):
        rid1 = generate_run_id()
        rid2 = generate_run_id()
        assert rid1 != rid2

    def test_run_id_format(self):
        rid = generate_run_id()
        parts = rid.split("-")
        # RUN-{YYYYMMDD}-{SUFFIX} => 3 parts
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD


class TestFindingIDGeneration:

    def test_generates_correct_format(self):
        fid = generate_finding_id("RUN-20260724-A3F2", 142)
        assert fid == "FND-A3F2-000142"


class TestBundleIDGeneration:

    def test_generates_uppercase_department(self):
        bid = generate_bundle_id("cse", "Agentic AI Workshop")
        assert bid.startswith("BUNDLE-CSE-")

    def test_slug_truncated_to_20_chars(self):
        bid = generate_bundle_id("CSE", "A very long event title that should be truncated")
        parts = bid.split("-")
        # BUNDLE-CSE-{slug}; slug is at most 20 chars (no spaces)
        slug = parts[-1]
        assert len(slug) <= 20


# ===========================================================================
# Enum & Confidence Tests
# ===========================================================================

class TestConfidenceRouting:

    def test_high_confidence(self):
        assert classify_confidence(0.95) == ConfidenceLevel.HIGH

    def test_medium_confidence(self):
        assert classify_confidence(0.80) == ConfidenceLevel.MEDIUM

    def test_low_confidence(self):
        assert classify_confidence(0.60) == ConfidenceLevel.LOW

    def test_very_low_confidence(self):
        assert classify_confidence(0.40) == ConfidenceLevel.VERY_LOW

    def test_boundary_at_0_90(self):
        assert classify_confidence(0.90) == ConfidenceLevel.HIGH

    def test_boundary_at_0_75(self):
        assert classify_confidence(0.75) == ConfidenceLevel.MEDIUM

    def test_boundary_at_0_50(self):
        assert classify_confidence(0.50) == ConfidenceLevel.LOW

    def test_below_0_50_is_very_low(self):
        assert classify_confidence(0.49) == ConfidenceLevel.VERY_LOW

    def test_zero_confidence_is_very_low(self):
        assert classify_confidence(0.0) == ConfidenceLevel.VERY_LOW

    def test_all_levels_are_distinct(self):
        levels = {
            classify_confidence(0.95),
            classify_confidence(0.80),
            classify_confidence(0.60),
            classify_confidence(0.30),
        }
        assert len(levels) == 4


class TestEnumValues:

    def test_severity_enum_values(self):
        assert Severity.HIGH == "high"
        assert Severity.CRITICAL == "critical"

    def test_document_type_enum(self):
        assert DocumentType.EVENT_REPORT == "event_report"
        assert DocumentType.UNKNOWN == "unknown"

    def test_workflow_stage_ordering(self):
        # Stages should be defined
        stages = [s.value for s in WorkflowStage]
        assert "CREATED" in stages
        assert "COMPLETED" in stages
        assert "FAILED" in stages


# ===========================================================================
# Exception Hierarchy Tests
# ===========================================================================

class TestExceptionHierarchy:

    def test_collector_error_is_proofchain_error(self):
        err = DirectoryNotFoundError("dir not found")
        assert isinstance(err, ProofChainError)
        assert isinstance(err, CollectorError)

    def test_extraction_error_is_proofchain_error(self):
        err = ExtractionError("pdf failed")
        assert isinstance(err, ProofChainError)

    def test_stage_gate_error_not_recoverable(self):
        err = StageGateError("gate failed")
        assert err.recoverable is False

    def test_directory_not_found_is_recoverable(self):
        err = DirectoryNotFoundError("not found")
        assert err.recoverable is True

    def test_error_code_is_set(self):
        err = DirectoryNotFoundError("x")
        assert err.error_code == "COLLECTOR_DIRECTORY_NOT_FOUND"

    def test_error_message_accessible(self):
        err = ProofChainError("test message")
        assert err.message == "test message"

    def test_recoverable_agent_error_wraps_original(self):
        original = ValueError("original error")
        err = RecoverableAgentError("wrapped", agent_name="collector", original_error=original)
        assert err.original_error is original
        assert err.agent_name == "collector"


# ===========================================================================
# TraceLogger Tests
# ===========================================================================

class TestTraceLogger:
    """TraceLogger tests using a local temp directory to avoid Windows AppData permission issues."""

    @pytest.fixture
    def local_tmp(self, tmp_path_factory):
        """Create a temp directory inside the project outputs folder."""
        import uuid
        base = Path(__file__).resolve().parents[2] / "outputs" / "test_tmp" / uuid.uuid4().hex[:8]
        base.mkdir(parents=True, exist_ok=True)
        yield base
        import shutil
        shutil.rmtree(base, ignore_errors=True)

    def test_creates_trace_file(self, local_tmp):
        trace_path = local_tmp / "trace.jsonl"
        tracer = TraceLogger(run_id="RUN-TEST-0001", trace_path=trace_path)
        tracer.log(agent="collector", event="file_discovered", evidence_id="EVD-CSE-001")
        assert trace_path.exists()

    def test_trace_entry_is_valid_json(self, local_tmp):
        trace_path = local_tmp / "trace.jsonl"
        tracer = TraceLogger(run_id="RUN-TEST-0001", trace_path=trace_path)
        tracer.log(agent="collector", event="file_discovered")
        line = trace_path.read_text(encoding="utf-8").strip()
        entry = json.loads(line)
        assert entry["agent"] == "collector"
        assert entry["event"] == "file_discovered"
        assert entry["run_id"] == "RUN-TEST-0001"
        assert "timestamp" in entry

    def test_multiple_entries_each_on_own_line(self, local_tmp):
        trace_path = local_tmp / "trace.jsonl"
        tracer = TraceLogger(run_id="RUN-TEST-0001", trace_path=trace_path)
        tracer.log(agent="collector", event="started")
        tracer.log(agent="collector", event="completed")
        lines = trace_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

    def test_log_rule_result_pass(self, local_tmp):
        trace_path = local_tmp / "trace.jsonl"
        tracer = TraceLogger(run_id="RUN-TEST-0001", trace_path=trace_path)
        tracer.log_rule_result(rule_id="EVT-COUNT-001", passed=True)
        entry = json.loads(trace_path.read_text().strip())
        assert entry["event"] == "rule_passed"

    def test_log_rule_result_fail(self, local_tmp):
        trace_path = local_tmp / "trace.jsonl"
        tracer = TraceLogger(run_id="RUN-TEST-0001", trace_path=trace_path)
        tracer.log_rule_result(rule_id="SIGN-001", passed=False, finding_id="FND-0001")
        entry = json.loads(trace_path.read_text().strip())
        assert entry["event"] == "rule_failed"
        assert entry["finding_id"] == "FND-0001"

    def test_log_error_entry(self, local_tmp):
        trace_path = local_tmp / "trace.jsonl"
        tracer = TraceLogger(run_id="RUN-TEST-0001", trace_path=trace_path)
        tracer.log_error(agent="integrity", error_code="INTEGRITY_RULE_EXECUTION_FAILED", message="boom")
        entry = json.loads(trace_path.read_text().strip())
        assert entry["event"] == "error"
        assert entry["error_code"] == "INTEGRITY_RULE_EXECUTION_FAILED"

    def test_extra_fields_are_included(self, local_tmp):
        trace_path = local_tmp / "trace.jsonl"
        tracer = TraceLogger(run_id="RUN-TEST-0001", trace_path=trace_path)
        tracer.log(agent="collector", event="file_discovered", department="CSE", confidence=0.95)
        entry = json.loads(trace_path.read_text().strip())
        assert entry["department"] == "CSE"
        assert entry["confidence"] == 0.95
