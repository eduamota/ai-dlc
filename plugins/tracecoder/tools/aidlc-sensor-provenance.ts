// plugins/tracecoder/tools/aidlc-sensor-provenance.ts
//
// TraceCoder provenance sensor for AI-DLC.
// Checks that generated/modified files during code-generation have
// corresponding provenance records in .provenance/sessions/.
//
// Invoked by the sensor-fire hook when a file matching the sensor's
// `matches` glob is written during a stage that imports this sensor.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";

interface ProvenanceRecord {
  type: string;
  file_path?: string;
  timestamp: string;
  edit_type?: string;
  scope?: string;
  content_hash?: string;
  explanation?: string | null;
}

interface SensorInput {
  file_path: string;
  stage_slug?: string;
}

interface SensorOutput {
  pass: boolean;
  findings_count: number;
  records_found: number;
  files_without_provenance: string[];
  message: string;
}

function findSessionFiles(projectDir: string): string[] {
  const dir = join(projectDir, ".provenance", "sessions");
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".jsonl"))
    .map((f) => join(dir, f));
}

function loadRecords(sessionFile: string): ProvenanceRecord[] {
  const content = readFileSync(sessionFile, "utf-8").trim();
  if (!content) return [];
  return content.split("\n").map((line) => JSON.parse(line));
}

function checkProvenance(input: SensorInput): SensorOutput {
  const projectDir = process.cwd();
  const targetFile = relative(projectDir, input.file_path);

  // Find all session files and load records
  const sessionFiles = findSessionFiles(projectDir);
  if (sessionFiles.length === 0) {
    return {
      pass: false,
      findings_count: 1,
      records_found: 0,
      files_without_provenance: [targetFile],
      message: `No provenance sessions found at .provenance/sessions/. TraceCoder hooks may not be active.`,
    };
  }

  // Check the most recent session(s) for records matching this file
  let matchingRecords = 0;
  for (const sessionFile of sessionFiles) {
    const records = loadRecords(sessionFile);
    const fileEdits = records.filter(
      (r) => r.type === "edit" && r.file_path === targetFile
    );
    matchingRecords += fileEdits.length;
  }

  if (matchingRecords === 0) {
    return {
      pass: false,
      findings_count: 1,
      records_found: 0,
      files_without_provenance: [targetFile],
      message: `No provenance records found for '${targetFile}'. File was written outside TraceCoder-instrumented hooks.`,
    };
  }

  return {
    pass: true,
    findings_count: 0,
    records_found: matchingRecords,
    files_without_provenance: [],
    message: `${matchingRecords} provenance record(s) found for '${targetFile}'.`,
  };
}

// --- Entry point ---
// Sensor is invoked with JSON on stdin containing { file_path, stage_slug }
const chunks: Buffer[] = [];
process.stdin.on("data", (chunk) => chunks.push(chunk));
process.stdin.on("end", () => {
  try {
    const input: SensorInput = JSON.parse(Buffer.concat(chunks).toString());
    const result = checkProvenance(input);
    process.stdout.write(JSON.stringify(result));
    process.exit(result.pass ? 0 : 1);
  } catch (e) {
    process.stdout.write(
      JSON.stringify({
        pass: false,
        findings_count: 1,
        records_found: 0,
        files_without_provenance: [],
        message: `Sensor error: ${e instanceof Error ? e.message : String(e)}`,
      })
    );
    process.exit(1);
  }
});
