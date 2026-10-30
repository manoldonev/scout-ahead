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

- Before parking a question, try to settle it without the operator. If a run on the scout branch could answer it, run it and note the result. If a default is cheap to reverse, take it, keep building, and park the question with the default it proceeds on (`--assuming`). Park a bare question only when the operator alone can settle it.

- Questions you would ask the operator mid-build go to the parking lot, not to the operator:

  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" question "<the question>" [--assuming "<the default the build proceeds on>"]
  ```

  Each gets an id (Q1, Q2, …) that never shifts. They are raised at a boundary: a pivot, a close, or when the operator asks.

- Every fake is recorded when you make it (a mocked call, a fixture, a hard-coded value), and unstubbed with a pointer when the real thing replaces it:

  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" stub "<what is faked, in one sentence>"
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" unstub S1 "<file:line or commit of the real thing>"
  ```

  Never stub the part the question is about; blocked on access means `question`, not a mock.

## Recording a decision

Only when the operator says "record this" (or an unmistakable equivalent):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" decide "<the decision, in one line>" --by operator --evidence - <<'EOF'
<their words, exactly as they typed them>
EOF
```

`--evidence` for an operator decision is their words or a transcript path. The script checks the words verbatim against the operator's recorded turns: one contiguous span, at least 10 characters, nothing paraphrased; a compaction summary does not count, and neither does a bare "yes". `--by code --proof proved|inferred` is for decisions the code settled: `proved` only when this scout saw the check fail with the mechanism reverted or stubbed, with the evidence naming that run and the seat (process, layer and mode) it was observed from; otherwise `inferred`. `--by open --ask "<question>"` is for something that must be decided later, with the question to put to the operator. A decision that replaces an earlier one takes `--supersedes D1`; the old one stays as history. Never record a decision because you think one was made; the operator says so, or it is recovered at the close.

## When the direction is spent

Say so in one line and offer `/scout:pivot <new direction>` or `/scout:close`. Do not keep going past the box: a line starting `BOX:` in any output (a command's, `status`, the top of the session-start context) is the ring, and the next message is a pivot or a close. It says which clock rang: dollars metered from spawns, hours logged, or hours on the calendar.

Three shapes of "spent" are easy to miss. Blocked on access, not knowledge (credentials, a license, a decision only the operator can make): park it with `question` and stop that thread; never mock the part the question is about, because a mock of the unknown part proves nothing about it. Answered early, including a first build that disproves the idea: say so and offer `/scout:close` now; do not keep building to justify the box. Growing with no verdict in sight once more than half the box is gone: the question is unfalsifiable or several at once; offer a `/scout:pivot` whose direction names the one falsifiable part.

## Never

- Put the operator's words inside double quotes; they go through the quoted heredoc, where `$`, backticks and quotes arrive as typed.
- Ask the operator a question mid-build that could be parked.
- Pull anything into context by similarity search; read the log and the files the operator and the code point to.
- Write a customer, client or employer name into any scout artifact. Copy what the operator wrote; everything from outside gets a pointer, not a copy.
