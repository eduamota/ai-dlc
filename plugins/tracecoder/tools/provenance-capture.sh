#!/bin/bash
# plugins/tracecoder/tools/provenance-capture.sh
#
# TraceCoder-inspired provenance capture hook for AI-DLC.
# Routes hook events to the Python processor based on event type.
#
# This script is called by the harness hook system with JSON on STDIN.
# It uses the session ID (KIRO_SESSION_ID or fallback) to correlate events.
#
# Install: wire into the harness's postToolUse(write), postToolUse(shell),
# stop, and userPromptSubmit hooks alongside the existing AI-DLC hooks.

set -uo pipefail

# Resolve paths relative to where this script lives
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROCESSOR="${HOOK_DIR}/provenance_processor.py"

# Session file path — one JSONL file per session
SESSION_ID="${KIRO_SESSION_ID:-${AIDLC_SESSION_ID:-$(date +%s)}}"
PROVENANCE_DIR=".provenance/sessions"
SESSION_FILE="${PROVENANCE_DIR}/${SESSION_ID}.jsonl"

# Read the full event from STDIN into a variable
EVENT=$(cat)

# Extract the hook event name (support both Kiro and Claude Code formats)
HOOK_NAME=$(echo "$EVENT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    # Kiro format
    name = data.get('hook_event_name', '')
    if not name:
        # Claude Code format
        name = data.get('event', '')
    print(name or 'unknown')
except:
    print('unknown')
" 2>/dev/null)

# Route to the appropriate processor command
case "$HOOK_NAME" in
    postToolUse|PostToolUse)
        echo "$EVENT" | python3 "$PROCESSOR" record-edit "$SESSION_FILE"
        ;;
    stop|Stop)
        echo "$EVENT" | python3 "$PROCESSOR" attach-explanation "$SESSION_FILE"
        ;;
    userPromptSubmit|UserPromptSubmit)
        echo "$EVENT" | python3 "$PROCESSOR" record-prompt "$SESSION_FILE"
        ;;
    *)
        # Unknown event type — silently ignore
        ;;
esac

# Always exit 0 so we never block the agent
exit 0
