#!/usr/bin/env python3
"""
Provenance viewer — query and visualize code provenance from agent sessions.

Usage:
    python3 .kiro/hooks/provenance_viewer.py sessions
    python3 .kiro/hooks/provenance_viewer.py timeline [session_id]
    python3 .kiro/hooks/provenance_viewer.py show <file_path>
    python3 .kiro/hooks/provenance_viewer.py annotate <file_path>
    python3 .kiro/hooks/provenance_viewer.py summary [session_id]
    python3 .kiro/hooks/provenance_viewer.py export [session_id] [--output file.html]
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# --- ANSI Colors ---

class C:
    """ANSI color codes. Disabled if NO_COLOR env is set or not a TTY."""
    _enabled = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    RESET = "\033[0m" if _enabled else ""
    BOLD = "\033[1m" if _enabled else ""
    DIM = "\033[2m" if _enabled else ""
    ITALIC = "\033[3m" if _enabled else ""

    RED = "\033[31m" if _enabled else ""
    GREEN = "\033[32m" if _enabled else ""
    YELLOW = "\033[33m" if _enabled else ""
    BLUE = "\033[34m" if _enabled else ""
    MAGENTA = "\033[35m" if _enabled else ""
    CYAN = "\033[36m" if _enabled else ""
    WHITE = "\033[37m" if _enabled else ""

    BG_RED = "\033[41m" if _enabled else ""
    BG_GREEN = "\033[42m" if _enabled else ""
    BG_YELLOW = "\033[43m" if _enabled else ""
    BG_BLUE = "\033[44m" if _enabled else ""


# --- Data Loading ---

PROVENANCE_DIR = Path(".provenance/sessions")


def load_session(session_file: Path) -> list[dict]:
    """Load all records from a session JSONL file."""
    records = []
    with open(session_file) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_all_sessions() -> dict[str, list[dict]]:
    """Load all sessions, keyed by session filename."""
    sessions = {}
    if not PROVENANCE_DIR.exists():
        return sessions
    for f in sorted(PROVENANCE_DIR.glob("*.jsonl")):
        sessions[f.stem] = load_session(f)
    return sessions


def get_latest_session(sessions: dict) -> tuple[str, list[dict]] | None:
    """Get the most recent session."""
    if not sessions:
        return None
    key = list(sessions.keys())[-1]
    return key, sessions[key]


# --- Commands ---

def cmd_sessions():
    """List all sessions with stats."""
    sessions = load_all_sessions()
    if not sessions:
        print(f"{C.YELLOW}No provenance sessions found in .provenance/sessions/{C.RESET}")
        return

    print(f"\n{C.BOLD}Provenance Sessions{C.RESET}")
    print(f"{'─' * 70}")
    print(f"  {'Session ID':<36} {'Edits':<7} {'Tests':<7} {'Triggers':<9} {'Files'}")
    print(f"{'─' * 70}")

    for sid, records in sessions.items():
        edits = sum(1 for r in records if r.get("type") == "edit")
        tests = sum(1 for r in records if r.get("type") == "test_result")
        triggers = sum(1 for r in records if r.get("type") == "trigger")
        files = set(r.get("file_path", "") for r in records if r.get("type") == "edit")
        files_str = ", ".join(sorted(f for f in files if f)[:3])
        if len(files) > 3:
            files_str += f" +{len(files)-3}"

        print(f"  {C.CYAN}{sid:<36}{C.RESET} {edits:<7} {tests:<7} {triggers:<9} {C.DIM}{files_str}{C.RESET}")

    print()


def cmd_timeline(session_id: str = None):
    """Show chronological timeline of events in a session."""
    sessions = load_all_sessions()

    if session_id:
        matches = [k for k in sessions if session_id in k]
        if not matches:
            print(f"{C.RED}No session matching '{session_id}'{C.RESET}")
            return
        target = matches[0]
    else:
        result = get_latest_session(sessions)
        if not result:
            print(f"{C.YELLOW}No sessions found.{C.RESET}")
            return
        target, _ = result

    records = sessions[target]
    print(f"\n{C.BOLD}Timeline: {C.CYAN}{target}{C.RESET}")
    print(f"{'═' * 70}")

    for r in records:
        ts = r.get("timestamp", "")[:19].replace("T", " ")
        rtype = r.get("type", "?")

        if rtype == "trigger":
            trigger_type = r.get("trigger_type", "?")
            msg = r.get("message", "")[:100]
            color = C.RED if trigger_type == "test_failure" else C.YELLOW
            print(f"\n  {C.DIM}{ts}{C.RESET}  {color}▶ TRIGGER{C.RESET} ({trigger_type})")
            print(f"  {'':>21}{C.DIM}{msg}{C.RESET}")

        elif rtype == "edit":
            file_path = r.get("file_path", "?")
            scope = r.get("scope", "?")
            edit_type = r.get("edit_type", "?")
            success = r.get("success", False)
            explanation = r.get("explanation", "")

            icon = f"{C.GREEN}✓{C.RESET}" if success else f"{C.RED}✗{C.RESET}"
            print(f"\n  {C.DIM}{ts}{C.RESET}  {icon} {C.BOLD}EDIT{C.RESET} {C.BLUE}{file_path}{C.RESET}::{C.MAGENTA}{scope}{C.RESET} ({edit_type})")

            if r.get("before_snippet") and r.get("after_snippet"):
                before_short = r["before_snippet"][:60].replace('\n', '↵')
                after_short = r["after_snippet"][:60].replace('\n', '↵')
                print(f"  {'':>21}{C.RED}- {before_short}{C.RESET}")
                print(f"  {'':>21}{C.GREEN}+ {after_short}{C.RESET}")
            elif r.get("after_snippet"):
                after_short = r["after_snippet"][:60].replace('\n', '↵')
                print(f"  {'':>21}{C.GREEN}+ {after_short}{C.RESET}")

            if explanation:
                print(f"  {'':>21}{C.ITALIC}{C.DIM}↳ {explanation[:90]}{C.RESET}")

        elif rtype == "test_result":
            cmd = r.get("command", "?")[:50]
            success = r.get("success", False)
            failures = r.get("failures", [])

            if success:
                print(f"\n  {C.DIM}{ts}{C.RESET}  {C.GREEN}✓ TEST PASS{C.RESET} {C.DIM}{cmd}{C.RESET}")
            else:
                print(f"\n  {C.DIM}{ts}{C.RESET}  {C.RED}✗ TEST FAIL{C.RESET} {C.DIM}{cmd}{C.RESET}")
                for f in failures[:3]:
                    print(f"  {'':>21}{C.RED}  ! {f[:70]}{C.RESET}")

    print(f"\n{'─' * 70}\n")


def cmd_show(file_path: str):
    """Show provenance for a specific file, grouped by scope."""
    sessions = load_all_sessions()

    file_edits = []
    for session_id, records in sessions.items():
        for r in records:
            if r.get("type") == "edit" and r.get("file_path") == file_path:
                r["_session"] = session_id
                file_edits.append(r)

    if not file_edits:
        print(f"{C.YELLOW}No provenance for: {file_path}{C.RESET}")
        all_files = _list_tracked_files(sessions)
        if all_files:
            print(f"  Tracked files: {all_files}")
        return

    by_scope = defaultdict(list)
    for edit in file_edits:
        by_scope[edit.get("scope", "unknown")].append(edit)

    total = len(file_edits)
    sess_count = len(set(e["_session"] for e in file_edits))
    print(f"\n{C.BOLD}{C.BLUE}{file_path}{C.RESET} — {total} edit(s) across {sess_count} session(s)")
    print(f"{'═' * 70}")

    for scope, edits in by_scope.items():
        rounds = len(edits)
        print(f"\n  {C.MAGENTA}{C.BOLD}{scope}{C.RESET} ({rounds} round{'s' if rounds != 1 else ''})")
        print(f"  {'─' * 55}")

        for i, edit in enumerate(edits, 1):
            ts = edit.get("timestamp", "")[:19].replace("T", " ")
            edit_type = edit.get("edit_type", "?")
            success = edit.get("success", False)
            explanation = edit.get("explanation", "")

            status = f"{C.GREEN}pass{C.RESET}" if success else f"{C.RED}fail{C.RESET}"
            print(f"  {C.BOLD}Round {i}{C.RESET} | {C.DIM}{ts}{C.RESET} | {edit_type} | {status}")

            if edit.get("before_snippet"):
                preview = edit["before_snippet"][:70].replace('\n', '↵')
                print(f"         {C.RED}  - {preview}{C.RESET}")
            if edit.get("after_snippet"):
                preview = edit["after_snippet"][:70].replace('\n', '↵')
                print(f"         {C.GREEN}  + {preview}{C.RESET}")
            if explanation:
                print(f"         {C.ITALIC}  ↳ {explanation[:80]}{C.RESET}")
            print()

    print()


def cmd_annotate(file_path: str):
    """Annotate a source file with provenance markers on edited lines."""
    sessions = load_all_sessions()

    # Collect edits for this file
    file_edits = []
    for session_id, records in sessions.items():
        for r in records:
            if r.get("type") == "edit" and r.get("file_path") == file_path:
                file_edits.append(r)

    if not file_edits:
        print(f"{C.YELLOW}No provenance for: {file_path}{C.RESET}")
        return

    # Try to read the actual source file
    source_path = Path(file_path)
    if not source_path.exists():
        print(f"{C.RED}File not found: {file_path}{C.RESET}")
        print("Showing edit records only:\n")
        cmd_show(file_path)
        return

    source_lines = source_path.read_text().splitlines()

    # Build a map of scope -> edits with explanations
    scope_info = defaultdict(list)
    for edit in file_edits:
        scope = edit.get("scope", "unknown")
        scope_info[scope].append(edit)

    # Detect which scopes exist at which lines in the source
    scope_lines = {}  # line_number -> scope_name
    current_scope = "module_level"
    for i, line in enumerate(source_lines):
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("async def "):
            current_scope = stripped.split("(")[0].replace("def ", "").replace("async ", "").strip()
        elif stripped.startswith("class "):
            current_scope = stripped.split("(")[0].split(":")[0].replace("class ", "").strip()
        elif stripped.startswith("function "):
            current_scope = stripped.split("function ")[1].split("(")[0].strip()
        scope_lines[i] = current_scope

    # Print annotated source
    print(f"\n{C.BOLD}Annotated: {C.BLUE}{file_path}{C.RESET}")
    print(f"{'═' * 70}")
    print(f"  {C.DIM}Lines with provenance are marked with round count{C.RESET}\n")

    last_scope_shown = None
    for i, line in enumerate(source_lines):
        line_num = i + 1
        scope = scope_lines.get(i, "module_level")
        edits_for_scope = scope_info.get(scope, [])

        # Show scope header when entering a tracked scope
        if scope != last_scope_shown and edits_for_scope:
            rounds = len(edits_for_scope)
            last_explanation = next(
                (e.get("explanation", "") for e in reversed(edits_for_scope) if e.get("explanation")),
                ""
            )
            print(f"  {C.MAGENTA}{'─' * 60}{C.RESET}")
            print(f"  {C.MAGENTA}▎ {scope}: {rounds} edit(s){C.RESET}", end="")
            if last_explanation:
                print(f" {C.DIM}— {last_explanation[:50]}{C.RESET}", end="")
            print()
            last_scope_shown = scope

        # Print the line with annotation marker
        if edits_for_scope:
            marker = f"{C.CYAN}●{C.RESET}"
        else:
            marker = " "

        print(f"  {marker} {C.DIM}{line_num:>4}{C.RESET} │ {line}")

    print(f"\n{'─' * 70}")
    print(f"  {C.CYAN}●{C.RESET} = line in a scope with provenance records")
    print()


def cmd_summary(session_id: str = None):
    """Show summary of a session or all sessions."""
    sessions = load_all_sessions()
    if not sessions:
        print(f"{C.YELLOW}No provenance sessions found.{C.RESET}")
        return

    if session_id:
        matches = [k for k in sessions if session_id in k]
        if not matches:
            print(f"{C.RED}No session matching '{session_id}'{C.RESET}")
            return
        for match in matches:
            _print_session_summary(match, sessions[match])
    else:
        for sid, records in sessions.items():
            _print_session_summary(sid, records)
            print()


def cmd_export(session_id: str = None, output_path: str = None):
    """Export session provenance as a standalone HTML file."""
    sessions = load_all_sessions()

    if session_id:
        matches = [k for k in sessions if session_id in k]
        if not matches:
            print(f"{C.RED}No session matching '{session_id}'{C.RESET}")
            return
        target = matches[0]
    else:
        result = get_latest_session(sessions)
        if not result:
            print(f"{C.YELLOW}No sessions found.{C.RESET}")
            return
        target, _ = result

    records = sessions[target]
    html = _generate_html(target, records)

    if not output_path:
        output_path = f".provenance/{target}-report.html"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html)
    print(f"{C.GREEN}Exported:{C.RESET} {output_path}")
    print(f"  Open in browser: open {output_path}")


def _generate_html(session_id: str, records: list[dict]) -> str:
    """Generate a standalone HTML provenance report."""
    edits = [r for r in records if r.get("type") == "edit"]
    tests = [r for r in records if r.get("type") == "test_result"]
    triggers = [r for r in records if r.get("type") == "trigger"]

    # Build timeline HTML
    timeline_html = ""
    for r in records:
        ts = r.get("timestamp", "")[:19].replace("T", " ")
        rtype = r.get("type", "?")

        if rtype == "trigger":
            trigger_type = r.get("trigger_type", "?")
            msg = _html_escape(r.get("message", "")[:200])
            timeline_html += f'<div class="event trigger"><span class="time">{ts}</span> <span class="badge badge-trigger">▶ {trigger_type}</span><div class="detail">{msg}</div></div>\n'

        elif rtype == "edit":
            fp = _html_escape(r.get("file_path", "?"))
            scope = _html_escape(r.get("scope", "?"))
            edit_type = r.get("edit_type", "?")
            success = r.get("success", False)
            explanation = _html_escape(r.get("explanation", ""))
            before = _html_escape(r.get("before_snippet", ""))
            after = _html_escape(r.get("after_snippet", ""))
            badge_cls = "badge-pass" if success else "badge-fail"
            status_txt = "pass" if success else "fail"

            timeline_html += f'<div class="event edit">'
            timeline_html += f'<span class="time">{ts}</span> '
            timeline_html += f'<span class="badge {badge_cls}">EDIT [{status_txt}]</span> '
            timeline_html += f'<span class="filepath">{fp}</span>::<span class="scope">{scope}</span> ({edit_type})'
            if before:
                timeline_html += f'<pre class="diff-remove">- {before}</pre>'
            if after:
                timeline_html += f'<pre class="diff-add">+ {after}</pre>'
            if explanation:
                timeline_html += f'<div class="explanation">↳ {explanation}</div>'
            timeline_html += f'</div>\n'

        elif rtype == "test_result":
            cmd = _html_escape(r.get("command", "?")[:80])
            success = r.get("success", False)
            failures = r.get("failures", [])
            badge_cls = "badge-pass" if success else "badge-fail"
            status_txt = "PASS" if success else "FAIL"

            timeline_html += f'<div class="event test">'
            timeline_html += f'<span class="time">{ts}</span> '
            timeline_html += f'<span class="badge {badge_cls}">TEST {status_txt}</span> '
            timeline_html += f'<code>{cmd}</code>'
            for fail in failures[:5]:
                timeline_html += f'<div class="failure">! {_html_escape(fail[:100])}</div>'
            timeline_html += f'</div>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Code Provenance Report — {session_id}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; background: #1a1a2e; color: #eee; }}
  h1 {{ color: #64ffda; font-size: 1.5rem; }}
  h2 {{ color: #bb86fc; font-size: 1.2rem; margin-top: 2rem; }}
  .stats {{ display: flex; gap: 2rem; margin: 1rem 0; }}
  .stat {{ background: #16213e; padding: 1rem; border-radius: 8px; text-align: center; }}
  .stat-value {{ font-size: 2rem; font-weight: bold; color: #64ffda; }}
  .stat-label {{ font-size: 0.8rem; color: #aaa; }}
  .event {{ margin: 1rem 0; padding: 0.75rem 1rem; border-left: 3px solid #333; border-radius: 4px; background: #16213e; }}
  .event.trigger {{ border-left-color: #ff9800; }}
  .event.edit {{ border-left-color: #64ffda; }}
  .event.test {{ border-left-color: #bb86fc; }}
  .time {{ color: #888; font-size: 0.8rem; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
  .badge-trigger {{ background: #ff9800; color: #000; }}
  .badge-pass {{ background: #4caf50; color: #000; }}
  .badge-fail {{ background: #f44336; color: #fff; }}
  .filepath {{ color: #82aaff; }}
  .scope {{ color: #c792ea; }}
  .explanation {{ color: #aaa; font-style: italic; margin-top: 0.5rem; }}
  .detail {{ color: #ccc; margin-top: 0.3rem; }}
  .failure {{ color: #f44336; font-size: 0.85rem; }}
  pre {{ margin: 0.5rem 0; padding: 0.5rem; border-radius: 4px; font-size: 0.8rem; overflow-x: auto; }}
  .diff-remove {{ background: #3d1f1f; color: #f88; }}
  .diff-add {{ background: #1f3d1f; color: #8f8; }}
  code {{ background: #0d1117; padding: 2px 6px; border-radius: 3px; font-size: 0.85rem; }}
</style>
</head>
<body>
<h1>Code Provenance Report</h1>
<p>Session: <code>{session_id}</code></p>

<div class="stats">
  <div class="stat"><div class="stat-value">{len(edits)}</div><div class="stat-label">Edits</div></div>
  <div class="stat"><div class="stat-value">{len(tests)}</div><div class="stat-label">Tests</div></div>
  <div class="stat"><div class="stat-value">{len(triggers)}</div><div class="stat-label">Triggers</div></div>
  <div class="stat"><div class="stat-value">{sum(1 for e in edits if e.get('explanation'))}</div><div class="stat-label">Explained</div></div>
</div>

<h2>Timeline</h2>
{timeline_html}
</body>
</html>"""


