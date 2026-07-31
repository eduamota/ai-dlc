---
id: provenance
kind: deterministic
command: bun {{HARNESS_DIR}}/tools/aidlc-sensor-provenance.ts
default_severity: advisory
description: Verifies that generated/modified source files have corresponding TraceCoder provenance records in .provenance/sessions/ (tracecoder plugin, advisory)
category: traceability
matches: "**/*.{ts,js,py,java,go,rs,rb,tsx,jsx}"
input_schema:
  file_path: string
  stage_slug: string
output_schema:
  pass: boolean
  findings_count: integer
  records_found: integer
  files_without_provenance: array
  message: string
timeout_seconds: 10
---

# provenance sensor (tracecoder)

ADVISORY. Checks that source files written during code-generation have
corresponding provenance records in `.provenance/sessions/`. A missing record
means the file was written outside the TraceCoder-instrumented hook chain —
possibly via a direct file write that bypassed the harness, or the provenance
hooks are not active.

## What it verifies

For each source file written during a stage that imports this sensor:
1. At least one `.provenance/sessions/*.jsonl` file exists
2. At least one `type: "edit"` record references this file path
3. Reports the count of provenance records (useful for seeing repair chains)

## Advisory note

The framework has no blocking sensor severity yet, so a `SENSOR_FAILED` here
is REPORTED, not enforced. The code-generation stage prose drives provenance
compliance. A failing check means the audit trail has gaps — not that the code
is wrong.

## Causal chain expectation

A well-instrumented session produces this sequence per edit cycle:
```
trigger (user prompt) → edit (file write) → test_result (test run) → explanation (stop hook)
```

The sensor checks the `edit` records exist. The full causal chain (trigger →
edit → test → explanation) is validated by the provenance viewer's `summary`
command, not by this real-time sensor.

## Inspired by

[TraceCoder: Explainable and Auditable Code Generation with Position-Key
Snippet Versioning](https://arxiv.org/abs/2607.26307) — AGENTICS 2026.
