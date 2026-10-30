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
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" prereg --question "<q>" --arms "<arms>" --runs <k> --pass-rule "<rule>" --cost-usd <bound>
   ```

   Do not invent one. A question is measurable when two arms can be named, a pass rule stated, and a cost bounded.

2. Write it:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" handoff --print
   ```

3. Read it back once as the downstream reader would: every decision has a settled-by and an evidence pointer, every open question is a question, every pointer resolves (`git rev-parse` the commits). If something is missing, fix it with `decide`, `answer`, `question` or `note`, and run `handoff` again; never edit `handoff.md` by hand, it is regenerated.

4. Commit the scout folder. Give the operator the path and the count of settled vs open decisions.

The format is documented in the plugin's `docs/handoff-format.md`.
