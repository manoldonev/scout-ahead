# Borrow loop: where it stands and how to continue

Goal (operator's words): iterate on the prior art till we have nothing more to borrow.

## State after round 1 (2026-10-30, stopped at the usage limit)

- `round-1/results.json`: 18 readers' full output (233 candidates, each with mechanic, source pointer, quote, what scout-ahead does today, proposed change, kind, value, cost) and 13 judgments (all accepts, with refined changes). The unsearched-tail reader did not finish.
- `docs/borrow-round-1.md`: the same, readable.
- `round-script.js`: the workflow that produced it (readers on Opus, judges on Fable). The original run id was wf_9689d712-9f9 in a session that is gone; a workflow resume is same-session only, so do NOT try to resume it.

## How to continue in a new session

1. Judge the 220 unjudged candidates from `round-1/results.json` with a judge-only workflow: pass the candidates as `args`, one judge agent per candidate on Opus (Fable budget is the scarce one), same VERDICT schema and rules as in `round-script.js`, then the planner stage. Readers do not need to run again.
2. Implement the ranked accepts in `plugins/scout/scripts/scout.py`, the skills and docs; add a test per mechanic in `tests/test_scout.py`; `./selftest.sh`; commit; push. Append each borrow to "What was borrowed" in `docs/prior-art.md`.
3. Run round 2 with `round-script.js` (set judges to `model: 'opus'`), sources unchanged plus anything the unsearched-tail reader was meant to cover (naishtech/cadet-agent cadet-spike, DEFRA/ai-sdlc-content-audit spike, mistakenot/skills tech-spike, majiayu000/claude-skill-registry spike entries).
4. Stop when a round accepts nothing.

## Standing constraints

- Repo is public at github.com/manoldonev/scout-ahead (personal account); push to main as work lands.
- Not submitting to the Anthropic plugin directory yet: "too early to submit something that we haven't used".
- Next real test after the loop: a real scout on an open question in sales or sales-ui, installed at local scope.
