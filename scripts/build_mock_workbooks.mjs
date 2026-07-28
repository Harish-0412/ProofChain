import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const payloadPath = process.argv[2];
const previewRoot = process.argv[3];
if (!payloadPath || !previewRoot) {
  throw new Error("Usage: node build_mock_workbooks.mjs <payload.json> <preview-dir>");
}

const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));
await fs.mkdir(previewRoot, { recursive: true });

const headerFormat = {
  fill: "#0F766E",
  font: { bold: true, color: "#FFFFFF" },
  verticalAlignment: "center",
};
const bodyBorder = {
  preset: "inside",
  style: "thin",
  color: "#D7E2E0",
};

function fitColumns(sheet, widths) {
  for (const [column, width] of Object.entries(widths)) {
    sheet.getRange(`${column}:${column}`).format.columnWidth = width;
  }
}

async function saveAndPreview(workbook, outputPath, previewPrefix, sheets) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  for (const sheetName of sheets) {
    const preview = await workbook.render({
      sheetName,
      autoCrop: "all",
      scale: 1.4,
      format: "png",
    });
    const safeName = sheetName.toLowerCase().replaceAll(" ", "-");
    await fs.writeFile(
      path.join(previewRoot, `${previewPrefix}-${safeName}.png`),
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
  await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
}

async function buildStudentMaster() {
  const workbook = Workbook.create();
  const summary = workbook.worksheets.add("Summary");
  const students = workbook.worksheets.add("Students");

  summary.showGridLines = false;
  students.showGridLines = false;
  summary.getRange("A1:D1").merge();
  summary.getRange("A1").values = [["ProofChain Synthetic Student Master"]];
  summary.getRange("A1:D1").format = {
    fill: "#0F766E",
    font: { bold: true, color: "#FFFFFF", size: 16 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  summary.getRange("A1:D1").format.rowHeight = 30;
  summary.getRange("A3:D3").values = [["Department", "Total", "Female", "Male"]];
  summary.getRange("A3:D3").format = headerFormat;
  summary.getRange("A4:A6").values = [["AIML"], ["AIDS"], ["CSE"]];
  summary.getRange("B4").formulas = [["=COUNTIF('Students'!$D$2:$D$91,A4)"]];
  summary.getRange("B4:B6").fillDown();
  summary.getRange("C4").formulas = [["=COUNTIFS('Students'!$D$2:$D$91,A4,'Students'!$C$2:$C$91,\"Female\")"]];
  summary.getRange("C4:C6").fillDown();
  summary.getRange("D4").formulas = [["=COUNTIFS('Students'!$D$2:$D$91,A4,'Students'!$C$2:$C$91,\"Male\")"]];
  summary.getRange("D4:D6").fillDown();
  summary.getRange("A3:D6").format.borders = bodyBorder;
  summary.getRange("B4:D6").format.numberFormat = "0";
  summary.getRange("A8:D9").merge();
  summary.getRange("A8").values = [[
    "All records are synthetic. Email addresses use the reserved example.invalid domain."
  ]];
  summary.getRange("A8:D9").format = {
    fill: "#E8F3F1",
    font: { color: "#334155", italic: true },
    wrapText: true,
    verticalAlignment: "center",
  };
  fitColumns(summary, { A: 22, B: 14, C: 14, D: 14 });

  const headers = [
    "Roll Number", "Student Name", "Gender", "Department", "Program",
    "Semester", "Batch", "Email", "Active",
  ];
  students.getRange("A1:I1").values = [headers];
  students.getRange("A1:I1").format = headerFormat;
  students.getRange("A2:I91").values = payload.students.map((student) => [
    student.roll_number,
    student.full_name,
    student.gender,
    student.department,
    student.program,
    student.semester,
    student.batch,
    student.email,
    student.active,
  ]);
  students.getRange("A1:I91").format.borders = bodyBorder;
  students.getRange("F2:F91").format.numberFormat = "0";
  students.freezePanes.freezeRows(1);
  students.tables.add("A1:I91", true, "SyntheticStudentsTable");
  fitColumns(students, {
    A: 17, B: 24, C: 12, D: 13, E: 48, F: 11, G: 14, H: 46, I: 10,
  });

  const inspection = await workbook.inspect({
    kind: "table,formula",
    range: "A1:I12",
    maxChars: 4000,
    tableMaxRows: 12,
    tableMaxCols: 9,
  });
  console.log(inspection.ndjson);
  await saveAndPreview(
    workbook,
    payload.student_master_output,
    "all-students",
    ["Summary", "Students"],
  );
}

async function buildAttendanceWorkbook(item) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("Attendance");
  sheet.showGridLines = false;
  const rowCount = item.rows.length;
  const columnCount = item.rows[0].length;
  const endColumn = String.fromCharCode(64 + columnCount);
  sheet.getRange(`A1:${endColumn}${rowCount}`).values = item.rows;
  sheet.getRange(`A1:${endColumn}1`).format = headerFormat;
  sheet.getRange(`A1:${endColumn}${rowCount}`).format.borders = bodyBorder;
  sheet.freezePanes.freezeRows(1);
  sheet.tables.add(
    `A1:${endColumn}${rowCount}`,
    true,
    `Attendance${item.event["Department"]}${item.event["Event ID"].slice(-3)}`,
  );
  fitColumns(sheet, {
    A: 18, B: 48, C: 13, D: 17, E: 14,
    F: 17, G: 24, H: 12, I: 18, J: 23,
  });
  const fileStem = path.basename(item.output, ".xlsx").toLowerCase();
  const inspection = await workbook.inspect({
    kind: "table",
    range: `A1:${endColumn}8`,
    maxChars: 2600,
    tableMaxRows: 8,
    tableMaxCols: 10,
  });
  console.log(inspection.ndjson);
  await saveAndPreview(workbook, item.output, fileStem, ["Attendance"]);
}

await buildStudentMaster();
for (const item of payload.attendance_workbooks) {
  await buildAttendanceWorkbook(item);
}
