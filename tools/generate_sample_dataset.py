from __future__ import annotations

import csv
import json
import random
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample_data"
DEPT_ROOT = SAMPLE_ROOT / "departments"
GENERATED_ROOT = SAMPLE_ROOT / "_generated"
ATTENDANCE_JSON = GENERATED_ROOT / "attendance_workbooks.json"
MANIFEST_PATH = SAMPLE_ROOT / "dataset_manifest.json"
ERRORS_PATH = SAMPLE_ROOT / "injected_errors" / "injected_errors_manifest.json"
EXPECTED_PATH = SAMPLE_ROOT / "extraction_outputs" / "expected_extraction_results.json"


DEPARTMENTS = {
    "CSE": "Computer Science and Engineering",
    "ECE": "Electronics and Communication Engineering",
    "EEE": "Electrical and Electronics Engineering",
    "Mechanical": "Mechanical Engineering",
    "Civil": "Civil Engineering",
}

REQUIREMENTS = {
    "C3.2.1": "Industry interaction activities",
    "C5.1.3": "Student enrichment programmes",
    "C6.3.2": "Faculty development activities",
    "C7.1.1": "Extension and outreach activities",
    "C1.2.1": "Value-added courses",
}

COORDINATORS = {
    "CSE": "Dr. Kavya Srinivasan",
    "ECE": "Dr. Nikhil Varadarajan",
    "EEE": "Dr. Meera Krishnamurthy",
    "Mechanical": "Prof. Aditya Narayanan",
    "Civil": "Dr. Ishwarya Ramesh",
}

STUDENTS = [
    "Aadhya Raman", "Abhinav Suresh", "Advik Rajan", "Aishwarya Prasad",
    "Akshay Venkatesh", "Ananya Murali", "Arjun Balaji", "Ashwin Kumar",
    "Bharath Kannan", "Charvi Natarajan", "Darshan Prakash", "Deepika Iyer",
    "Diya Chandran", "Gautham Menon", "Harini Subramanian", "Ishaan Raghavan",
    "Janani Gopal", "Karthik Narayan", "Kavin Senthil", "Keerthana Ravi",
    "Lakshmi Varun", "Madhav Seshadri", "Meghana Rajendran", "Mithun Ramesh",
    "Nandhini Venkataraman", "Naveen Hariharan", "Nila Krishnan",
    "Nithya Shankar", "Pranav Karthikeyan", "Raghavendra Mani",
    "Rahul Vishwanath", "Rithika Anand", "Rohan Subbu", "Sai Charan",
    "Sahana Vivek", "Sanjay Narasimhan", "Shruthi Ganesan", "Siddharth Mohan",
    "Sneha Vaidyanathan", "Sreeja Balasubramaniam", "Tarun Elango",
    "Tejas Nandakumar", "Varsha Sriram", "Vignesh Aravind", "Yamini Sekhar",
]

FIRST_NAMES = [
    "Aadhya", "Abhinav", "Advik", "Aishwarya", "Akshay", "Ananya", "Arjun",
    "Ashwin", "Bharath", "Charvi", "Darshan", "Deepika", "Diya", "Gautham",
    "Harini", "Ishaan", "Janani", "Karthik", "Kavin", "Keerthana", "Lakshmi",
    "Madhav", "Meghana", "Mithun", "Nandhini", "Naveen", "Nila", "Nithya",
    "Pranav", "Raghav", "Rahul", "Rithika", "Rohan", "Sai", "Sahana",
    "Sanjay", "Shruthi", "Siddharth", "Sneha", "Sreeja", "Tarun", "Tejas",
    "Varsha", "Vignesh", "Yamini", "Kishore", "Lavanya", "Manoj", "Pavithra",
    "Rakesh", "Sandhya", "Vikram", "Yashika",
]

LAST_NAMES = [
    "Raman", "Suresh", "Rajan", "Prasad", "Venkatesh", "Murali", "Balaji",
    "Kumar", "Kannan", "Natarajan", "Prakash", "Iyer", "Chandran", "Menon",
    "Subramanian", "Raghavan", "Gopal", "Narayan", "Senthil", "Ravi", "Varun",
    "Seshadri", "Rajendran", "Ramesh", "Venkataraman", "Hariharan", "Krishnan",
    "Shankar", "Karthikeyan", "Mani", "Vishwanath", "Anand", "Subbu",
    "Narasimhan", "Vivek", "Ganesan", "Mohan", "Vaidyanathan",
    "Balasubramaniam", "Elango", "Nandakumar", "Sriram", "Aravind", "Sekhar",
    "Sivakumar", "Ravichandran", "Padmanabhan", "Sundaram", "Mahadevan",
]

