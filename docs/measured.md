# What was measured, and what was not

All runs on Claude Code 2.1.314, macOS, `claude -p` with `--plugin-dir`, 2026-10-30.

## Measured

- **Skills resolve headless.** `claude -p --plugin-dir plugins/scout "/scout:start …"` ran
  the start skill, substituted `${CLAUDE_PLUGIN_ROOT}` in the skill body, created the folder
  and branch, explored the code and parked a question. Pivot, close and handoff ran on the
  same session via `--resume <session-id>`. `tests/live.sh` repeats this.
- **Compaction re-injection.** `claude -p --resume <id> "/compact"` compacts a headless
  session (`compact_boundary`, trigger `manual`). The `SessionStart` hook with matcher
  `compact` fired and injected the scout. The next turn, asked without tools, stated the
  open scout's question and kill criterion from the injected context. `tests/live.sh`
  asserts all four: the boundary, the hook firing, the injected text, the answer.
- **The hook under `-p`.** `SessionStart:startup` and `:resume` fired in every headless run
  and recorded the transcript path into the scout's state.
- **Variant plumbing.** With a stub `claude` on PATH, two arms ran as separate processes in
  separate sibling worktrees, each receiving `--max-budget-usd` and `--model opus`, each
  committed on its own branch, each result and `VARIANT.md` collected (`tests/test_scout.py`).
- **Variants with real arms.** `scouting/variants-command/` run 4: two Opus arms, cap $0.75
  each, on a question about the plugin's own code. Both finished in 8 turns for $0.43 and
  $0.44, both reached the same recommendation, and both reproduced the same defect by their
  own experiment in a throwaway repo without seeing each other. The three failed runs before
  it (1 to 3) were all launch bugs, recorded in that scout's log: arm branches nested under
  the scout branch, the prompt swallowed by `--allowedTools`, stdin written too late. The
  scripted live test also runs two arms through the `/scout:variants` skill.

## Not measured

- **Automatic compaction.** Only manual `/compact` was triggered. Whether
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW` is honored under `-p` is undocumented and untested here;
  the hook matcher is the same for `auto` and `manual`, so the injection path is shared.
- **How much of the side constraint survives without the hook.** The brief's figure
  (about 17 percent) was not re-measured.
- **Four arms vs two.** Only two-arm runs were made.
- **The concurrency race** two arms found (parallel `scout note` calls lose writes) is
  pre-registered in `scouting/variants-command/handoff.md` and not yet run.
- **The interactive session's own cost.** Not visible to the plugin; the box meters spawn
  costs and operator-logged hours only.
- **Successor quality.** Whether a successor session with log + transcript outperforms one
  with the log alone was the brief's claim, not re-tested.

## What to measure next

1. Auto-compaction under `-p` with `CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000` and a padded
   context: does the `compact` matcher fire with trigger `auto`?
2. Two arms vs four on the same question: does the fourth arm add evidence or noise?
3. Decision recovery accuracy: run close on a scout with a known decision set and count
   recovered vs missed vs invented.
