#!/usr/bin/env bash
# SessionStart hook: records this session's id and transcript path for the open
# spike and re-injects its question, current direction, decisions in force and
# parked questions. Emits nothing when no spike is open.
set -uo pipefail
case "$0" in
  */*) HOOK_DIR="$(cd "${0%/*}" && pwd)" ;;
  *) HOOK_DIR="$(pwd)" ;;
esac
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$HOOK_DIR/.." && pwd)}"
PY="$(command -v python3 || command -v python || true)"
[ -z "$PY" ] && exit 0
"$PY" "$ROOT/scripts/spike.py" hook-session-start
