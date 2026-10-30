# Handoff: Is a pivot cheap enough to be the common path, and what does superseding a decision mean?

<!-- scout-ahead handoff v1; plain markdown, fixed headings; written 2026-10-30 12:22Z -->

## Question

Is a pivot cheap enough to be the common path, and what does superseding a decision mean?

## Status

closed, commit. 2 direction(s) tried. Box: 0.0/1.0h logged, $0.00/$2.0 spawn-metered, 0.0h on the calendar.
Kill criteria: a pivot needs more than one command or a dialog.

Learned: a pivot is one command and one line of prose; the boundary print, not a dialog, is what keeps parked questions from being lost; supersession is a marker, not a deletion

## Decisions

| id | decision | settled by | evidence | superseded by |
|---|---|---|---|---|
| D1 | a superseded decision is kept, marked with the direction that reversed it, never deleted or rewritten | code | scripts/scout.py cmd_pivot, render_decisions; scouting/handoff-format/handoff.md table |  |
| D2 | --learned stays optional in the script and mandatory in the skill; an empty learned line renders visibly | code | scripts/scout.py cmd_pivot; skills/pivot/SKILL.md |  |
| D3 | whether pivot should auto-commit a dirty tree | open |  |  |

settled by: operator = the operator said it (maps to a ledger's user-answered); code = the code or a measurement forced it (codebase-derived); open = nobody settled it (deferred).

## Open questions

- D3: whether pivot should auto-commit a dirty tree
- should a pivot commit the scout branch automatically when the tree is dirty, so the direction's pointer is never lost?

## Pointers

- branch: `scout/pivot-mechanics`
- base: `4674d60aa210c6d4130fffa40cca07c7ee9ec220`
- head: `e31895d54033144d873f463b5242ce27350a9c37`
- direction 1: pivot as one command: close the direction with a learned line, mark superseded decisions, open the next, print the boundary (opened 2026-10-30 12:21Z, closed 2026-10-30 12:21Z)
- direction 2: should --learned be mandatory at the script level? (opened 2026-10-30 12:21Z, closed 2026-10-30 12:22Z)
- transcript: /Users/manoldonev/.claude/projects/-Users-manoldonev-work-sales/0e3c3ce1-0054-4278-8f9c-7ca95a26652a.jsonl
- log: scouting/pivot-mechanics/log.md
- decisions: scouting/pivot-mechanics/decisions.md

## Thrown away

argparse-level enforcement of --learned
