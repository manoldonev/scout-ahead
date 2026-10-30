# Scout: Is a pivot cheap enough to be the common path, and what does superseding a decision mean?

Opened 2026-10-30 12:21Z on branch `scout/pivot-mechanics` from `4674d60aa210`.
Box: 1.0 hours, $2.0. Spent: 0.0/1.0h logged, $0.00/$2.0 spawn-metered, 0.0h on the calendar.
Kill when: a pivot needs more than one command or a dialog.
Status: closed (commit).

## Direction 1: pivot as one command: close the direction with a learned line, mark superseded decisions, open the next, print the boundary

Opened 2026-10-30 12:21Z.
- 2026-10-30 12:21Z note: code: cmd_pivot in scripts/scout.py takes the new direction, --learned and --supersedes D1,D2; it closes the direction, stamps superseded_by with the NEW direction's number, opens the next, re-renders all three files and prints the parked questions and open decisions so the boundary is visible.
- 2026-10-30 12:21Z note: measured: in tests/live.sh a sonnet session ran /scout:pivot for $0.16 in 3 turns and wrote its own learned line from the log without being given one; the live run on 2026-10-30 passed all pivot checks.
- 2026-10-30 12:21Z note: code: supersession is by direction number, not by a replacement decision id. The reversed decision stays in decisions.md and in the handoff table with 'superseded by: direction N'; a reader treats it as history. A new decision for the new direction is recorded separately when it is settled.
- 2026-10-30 12:21Z question parked: should a pivot commit the scout branch automatically when the tree is dirty, so the direction's pointer is never lost?
- 2026-10-30 12:21Z decision D1 (code): a superseded decision is kept, marked with the direction that reversed it, never deleted or rewritten
- 2026-10-30 12:21Z closed by pivot. Learned: one command is enough; the boundary print is what makes the pivot safe, not a dialog

## Direction 2: should --learned be mandatory at the script level?

Opened 2026-10-30 12:21Z.
- 2026-10-30 12:21Z note: tried: making --learned required in argparse. It would refuse a pivot when a direction taught nothing, which is itself worth writing down; the skill demands the line and the script renders '(nothing recorded)' when it is absent, so the gap is visible instead of blocking.
- 2026-10-30 12:21Z note: found: in scout handoff-format the handoff's head pointer equals its base because close, handoff and the commit happened in one step. The close skill commits before handoff and the handoff skill commits after, so in the normal flow head is the close commit; recorded here rather than silently fixed.
- 2026-10-30 12:21Z decision D2 (code): --learned stays optional in the script and mandatory in the skill; an empty learned line renders visibly
- 2026-10-30 12:22Z decision D3 (open): whether pivot should auto-commit a dirty tree
- 2026-10-30 12:22Z closed by close. Learned: a pivot is one command and one line of prose; the boundary print, not a dialog, is what keeps parked questions from being lost; supersession is a marker, not a deletion

## Questions parked for the next boundary

- [ ] should a pivot commit the scout branch automatically when the tree is dirty, so the direction's pointer is never lost?

## Closed 2026-10-30 12:22Z: commit

Tried: one-command pivot with a boundary print; then whether the learned line should be enforced by the script

Learned: a pivot is one command and one line of prose; the boundary print, not a dialog, is what keeps parked questions from being lost; supersession is a marker, not a deletion

Thrown away: argparse-level enforcement of --learned

## Sessions

- 0e3c3ce1-0054-4278-8f9c-7ca95a26652a — /Users/manoldonev/.claude/projects/-Users-manoldonev-work-sales/0e3c3ce1-0054-4278-8f9c-7ca95a26652a.jsonl
