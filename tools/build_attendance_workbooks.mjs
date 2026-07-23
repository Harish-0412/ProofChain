import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const __filename = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(__filename), "..");
const payloadPath = path.join(repoRoot, "sample_data", "_generated", "attendance_workbooks.json");
const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));

for (const item of payload) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("Attendance");
  sheet.showGridLines = false;

  const headers = [
    "S.No",
    "Roll Number",
    "Student Name",
    "Department",
    "Event ID",
    "Event Title",
    "Attendance Status",
    "Signature",
  ];
  const rows = item.rows.map((row) => headers.map((header) => row[header] ?? ""));

  sheet.getRange("A1:H1").values = [[`${item.department} Attendance Sheet - ${item.event_id}`]];
  sheet.getRange("A1:H1").merge();
  sheet.getRange("A1:H1").format = {
    fill: "#163B5C",
    font: { bold: true, color: "#FFFFFF", size: 14 },
  };

  sheet.getRange("A3:H3").values = [headers];
  sheet.getRange("A3:H3").format = {
    fill: "#DCEAF5",
    font: { bold: true, color: "#111827" },
    borders: { preset: "all", style: "thin", color: "#AAB7C4" },
  };

  const startRow = 4;
  const endRow = startRow + rows.length - 1;
  sheet.getRange(`A${startRow}:H${endRow}`).values = rows;
  sheet.getRange(`A${startRow}:H${endRow}`).format = {
    borders: { preset: "all", style: "thin", color: "#D9E2EA" },
  };
  sheet.getRange(`A${startRow}:A${endRow}`).format.numberFormat = "0";
  sheet.getRange(`A1:H${endRow}`).format.autofitColumns();
  sheet.freezePanes.freezeRows(3);

  const outputPath = path.join(repoRoot, item.xlsx_path);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
}

console.log(`Created ${payload.length} attendance workbooks.`);
