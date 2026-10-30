# The handoff file

`spikes/<slug>/handoff.md` is one plain markdown file with fixed headings. Nothing in it
depends on which tool reads it. It is regenerated from `state.json` by `/spike:handoff`;
to change it, change the record (`decide`, `answer`, `question`, `prereg`) and run handoff
again.

## Shape

```
# Handoff: <question>
<!-- spike handoff v1; plain markdown, fixed headings; written <timestamp> -->

## Question
## Status
## Decisions            table: id | decision | settled by | evidence | superseded by
## Open questions       bullets: open decisions (D-ids) and parked questions
## Pointers             bullets: branch, base, head, directions, variant arms, transcripts, log, decisions
## Pre-registration     present only when a question became measurable
## Thrown away
```

The version marker in the HTML comment lets a reader detect the shape without parsing.

## Fields

- **Decisions.** `settled by` is one of `operator`, `code`, `open`. `evidence` is a
  pointer: a file:line, a commit, a transcript path, the operator's quoted words. A
  superseded decision stays in the table with `superseded by: direction N`; the reader
  treats it as history, not as a constraint.
- **Open questions.** Everything the spike did not settle: open decisions by id, and parked
  questions nobody answered at a boundary.
- **Pointers.** Branch and commits resolve with `git rev-parse`; transcript paths are the
  raw session traces (`~/.claude/projects/…/<session>.jsonl`), which beat structured notes
  for a successor.
- **Pre-registration.** `question`, `arms`, `runs`, `pass rule`, `cost bound`, and when it
  was registered. It is written before any scored run; a scored track runs it as given.
- **Thrown away.** What is discarded and why, so nobody reopens it by accident.

## How a spec-driven tool reads it

- **Decisions settled by the operator** go into the spec as given, with their evidence
  pointer as provenance. They are not re-asked.
- **Decisions settled by the code** go in as constraints; the pointer is the citation.
- **Open questions** are the interview: a spec-driven intake asks exactly these and nothing
  that is already settled.
- **Pre-registration** is the scored run's contract: the arms, runs and pass rule are fixed
  before the run starts, and the cost bound caps it.
- **Pointers** replace copying: the downstream tool links the branch and commits rather
  than pasting diffs.

A tool that reads only the Decisions table and the Open questions list has what it needs.
