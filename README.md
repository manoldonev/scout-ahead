# spike

Skills for work where the decisions are discovered by building: prototypes and research
that pivot several times a day. A spike has a question, a box (hours and dollars), kill
criteria, and an ordered list of directions. Decisions are written when a direction ends,
recovered from the code and the transcript, and handed over as one plain markdown file
that any spec-driven or scored track can read.

Every workflow framework we found assumes the decisions come first: spec, interview,
record, then build. That is right for a ticket an unattended agent builds and wrong for
exploratory work. This plugin fills the gap and hands over cleanly.

## Install

One command, from any repository, empty or not:

```
claude plugin install spike --marketplace /path/to/this/checkout
```

or from a git URL once it has one:

```
claude plugin install spike --marketplace https://example.invalid/owner/spike.git
```

Try it for one session without installing:

```
claude --plugin-dir /path/to/this/checkout/plugins/spike
```

Requires Claude Code 2.1.292 or later (for `--marketplace`), Python 3.8+, git. Nothing
else: no tracker, no pipeline, no project layout.

## Commands

| command | what it does |
|---|---|
| `/spike:start <question> [--hours N] [--usd N] [--kill "…"]` | opens the spike: folder, log, box, kill criteria, branch `spike/<slug>`; then explores the code before anything else |
| `/spike:spike` | conversation mode: think out loud, get prose and evidence back; a decision is recorded only when you say "record this" |
| `/spike:note <text>` | append to the log |
| `/spike:variants <n> [question]` | 2 to 4 arms of one question in separate worktrees, each a capped `claude -p` on Opus, compared as evidence |
| `/spike:pivot <new direction>` | close the current direction with what it taught, mark superseded decisions, open the next; the common path |
| `/spike:close kill\|commit` | recover decisions from the diff and the transcript, tag each operator / code / open, write tried / learned / thrown away |
| `/spike:handoff` | write `handoff.md`: decisions with provenance, open questions, pointers, pre-registration when a question became measurable |
| `/spike:status` | spikes, directions, boxes spent, open decisions |

## Artifacts

`spikes/<slug>/` in your repository:

- `log.md` — question, box, kill criteria, directions in order, what each taught, status
- `decisions.md` — each decision with who settled it, the evidence pointer, and a supersession marker
- `handoff.md` — the downstream artifact (`docs/handoff-format.md`)
- `state.json` — the machine view the three files above are rendered from; edit through the commands, not by hand
- `variants/run-<n>/v<i>/` — each arm's result, output and diff stat

Pointers, not copies: branches, commits, file:line, transcript paths.

## Session boundaries

A spike outlives a session. The plugin's `SessionStart` hook (matcher `startup|resume|compact|clear`)
records the session's transcript path for the successor and re-injects the open spike's question,
current direction, decisions in force and parked questions. Verified live under `claude -p`; see
`docs/measured.md`.

## Selftest

```
./selftest.sh                 # offline tests, then a live claude -p run (costs ~$1 on sonnet)
SPIKE_SKIP_LIVE=1 ./selftest.sh
```

## Worked examples

The first three spikes run through the plugin were spikes about the plugin:
`spikes/handoff-format/`, `spikes/pivot-mechanics/`, `spikes/variants-command/`. Each has its
log, decisions and handoff.

## Docs

- `docs/protocol.md` — the loop and the rules
- `docs/handoff-format.md` — the handoff file and how a spec-driven tool reads it
- `docs/measured.md` — what was measured and what was not
- `DESIGN.md` — the one-page design and the defaults that were not grounded in the brief

MIT.
