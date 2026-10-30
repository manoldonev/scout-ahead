# Decisions: What must handoff.md contain so a spec-driven tool can read it without knowing the plugin?

Recovered at the end of a direction or recorded when the operator said so. Never the output of a dialog.

## D1 — handoff.md keeps its own three provenance words (operator, code, open) and states the mapping to ledger vocabularies in the file itself, so no reader needs the plugin

- settled by: code
- evidence: intake-toolkit interviewing-baseline SKILL.md 'Provenance closed enum'; scripts/spike.py render_handoff
- direction: 1, recorded 2026-10-30 12:20Z

## D2 — no second machine-readable format in handoff.md; the fixed headings, the version marker and the table are the contract

- settled by: code
- evidence: scripts/spike.py render_handoff; docs/handoff-format.md
- direction: 2, recorded 2026-10-30 12:20Z

## D3 — whether a downstream tool should get a converter script (handoff → its ledger) ships with the plugin

- settled by: open
- evidence: (none)
- direction: 2, recorded 2026-10-30 12:20Z
