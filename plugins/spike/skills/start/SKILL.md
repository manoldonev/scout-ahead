---
name: start
description: Use when the operator opens a spike — a question to answer by building, with a time and dollar box — before any design or code.
argument-hint: <question> [--hours N] [--usd N] [--kill "criterion"]...
disable-model-invocation: true
---

# /spike:start

Open the spike, then explore the code before deciding anything. Agents find most blockers in code, not in specs.

1. Run, from the repository root (the question verbatim; copy only the operator's words into it):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" start "<question>" [--hours N] [--usd N] [--kill "<criterion>"]... [--worktree]
   ```

   `$ARGUMENTS` holds what the operator typed. If no box was given, use `--hours 4 --usd 10` and say so in one line. If no kill criterion was given, derive one from the question ("kill if <the cheapest thing that would prove it cannot work>") and pass it with `--kill`. The script creates `spikes/<slug>/`, branch `spike/<slug>` in place (`--worktree` for a worktree), and records the box.

2. Explore the code that the question touches. Read the real files; grep callers; run the existing tests if they are cheap. No design yet.

3. Record what the code says, in plain sentences, as one or more notes:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" note "code: <what you found, with file:line pointers>"
   ```

   Anything you would have asked the operator goes to the parking lot instead, to be raised at the next boundary:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spike.py" question "<the question>"
   ```

4. Tell the operator in three lines: the slug and branch, the box and kill criteria, and the one thing the code told you that changes the plan. Then continue in conversation mode (`/spike:spike`).

Never write a decision at this point. Decisions are written when a direction ends.
