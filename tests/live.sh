#!/usr/bin/env bash
# Live selftest: a scripted `claude -p` run that starts a spike, pivots, closes and
# hands off, then checks the artifacts; and the compaction re-injection check.
# Costs money (a few tenths of a dollar on the default model). SPIKE_TEST_MODEL and
# SPIKE_TEST_USD override the model and the per-step cap.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN="$HERE/../plugins/spike"
MODEL="${SPIKE_TEST_MODEL:-sonnet}"
CAP="${SPIKE_TEST_USD:-1}"
unset CLAUDECODE
command -v claude >/dev/null || { echo "SKIP: claude not on PATH"; exit 0; }

WORK="$(mktemp -d -t spike-live.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK" && git init -q -b main && git config user.email t@example.invalid && git config user.name t
echo "def add(a, b): return a + b" > calc.py && git add calc.py && git commit -qm init
SID="$(python3 -c 'import uuid;print(uuid.uuid4())')"
fail=0
ok()   { echo "  ok   $1"; }
bad()  { echo "  FAIL $1"; fail=1; }
check(){ if eval "$2"; then ok "$1"; else bad "$1"; fi; }

run() { # run <label> <prompt> [extra flags]
  local label="$1" prompt="$2"; shift 2
  local out
  out="$(claude -p --plugin-dir "$PLUGIN" --model "$MODEL" --max-budget-usd "$CAP" \
        --permission-mode acceptEdits --permission-prompts none --allowedTools Bash \
        --output-format json "$@" "$prompt" 2>/dev/null)"
  local sub cost
  sub="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("subtype"))' 2>/dev/null)"
  cost="$(printf '%s' "$out" | python3 -c 'import json,sys; print(round(json.load(sys.stdin).get("total_cost_usd",0),3))' 2>/dev/null)"
  echo "  step $label: $sub, \$$cost"
  printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("result",""))' 2>/dev/null > "$WORK/.last-result"
  [ "$sub" = "success" ] || fail=1
}

echo "live: scripted loop (model $MODEL, cap \$$CAP per step)"
run start "/spike:start Can add() be made total over floats and ints without a type check? --hours 1 --usd 2 --kill 'no path without isinstance'" --session-id "$SID"
SLUG="$(cat spikes/.current 2>/dev/null)"
check "spike folder created" '[ -n "$SLUG" ] && [ -f "spikes/$SLUG/state.json" ]'
check "branch created" '[ "$(git branch --show-current)" = "spike/$SLUG" ]'
check "code explored before deciding (a code: note exists)" 'grep -q "note: code:" "spikes/$SLUG/log.md"'
check "no decision at start" '[ "$(python3 -c "import json;print(len(json.load(open(\"spikes/$SLUG/state.json\"))[\"decisions\"]))")" = 0 ]'
check "hook recorded the session transcript" 'grep -q "\"session_id\": \"$SID\"" "spikes/$SLUG/state.json"'

run pivot "/spike:pivot coerce both operands with float() and accept the precision loss" --resume "$SID"
check "direction 2 open" 'grep -q "## Direction 2:" "spikes/$SLUG/log.md"'
check "direction 1 closed with a learned line" 'grep -q "closed by pivot. Learned:" "spikes/$SLUG/log.md"'

run close "/spike:close kill" --resume "$SID"
check "spike closed" 'grep -q "\"status\": \"closed\"" "spikes/$SLUG/state.json"'
check "close wrote learned" 'grep -q "^Learned: ." "spikes/$SLUG/log.md"'
check ".current cleared" '[ ! -f spikes/.current ]'

run handoff "/spike:handoff" --resume "$SID"
check "handoff.md written" '[ -f "spikes/$SLUG/handoff.md" ]'
for h in "## Question" "## Status" "## Decisions" "## Open questions" "## Pointers" "## Thrown away"; do
  check "handoff has '$h'" 'grep -q "^$h" "spikes/$SLUG/handoff.md"'
done
check "handoff points at the transcript" 'grep -q "^- transcript: .*$SID.jsonl" "spikes/$SLUG/handoff.md"'
check "no pre-registration invented" '! grep -q "## Pre-registration" "spikes/$SLUG/handoff.md" || grep -q "pre-registered" "spikes/$SLUG/log.md"'

echo "live: compaction re-injection"
SID2="$(python3 -c 'import uuid;print(uuid.uuid4())')"
git checkout -q main
run start2 "/spike:start Which of the two add() paths survives compaction? --hours 1 --usd 1 --kill 'direction lost after compact'" --session-id "$SID2"
SLUG2="$(cat spikes/.current 2>/dev/null)"
run compact "/compact" --resume "$SID2"
run after "Answer in one line, from context only, without running any tool: what is the open spike's question and its kill criterion?" --resume "$SID2"
TRANSCRIPT="$(python3 -c 'import json;print(json.load(open("spikes/.session.json"))["transcript_path"])')"
check "compact_boundary in transcript" 'grep -q "\"subtype\":\"compact_boundary\"" "$TRANSCRIPT"'
check "SessionStart:compact hook fired" 'grep -q "\"hookName\":\"SessionStart:compact\"" "$TRANSCRIPT"'
check "hook re-injected the spike" 'grep -q "Context was just compacted" "$TRANSCRIPT"'
check "post-compact answer names the question" 'grep -qi "survives compaction" "$WORK/.last-result"'
check "post-compact answer names the kill criterion" 'grep -qi "direction lost after compact" "$WORK/.last-result"'

if [ "$fail" = 0 ]; then echo "live: PASS"; else echo "live: FAIL"; fi
exit $fail
