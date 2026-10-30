---
name: handoff
description: Use when a closed (or closing) scout must be handed to a spec-driven or scored track — one plain markdown file any downstream tool can read.
argument-hint: [slug]
disable-model-invocation: true
---

# /scout:handoff

Produce `scouting/<slug>/handoff.md`: the decisions with provenance, the open questions, pointers to branches and commits and transcripts, and a pre-registration block when a question became measurable. Nothing in it depends on which tool reads it.

1. If a measurable question emerged and is not yet pre-registered, register it now, before any scored run:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" prereg --question "<q>" --arms "<arms>" --runs <k> --pass-rule "<rule>" --floor "<what an arm that changed nothing scores, and why that fails the rule>" --cost-usd <bound>
   ```

   Do not invent one. A question is measurable when two arms can be named, a pass rule stated, and a cost bounded. The pass rule states the runs discarded as warmup and the spread tolerated. Registrations are append-only; a registration whose scored run was done or abandoned is closed with `prereg-status R<n> passed|failed|dropped --evidence "<run pointer>"`, never rewritten.

2. Write it:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" handoff --print
   ```

   The command refuses to write a handoff that drops a decision id, a direction, a branch or an open question from the record; fix the record, not the file.

3. Have a stranger read it. A fresh agent that cannot talk to you reads only the handoff, read-only and capped, and lists the questions where a wrong guess would change the plan, ranked:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" coldread [--usd 0.5] [--model opus]
   ```

   It writes `scouting/<slug>/coldread.md` and meters its cost into the box. Sort each question into one pile:

   - answered by the record or the code: fix the record with `decide`, `answer` or `note`, and regenerate;
   - minor, a sensible builder could settle it without changing what gets built: settle it and record it as the scout's call: `note "scout's call: <question> → <what was chosen>"`;
   - the operator's: `question`, or `decide --by open --ask "<question>"`.

   One round only; do not re-run the cold read on the regenerated file.

4. Read it back once as the downstream reader would: every decision has a settled-by and an evidence pointer, and every open question is a question. The script marks each branch `(missing)`, `(no commits past base)` or `(not pushed)` and each transcript `(local to this machine)` or `(missing)`, and refuses only when the scout branch itself is missing; push what the downstream reader must be able to follow. The evidence column is free text, so check those pointers by hand; each carries the commit it was cited against (`@ <sha>`, `+dirty` when the tree had uncommitted changes). If something is missing, fix it with `decide`, `answer`, `question` or `note`, and run `handoff` again; never edit `handoff.md` by hand, it is regenerated.

5. Commit the scout folder. Give the operator the path, the count of settled vs open decisions, and the cold read's operator pile, most important first, and propose where the verdict should land (the issue the scout was commissioned from, a new ticket, or nowhere, which is a complete result too); filing it is outward-facing, so propose and stop.

The format is documented in the plugin's `docs/handoff-format.md`.
