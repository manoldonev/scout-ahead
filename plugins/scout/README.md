# scout

For work where the decisions are discovered by building: prototypes and research that pivot several times a day. A scout has a question, a box (hours and dollars), kill criteria and an ordered list of directions. Decisions are recovered from the code and the transcript when a direction ends, and handed over as one plain markdown file any spec-driven tool can read.

## Commands

- `/scout:start <question> [--hours N] [--usd N] [--kill "…"]` opens a scout: its folder, log, box, kill criteria and a `scout/<slug>` branch.
- `/scout:think` is conversation mode. A decision is recorded only when you say so.
- `/scout:note <text>` appends to the log.
- `/scout:variants` runs 2 to 4 arms of one question side by side, each in its own git worktree.
- `/scout:pivot <new direction>` closes the current direction with what it taught and opens the next.
- `/scout:close kill|commit` recovers the decisions and gives the question a verdict.
- `/scout:handoff` writes `handoff.md`, then has a fresh agent cold-read it and returns only the questions that are yours to answer.
- `/scout:status` lists scouts, directions, boxes spent and open decisions.

Everything is written under `scouting/<slug>/` in your repository.

## What it runs and sends

- Runs `python3` and `git` on your machine: branches, and worktrees for variants.
- `/scout:variants` and the handoff cold read start `claude -p` processes, each capped with `--max-budget-usd` and run on your subscription (Opus by default for variants).
- Hook: at session start, resume, compaction and clear, it records the session's transcript path for the open scout and re-injects its question, current direction and open decisions. It does nothing when no scout is open.
- Nothing is sent anywhere else.

Requires Python 3.8+ and git. License: MIT.
