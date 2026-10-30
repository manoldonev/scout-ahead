---
name: start
description: Use when the operator opens a scout — a question to answer by building, with a time and dollar box — before any design or code.
argument-hint: <question> [--hours N] [--usd N] [--kill "criterion"]...
disable-model-invocation: true
---

# /scout:start

Open the scout, then explore the code before deciding anything. Agents find most blockers in code, not in specs.

1. Run, from the repository root (the question verbatim; copy only the operator's words into it):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" start "<question>" [--hours N] [--usd N] [--kill "<criterion>"]... [--worktree]
   ```

   `$ARGUMENTS` holds what the operator typed. If no box was given, use `--hours 4 --usd 10` and say so in one line. If no kill criterion was given, derive one from the question ("kill if <the cheapest observation that would prove it cannot work>") and pass it with `--kill`; add a `--keep` criterion when the question has a yes ("keep if <the observation that would settle it>"). Both are fixed now, before anything is built: deciding what counts as failure after seeing results turns a scout into a rationalization. Pick the first `--direction` by risk: the one most likely to kill the idea runs first. The script creates `scouting/<slug>/`, branch `scout/<slug>` in place (`--worktree` for a worktree), and records the box.

2. Explore the code that the question touches. Read the real files; grep callers; run the existing tests if they are cheap. No design yet.

3. Record what the code says, in plain sentences, as one or more notes:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" note "code: <what you found, with file:line pointers>"
   ```

   Anything you would have asked the operator goes to the parking lot instead, to be raised at the next boundary:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" question "<the question>"
   ```

4. Tell the operator in three lines: the slug and branch, the box and kill criteria, and the one thing the code told you that changes the plan. Then continue in conversation mode (`/scout:think`).

Never write a decision at this point. Decisions are written when a direction ends. Reconnaissance may sharpen the question; findings produced by the thing built to test it must never reshape it.
