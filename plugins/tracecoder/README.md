# TraceCoder — AI-DLC Provenance Plugin

Automatic snippet-level audit trail for AI agent code edits, inspired by
[TraceCoder](https://arxiv.org/abs/2607.26307) (AGENTICS 2026).

## What It Does

Every time the AI agent edits a file, runs tests, or explains its reasoning during
code generation, a structured provenance record is captured. This creates an auditable
causal chain:

```
User reports error → Agent edits file → Tests fail → Agent edits again → Tests pass
       ↓                   ↓                ↓              ↓              ↓
    [trigger]           [edit]        [test_result]     [edit]       [test_result]
                     + explanation                   + explanation
```

## What It Adds to AI-DLC

| Component | Purpose |
|-----------|---------|
| **Provenance sensor** | Advisory check that generated files have provenance records |
| **Code-generation overlay** | Adds Step 5a to produce `tracecoder-provenance-summary.md` |
| **Developer knowledge** | Teaches the developer agent to write provenance-friendly code |
| **Hook scripts** | `provenance-capture.sh` + `provenance_processor.py` for capture |
| **Viewer** | `provenance_viewer.py` CLI for timeline, export, and annotation |

## Installation

### 1. Enable the plugin in your project

The plugin is included in the AI-DLC `plugins/` directory. To activate it,
add `"tracecoder"` to your project's plugin list in `aidlc/spaces/<space>/harness.json`:

```json
{
  "plugins": ["tracecoder"]
}
```

### 2. Wire the provenance hooks

Add the TraceCoder hooks to your agent configuration. For Kiro CLI, add to your
agent's `hooks` section (alongside existing AI-DLC hooks):

```json
{
  "hooks": {
    "userPromptSubmit": [
      {
        "command": "plugins/tracecoder/tools/provenance-capture.sh",
        "timeout_ms": 3000
      }
    ],
    "postToolUse": [
      {
        "matcher": "write",
        "command": "plugins/tracecoder/tools/provenance-capture.sh",
        "timeout_ms": 5000
      },
      {
        "matcher": "shell",
        "command": "plugins/tracecoder/tools/provenance-capture.sh",
        "timeout_ms": 5000
      }
    ],
    "stop": [
      {
        "command": "plugins/tracecoder/tools/provenance-capture.sh",
        "timeout_ms": 5000
      }
    ]
  }
}
```

For global installation (all projects), copy the hook scripts to `~/.kiro/hooks/`
and reference them with absolute paths.

### 3. Add .provenance/ to .gitignore

```
.provenance/
```

Session data may contain code snippets and is `.gitignore`'d by default.

## Viewing Provenance

```bash
# List sessions
python3 plugins/tracecoder/tools/provenance_viewer.py sessions

# Show timeline for most recent session
python3 plugins/tracecoder/tools/provenance_viewer.py timeline

# Show provenance for a specific file
python3 plugins/tracecoder/tools/provenance_viewer.py show src/calculator.py

# Export HTML report
python3 plugins/tracecoder/tools/provenance_viewer.py export

# Session summary
python3 plugins/tracecoder/tools/provenance_viewer.py summary
```

Or use the `provenance` skill (if installed globally): just say "provenance timeline"
in a Kiro session.

## How It Works with AI-DLC

1. **During code generation** — hooks capture every file write, test run, and user
   prompt as JSONL records in `.provenance/sessions/<session-id>.jsonl`
2. **After code generation** (Step 5a overlay) — the developer agent reads the
   session file and produces `tracecoder-provenance-summary.md` documenting causal
   chains, repair cycles, and gaps
3. **On file write** (sensor) — the `provenance` sensor fires and ADVISES whether
   the written file has a corresponding provenance record

## Record Types

| Type | Captured When | Contents |
|------|---------------|----------|
| `trigger` | User submits a prompt | Prompt text, classified type |
| `edit` | Agent writes/modifies a file | File path, before/after snippets, scope, content hash |
| `test_result` | Agent runs test commands | Command, pass/fail, failure messages |
| `explanation` | Agent turn ends (stop hook) | Reasoning attached to recent edits |

## Research Basis

Key adaptations from the TraceCoder paper:
- **Position-key**: Function-anchored scoping + content hashes instead of fractional indexing
- **Storage**: Local JSONL instead of a relational DB (simpler for experimentation)
- **Capture**: Automated via harness hooks instead of manual annotation
- **Integration**: Wired into AI-DLC's sensor + overlay system for automatic verification

## File Structure

```
plugins/tracecoder/
├── .aidlc-plugin/plugin.json              # Plugin manifest
├── README.md                               # This file
├── contributions/
│   └── construction/code-generation.md     # Overlay: adds Step 5a + sensor
├── knowledge/
│   └── aidlc-developer-agent/
│       └── provenance-guide.md             # Developer agent provenance knowledge
├── sensors/
│   └── aidlc-provenance.md                 # Sensor descriptor
└── tools/
    ├── aidlc-sensor-provenance.ts          # Sensor implementation (TypeScript)
    ├── provenance-capture.sh               # Hook entry point (shell)
    ├── provenance_processor.py             # Record processor (Python)
    └── provenance_viewer.py                # CLI viewer (Python)
```
