My recommendation is to keep rendering all three markdown files from `state.json` on every command, not switch to appending. The full write-up is in `VARIANT.md` at the repo root. I didn't change `scout.py` or commit anything; I tested its current behaviour in a scratch git repo.

**Why rendering:** much of what the files show changes after it's first written. Examples:
- the `Status:` line and the spent line at the top of `log.md`;
- a parked question flipping from `[ ]` to `[x] → answer`;
- the "superseded by" marker on an earlier decision;
- the whole of `handoff.md`.

Appending can't update a line that's already in the file. It would leave a second line that contradicts the first.

**Strongest argument against:** rendering makes the files output-only. The next `scout` command wipes anything a person or agent typed into them, even an unrelated one like `scout spent`, with no warning.

**Failure cases:**
- **Rendering (tested):** I added a line by hand to `log.md`, then ran `scout note`. The line was gone. Separately, `handoff.md` contains a "written at" timestamp, so every later command rewrites it and creates a git diff with no real change.
- **Appending (reasoned):** after `scout question` then `scout answer`, the current output is one line, `- [x] which? → this` (tested). An appended log would keep `- [ ] which?` near the top and add the answer further down. Someone reading top-down at a direction change would see a question that was already answered.

**A problem in both approaches (tested):** I ran 10 `scout note` commands at once and only 3 of the 10 notes survived, in both `state.json` and `log.md`. Each command reads `state.json`, changes it and writes it back with no lock, so parallel runs overwrite each other. Appending would have kept all 10 lines in `log.md` while `state.json` kept 3, so the files would quietly disagree. The fix is a lock around the read-and-write, plus writing each file via a temp file and rename.

**Proposed fix for the lost-edits problem (not built):** add a "generated from state.json; edits are overwritten" banner to each file. Or have the script refuse to write when a file differs from what it last rendered, so a lost edit becomes a loud error.

**What I'd measure next:**
- how often agents actually edit these files by hand;
- whether commands ever run at the same time in real use;
- how badly each approach conflicts when two branches add notes to the same scout.

**Assumptions:** `state.json` stays the source of truth either way, and readers want the current view rather than an append-only history (the entries list in `state.json` already serves as that history).
