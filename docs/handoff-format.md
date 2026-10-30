# The handoff file

`scouting/<slug>/handoff.md` is one plain markdown file with fixed headings. Nothing in it
depends on which tool reads it. It is regenerated from `state.json` by `/scout:handoff`;
to change it, change the record (`decide`, `answer`, `question`, `prereg`) and run handoff
again.

## Shape

```
# Handoff: <question>
<!-- scout-ahead handoff v1; plain markdown, fixed headings; written <timestamp> -->

## Question
## Status               status, directions, box, keep/kill criteria, verdict on the question, learned
## Decisions            table: id | decision | settled by | evidence | superseded by
## Open questions       bullets: open decisions (D-ids, with the question to ask) and parked questions
## Pointers             bullets: branch, base, head, directions, variant arms, transcripts, log, decisions
## Pre-registration     present only when a question became measurable
## Thrown away
## Still unknown        what the scout did not settle
```

The version marker in the HTML comment lets a reader detect the shape without parsing.

## Fields

- **Decisions.** `settled by` is one of `operator`, `code, proved`, `code, inferred`, `open`. The file states the mapping onto ledger-style vocabularies itself (`user-answered`, `codebase-derived`, `deferred`; why-log's testimony / stated / inferred), so a reader with a closed provenance enum needs no plugin knowledge. An `operator` row always carries a quote or a transcript pointer. `evidence` is a
  pointer: a file:line, a commit, a transcript path, the operator's quoted words. A
  superseded decision stays in the table with `superseded by: direction N`; the reader
  treats it as history, not as a constraint.
- **Open questions.** Everything the scout did not settle: open decisions by id, and parked
  questions nobody answered at a boundary.
- **Pointers.** Branch and commits resolve with `git rev-parse`; transcript paths are the
  raw session traces (`~/.claude/projects/…/<session>.jsonl`), which beat structured notes
  for a successor.
- **Pre-registration.** `question`, `arms`, `runs`, `pass rule`, `cost bound`, and when it
  was registered. It is written before any scored run; a scored track runs it as given. An
  A/B harness such as [agent-ab](https://github.com/h-a-forster/agent-ab) is the natural consumer.
- **Still unknown.** The conditions never exercised, the parts stubbed, the scale untested; it
  bounds the scout's authority so a narrow result is not read as a general one.
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

The generator refuses to write a handoff that drops a decision id, a direction, a branch or an
open question from the record (a cover check). A tool that reads only the Decisions table and
the Open questions list has what it needs.
