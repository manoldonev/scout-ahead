# Arm v1: render the markdown from state.json, or append to it?

## Recommendation

**Keep rendering all three files from state.json on every save** (what `save()` does now, `plugins/scout/scripts/scout.py:73-81`). Add two small fixes:

1. Write each file to a temp file and `os.replace` it.
2. Take a lock (or compare-and-swap on `updated_at`) around load→save.

Don't switch to appending.

Why: the markdown shows state that changes after it was first written, and appending can't update a line that is already in the file. Examples from scout.py:

- the header lines in `render_log`: `Status:` and the `Spent:` box line
- the question checkbox `[ ]` → `[x] … → answer` (`cmd_answer`)
- `superseded by: direction N` on an earlier decision (`cmd_pivot --supersedes`)
- each direction's `closed by … Learned:` line
- the variants table and the whole of handoff.md

With appending, every one of these becomes either a second, contradicting line or an in-place edit, and an in-place edit is just rendering done badly.

## Strongest argument against the recommendation

Rendering makes the markdown output-only. Anything a person or agent writes into log.md, decisions.md or handoff.md is silently destroyed by the next `scout` command, even an unrelated one like `spent`. The docstring says "nothing in them is ever out of step". That guarantee is bought by making the files read-only, and nothing in the files says so. Agents in particular like to "update the log" by editing it directly.

## Concrete failure case: rendering (observed)

I made a scratch repo, ran `scout start q`, appended `HAND EDIT: operator context` to `scouting/q/log.md`, then ran `scout note "after edit"`. Afterwards `grep -c "HAND EDIT" scouting/q/log.md` returned **0**: the edit was gone, with no warning.

A second, smaller one: handoff.md embeds `written {short(now())}` (line 251). Once a handoff exists, every later `save()` re-renders it, so an unrelated `scout spent --hours 0` a minute later produced a diff in handoff.md (`12:27Z` → `12:28Z`). That's a git-churn commit with no content change.

## Concrete failure case: appending (reasoned, then partly observed)

`scout question "which?"` followed by `scout answer 1 "this"`:

- **Rendered (observed):** the log shows a single line, `- [x] which? → this`.
- **Appended:** the log would keep `- [ ] which?` and add a later line with the answer. The open-question list near the top of the file then says the question is still open. Someone reading top-down at a boundary (the point at which `cmd_pivot` says to "raise the parked questions") sees a question that was already answered.

`pivot --supersedes D1` has the same problem. D1 stays in decisions.md with no `superseded by` marker unless the earlier section is edited.

## Finding that applies to both approaches (observed)

I ran 10 `scout note` commands in parallel. Only **3 of 10** notes survived, in both state.json and log.md. The cause is an unlocked load→modify→save race in every `cmd_*`, so it isn't about rendering versus appending. With appending, log.md would probably have kept all 10 lines while state.json kept 3. That looks like a point for appending, but it means the files disagree silently, and the next render (handoff) would quietly drop the 7. The fix is the lock, not appending.

Rendering is also not atomic: `save()` writes state.json first, then log.md, then decisions.md. If the process dies between those writes, the files drift. Rendering heals that on the next command; appending would not.

## Mitigation for the hand-edit failure (not built)

Either put a `<!-- generated from state.json by scout; edits are overwritten — use scout note -->` banner at the top of each rendered file, or have `save()` refuse to write when a file's current content differs from the last render (store a hash in state.json). The banner costs one line. The hash check turns silent loss into a loud error.

## What I built

Nothing in the repo. scout.py is unchanged. I ran four probes against the real script in a throwaway `mktemp -d` git repo with `start --no-branch`: the hand-edit loss, the 10-way concurrency race, the handoff timestamp churn, and the question checkbox rewrite. The outputs are quoted above.

## What I would measure next

- How often agents in real scout sessions edit `scouting/*/log.md` directly (grep transcripts for Edit/Write calls on those paths). That tells us whether the hand-edit loss happens in practice or only in theory.
- Whether two commands ever overlap in practice, for example the SessionStart hook running while `scout note` runs, or variant arms calling `scout` in parallel. That decides whether the lock is urgent.
- The size of git merge conflicts on log.md when two branches each add notes to the same scout, under each approach. Both approaches touch the tail of the file, so I expect both to conflict, but I haven't measured it.

## Assumptions

- "The three markdown files" means log.md, decisions.md and handoff.md under `scouting/<slug>/`.
- state.json stays the source of truth either way. The question is only how the markdown is produced.
- The readers of these files are people and resuming agents, who read the current view top-down, not as an audit stream. If an append-only audit trail is wanted, the entries list in state.json (or a separate JSONL file) already does that job better than markdown.
- The concurrency probe used 10 local background processes. Real overlap is probably rarer, but the race itself is real.