EVENT_THEMES = [
    ("Agentic AI Industry Workshop", "C3.2.1", "industry_training"),
    ("Cloud Native Application Bootcamp", "C5.1.3", "student_enrichment"),
    ("Research Publication Writing Clinic", "C6.3.2", "faculty_development"),
    ("Smart Village Outreach Camp", "C7.1.1", "extension_activity"),
    ("Data Analytics Value Added Course", "C1.2.1", "value_added_course"),
]


@dataclass
class EventRecord:
    event_id: str
    department: str
    requirement_id: str
    title: str
    event_date: str
    academic_year: str
    coordinator: str
    reported_count: int
    attendance_count: int
    approval_signed: bool
    has_approval: bool
    mapped_requirement_id: str
    injected_issues: list[str]


def reset_generated_dirs() -> None:
    for dept in DEPARTMENTS:
        dept_path = DEPT_ROOT / dept
        for folder in [
            "event_reports",
            "attendance_sheets",
            "approval_documents",
            "certificates",
            "photos",
        ]:
            target = dept_path / folder
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)

    for folder in ["extraction_outputs", "_generated"]:
        target = SAMPLE_ROOT / folder
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)


def paragraph(text: str):
    styles = getSampleStyleSheet()
    return Paragraph(text, styles["BodyText"])


def build_pdf(path: Path, title: str, rows: list[tuple[str, str]], note: str | None = None) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=46,
        bottomMargin=42,
    )
    story = [Paragraph(title, styles["Title"]), Spacer(1, 16)]
    data = [["Field", "Value"]] + [[k, v] for k, v in rows]
    table = Table(data, colWidths=[160, 330])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163B5C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#AAB7C4")),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#EEF4F8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    if note:
        story.extend([Spacer(1, 16), paragraph(note)])
    story.extend(
        [
            Spacer(1, 18),
            paragraph("Generated for ProofChain MVP synthetic testing. Names and records are fictional."),
        ]
    )
    doc.build(story)


def create_event_report(event: EventRecord, path: Path) -> None:
    rows = [
        ("Event ID", event.event_id),
        ("Accreditation Requirement", f"{event.requirement_id} - {REQUIREMENTS[event.requirement_id]}"),
        ("Mapped Requirement", f"{event.mapped_requirement_id} - {REQUIREMENTS[event.mapped_requirement_id]}"),
        ("Department", event.department),
        ("Academic Year", event.academic_year),
        ("Event Title", event.title),
        ("Event Date", event.event_date),
        ("Coordinator", event.coordinator),
        ("Reported Participant Count", str(event.reported_count)),
        ("Venue", "Seminar Hall B, Main Academic Block"),
        ("Industry / Partner", "Chennai Tech Leaders Forum"),
    ]
    note = (
        "Summary: The session included expert talks, hands-on exercises, and a feedback round. "
        "Participants signed the attendance sheet before receiving completion certificates."
    )
    build_pdf(path, f"Event Report - {event.title}", rows, note)


def create_approval(event: EventRecord, path: Path) -> None:
    rows = [
        ("Approval ID", f"APR-{event.event_id}"),
        ("Department", event.department),
        ("Academic Year", event.academic_year),
        ("Event Title", event.title),
        ("Event Date", event.event_date),
        ("Approved By", "Head of Department"),
        ("Approval Status", "Approved"),
        ("Signature Present", "Yes" if event.approval_signed else "No"),
        ("Approver Name", f"{event.department} HoD"),
    ]
    note = "Signature block: " + ("Signed and sealed by HoD." if event.approval_signed else "Signature field intentionally left blank.")
    build_pdf(path, f"Approval Document - {event.title}", rows, note)


def create_certificate(event: EventRecord, student_name: str, path: Path) -> None:
    rows = [
        ("Certificate ID", f"CERT-{event.event_id}-{student_name.split()[0].upper()}"),
        ("Student Name", student_name),
        ("Department", event.department),
        ("Event Title", event.title),
        ("Event Date", event.event_date),
        ("Academic Year", event.academic_year),
        ("Issued By", event.coordinator),
    ]
    build_pdf(path, "Certificate of Participation", rows, "This certificate is generated as synthetic sample evidence.")


def create_photo(event: EventRecord, path: Path, duplicate_source: Path | None = None) -> None:
    if duplicate_source:
        shutil.copyfile(duplicate_source, path)
        return
    image = Image.new("RGB", (1200, 800), "#EFF6FF")
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 40, 1160, 760], outline="#163B5C", width=8)
    draw.rectangle([70, 90, 1130, 240], fill="#163B5C")
    draw.text((100, 125), "ProofChain Sample Event Photo", fill="white")
    draw.text((100, 300), event.title, fill="#111827")
    draw.text((100, 360), f"Department: {event.department}", fill="#111827")
    draw.text((100, 420), f"Date: {event.event_date}", fill="#111827")
    draw.text((100, 520), "Synthetic image evidence for MVP testing", fill="#374151")
    image.save(path, "PNG")


