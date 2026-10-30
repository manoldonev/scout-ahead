# The handoff file

`scouting/<slug>/handoff.md` is one plain markdown file with fixed headings. Nothing in it
depends on which tool reads it. It is regenerated from `state.json` by `/scout:handoff`;
to change it, change the record (`decide`, `answer`, `question`, `prereg`) and run handoff
again.

## Shape

```
# Handoff: <question>
<!-- scout-ahead handoff v1; plain markdown, fixed headings; written <timestamp> -->

## Question             the question, and its stakes when `start` recorded them
## Status               status, directions, box, keep/kill criteria and which fired, verdict on the question, blast radius, learned
## Decisions            table: id | decision | settled by | evidence | superseded by
## Open questions       bullets: open decisions (D-ids, with the question to ask) and parked questions (Q-ids, with what the build proceeded on)
## Pointers             bullets: branch, base, head, directions (with what each taught), variant arms, transcripts, log, decisions
## Reproducing          present only when the close gave a repro: the command, run from the scout branch, and what to look at
## Pre-registration     present only when a question became measurable: one `### R<n>` block per registration
## Thrown away
## Still unknown        what the scout did not settle, and the stubs still open
```

The version marker in the HTML comment lets a reader detect the shape without parsing.

## Fields

- **Status.** Kill criteria are numbered K1.., keep criteria P1... After a close, each is
  marked `fired` or `did not fire`, or the line `Criteria: none fired.` says none did. The
  script refuses a verdict without its evidence: `proven` needs a `code, proved` decision,
  `disproven` a note and a repro, `conditional` a note and a blast radius (what depends on the
  constraint held fixed). The box line is what the scout spent, not an estimate.
- **Decisions.** `settled by` is one of `operator`, `code, proved`, `code, inferred`, `open`. The file states the mapping onto ledger-style vocabularies itself (`user-answered`, `codebase-derived`, `deferred`; why-log's testimony / stated / inferred), so a reader with a closed provenance enum needs no plugin knowledge. An `operator` row always carries a transcript pointer or a quote the script found verbatim in a
  recorded operator turn (compaction summaries excluded), and only another operator decision
  supersedes it. `code, proved` means the check was seen to fail with the mechanism reverted,
  and the evidence names that run and its seat. `evidence` is a pointer: a file:line, a commit,
  a transcript path, the operator's quoted words, followed by `@ <sha12>` for the commit it was
  cited against and `+dirty` when the tree had uncommitted changes then. A
  superseded decision stays in the table with `superseded by: direction N`; the reader
  treats it as history, not as a constraint.
- **Question.** The question verbatim, followed by `Stakes: …` when the scout recorded the
  decision waiting on the answer and what yes and no would each change.
- **Open questions.** Everything the scout did not settle: open decisions by id, and parked
  questions nobody answered at a boundary, as `Q<n>: <question> (proceeding on: <default>)`.
  The id never shifts; the default is what the build was done under, so an answer that
  differs from it means re-checking that work.
- **Pointers.** Each variant arm line names the approach the arm was told to take (`sampled`
  when the run named none). Branch and commits resolve with `git rev-parse`; transcript paths are the
  raw session traces (`~/.claude/projects/…/<session>.jsonl`), which beat structured notes
  for a successor. The generator marks a branch `(missing)`, `(no commits past base)` or
  `(not pushed)`, and a transcript `(local to this machine)` or `(missing)`, so a reader knows
  which pointers it can follow. Each closed direction carries what it taught and the
  observation that turned it (`— learned: …; turned on: …`).
- **Reproducing.** The command that shows the result, run from the scout branch, and what to
  look at in its output. Required for a `disproven` verdict.
- **Pre-registration.** One `### R<n>` block per registration, each with `question`, `arms`,
  `runs`, `pass rule` (stating the runs discarded as warmup and the spread tolerated),
  `floor` (what an arm that changed nothing scores, and why that fails the rule), `cost
  bound`, when it was registered, and `status`: `open`, or `passed` / `failed` / `dropped`
  followed by the pointer to the run in parentheses. Registrations are append-only; only the
  status changes after one is written, and the cover check refuses a handoff that drops a
  P-id. A registration from before floors existed reads `floor: (not recorded; …)`. It is
  written before any scored run; a scored track runs it as given. An
  A/B harness such as [agent-ab](https://github.com/h-a-forster/agent-ab) is the natural consumer.
- **Still unknown.** The conditions never exercised, the parts stubbed, the scale untested; it
  bounds the scout's authority so a narrow result is not read as a general one. Every stub
  recorded with `scout stub` and not yet replaced appears as `- stubbed: S<n> …`; the cover
  check refuses a handoff that drops one.
- **Thrown away.** What is discarded and why, so nobody reopens it by accident.

## How a spec-driven tool reads it

- **Decisions settled by the operator** go into the spec as given, with their evidence
  pointer as provenance. They are not re-asked.
- **Decisions settled by the code** go in as constraints; the pointer is the citation.
- **Open questions** are the interview: a spec-driven intake asks exactly these and nothing
  that is already settled.
- **The verdict** (proven / disproven / conditional / unanswered) says what to do with the
  question: proven unblocks work, disproven closes a path, conditional is a priced decision that
  needs a decision-maker rather than a ticket.
- **Pre-registration** is the scored run's contract: the arms, runs and pass rule are fixed
  before the run starts, and the cost bound caps it.
- **Pointers** replace copying: the downstream tool links the branch and commits rather
  than pasting diffs.
- **The scout branch is evidence**: it is re-run and cited, never merged. A `commit` outcome
  authorizes a rebuild of what it proved under the receiving track's own rules.
- **The box** is what the scout spent without tests, error handling or edge cases. It is not
  an estimate for the real build.

The generator refuses to write a handoff that drops a decision id, a direction, a branch, an
open stub or an open question from the record (a cover check), or that points at a scout branch that no longer
exists. A tool that reads only the Decisions table and the Open questions list has what it
needs.

Before it ships, `/scout:handoff` has a fresh, capped, read-only agent read the file cold
(`scout coldread`), writing `coldread.md` beside it. That file is a pointer for the author,
not a handoff section: its questions are folded back into the record and the handoff is
regenerated.
