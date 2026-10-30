# The protocol

## The loop

```
start ─► explore the code ─► think and build (conversation) ─► pivot ─┐
  ▲                                                                   │
  └───────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          close (kill | commit) ─► handoff
```

A spike is one question. It has a box (hours and dollars), kill criteria, and an ordered
list of directions. One direction is open at a time. A pivot closes it with what it taught
and opens the next; a close ends the spike. Pivots are cheap on purpose: they are the
common path.

## Rules

1. **Explore the code before deciding anything.** `start` ends with a note that says what
   the code says. Agents find most blockers in code, not in specs.
2. **No asking mid-build.** A question that comes up while building is parked
   (`spike question`) and raised at a boundary: a pivot, a close, or when the operator asks.
   The pivot and close commands print the parked list so the boundary cannot be skipped.
3. **Curated, not retrieved.** Nothing is pulled into context by similarity. A successor
   reads the log and the raw transcript, which the hook records and re-injects.
4. **Decisions are written at the end of a direction, not the start.** `decisions.md` is
   never the output of a dialog: it is recorded when the operator says "record this", or
   recovered at the close from the diff and the transcript. Each decision carries who settled
   it: `operator` (their words, quoted or pointed to), `code` (a constraint with a file:line
   or commit), or `open`. A later direction that reverses a decision marks it superseded and
   leaves it in place.
5. **Pre-registration only once a question is measurable**, and then before the scored run:
   arms, runs, pass rule, cost bound. The handoff carries it; the plugin never invents one.
6. **Two to four variants at most**, each in its own worktree and branch, each its own
   `claude -p` process with its own `--max-budget-usd`, compared as evidence. The prompt
   forbids leaving the worktree; the worktrees are siblings, so no arm sees another's draft.
7. **Every spawn has a dollar cap**, enforced by the CLI between turns. The spike's own box is
   metered from spawn costs plus what the operator logs (`spike spent`); the interactive
   session's own bill is not visible to the plugin and is not claimed.
8. **No dependence** on agent teams running headless, on credential pass-through, or on a
   long-lived session surviving compaction without the hook. Opus by default for anything the
   plugin spawns.
9. **No names.** The plugin never writes a customer, client or employer name into an
   artifact. It copies what the operator wrote and gives everything from outside a pointer.

## Session boundaries

The `SessionStart` hook runs on `startup`, `resume`, `compact` and `clear`. It writes the
session id and transcript path to `spikes/.session.json` (gitignored), appends them to the
open spike's `sessions[]`, and emits the open spike's question, current direction, last
notes, decisions in force, parked questions and transcript paths as additional context. On
`compact` it says so, because automatic compaction keeps only a fraction of side constraints.

## What the model does and what the script does

The script (`scripts/spike.py`) owns structure: folders, branches, state, rendering, the
variant runs, the hook payload. The model owns judgment: what the code says, the learned
line at a pivot, which recovered decision was settled by whom, the comparison of variants.
The three markdown files are rendered from `state.json` on every command so they never
disagree with what was recorded.
