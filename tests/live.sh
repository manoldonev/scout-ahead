#!/usr/bin/env bash
# Live selftest: a scripted `claude -p` run that starts a scout, pivots, closes and
# hands off, then checks the artifacts; and the compaction re-injection check.
# Costs money (a few tenths of a dollar on the default model). SCOUT_TEST_MODEL and
# SCOUT_TEST_USD override the model and the per-step cap.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN="$HERE/../plugins/scout"
MODEL="${SCOUT_TEST_MODEL:-sonnet}"
CAP="${SCOUT_TEST_USD:-1}"
unset CLAUDECODE
command -v claude >/dev/null || { echo "SKIP: claude not on PATH"; exit 0; }

WORK="$(mktemp -d -t scout-live.XXXXXX)"
trap 'rm -rf "$WORK" "$WORK-scout-worktrees"' EXIT
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
run start "/scout:start Can add() be made total over floats and ints without a type check? --hours 1 --usd 2 --kill 'no path without isinstance'" --session-id "$SID"
SLUG="$(cat scouting/.current 2>/dev/null)"
check "scout folder created" '[ -n "$SLUG" ] && [ -f "scouting/$SLUG/state.json" ]'
check "branch created" '[ "$(git branch --show-current)" = "scout/$SLUG" ]'
check "code explored before deciding (a code: note exists)" 'grep -q "note: code:" "scouting/$SLUG/log.md"'
check "no decision at start" '[ "$(python3 -c "import json;print(len(json.load(open(\"scouting/$SLUG/state.json\"))[\"decisions\"]))")" = 0 ]'
check "hook recorded the session transcript" 'grep -q "\"session_id\": \"$SID\"" "scouting/$SLUG/state.json"'

run note "/scout:note operator: floats must round-trip through json, so the answer has to survive json.dumps" --resume "$SID"
check "note appended verbatim" 'grep -q "note: operator: floats must round-trip through json" "scouting/$SLUG/log.md"'

run scout "/scout:think I keep going back and forth: is a type check really worse than silent coercion here? Give me your read, with evidence from calc.py." --resume "$SID"
check "conversation answered in prose" '[ "$(wc -w < "$WORK/.last-result")" -gt 40 ]'
check "no option dialog in conversation mode" '! grep -qiE "option [ab]\)|^\s*[0-9]\. \*\*(Option|Choice)" "$WORK/.last-result"'
check "no decision recorded without 'record this'" '[ "$(python3 -c "import json;print(len(json.load(open(\"scouting/$SLUG/state.json\"))[\"decisions\"]))")" = 0 ]'

run status "/scout:status" --resume "$SID"
check "status names the scout" 'grep -q "$SLUG" "$WORK/.last-result"'

VCAP="${SCOUT_TEST_ARM_USD:-0.35}"
run variants "/scout:variants 2 'Can add() stay total over floats and ints without a type check? Answer in VARIANT.md only, no code.' --usd $VCAP --model $MODEL" --resume "$SID"
check "two arms recorded" '[ "$(python3 -c "import json;print(len(json.load(open(\"scouting/$SLUG/state.json\"))[\"variants\"][0][\"arms\"]))")" = 2 ]'
check "arm results collected" '[ -f "scouting/$SLUG/variants/run-1/v1/result.json" ] && [ -f "scouting/$SLUG/variants/run-1/v2/result.json" ]'
check "arms ran (a turn count > 0)" 'python3 -c "import json;d=json.load(open(\"scouting/$SLUG/variants/run-1/v1/result.json\"));import sys;sys.exit(0 if (d.get(\"num_turns\") or 0)>0 else 1)"'
check "arm cost metered into the box" 'python3 -c "import json;import sys;sys.exit(0 if json.load(open(\"scouting/$SLUG/state.json\"))[\"spent\"][\"usd\"]>0 else 1)"'
check "arms on separate branches" '[ "$(git branch --list "scout/$SLUG-run1-v*" | wc -l | tr -d " ")" = 2 ]'
check "comparison written to the log" 'grep -qi "variants run 1" "scouting/$SLUG/log.md"'
git worktree list --porcelain | grep "^worktree .*-scout-worktrees" | cut -d" " -f2 | while read -r w; do git worktree remove --force "$w"; done; git worktree prune

run pivot "/scout:pivot coerce both operands with float() and accept the precision loss" --resume "$SID"
check "direction 2 open" 'grep -q "## Direction 2:" "scouting/$SLUG/log.md"'
check "direction 1 closed with a learned line" 'grep -q "closed by pivot. Learned:" "scouting/$SLUG/log.md"'

run close "/scout:close kill" --resume "$SID"
check "scout closed" 'grep -q "\"status\": \"closed\"" "scouting/$SLUG/state.json"'
check "close wrote learned" 'grep -q "^Learned: ." "scouting/$SLUG/log.md"'
check ".current cleared" '[ ! -f scouting/.current ]'

run handoff "/scout:handoff" --resume "$SID"
check "handoff.md written" '[ -f "scouting/$SLUG/handoff.md" ]'
for h in "## Question" "## Status" "## Decisions" "## Open questions" "## Pointers" "## Thrown away"; do
  check "handoff has '$h'" 'grep -q "^$h" "scouting/$SLUG/handoff.md"'
done
check "handoff points at the transcript" 'grep -q "^- transcript: .*$SID.jsonl" "scouting/$SLUG/handoff.md"'
check "no pre-registration invented" '! grep -q "## Pre-registration" "scouting/$SLUG/handoff.md" || grep -q "pre-registered" "scouting/$SLUG/log.md"'

echo "live: compaction re-injection"
SID2="$(python3 -c 'import uuid;print(uuid.uuid4())')"
git checkout -q main
run start2 "/scout:start Which of the two add() paths survives compaction? --hours 1 --usd 1 --kill 'direction lost after compact'" --session-id "$SID2"
SLUG2="$(cat scouting/.current 2>/dev/null)"
run compact "/compact" --resume "$SID2"
run after "Answer in one line, from context only, without running any tool: what is the open scout's question and its kill criterion?" --resume "$SID2"
TRANSCRIPT="$(python3 -c 'import json;print(json.load(open("scouting/.session.json"))["transcript_path"])')"
check "compact_boundary in transcript" 'grep -q "\"subtype\":\"compact_boundary\"" "$TRANSCRIPT"'
check "SessionStart:compact hook fired" 'grep -q "\"hookName\":\"SessionStart:compact\"" "$TRANSCRIPT"'
check "hook re-injected the scout" 'grep -q "Context was just compacted" "$TRANSCRIPT"'
check "post-compact answer names the question" 'grep -qi "survives compaction" "$WORK/.last-result"'
check "post-compact answer names the kill criterion" 'grep -qi "direction lost after compact" "$WORK/.last-result"'

if [ "$fail" = 0 ]; then echo "live: PASS"; else echo "live: FAIL"; fi
exit $fail
