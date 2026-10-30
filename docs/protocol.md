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

A scout is one question. It has a box (hours and dollars), kill criteria, and an ordered
list of directions. One direction is open at a time. A pivot closes it with what it taught
and opens the next; a close ends the scout. Pivots are cheap on purpose: they are the
common path.

## Rules

1. **Explore the code before deciding anything.** `start` ends with a note that says what
   the code says. Agents find most blockers in code, not in specs.
2. **No asking mid-build.** A question that comes up while building is parked
   (`scout question`) and raised at a boundary: a pivot, a close, or when the operator asks.
   The pivot and close commands print the parked list so the boundary cannot be skipped.
3. **Curated, not retrieved.** Nothing is pulled into context by similarity. A successor
   reads the log and the raw transcript, which the hook records and re-injects.
4. **Decisions are written at the end of a direction, not the start.** `decisions.md` is
   never the output of a dialog: it is recorded when the operator says "record this", or
   recovered at the close from the diff and the transcript. Each decision carries who settled
   it: `operator` (their words or a transcript pointer; the script checks the words verbatim
   against the operator's recorded turns, never a compaction summary, and only another
   operator decision supersedes one), `code` (a constraint with a file:line or commit,
   labelled `proved` only when this scout saw the check fail with the mechanism reverted or
   stubbed, at a named seat, and `inferred` otherwise), or `open` (with the question to
   ask). Each decision records the commit its evidence was cited against. A later direction
   that reverses a decision marks it superseded and leaves it in place; a replacement decision
   marks the old one by id. Before closing, the inferred ones are re-run: the setup exists by
   then, and an inference is where a scout is most confidently wrong.
4a. **Kill and keep criteria are fixed before the build**, and re-read before a pivot or close,
   not after. The close gives the question a verdict, `proven`, `disproven`, `conditional` or
   `unanswered`, and lists what is still unknown, because a scout that names what it did not
   settle bounds its own authority. Most honest disproofs are conditional: name the thing held
   fixed. The script refuses a verdict without the evidence its kind needs: `proven` an
   observed (`code, proved`) decision, `disproven` the wall and a repro, `conditional` the
   constraint and its blast radius. The close records which criteria fired, as written; a
   criterion is never widened after the fact. A `commit` carries the branch forward as
   evidence, never as code to merge.
4b. **Every fake is recorded when it is made** (`scout stub`), survives pivots and compaction,
   and is re-read against the question before the verdict. A stub of the part under test makes
   the verdict `unanswered`; blocked on access is a parked question, not a mock.
5. **Pre-registration only once a question is measurable**, and then before the scored run:
   arms, runs, pass rule, cost bound. The handoff carries it; the plugin never invents one.
6. **Two to four variants at most**, each in its own worktree and branch, each its own
   `claude -p` process with its own `--max-budget-usd`, compared as evidence. The prompt
   forbids leaving the worktree; the worktrees are siblings, so no arm sees another's draft.
   The arms differ on one axis, the criteria are written before the race and judged on
   behavior, no hybrid is cherry-picked, and nothing is deleted before the operator has seen
   the comparison.
7. **Every spawn has a dollar cap**, enforced by the CLI between turns. The scout's own box is
   metered from spawn costs plus what the operator logs (`scout spent`); the interactive
   session's own bill is not visible to the plugin and is not claimed.
8. **No dependence** on agent teams running headless, on credential pass-through, or on a
   long-lived session surviving compaction without the hook. Opus by default for anything the
   plugin spawns.
9. **No names.** The plugin never writes a customer, client or employer name into an
   artifact. It copies what the operator wrote and gives everything from outside a pointer.

## Session boundaries

The `SessionStart` hook runs on `startup`, `resume`, `compact` and `clear`. It writes the
session id and transcript path to `scouting/.session.json` (gitignored), appends them to the
open scout's `sessions[]`, and emits the open scout's question, the directions already
tried and left (each with what it taught and the observation that turned it), current
direction, last notes, decisions in force, parked questions, open stubs and transcript paths
as additional context. On `compact` it says so, because automatic compaction keeps only a
fraction of side constraints.

## What the model does and what the script does

The script (`scripts/scout.py`) owns structure: folders, branches, state, rendering, the
variant runs, the hook payload. The model owns judgment: what the code says, the learned
line at a pivot, which recovered decision was settled by whom, the comparison of variants.
The three markdown files are rendered from `state.json` on every command so they never
disagree with what was recorded.
