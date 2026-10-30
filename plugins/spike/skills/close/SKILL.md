---
name: close
description: Use when the operator ends a spike — kill or commit — and wants what was tried, learned, settled and thrown away written down, with decisions recovered from the diff and the transcript.
argument-hint: kill|commit
disable-model-invocation: true
---

# /spike:close

Decisions are recovered after the fact, from the code and from what the operator said, and each is tagged with who settled it.

1. Gather the material:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" recover
   ```

   It prints the log, the commits and diff stat since the base, the uncommitted changes, and the operator's own utterances from every recorded transcript (lines that sound like a decision are marked `**`).

2. Recover the decisions. Walk the diff and the utterances and record each one you find that is not already in `decisions.md`:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" decide "<decision>" --by operator --evidence "<transcript path or the quoted words>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" decide "<decision>" --by code --evidence "<file:line or commit>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" decide "<decision>" --by open
   ```

   `operator`: the operator said it, in their words. `code`: the code or a measurement forced it, and the pointer shows where. `open`: it came up and nobody settled it. When unsure between operator and code, it is `open`.

3. Raise the parked questions with the operator, all at once, in prose; record the answers with `answer`. This is the last boundary.

4. Close:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" close --outcome kill|commit --tried "<directions, one clause each>" --learned "<the two or three sentences a successor needs>" --thrown-away "<what is discarded and why>"
   ```

   `kill`: the question is answered no, or the box is spent without an answer; say which. `commit`: something built is worth carrying forward; name the branch and commit.

5. Commit the spike folder on the spike branch with a plain message. Then run `/spike:handoff`.
