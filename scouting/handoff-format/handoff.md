# Handoff: What must handoff.md contain so a spec-driven tool can read it without knowing the plugin?

<!-- scout-ahead handoff v1; plain markdown, fixed headings; written 2026-10-30 12:20Z -->

## Question

What must handoff.md contain so a spec-driven tool can read it without knowing the plugin?

## Status

closed, commit. 2 direction(s) tried. Box: 0.0/1.0h logged, $0.00/$2.0 spawn-metered, 0.0h on the calendar.
Kill criteria: a downstream reader needs plugin knowledge to use the file.

Learned: one plain markdown file with fixed headings, a version marker and a five-column decisions table is readable by a ledger-style tool with a three-line vocabulary mapping; a second format adds drift, not readability

## Decisions

| id | decision | settled by | evidence | superseded by |
|---|---|---|---|---|
| D1 | handoff.md keeps its own three provenance words (operator, code, open) and states the mapping to ledger vocabularies in the file itself, so no reader needs the plugin | code | intake-toolkit interviewing-baseline SKILL.md 'Provenance closed enum'; scripts/scout.py render_handoff |  |
| D2 | no second machine-readable format in handoff.md; the fixed headings, the version marker and the table are the contract | code | scripts/scout.py render_handoff; docs/handoff-format.md |  |
| D3 | whether a downstream tool should get a converter script (handoff → its ledger) ships with the plugin | open |  |  |

settled by: operator = the operator said it (maps to a ledger's user-answered); code = the code or a measurement forced it (codebase-derived); open = nobody settled it (deferred).

## Open questions

- D3: whether a downstream tool should get a converter script (handoff → its ledger) ships with the plugin

## Pointers

- branch: `scout/handoff-format`
- base: `ab83153135dc9ebd388a0676bd67abaa24c4a4f3`
- head: `ab83153135dc9ebd388a0676bd67abaa24c4a4f3`
- direction 1: fixed markdown headings with a decisions table and pointer bullets (opened 2026-10-30 12:20Z, closed 2026-10-30 12:20Z)
- direction 2: add a machine-readable block (YAML front matter or a JSON fence) beside the markdown (opened 2026-10-30 12:20Z, closed 2026-10-30 12:20Z)
- transcript: /Users/manoldonev/.claude/projects/-Users-manoldonev-work-sales/0e3c3ce1-0054-4278-8f9c-7ca95a26652a.jsonl
- log: scouting/handoff-format/log.md
- decisions: scouting/handoff-format/decisions.md

## Thrown away

the JSON/YAML block; it duplicated the table
