# scout-ahead

A Claude Code plugin, command prefix `scout`, for work where the decisions are discovered by building: prototypes and research
that pivot several times a day. A scout has a question, a box (hours and dollars), kill
criteria, and an ordered list of directions. Decisions are written when a direction ends,
recovered from the code and the transcript, and handed over as one plain markdown file
that any spec-driven or scored track can read.

Spec-first frameworks assume the decisions come first: spec, interview, record, then build.
That is right for a ticket an unattended agent builds and wrong for exploratory work. Several
of them ship a spike mode, and a few tools reject the up-front spec outright (see Prior art);
all of them run one question to one verdict and feed a spec. None runs exploration as a boxed,
multi-pivot loop whose decisions are recovered afterwards with provenance and handed, in a
tool-neutral file, to whatever spec-driven or scored track a team already uses. That seam is
what this plugin occupies.

## Install

One command, from any repository, empty or not:

```
claude plugin install scout --marketplace /path/to/this/checkout
```

or from a git URL once it has one:

```
claude plugin install scout --marketplace https://example.invalid/owner/scout.git
```

Try it for one session without installing:

```
claude --plugin-dir /path/to/this/checkout/plugins/scout
```

Requires Claude Code 2.1.292 or later (for `--marketplace`), Python 3.8+, git. Nothing
else: no tracker, no pipeline, no project layout.

## Commands

| command | what it does |
|---|---|
| `/scout:start <question> [--hours N] [--usd N] [--kill "…"]` | opens the scout: folder, log, box, kill criteria, branch `scout/<slug>`; then explores the code before anything else |
| `/scout:think` | conversation mode: think out loud, get prose and evidence back; a decision is recorded only when you say "record this" |
| `/scout:note <text>` | append to the log |
| `/scout:variants <n> [question]` | 2 to 4 arms of one question in separate worktrees, each a capped `claude -p` on Opus, compared as evidence |
| `/scout:pivot <new direction>` | close the current direction with what it taught, mark superseded decisions, open the next; the common path |
| `/scout:close kill\|commit` | recover decisions from the diff and the transcript, tag each operator / code (proved or inferred) / open, give the question a verdict (proven / disproven / conditional / unanswered), write tried / learned / thrown away / still unknown |
| `/scout:handoff` | write `handoff.md`: decisions with provenance, open questions, pointers, pre-registration when a question became measurable |
| `/scout:status` | scouts, directions, boxes spent, open decisions |

## Artifacts

`scouting/<slug>/` in your repository:

- `log.md` — question, box, kill criteria, directions in order, what each taught, status
- `decisions.md` — each decision with who settled it, the evidence pointer, and a supersession marker
- `handoff.md` — the downstream artifact (`docs/handoff-format.md`)
- `state.json` — the machine view `log.md` and `decisions.md` are rendered from on every command, and `handoff.md` on `/scout:handoff`; the rendered files carry a banner saying so, because a hand edit is overwritten by the next command
- `variants/run-<n>/v<i>/` — each arm's result, output and diff stat

Pointers, not copies: branches, commits, file:line, transcript paths.

## Session boundaries

A scout outlives a session. The plugin's `SessionStart` hook (matcher `startup|resume|compact|clear`)
records the session's transcript path for the successor and re-injects the open scout's question,
current direction, decisions in force and parked questions. Verified live under `claude -p`; see
`docs/measured.md`.

## Selftest

```
./selftest.sh                 # offline tests, then a live claude -p run (costs ~$1 on sonnet)
SCOUT_SKIP_LIVE=1 ./selftest.sh
```

## Worked examples

The first three scouts run through the plugin were scouts about the plugin:
`scouting/handoff-format/`, `scouting/pivot-mechanics/`, `scouting/variants-command/`. Each has its
log, decisions and handoff.

## Prior art

Found by a research sweep on 2026-10-30 (`docs/prior-art.md` has the full table, what each covers
and lacks, and what was borrowed). The closest, strongest first:

- [spikekit](https://github.com/gongxh13/spikekit): the same thesis, an explicit rejection of
  design-then-build, parked "not the model's call" items; no box, pivots, provenance or variants.
- [prp-spike](https://github.com/Wirasm/prp/blob/main/.agents/skills/prp-spike/SKILL.md): kill criteria
  frozen before the build, `proved`/`inferred` labels, PROVEN/DISPROVEN/CONDITIONAL verdicts, a
  "still unknown" list; one question, one direction, no pivot or dollar box. The evidence rules here
  are borrowed from it.
- [GSD `/gsd:spike`](https://github.com/open-gsd/gsd-core): risk-ordered experiments with a
  Continue/Pivot/Abandon checkpoint and a wrap-up into planning; asks mid-build, no box or provenance.
- [hordev](https://github.com/heffrey/hordev): `racing-prototypes` (2 to 4 candidates, own worktree
  each, criteria before the race, losers kept until the human has seen them) and an assumption ledger;
  the fair-race rules in `/scout:variants` are borrowed from it.
- [mattpocock/skills](https://github.com/mattpocock/skills) `/prototype` + `/handoff`: throwaway code
  that answers a question, a handoff that references by path and never copies.
- [Continuity](https://github.com/vikcena01/ai-continuity-plugin): decisions with `supersedes` /
  `superseded_by` and the reason, re-injected on the compaction hook.
- [why-log](https://github.com/oh-namgyu/why-log): decisions recovered from history with a provenance
  label (stated, inferred, testimony); the rule that an operator decision needs a verbatim quote is
  borrowed from it.
- [agent-lab-kit](https://github.com/Campanadas/agent-lab-kit): `prereg` before the scored run, and a
  cover check that refuses a handoff that dropped something; both borrowed.

What is specific to scout-ahead: the dollar box metered from capped spawns, parking questions to a
boundary and printing them there, close-time recovery tagged operator / code / open with pointers,
supersession marked at the pivot, and a handoff that states its provenance mapping so a spec tool
does not re-ask settled decisions.

## Docs

- `docs/protocol.md` — the loop and the rules
- `docs/handoff-format.md` — the handoff file and how a spec-driven tool reads it
- `docs/measured.md` — what was measured and what was not
- `docs/prior-art.md` — the prior-art sweep, feature-by-feature bearings, and what was borrowed
- `DESIGN.md` — the one-page design and the defaults that were not grounded in the brief

MIT.
