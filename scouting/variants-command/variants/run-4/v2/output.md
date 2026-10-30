I recommend keeping the current design, where the three markdown files are rendered from `state.json` on every save, with one added guard. `VARIANT.md` at the repo root has the full write-up; `scout.py` is untouched and nothing is committed.

**Why rendering wins:** the markdown is a view of state that changes, not a log of events. Several commands rewrite earlier content:
- `pivot --supersedes` adds a "superseded by" line inside an old decision. I confirmed this with a diff in a throwaway repo.
- `pivot` and `close` fill in the previous direction's closing details, and `answer` ticks off a parked question that was written earlier.
- `handoff.md` is a fixed-heading snapshot, so it can't be appended to at all.

**Strongest argument against it:** anything a person or agent writes into these files by hand is erased by the next command, with no warning. I reproduced this: after a hand-written line was added to `log.md`, one `note` command removed it (`grep -c` returned 0). The proposed guard is to store a hash of what was last rendered and warn if the file changed in between.

**Failure case for each approach:**
- **Rendering:** a note an agent typed directly into `log.md` disappears on the next `scout.py note`.
- **Appending:** after `pivot --supersedes D1`, decision D1 still reads as live in `decisions.md` and in the handoff, so the next session acts on a decision the scout already overturned.

**Related problem neither approach fixes:** `cmd_variants` loads state, runs the arms for minutes, then saves (`scout.py:796` to `818`). Any `note` or `decide` the operator runs during that window is lost from `state.json`. I found this by reading the code and did not reproduce it; the fix would be to reload and merge before saving, or to use a lock.

The write-up also lists what to measure next and every assumption I made.
