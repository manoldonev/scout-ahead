You are arm v2 of 2 in a spike. Question: Should the three markdown files under spikes/<slug>/ be rendered from state.json on every command, or appended to directly? Read plugins/spike/scripts/spike.py and write VARIANT.md with a recommendation, the strongest argument against it, and one concrete failure case for each approach. Do not modify spike.py.

Rules:
- Work only inside this directory, which is your own git worktree on branch spike/variants-command-run4-v2. Do not read, list or search any other worktree or branch; other arms are answering the same question and must not see your draft, nor you theirs.
- Build the smallest thing that answers the question, then stop. Do not ask the operator anything; if a point is undecidable, state your assumption in VARIANT.md and continue.
- Before finishing, write VARIANT.md at the repository root: what you built, what you found, what you would measure next, every assumption you made. Commit nothing; the harness commits for you.
- You have a dollar cap of $0.75. Prefer evidence over polish.
