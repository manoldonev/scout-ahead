---
name: variants
description: Use when the operator wants two to four independent attempts at the same question compared side by side, each in its own worktree with its own dollar cap.
argument-hint: <n> [question] [--arm "<approach>"]... [--criterion "<check>"]... [--check "<cmd>"]... [--usd cap-per-arm] [--model opus]
disable-model-invocation: true
---

# /scout:variants

Run `n` arms (2 to 4) of one question, each a separate `claude -p` process in its own git worktree and branch, each with `--max-budget-usd`, Opus by default. Arms never see each other's drafts: the prompt forbids leaving the worktree and the worktrees are siblings, not nested.

1. Race only when argument cannot settle it: the arms must differ on one axis the operator cannot decide by reading, and everything else stays the same. Cosmetic variants, or racing to avoid deciding, are not worth n times the cost. Name the axis and write one `--arm "<approach>"` per position on it, one of them the existing pattern in this codebase, the path of least resistance, as the baseline; each arm is told only its own position. Write the comparison criteria before launching, one `--criterion` each, observable from running the arms, not from reading them; the metric chosen afterwards will be the one the favorite happens to win. The script stores them in the run record before any arm spawns and refuses a run without them. Where a criterion can be a command, also pass it as `--check "<cmd>"`: each arm is told it will be judged by it, and the harness runs it in every arm's worktree after the arm finishes. The tree must be clean so every arm starts from the same base. If it is not, commit the scout's work first.
2. Run (from the repository root; `--dry-run` first if the operator wants to see the plan):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" variants <n> "<question>" --arm "<approach 1>" --arm "<approach 2>" --criterion "<observable check>" [--check "<cmd>"] --usd <cap> [--model opus] [--tools "Bash"] [--timeout 1800] [--check-timeout 300]
   ```

   Defaults: `--usd 2` per arm, `--model opus`, `--tools Bash` (each arm may run commands inside its own worktree; pass `--tools ""` to forbid). `--arm` is given exactly `n` times, or not at all, and then the arms differ only by sampling. The command blocks until every arm finishes or times out, then prints the criteria and one table: arm, approach, branch, cost, turns, files changed, status, one `c<k>` column per check (`pass` or `fail`, output in `v<i>/check-<k>.txt`), and the tool calls the arm was denied.

3. Compare the arms as evidence against the criteria you wrote, judging behavior, not code style. VARIANT.md is a claim: a criterion counts only from the check output, and where the two disagree, report both. An arm with denials is not evidence against its approach; name the refused command (`v<i>/denials.txt`) and the `--tools` value that would allow it. Before trusting a measured difference, change the thing under test and see the number move, and name any cache or service one arm could have warmed for another. When the criterion is taste, the note names who judged. Do not cherry-pick a hybrid from several arms: it is something none of them was, and the evidence no longer says which approach held. Report the losers' strengths; "A overall, but B's handling of X is worth stealing" is the usual useful outcome. Read each `scouting/<slug>/variants/run-<id>/v<i>/VARIANT.md` and `output.md`, and `git diff <base>..scout/<slug>-run<id>-v<i>` for the ones that built something. Write the comparison into the log, in sentences, with pointers:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" note "variants run <id>: <what the arms agreed on>; <where they diverged and why>; <which assumption each made>"
   ```

4. If the comparison produced a measurable question (two arms disagree and a run could settle it), pre-register it before any scored run:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" prereg --question "<q>" --arms "<a, b>" --runs <k> --pass-rule "<rule>" --floor "<what an arm that changed nothing scores, and why that fails the rule>" --cost-usd <bound>
   ```

   The pass rule states the runs discarded as warmup and the spread tolerated. A registration is never replaced: a second `prereg` adds P2. When the scored run is done, or abandoned, record it: `prereg-status R<n> passed|failed|dropped --evidence "<run pointer>"`.

Tell the operator the table and the one-paragraph comparison. Decisions, if any, are recorded only on "record this" or at the close.

Worktrees and branches stay in place until the operator has seen the comparison; the script never deletes either. The point of racing is that a human looks at working versions, not at a summary written by the model that picked the winner. The operator removes worktrees with `git worktree remove` when the scout closes.
