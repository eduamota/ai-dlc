#!/usr/bin/env python3
"""
TraceCoder-inspired provenance processor for Kiro hooks.

Captures snippet-level edit provenance automatically during agent sessions.
Receives hook events via STDIN, processes them, and appends structured
records to a per-session JSONL file.

Records three event types:
  - edit:        A file was written/modified by the agent
  - test_result: A test command was run (pass/fail captured)
  - trigger:     User submitted a prompt (potential trigger context)

The stop hook attaches the agent's explanation to recent unexplained edits.
"""

import json
import sys
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


# --- Record Processors ---

def record_edit(session_file: str):
    """Process a postToolUse(write) or postToolUse(shell) event."""
    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")

    if tool_name in ("write", "fs_write", "fsWrite"):
        record = _process_write_event(event)
    elif tool_name in ("shell", "execute_bash", "execute_cmd"):
        record = _process_shell_event(event)
    else:
        return

    if record:
        _append(session_file, record)


def attach_explanation(session_file: str):
    """Attach the agent's explanation to recent unexplained edits.

    Called by the stop hook at the end of each agent turn.
    Walks backward through session records and attaches the explanation
    to any edit records that don't yet have one.
    """
    event = json.load(sys.stdin)
    explanation = event.get("assistant_response", "")

    if not explanation or not Path(session_file).exists():
        return

    # Read all records, attach explanation to recent edits that lack one
    lines = Path(session_file).read_text().strip().split('\n')
    if not lines or lines == ['']:
        return

    updated_lines = []
    for line in lines:
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("type") == "edit" and record.get("explanation") is None:
            # Truncate explanation to a useful summary
            record["explanation"] = _extract_explanation(explanation)
        updated_lines.append(json.dumps(record, separators=(',', ':')))

    Path(session_file).write_text('\n'.join(updated_lines) + '\n')


def record_prompt(session_file: str):
    """Record user prompt as context for subsequent edits.

    Called by the userPromptSubmit hook. Classifies the prompt
    heuristically as a test failure, bug report, or user instruction.
    """
    event = json.load(sys.stdin)
    prompt = event.get("prompt", "")

    if not prompt:
        return

    record = {
        "type": "trigger",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger_type": _classify_prompt(prompt),
        "message": prompt[:1000],
    }
    _append(session_file, record)


# --- Event Processing ---

def _process_write_event(event: dict) -> dict | None:
    """Extract provenance from a file write event."""
    tool_input = event.get("tool_input", {})
    tool_response = event.get("tool_response", {})

    file_path = tool_input.get("path", "")
    command = tool_input.get("command", "")  # create, strReplace, insert

    if not file_path:
        return None

    # Extract before/after based on edit type
    if command == "strReplace":
        before = tool_input.get("oldStr", "")
        after = tool_input.get("newStr", "")
    elif command == "create":
        before = ""
        after = tool_input.get("content", "")
    elif command == "insert":
        before = ""
        after = tool_input.get("content", "")
    else:
        before = ""
        after = tool_input.get("content", "")

    # Detect the scope (function/class) from the content
    scope = _detect_scope_from_content(after or before)

    return {
        "type": "edit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file_path": _relative_path(file_path, event.get("cwd", "")),
        "edit_type": command,
        "before_snippet": before[:500],
        "after_snippet": after[:500],
        "content_hash": hashlib.sha256((after or "").encode()).hexdigest()[:16],
        "scope": scope,
        "success": tool_response.get("success", False),
        "explanation": None,  # Attached later by stop hook
    }


def _process_shell_event(event: dict) -> dict | None:
    """Extract test results from shell commands."""
    tool_input = event.get("tool_input", {})
    tool_response = event.get("tool_response", {})

    command = tool_input.get("command", "")

    # Only record test-related commands
    test_indicators = [
        "pytest", "test", "jest", "mocha", "vitest",
        "cargo test", "go test", "npm test", "npm run test",
        "python -m pytest", "python -m unittest",
    ]
    if not any(ind in command.lower() for ind in test_indicators):
        return None

    # Extract output
    result = tool_response.get("result", "")
    if isinstance(result, list):
        result = "\n".join(str(r) for r in result)

    # Try to extract specific failure info
    failures = _extract_test_failures(str(result))

    return {
        "type": "test_result",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command[:200],
        "success": tool_response.get("success", False),
        "output_snippet": str(result)[:1500],
        "failures": failures,
    }