# --- Helpers ---

def _print_session_summary(session_id: str, records: list[dict]):
    """Print a colored summary for one session."""
    edits = [r for r in records if r.get("type") == "edit"]
    tests = [r for r in records if r.get("type") == "test_result"]
    triggers = [r for r in records if r.get("type") == "trigger"]

    files_edited = sorted(set(e.get("file_path", "") for e in edits if e.get("file_path")))
    test_passes = sum(1 for t in tests if t.get("success"))
    test_fails = sum(1 for t in tests if not t.get("success"))
    explained = sum(1 for e in edits if e.get("explanation"))

    print(f"  {C.BOLD}Session:{C.RESET} {C.CYAN}{session_id}{C.RESET}")
    print(f"    Edits:    {len(edits)} ({C.GREEN}{explained} explained{C.RESET})")
    print(f"    Tests:    {len(tests)} ({C.GREEN}{test_passes} pass{C.RESET}, {C.RED}{test_fails} fail{C.RESET})")
    print(f"    Triggers: {len(triggers)}")
    print(f"    Files:    {C.DIM}{', '.join(files_edited[:5]) or 'none'}{C.RESET}")


def _list_tracked_files(sessions: dict) -> str:
    """Get list of all tracked files."""
    files = set()
    for records in sessions.values():
        for r in records:
            if r.get("type") == "edit" and r.get("file_path"):
                files.add(r["file_path"])
    return ", ".join(sorted(files)[:10]) or "none"


def _html_escape(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# --- Entry Point ---

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "sessions":
        cmd_sessions()

    elif cmd == "timeline":
        sid = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_timeline(sid)

    elif cmd == "show":
        if len(sys.argv) < 3:
            print(f"Usage: {sys.argv[0]} show <file_path>")
            sys.exit(1)
        cmd_show(sys.argv[2])

    elif cmd == "annotate":
        if len(sys.argv) < 3:
            print(f"Usage: {sys.argv[0]} annotate <file_path>")
            sys.exit(1)
        cmd_annotate(sys.argv[2])

    elif cmd == "summary":
        sid = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_summary(sid)

    elif cmd == "export":
        sid = None
        output = None
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--output" and i + 1 < len(args):
                output = args[i + 1]
                i += 2
            elif args[i].startswith("--output="):
                output = args[i].split("=", 1)[1]
                i += 1
            elif not args[i].startswith("-"):
                sid = args[i]
                i += 1
            else:
                i += 1
        cmd_export(sid, output)

    else:
        print(f"{C.RED}Unknown command: {cmd}{C.RESET}")
        print(__doc__)
        sys.exit(1)
