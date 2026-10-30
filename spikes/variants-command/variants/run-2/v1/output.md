I wrote `VARIANT.md` at the repository root. My recommendation is to **keep rendering the three files from `state.json` on every command**, as the code already does in `save()` (`spike.py:73-81`). I built nothing and ran nothing: the answer comes from reading the code. The one detail I double-checked is that `short()` rounds timestamps to the minute. I left `spike.py` unchanged and committed nothing.

**Why rendering:** a lot of what's in these files changes in place, not just at the end:
- The "Spent" and "Status" lines at the top of `log.md` change on every command.
- `pivot --supersedes` marks old decisions as replaced, after they've already been written (`spike.py:459`).
- Answering a parked question flips its checkbox from `[ ]` to `[x]`.
- New log entries go above the Variants and Sessions sections, not at the end of the file.
- `handoff.md` is a full snapshot with fixed headings.

An append-only writer would need its own edit logic for each of these, which could drift from the state file. Rendering every time avoids that.

**Strongest argument against it:** the files look editable but aren't. `save()` overwrites them without checking whether anyone changed them, so a hand edit disappears silently on the next command.

**Failure cases:**
- **Rendering:** an agent adds a note directly to `log.md`, and the next `spike note` wipes it. A second, smaller problem: once a handoff exists, every command rewrites it. Its first line has a "written at" time to the minute, so almost every commit carries a meaningless change to `handoff.md`.
- **Appending:** after `pivot --supersedes D2`, the earlier D2 entry in `decisions.md` is never marked as replaced. Readers then see a dropped decision as still open, which is exactly the mistake a handoff is meant to prevent.

**What I'd measure next:**
- How often people actually hand-edit these files in real spikes.
- A cheap guard: store a hash of each rendered file and refuse to overwrite one that changed since. This keeps rendering and fixes its main weakness.

My main assumption is that these files are meant to be read, not edited. If operators are expected to edit them, the case for appending gets much stronger and the guard becomes required.
