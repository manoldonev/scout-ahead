# Scout: What must handoff.md contain so a spec-driven tool can read it without knowing the plugin?

Opened 2026-10-30 12:20Z on branch `scout/handoff-format` from `ab83153135dc`.
Box: 1.0 hours, $2.0. Spent: 0.0/1.0h logged, $0.00/$2.0 spawn-metered, 0.0h on the calendar.
Kill when: a downstream reader needs plugin knowledge to use the file.
Status: closed (commit).

## Direction 1: fixed markdown headings with a decisions table and pointer bullets

Opened 2026-10-30 12:20Z.
- 2026-10-30 12:20Z note: code: the one downstream reader on this machine (an intake tool's Decision Ledger) uses a closed provenance enum of five values: user-answered, user-delegated, codebase-derived, deferred, ticket-sourced; its table is id | decision | resolution | provenance. Our three values map 1:1 onto three of them: operator→user-answered, code→codebase-derived, open→deferred. Pointer: the installed intake-toolkit interviewing-baseline SKILL.md, section 'Provenance closed enum'.
- 2026-10-30 12:20Z note: code: render_handoff in scripts/scout.py already emits a 5-column table (id, decision, settled by, evidence, superseded by) and a version marker in an HTML comment, so a reader can detect the shape without parsing anything else.
- 2026-10-30 12:20Z question parked: should the handoff adopt the downstream vocabulary outright (user-answered etc.) instead of its own three words plus a mapping line?
- 2026-10-30 12:20Z decision D1 (code): handoff.md keeps its own three provenance words (operator, code, open) and states the mapping to ledger vocabularies in the file itself, so no reader needs the plugin
- 2026-10-30 12:20Z closed by pivot. Learned: fixed headings plus a decisions table are enough for a human and for a ledger-style reader; the only thing missing was the vocabulary mapping, which is one line

## Direction 2: add a machine-readable block (YAML front matter or a JSON fence) beside the markdown

Opened 2026-10-30 12:20Z.
- 2026-10-30 12:20Z question answered: should the handoff adopt the downstream vocabulary outright (user-answered etc.) instead of its own three words plus a mapping line? → no: own words plus a mapping line; adopting one tool's enum would make the file depend on that tool
- 2026-10-30 12:20Z note: tried: a JSON fence duplicating the decisions table. It doubles the drift surface (two renderings of one record) and the brief forbids depending on the reader; the HTML-comment version marker plus a fixed table already gives a parser a stable anchor. Not adding it.
- 2026-10-30 12:20Z decision D2 (code): no second machine-readable format in handoff.md; the fixed headings, the version marker and the table are the contract
- 2026-10-30 12:20Z decision D3 (open): whether a downstream tool should get a converter script (handoff → its ledger) ships with the plugin
- 2026-10-30 12:20Z closed by close. Learned: one plain markdown file with fixed headings, a version marker and a five-column decisions table is readable by a ledger-style tool with a three-line vocabulary mapping; a second format adds drift, not readability

## Questions parked for the next boundary

- [x] should the handoff adopt the downstream vocabulary outright (user-answered etc.) instead of its own three words plus a mapping line? → no: own words plus a mapping line; adopting one tool's enum would make the file depend on that tool

## Closed 2026-10-30 12:20Z: commit

Tried: fixed headings with a table; then a parallel machine-readable block

Learned: one plain markdown file with fixed headings, a version marker and a five-column decisions table is readable by a ledger-style tool with a three-line vocabulary mapping; a second format adds drift, not readability

Thrown away: the JSON/YAML block; it duplicated the table

## Sessions

- 0e3c3ce1-0054-4278-8f9c-7ca95a26652a — /Users/manoldonev/.claude/projects/-Users-manoldonev-work-sales/0e3c3ce1-0054-4278-8f9c-7ca95a26652a.jsonl