# --- Helpers ---

def _classify_prompt(prompt: str) -> str:
    """Heuristic classification of the prompt as a trigger type."""
    prompt_lower = prompt.lower()

    # Check for error/failure patterns (likely pasted test output)
    error_patterns = [
        "error", "fail", "traceback", "exception",
        "assert", "FAILED", "TypeError", "ValueError",
        "undefined", "null", "panic",
    ]
    if any(p.lower() in prompt_lower for p in error_patterns):
        return "test_failure"

    # Check for fix/bug patterns
    bug_patterns = ["fix", "bug", "broken", "doesn't work", "not working", "wrong"]
    if any(p in prompt_lower for p in bug_patterns):
        return "bug_report"

    return "user_instruction"


def _detect_scope_from_content(content: str) -> str:
    """Detect function/class scope from the edited content."""
    if not content:
        return "unknown"

    for line in content.split('\n'):
        stripped = line.strip()
        # Python
        if stripped.startswith('def ') or stripped.startswith('async def '):
            name = stripped.split('(')[0].replace('def ', '').replace('async ', '').strip()
            if name:
                return name
        if stripped.startswith('class '):
            name = stripped.split('(')[0].split(':')[0].replace('class ', '').strip()
            if name:
                return name
        # JavaScript/TypeScript
        if stripped.startswith('function '):
            parts = stripped.split('function ')[1].split('(')[0].strip()
            if parts:
                return parts
        # Arrow function assignment: const foo = (...) =>
        if ('const ' in stripped or 'let ' in stripped) and '=>' in stripped:
            parts = stripped.split('const ')[-1].split('let ')[-1].split('=')[0].strip()
            if parts and '(' not in parts:
                return parts

    return "inline"


def _extract_explanation(response: str) -> str:
    """Extract a concise explanation from the agent's full response.

    Tries to get the most relevant sentence explaining the change.
    Falls back to first 300 chars if no clear explanation found.
    """
    # Look for common explanation patterns
    markers = [
        "I fixed", "I added", "I changed", "I updated", "I removed",
        "The issue was", "The problem was", "The error was",
        "This fixes", "This resolves", "This adds",
        "because", "since the",
    ]

    lines = response.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('```'):
            continue
        for marker in markers:
            if marker.lower() in stripped.lower():
                return stripped[:300]

    # Fallback: first non-empty, non-code line
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('```') and not stripped.startswith('#'):
            return stripped[:300]

    return response[:300]


def _extract_test_failures(output: str) -> list[str]:
    """Extract specific test failure names/messages from test output."""
    failures = []
    lines = output.split('\n')

    for line in lines:
        # pytest patterns
        if 'FAILED' in line:
            failures.append(line.strip()[:200])
        # AssertionError
        elif 'AssertionError' in line:
            failures.append(line.strip()[:200])
        # Jest/mocha patterns
        elif line.strip().startswith('✗') or line.strip().startswith('✕'):
            failures.append(line.strip()[:200])
        # Generic error
        elif 'Error:' in line and len(failures) < 5:
            failures.append(line.strip()[:200])

    return failures[:10]  # Cap at 10 failures


def _relative_path(file_path: str, cwd: str) -> str:
    """Convert to relative path if possible."""
    if not cwd:
        return file_path
    try:
        return str(Path(file_path).relative_to(cwd))
    except ValueError:
        return file_path


def _append(session_file: str, record: dict):
    """Append a record to the session JSONL file."""
    Path(session_file).parent.mkdir(parents=True, exist_ok=True)
    with open(session_file, 'a') as f:
        f.write(json.dumps(record, separators=(',', ':')) + '\n')


# --- CLI Entry Point ---

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: provenance_processor.py <command> <session_file>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    session_file = sys.argv[2]

    try:
        if command == "record-edit":
            record_edit(session_file)
        elif command == "attach-explanation":
            attach_explanation(session_file)
        elif command == "record-prompt":
            record_prompt(session_file)
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        # Never crash the hook — log error and exit cleanly
        print(f"Provenance error: {e}", file=sys.stderr)
        sys.exit(0)  # Exit 0 so we don't block the agent