def make_attendance_rows(event: EventRecord, duplicate_rows: bool = False) -> list[dict[str, str]]:
    random.seed(event.event_id)
    pool = build_student_pool(event.attendance_count)
    chosen = random.sample(pool, event.attendance_count)
    rows = []
    dept_prefix = event.department[:3].upper()
    for idx, name in enumerate(chosen, start=1):
        rows.append(
            {
                "S.No": str(idx),
                "Roll Number": f"{dept_prefix}25{idx:03d}",
                "Student Name": name,
                "Department": event.department,
                "Event ID": event.event_id,
                "Event Title": event.title,
                "Attendance Status": "Present",
                "Signature": f"{name.split()[0][0]}. {name.split()[-1]}",
            }
        )
    if duplicate_rows and rows:
        rows.append(dict(rows[4]))
        rows.append(dict(rows[7]))
    return rows


def build_student_pool(minimum_count: int) -> list[str]:
    pool = list(dict.fromkeys(STUDENTS))
    first_index = 0
    last_index = 0
    while len(pool) < minimum_count:
        name = f"{FIRST_NAMES[first_index % len(FIRST_NAMES)]} {LAST_NAMES[last_index % len(LAST_NAMES)]}"
        if name not in pool:
            pool.append(name)
        first_index += 1
        if first_index % len(FIRST_NAMES) == 0:
            last_index += 1
    return pool


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_events() -> list[EventRecord]:
    events: list[EventRecord] = []
    seq = 1
    for dept in DEPARTMENTS:
        for idx, (theme, req, activity_type) in enumerate(EVENT_THEMES, start=1):
            event_id = f"EVT-{dept[:3].upper()}-{seq:03d}"
            year = "2025-2026"
            month = 8 + idx
            event_date = date(2025 if month <= 12 else 2026, month if month <= 12 else month - 12, 10 + idx).isoformat()
            issues: list[str] = []
            reported = 48 + idx * 6
            attendance = reported
            signed = True
            has_approval = idx <= 2
            mapped_req = req

            if dept == "Civil" and idx == 3:
                has_approval = True

            if dept == "CSE" and idx == 1:
                reported = 120
                attendance = 108
                signed = False
                has_approval = True
                issues.extend(["count_mismatch", "missing_signature", "duplicate_student_rows"])
            if dept == "ECE" and idx == 2:
                has_approval = False
                issues.append("missing_approval")
            if dept == "EEE" and idx == 3:
                event_date = "2024-11-18"
                year = "2025-2026"
                issues.append("wrong_academic_year")
            if dept == "Mechanical" and idx == 4:
                mapped_req = "C3.2.1"
                issues.append("incorrect_mapping")
            if dept == "Civil" and idx == 5:
                issues.append("wrong_department")

            events.append(
                EventRecord(
                    event_id=event_id,
                    department=dept,
                    requirement_id=req,
                    title=theme,
                    event_date=event_date,
                    academic_year=year,
                    coordinator=COORDINATORS[dept],
                    reported_count=reported,
                    attendance_count=attendance,
                    approval_signed=signed,
                    has_approval=has_approval,
                    mapped_requirement_id=mapped_req,
                    injected_issues=issues,
                )
            )
            seq += 1
    return events


