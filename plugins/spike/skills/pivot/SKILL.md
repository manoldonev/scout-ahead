---
name: pivot
description: Use when the current direction of a spike is spent or wrong and the operator names the next one; the common path, cheap by design.
argument-hint: <new direction>
disable-model-invocation: true
---

# /spike:pivot

Close the current direction with what it taught, mark the decisions it reversed, open the next direction in the same spike.

1. Write the learned line yourself, one or two sentences, from what actually happened (the log, the diff, the failed run). Name the decision ids the new direction reverses, if any (`decisions.md`).
2. Run:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" pivot "<new direction>" --learned "<what direction N taught>" [--supersedes D1,D3]
   ```

3. This is a boundary. The command prints the parked questions and open decisions: raise them with the operator now, in prose, all at once, and record the answers (`answer <n> "<text>"`, or `decide` when the operator settles one). Then continue in conversation mode.

Commit the spike branch at the pivot if there is uncommitted work worth keeping as a pointer; a plain message naming the direction is enough.
