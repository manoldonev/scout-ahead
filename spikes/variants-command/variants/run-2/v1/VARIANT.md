# Arm v1: render the markdown, or append to it?

## What I built

Nothing runnable. I read `plugins/spike/scripts/spike.py` (913 lines) closely enough to answer the question from the code. I did not modify it. All line numbers below refer to that file at commit 5af6bf4.

## What the code does today

Every mutating command ends in `save()` (L73–81). `save()` writes `state.json`, then fully re-renders `log.md` and `decisions.md`, and re-renders `handoff.md` once one exists. There are about 11 call sites (L367, 381, 390, 403, 421, 432, 463, 490, 503, 513, 604, 799). The docstring (L4–5) states the contract: state.json is the source of truth.

## Recommendation: keep rendering from state.json on every command

The deciding evidence is that much of the rendered content changes **in place** rather than only at the end of the file:

1. **Header lines that change on every command.** `render_log` L174 writes `Spent: {box_line(st)}` and L179 writes `Status: ...` near the top of log.md. Both change after the file is first written.
2. **Retroactive edits to old records.** `cmd_pivot` L455–459 sets `superseded_by` on decisions recorded earlier. That changes an existing `## Dxx` section in decisions.md (L243–244), a row of the handoff table (L273) and the open-decisions list (L125).
3. **Toggled checkboxes.** Answering a parked question flips `- [ ]` to `- [x] … → answer` (L209).
4. **Sections that move.** Variants, Questions, Closed and Sessions are emitted *after* all directions (L191–226). Adding a direction-log entry after a variant run has to go above the Variants section, not at the end of the file.
5. **handoff.md is a snapshot by design.** It is a fixed-heading document versioned by `HANDOFF_VERSION` (L251), so it cannot be append-only.

An append-only writer would need its own find-and-replace code for each of those five cases. That is a second, hand-written projection of the state that can drift from the first. Rendering keeps one projection, and every save fixes any drift.

## Strongest argument against rendering

**The markdown files look editable but are not.** They are committed, human-readable files under `spikes/<slug>/`, and an operator or agent will naturally open log.md and add a line. `save()` overwrites all three files with `write_text` and never checks whether they changed since the last render. The edit disappears silently on the next `spike note`, and the only trace is in git history, if the edit was committed at all. Appending would keep such edits. A smaller cost: each command rewrites whole files, so a one-line note shows up in diffs as a full-file write. Git's line diff hides this, but tools that watch mtimes do not.

## Concrete failure cases

### Rendering (current approach)

- **Hand edit lost.** An agent follows the build prompt ("Read spikes/<slug>/log.md before continuing", L560) and adds a clarification under `## Direction 2` directly in log.md. The next `spike note "..."` runs `save()` → `render_log(st)` (L78), and the clarification is gone with no warning.
- **Handoff churn (secondary).** Once `handoff_written` is set (L510), every later command re-renders handoff.md (L80–81). Its first line includes `written {short(now())}` (L251), so every `spike note` changes handoff.md. Each commit then carries a handoff diff with no real change in it. I confirmed `short()` (L32–33) cuts timestamps to the minute (`ts[:16]`), so any command run in a different minute changes the file.

### Appending

- **Superseded decision shown as live.** Under direction 1 the operator records `D2: use SQLite` (by `open`). They later run `spike pivot --supersedes D2 "try flat files"`. state.json now has `D2.superseded_by = 2`. An append-only decisions.md either leaves D2's section with no "superseded by" line, or appends a separate "D2 superseded" note far from it. Anyone reading decisions.md or the handoff's Open questions sees D2 as an open, live decision. That is exactly the stale-decision error a handoff exists to prevent.
- **Partial write (secondary).** `save()` writes state.json first (L77). If an append to log.md fails or the process is killed after that, re-rendering repairs it on the next command. An append-only file is missing that line permanently, or gets it twice if the command is retried.

## What I would measure next

1. In a real spike transcript, count how often log.md or decisions.md is hand-edited between commands. Approximation: `git log -p spikes/*/log.md` hunks that are not explained by a `state.json` change in the same commit. If that count is about zero, the case against rendering is theoretical.
2. A cheap guard to test: store a hash of each rendered file in state.json and refuse to overwrite (or move the edit into a note) when the file on disk differs. Measure the false-positive rate. That keeps rendering and fixes its one real failure.
3. Measure how many commits change handoff.md only because of its timestamp line.

## Assumptions

- "The three markdown files" means log.md, decisions.md and handoff.md, the three that `save()` renders. It does not mean prompt.md, output.md or VARIANT.md under `variants/`, which are written once.
- The markdown files are meant to be read, not edited. I inferred this from the docstring and from decisions.md's own line "Never the output of a dialog" (L232). If operators are expected to edit them, the case against rendering gets much stronger and the hash guard becomes required.
- Single writer. No two `spike` processes write the same spike at the same time; both approaches race without a lock, so that does not separate them.
- My evidence is code reading only. I ran none of the failure cases above. The one fact I checked against the code is the minute resolution of `short()`.
