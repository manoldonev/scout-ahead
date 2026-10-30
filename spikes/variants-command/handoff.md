# Handoff: Do two arms in sibling worktrees with per-arm dollar caps give comparable evidence headless?

<!-- spike handoff v1; plain markdown, fixed headings; written 2026-10-30 12:29Z; generated from state.json, regenerate with `spike handoff` -->

## Question

Do two arms in sibling worktrees with per-arm dollar caps give comparable evidence headless?

## Status

closed, commit. 1 direction(s) tried. Box: 0.0/1.0h logged, $1.29/$3.0 spawn-metered, 0.1h on the calendar.
Kill criteria: arms cannot run in parallel without seeing each other, or a cap is not enforced.

Learned: two capped Opus arms in sibling worktrees cost about $0.43 each and converge on the same recommendation while finding the same defect by independent experiment; the comparison is evidence, and the divergence (lock vs hash guard) is the measurable question. The command's real bugs were all in how the arm is launched, none in the comparison.

## Decisions

| id | decision | settled by | evidence | superseded by |
|---|---|---|---|---|
| D1 | arm branches are named spike/<slug>-run<id>-v<i>, flat beside the spike branch, never nested under it | code | git refs/heads layout; scripts/spike.py _run_arm |  |
| D2 | arm prompts are passed on stdin; argv carries only flags | code | spikes/variants-command/variants/run-1/v1/stderr.txt; scripts/spike.py _run_arm |  |
| D3 | every arm's stdin is written and closed at launch; collection only waits | code | spikes/variants-command/variants/run-2/v2/stderr.txt; scripts/spike.py _run_arm |  |
| D4 | a variants run id is one above both the recorded runs and any leftover arm branch; the script never deletes a branch | code | scripts/spike.py next_run_id |  |
| D5 | rendered files carry a one-line generated-from-state banner, and handoff.md is rendered only by the handoff command | code | run-4 v1 and v2 VARIANT.md hand-edit experiment; scripts/spike.py GENERATED, cmd_handoff |  |
| D6 | whether to add a lock (v1) or a rendered-content hash guard (v2) against lost writes | open |  |  |

settled by: operator = the operator said it (maps to a ledger's user-answered); code = the code or a measurement forced it (codebase-derived); open = nobody settled it (deferred).

## Open questions

- D6: whether to add a lock (v1) or a rendered-content hash guard (v2) against lost writes

## Pointers

- branch: `spike/variants-command`
- base: `8fdb134d193d05a99d56702393484097c348bfec`
- head: `6099da7e9607d05686d1c07facbf518bc2e5863e`
- direction 1: prove the plumbing with a stub claude, then run two real arms on Opus with a small cap (opened 2026-10-30 12:22Z, closed 2026-10-30 12:29Z)
- variant run 1 arm v1: `spike/variants-command-run1-v1` @ `46b5d0c7e393`, $0.00
- variant run 1 arm v2: `spike/variants-command-run1-v2` @ `dc3682d0f515`, $0.00
- variant run 2 arm v1: `spike/variants-command-run2-v1` @ `c0c8ae7385ad`, $0.43
- variant run 2 arm v2: `spike/variants-command-run2-v2` @ `?`, $0.00
- variant run 4 arm v1: `spike/variants-command-run4-v1` @ `3ad680106a2e`, $0.43
- variant run 4 arm v2: `spike/variants-command-run4-v2` @ `1cade61eb5c2`, $0.44
- transcript: /Users/manoldonev/.claude/projects/-Users-manoldonev-work-sales/0e3c3ce1-0054-4278-8f9c-7ca95a26652a.jsonl
- log: spikes/variants-command/log.md
- decisions: spikes/variants-command/decisions.md

## Pre-registration

- question: do concurrent spike commands lose writes, and does a file lock around load-save stop it?
- arms: current script; script with an exclusive lock around load-modify-save
- runs: 5 runs of 10 parallel 'spike note' per arm
- pass rule: the locked arm keeps 10 of 10 notes in state.json and log.md in all 5 runs; the current arm is the baseline
- cost bound: $0.0
- registered: 2026-10-30 12:29Z (before any scored run)

## Thrown away

nested arm branch names; prompt as a positional argument; arms launched without their prompt
