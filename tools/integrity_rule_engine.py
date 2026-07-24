import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample_data"
INPUT_PATH = SAMPLE_ROOT / "mapping_outputs" / "mapped_evidence.json"
OUTPUT_PATH = SAMPLE_ROOT / "integrity_outputs" / "integrity_findings.json"

def evaluate_rules():
    if not INPUT_PATH.exists():
        print(f"Input file not found: {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Group files by event title (or event id)
    events = defaultdict(list)
    for item in data:
        fields = item.get("extracted_fields", {})
        # Group by event_title as it's present across all document types
        group_key = fields.get("event_title") or fields.get("event_id") or "UNKNOWN_EVENT"
        events[group_key].append(item)

    findings = []

    for event_key, files in events.items():
        if event_key == "UNKNOWN_EVENT":
            continue

        doc_types = defaultdict(list)
        departments = set()
        academic_years = set()
        
        event_report = None
        attendance_sheet = None
        approval_document = None

        for f_idx, file_item in enumerate(files):
            doc_type = file_item.get("document_type")
            doc_types[doc_type].append(file_item)
            
            fields = file_item.get("extracted_fields", {})
            
            if fields.get("department"):
                departments.add(fields.get("department"))
            if fields.get("academic_year"):
                academic_years.add(fields.get("academic_year"))

            if doc_type == "event_report":
                event_report = file_item
            elif doc_type == "attendance_sheet":
                attendance_sheet = file_item
            elif doc_type == "approval_document":
                approval_document = file_item

            # MAP-001: Requirement mapping confidence
            mapping = file_item.get("mapping", {})
            if mapping.get("confidence", 0) < 0.8:
                findings.append({
                    "rule_id": "MAP-001",
                    "severity": "medium",
                    "status": "failed",
                    "finding": f"Weak or incorrect evidence mapping for {file_item.get('file')}",
                    "file": file_item.get("file"),
                    "event_key": event_key
                })
                
            # Duplicate student row detection in attendance sheet
            if doc_type == "attendance_sheet":
                dups = fields.get("duplicate_roll_numbers", [])
                if dups:
                    findings.append({
                        "rule_id": "DUP-STUDENT-001",
                        "severity": "high",
                        "status": "failed",
                        "finding": f"Duplicate student rows detected in attendance sheet: {', '.join(map(str, dups))}",
                        "file": file_item.get("file"),
                        "event_key": event_key
                    })

        # DUP-001: Exact duplicate detection (Using doc_types count for same event)
        for d_type, d_files in doc_types.items():
            if len(d_files) > 1:
                findings.append({
                    "rule_id": "DUP-001",
                    "severity": "high",
                    "status": "failed",
                    "finding": f"Duplicate files found for document type: {d_type} in event '{event_key}'",
                    "event_key": event_key,
                    "files": [f.get("file") for f in d_files]
                })

        # CNT-001: Participant count reconciliation
        if event_report and attendance_sheet:
            rep_count = event_report.get("extracted_fields", {}).get("reported_participant_count")
            att_count = attendance_sheet.get("extracted_fields", {}).get("unique_student_count")
            
            # Use type conversion to handle any discrepancies
            try:
                if rep_count is not None and att_count is not None and int(rep_count) != int(att_count):
                    findings.append({
                        "rule_id": "CNT-001",
                        "severity": "high",
                        "status": "failed",
                        "finding": f"Event report claims {rep_count} participants, but attendance sheet contains {att_count} unique students.",
                        "expected_value": rep_count,
                        "observed_value": att_count,
                        "event_key": event_key
                    })
            except ValueError:
                pass

        # DATE-001: Academic year validation
        if len(academic_years) > 1:
            findings.append({
                "rule_id": "DATE-001",
                "severity": "medium",
                "status": "failed",
                "finding": f"Inconsistent academic years across evidence files: {list(academic_years)}",
                "event_key": event_key
            })

        # DOC-001: Required evidence checklist
        required = ["event_report", "attendance_sheet", "approval_document"]
        missing = [r for r in required if r not in doc_types]
        if missing:
            findings.append({
                "rule_id": "DOC-001",
                "severity": "high",
                "status": "failed",
                "finding": f"Missing required document types: {', '.join(missing)}",
                "event_key": event_key
            })

        # SIGN-001: Approval signature check
        if approval_document:
            sig = approval_document.get("extracted_fields", {}).get("signature_present")
            if str(sig).lower() != "yes":
                findings.append({
                    "rule_id": "SIGN-001",
                    "severity": "high",
                    "status": "failed",
                    "finding": "Approval document is missing signature.",
                    "file": approval_document.get("file"),
                    "event_key": event_key
                })

        # DEPT-001: Department consistency check
        if len(departments) > 1:
            findings.append({
                "rule_id": "DEPT-001",
                "severity": "high",
                "status": "failed",
                "finding": f"Inconsistent departments across evidence files: {list(departments)}",
                "event_key": event_key
            })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    print(f"Generated {len(findings)} integrity findings into {OUTPUT_PATH}")

if __name__ == "__main__":
    evaluate_rules()
