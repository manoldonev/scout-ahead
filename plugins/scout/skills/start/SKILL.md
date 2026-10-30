---
name: start
description: Use when the operator opens a scout — a question to answer by building, with a time and dollar box — before any design or code.
argument-hint: <question> [--stakes "…"] [--hours N] [--usd N] [--kill "criterion"]...
disable-model-invocation: true
---

# /scout:start

Open the scout, then explore the code before deciding anything. Agents find most blockers in code, not in specs.

1. Run, from the repository root (the question verbatim; copy only the operator's words into it):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" start "<question>" --stakes "<the decision waiting; what yes changes; what no changes>" [--hours N] [--usd N] [--kill "<criterion>"]... [--worktree]
   ```

   `$ARGUMENTS` holds what the operator typed. If no box was given, use `--hours 4 --usd 10` and say so in one line. If no kill criterion was given, derive one from the question ("kill if <the cheapest observation that would prove it cannot work>") and pass it with `--kill`; add a `--keep` criterion when the question has a yes ("keep if <the observation that would settle it>"). Both are fixed now, before anything is built: deciding what counts as failure after seeing results turns a scout into a rationalization.

   A criterion is an observation: a number, an error, a behavior, never an adjective. "Too slow", "clean", "scalable" stand in for a threshold nobody has decided; decide it now or the build decides it later. At least one kill criterion must be a real possibility: if every one is far-fetched, the question is trivially true and the scout is theater. When the threshold is genuinely unknown, say so and write the criterion as "record <metric> as a baseline finding": the number the scout produces is the finding, not a pass or fail, and pre-registration waits until that number makes the question measurable. The same shape holds for `--keep`.

   Pick the first `--direction` by risk: the one most likely to kill the idea runs first. The script creates `scouting/<slug>/`, branch `scout/<slug>` in place (`--worktree` for a worktree), and records the box.

   Before running the command, write the stakes in one sentence: the decision waiting on the answer, what a yes would change, what a no would change. If yes and no lead to the same next action, the question is not worth a scout: say so to the operator in one line, naming that shared next action, and stop without opening it. The operator re-issues `/scout:start` with a sharper question if they still want one. This check happens before anything is built; it is not a mid-build question.

2. Explore the code that the question touches. Read the real files; grep callers; run the existing tests if they are cheap. No design yet.

   List the gates the question rests on that the platform grants rather than the code provides (credentials, entitlements, quotas, toolchain or runtime versions, a service being reachable), and probe each with one command now. Record each as `note "gate: <x>: <command> -> <result>"`. A missing gate either hits a kill criterion or becomes the first direction; it is never a parked question.

3. Record what the code says, in plain sentences, as one or more notes:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" note "code: <what you found, with file:line pointers>"
   ```

   Anything you would have asked the operator goes to the parking lot instead, to be raised at the next boundary. Settle first what a run can settle, take a cheap-to-reverse default with `--assuming`, and park bare only what the operator alone can settle:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scout.py" question "<the question>" [--assuming "<the default the build proceeds on>"]
   ```

4. Tell the operator in three lines: the slug and branch, the box and kill criteria, and the one thing the code told you that changes the plan. Then continue in conversation mode (`/scout:think`).

Never write a decision at this point. Decisions are written when a direction ends. Reconnaissance may sharpen the question; findings produced by the thing built to test it must never reshape it.
