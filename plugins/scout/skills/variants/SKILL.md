---
name: variants
description: Use when the operator wants two to four independent attempts at the same question compared side by side, each in its own worktree with its own dollar cap.
argument-hint: <n> [question] [--usd cap-per-arm] [--model opus]
disable-model-invocation: true
---

# /scout:variants

Run `n` arms (2 to 4) of one question, each a separate `claude -p` process in its own git worktree and branch, each with `--max-budget-usd`, Opus by default. Arms never see each other's drafts: the prompt forbids leaving the worktree and the worktrees are siblings, not nested.

1. Race only when argument cannot settle it: the arms must differ on one axis the operator cannot decide by reading, and everything else stays the same. Cosmetic variants, or racing to avoid deciding, are not worth n times the cost. Write the comparison criteria before launching, observable from running the arms, not from reading them; the metric chosen afterwards will be the one the favorite happens to win. The tree must be clean so every arm starts from the same base. If it is not, commit the scout's work first.
2. Run (from the repository root; `--dry-run` first if the operator wants to see the plan):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" variants <n> "<question>" --usd <cap> [--model opus] [--tools "Bash"] [--timeout 1800]
   ```

   Defaults: `--usd 2` per arm, `--model opus`, `--tools Bash` (each arm may run commands inside its own worktree; pass `--tools ""` to forbid). The command blocks until every arm finishes or times out, then prints one table: arm, branch, cost, turns, files changed, status.

3. Compare the arms as evidence against the criteria you wrote, judging behavior, not code style. Do not cherry-pick a hybrid from several arms: it is something none of them was, and the evidence no longer says which approach held. Report the losers' strengths; "A overall, but B's handling of X is worth stealing" is the usual useful outcome. Read each `scouting/<slug>/variants/run-<id>/v<i>/VARIANT.md` and `output.md`, and `git diff <base>..scout/<slug>-run<id>-v<i>` for the ones that built something. Write the comparison into the log, in sentences, with pointers:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" note "variants run <id>: <what the arms agreed on>; <where they diverged and why>; <which assumption each made>"
   ```

4. If the comparison produced a measurable question (two arms disagree and a run could settle it), pre-register it before any scored run:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" prereg --question "<q>" --arms "<a, b>" --runs <k> --pass-rule "<rule>" --cost-usd <bound>
   ```

Tell the operator the table and the one-paragraph comparison. Decisions, if any, are recorded only on "record this" or at the close.

Worktrees and branches stay in place until the operator has seen the comparison; the script never deletes either. The point of racing is that a human looks at working versions, not at a summary written by the model that picked the winner. The operator removes worktrees with `git worktree remove` when the scout closes.
