---
name: pivot
description: Use when the current direction of a scout is spent or wrong and the operator names the next one; the common path, cheap by design.
argument-hint: <new direction>
disable-model-invocation: true
---

# /scout:pivot

Close the current direction with what it taught, mark the decisions it reversed, open the next direction in the same scout.

1. Write the learned line yourself, one or two sentences, from what actually happened (the log, the diff, the failed run), and name the observation that ended the direction as a pointer (the command and its output, file:line, commit) for `--evidence`; a successor sees both after a compaction and does not reopen the direction without new evidence. Re-read the kill and keep criteria before writing it, not after: they were written by someone who had not seen these results. Name the decision ids the new direction reverses, if any (`decisions.md`); a direction-level supersession marks them `superseded by: direction N`, and a replacement decision recorded later with `decide --supersedes D1` marks them by id.
2. Run:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" pivot "<new direction>" --learned "<what direction N taught>" --evidence "<the observation that ended it>" [--supersedes D1,D3]
   ```

3. This is a boundary. The command prints the parked questions (`Q<n>: …`, with what the build proceeded on) and the open decisions: raise them with the operator now, in prose, all at once. Ask each one openly, with its id and the pointer it concerns. Show an assumption as what was built, never as the likely answer, and accept "I don't know": the question then stays open. Record the answers (`answer Q<n> -` with their words on stdin through a quoted heredoc, or `decide` when the operator settles one); when an answer differs from the assumption, `answer` says so, and the work built on it since is re-checked. Then continue in conversation mode.

Commit the scout branch at the pivot if there is uncommitted work worth keeping as a pointer; a plain message naming the direction is enough.
