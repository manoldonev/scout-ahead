---
name: close
description: Use when the operator ends a scout — kill or commit — and wants what was tried, learned, settled and thrown away written down, with decisions recovered from the diff and the transcript.
argument-hint: kill|commit
disable-model-invocation: true
---

# /scout:close

Decisions are recovered after the fact, from the code and from what the operator said, and each is tagged with who settled it.

1. Gather the material:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" recover
   ```

   It prints the log, the commits and diff stat since the base, the uncommitted changes, and the operator's own utterances from every recorded transcript (lines that sound like a decision are marked `**`).

2. Recover the decisions. Walk the diff and the utterances and record each one you find that is not already in `decisions.md`:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" decide "<decision>" --by operator --evidence "<the quoted words, or the transcript path>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" decide "<decision>" --by code --proof proved|inferred --evidence "<file:line, commit, or the command and its output>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" decide "<decision>" --by open --ask "<the question to put to the operator>"
   ```

   `operator`: the operator said it, in their words; the script refuses it without the quote. `code`: the code or a measurement forced it, `proved` when this scout observed it and `inferred` when reasoned from elsewhere. `open`: it came up and nobody settled it; say what to ask. When unsure between operator and code, it is `open`.

   Then re-run the inferred ones. By the close the setup exists, and the experiment that looked expensive mid-run usually costs minutes; an inference is where a scout is most confidently wrong, because nothing pushed back. Re-record what you can prove with `--supersedes` on the inferred id; leave the rest labelled.

3. Raise the parked questions with the operator, all at once, in prose; record the answers with `answer`. This is the last boundary.

4. Close. Re-read the kill and keep criteria before choosing, not after:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" close --outcome kill|commit --verdict proven|disproven|conditional|unanswered [--verdict-note "<…>"] --tried "<directions, one clause each>" --learned "<the two or three sentences a successor needs>" --thrown-away "<what is discarded and why>" --unknown "<what this scout did not settle>"...
   ```

   `--outcome` is what happens to the work: `kill` throws it away, `commit` carries the branch forward. `--verdict` is what happened to the question: `proven` holds within current constraints, with evidence; `disproven` names the wall and why it is structural, not "this was harder than expected" (that is a cost estimate); `conditional` holds only if a named constraint changes, and the note names it, because most honest disproofs are conditional; `unanswered` when the box ran out. `--unknown`, repeatable: the conditions never exercised, the parts stubbed, the scale untested, the question raised and not answered. A scout that names what it did not settle bounds its own authority; one that does not gets read as general.

5. Commit the scout folder on the scout branch with a plain message. Then run `/scout:handoff`.
