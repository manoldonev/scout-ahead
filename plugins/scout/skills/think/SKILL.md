---
name: think
description: Use when the operator is thinking out loud inside an open scout — probing a question from several angles, asking for evidence, trying things — and no other scout command fits.
argument-hint: [what the operator is thinking about]
---

# /scout:think — conversation mode

The operator thinks out loud. You answer in prose, bring evidence when it helps, and keep rough notes of the threads. No option dialogs, no receipts, no stage names, no "Decision Ledger".

Read `scouting/<slug>/log.md` first if it is not already in context (the open scout's slug is in `scouting/.current`).

## How to answer

- Prose, at the depth of a senior colleague. One claim, one piece of evidence: a file:line, a command's output, a commit, a measurement. When you do not have evidence, say "I have not checked" rather than hedging.
- Build when building is faster than arguing. A ten-minute prototype on the scout branch is a valid answer.
- When the operator probes from a new angle, note the thread so it is not lost:

  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" note "<thread, in one sentence>"
  ```

- Questions you would ask the operator mid-build go to the parking lot, not to the operator:

  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" question "<the question>"
  ```

  They are raised at a boundary: a pivot, a close, or when the operator asks.

## Recording a decision

Only when the operator says "record this" (or an unmistakable equivalent):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" decide "<the decision in the operator's words>" --by operator --evidence "<pointer>"
```

`--by code` is for decisions the code settled (a constraint you found, with the file:line). `--by open` is for something that must be decided later. Never record a decision because you think one was made; the operator says so, or it is recovered at the close.

## When the direction is spent

Say so in one line and offer `/scout:pivot <new direction>` or `/scout:close`. Do not keep going past the box: when the box line in the log says the hours or dollars are spent, the next message is a pivot or a close.

## Never

- Ask the operator a question mid-build that could be parked.
- Pull anything into context by similarity search; read the log and the files the operator and the code point to.
- Write a customer, client or employer name into any scout artifact. Copy what the operator wrote; everything from outside gets a pointer, not a copy.