def generate_dataset() -> None:
    reset_generated_dirs()
    events = build_events()
    manifest = {"departments": DEPARTMENTS, "requirements": REQUIREMENTS, "events": []}
    errors = []
    expected = []
    attendance_payload = []
    first_photo: Path | None = None

    for event in events:
        dept_dir = DEPT_ROOT / event.department
        report_name = f"{event.event_id}_{event.department}_{event.mapped_requirement_id}_event_report.pdf"
        report_path = dept_dir / "event_reports" / report_name
        create_event_report(event, report_path)

        if "wrong_department" in event.injected_issues:
            wrong_report_path = dept_dir / "event_reports" / f"{event.event_id}_wrong_department_event_report.pdf"
            wrong_event = EventRecord(**{**event.__dict__, "department": "CSE"})
            create_event_report(wrong_event, wrong_report_path)

        duplicate_of = None
        if event.department == "CSE" and event.event_id.endswith("001"):
            duplicate_path = dept_dir / "event_reports" / f"{event.event_id}_duplicate_event_report.pdf"
            shutil.copyfile(report_path, duplicate_path)
            duplicate_of = str(report_path.relative_to(ROOT))
            errors.append(
                {
                    "issue": "duplicate_report",
                    "department": event.department,
                    "file": str(duplicate_path.relative_to(ROOT)),
                    "duplicate_of": duplicate_of,
                }
            )

        if event.has_approval:
            approval_path = dept_dir / "approval_documents" / f"APR_{event.event_id}_approval.pdf"
            create_approval(event, approval_path)
        else:
            approval_path = None

        if event.requirement_id == "C3.2.1":
            rows = make_attendance_rows(event, duplicate_rows="duplicate_student_rows" in event.injected_issues)
            csv_path = GENERATED_ROOT / f"{event.event_id}_attendance.csv"
            write_csv(csv_path, rows)
            attendance_payload.append(
                {
                    "department": event.department,
                    "event_id": event.event_id,
                    "title": event.title,
                    "csv_path": str(csv_path.relative_to(ROOT)),
                    "xlsx_path": str((dept_dir / "attendance_sheets" / f"{event.event_id}_attendance.xlsx").relative_to(ROOT)),
                    "rows": rows,
                }
            )

        if event.department in {"CSE", "ECE", "Mechanical"} and event.requirement_id in {"C3.2.1", "C5.1.3"}:
            random.seed(event.event_id + "cert")
            for student in random.sample(STUDENTS, 2):
                cert_path = dept_dir / "certificates" / f"CERT_{event.event_id}_{student.replace(' ', '_')}.pdf"
                create_certificate(event, student, cert_path)

        if event.requirement_id in {"C3.2.1", "C7.1.1"}:
            photo_path = dept_dir / "photos" / f"PHOTO_{event.event_id}.png"
            if first_photo and event.department == "ECE" and event.requirement_id == "C7.1.1":
                create_photo(event, photo_path, duplicate_source=first_photo)
                errors.append(
                    {
                        "issue": "duplicate_photo",
                        "department": event.department,
                        "file": str(photo_path.relative_to(ROOT)),
                        "duplicate_of": str(first_photo.relative_to(ROOT)),
                    }
                )
            else:
                create_photo(event, photo_path)
                if first_photo is None:
                    first_photo = photo_path

        for issue in event.injected_issues:
            errors.append(
                {
                    "issue": issue,
                    "event_id": event.event_id,
                    "department": event.department,
                    "requirement_id": event.requirement_id,
                    "description": describe_issue(issue, event),
                }
            )

        manifest["events"].append(
            {
                "event_id": event.event_id,
                "department": event.department,
                "requirement_id": event.requirement_id,
                "mapped_requirement_id": event.mapped_requirement_id,
                "title": event.title,
                "event_date": event.event_date,
                "academic_year": event.academic_year,
                "coordinator": event.coordinator,
                "reported_participant_count": event.reported_count,
                "attendance_unique_students": event.attendance_count,
                "approval_expected": event.has_approval,
                "approval_signed": event.approval_signed if event.has_approval else None,
                "injected_issues": event.injected_issues,
                "files": {
                    "event_report": str(report_path.relative_to(ROOT)),
                    "approval_document": str(approval_path.relative_to(ROOT)) if approval_path else None,
                },
            }
        )
        expected.append(
            {
                "evidence_hint": report_name,
                "document_type": "event_report",
                "extracted_fields": {
                    "event_id": event.event_id,
                    "event_title": event.title,
                    "event_date": event.event_date,
                    "department": event.department,
                    "academic_year": event.academic_year,
                    "coordinator": event.coordinator,
                    "reported_participant_count": event.reported_count,
                    "mapped_requirement_id": event.mapped_requirement_id,
                },
            }
        )

    ATTENDANCE_JSON.write_text(json.dumps(attendance_payload, indent=2), encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    ERRORS_PATH.write_text(json.dumps(errors, indent=2), encoding="utf-8")
    EXPECTED_PATH.write_text(json.dumps(expected, indent=2), encoding="utf-8")


def describe_issue(issue: str, event: EventRecord) -> str:
    descriptions = {
        "count_mismatch": f"Event report claims {event.reported_count}, but attendance has {event.attendance_count} unique students.",
        "missing_signature": "Approval document exists but signature is intentionally marked as absent.",
        "duplicate_student_rows": "Attendance sheet includes repeated student rows.",
        "missing_approval": "Approval document is intentionally omitted.",
        "wrong_academic_year": f"Event date {event.event_date} is outside academic year {event.academic_year}.",
        "incorrect_mapping": f"Evidence is mapped to {event.mapped_requirement_id} instead of {event.requirement_id}.",
        "wrong_department": "A report copy contains the wrong department value.",
    }
    return descriptions.get(issue, "Injected issue for MVP testing.")


if __name__ == "__main__":
    generate_dataset()
    print(f"Generated ProofChain sample dataset at {SAMPLE_ROOT}")
