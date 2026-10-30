# Arm v2: render the markdown from state.json, or append to it?

## Recommendation

**Keep rendering.** On every save, `log.md`, `decisions.md` and `handoff.md` should be rendered in full from `state.json`, as `save()` already does (`plugins/spike/scripts/spike.py:73-81`). Add one guard: before writing, compare each file against what was rendered last time (keep a hash of it in state), and refuse or warn if the file changed in between. That turns a silent overwrite into a visible one.

## What I built

Nothing new, and I did not modify spike.py. I read `save()`, the three `render_*` functions and the commands that mutate state. Then I ran two throwaway experiments in `mktemp -d` git repos against the unmodified script.

1. **Hand edit vs. render.** I ran `start`, appended `HAND EDIT: operator insight` to `spikes/s/log.md`, then ran `note "first note"`. Running `grep -c "HAND EDIT"` on the file afterwards returned `0`. The edit was erased with no warning.
2. **Retroactive change.** I ran `decide "use X" --by code`, then `pivot "dir B" --supersedes D1`. Diffing `decisions.md` before and after showed that line 10 was inserted *inside* the existing D1 block: `- superseded by: direction 2`. A later command changed an earlier record.

## Why rendering wins

The markdown is not a log of events. It is a view of a state that changes, and several commands change *earlier* parts of it:

- `pivot --supersedes` adds `superseded by` to old decisions (experiment 2).
- `pivot` and `close` set `closed_at`/`learned` on the previous direction. In `render_log` these sit under that direction's heading, before any later directions.
- `answer` flips a parked question from `[ ]` to `[x]` and adds `→ answer`.
- The header lines of `log.md` (Box/Spent, Status) are recomputed on every change.
- `handoff.md` is a fixed-heading snapshot with a `written <ts>` stamp and a decisions table, so it cannot be appended to at all.
- The `## Variants` and `## Sessions` sections are grouped by section, not by time.

With append-only writes, each of these needs either an in-place patch (which is just rendering, done badly) or an "erratum" line appended later that readers must reconcile by hand. That would also break the guarantee in the module docstring (`spike.py:4-6`) that nothing in the markdown is ever out of step with what the commands recorded.

## Strongest argument against rendering

**The markdown files look editable, and they are committed and read by humans, but anything a human or agent writes into them is silently destroyed on the next command.** Experiment 1 shows it. The operator, or an agent told to "update the log", has no signal that the files are generated. A spike tool exists to capture what was learned, so losing a hand-written insight is exactly the failure it should never have. Append-only writes would naturally keep that edit.

## Concrete failure case for each approach

**Rendering (current):** An agent mid-spike opens `spikes/s/log.md` and adds a paragraph under `## Direction 1` explaining why an approach failed. A minute later it runs `spike.py note "trying Y"`. `save()` rewrites `log.md` from `state.json`, and the paragraph is gone. It survives only in git, and only if someone committed in between. Reproduced: `grep -c "HAND EDIT"` → `0`.

**Appending:** Direction 1 records `D1 — use X` in `decisions.md`. Direction 2 runs `pivot --supersedes D1`. Under append-only writes, the D1 block keeps saying it is live. The supersession appears, if at all, as a later line far down the file. `handoff.md`, which the next session reads first, would either list D1 as a live decision or have to be fully rewritten anyway. So the next session acts on a decision that the spike already overturned. The same thing happens to parked questions: `answer` cannot tick an `[ ]` that was already appended.

## Related finding (affects both approaches)

`cmd_variants` loads state at the start (`spike.py:796`), runs the arms for minutes, then calls `save()` (`spike.py:818`). Any `note`, `decide` or `spent` the operator runs from another shell during that window is lost from `state.json`, because the last write wins. With rendering, it then disappears from the markdown too, so it is consistent but lost. With appending, it would survive in `log.md` but be missing from `state.json`, so the two diverge. Neither write strategy fixes this. It needs a reload-and-merge just before `save()`, or a lock. I did not reproduce it; I found it by reading the code.

## What I would measure next

- How often operators or agents actually hand-edit the three files in real spike sessions. Grep the committed `spikes/*/log.md` history for diffs that no command produced. If that never happens, the guard is cheap insurance; if it is common, consider adding a `spike note --from-file` path.
- Test the guard: hash the rendered output into state as `rendered_sha`, and on `save()` warn if the on-disk sha differs. Check that this fires in experiment 1 and stays quiet in normal use.
- Reproduce the `variants` lost-update race: start a run with a stub `claude`, run `note` while it is running, and check `state.json` afterwards.

## Assumptions

- The question is about the write strategy for the three files, not whether `state.json` should exist. I assumed `state.json` stays the source of truth either way.
- "Appended to directly" means each command appends text to the relevant `.md` and never rewrites earlier content. A hybrid (append to `log.md`, render the other two) is a weaker form of the same trade-off. It fails the same way for `pivot` and `answer` edits to directions and questions in `log.md`.
- Humans and agents do sometimes edit these files by hand. That is plausible because they are plain committed markdown, but I have not measured it.
- I used `--no-branch` in the experiments to avoid creating branches. I assumed this does not affect `save()`.
