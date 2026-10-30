# Design, on one page

## The loop

```
start ──► explore code ──► build/think (conversation) ──► pivot ──┐
  ▲                                                               │
  └───────────────────────────────────────────────────────────────┘
                                   │
                                   ▼ close (kill | commit) ──► handoff
```

A spike is one question, one box (hours + dollars), kill criteria, and an ordered
list of directions. A direction is closed by a pivot or by the close. Decisions
are written when a direction ends, never when it starts. The plugin's scripts own
the structure; the model owns the prose and the judgment.

## Artifacts — `spikes/<slug>/`

| file | written by | content |
|---|---|---|
| `state.json` | scripts only | the machine view: question, box, kill criteria, directions[], decisions[], sessions[], status |
| `log.md` | scripts append; `/spike:note` appends prose | question, box, kill criteria, directions in order with what each taught, notes, status |
| `decisions.md` | scripts append on `decide` / `pivot` / `close` | one entry per decision: who settled it (operator / code / open), evidence pointer, superseded-by |
| `handoff.md` | `/spike:handoff` | the downstream artifact; fixed headings, plain markdown |
| `variants/v<n>/` | `/spike:variants` | per-arm result.json (cost, turns, session) and output.md |

`spikes/.current` names the open spike. `spikes/.session.json` (gitignored) is
the latest session's id and transcript path, written by the hook so `start` can
record it. Pointers only: branch, base commit, HEAD, file:line, transcript path.

## Commands (`skills/<name>/SKILL.md`, invoked as `/spike:<name>`)

| skill | script call | what the model does after |
|---|---|---|
| `start <q>` | `spike.py start` → folder, branch `spike/<slug>`, box, kill criteria | explores the code first, appends a "what the code says" note |
| `spike` | none | conversation: prose, evidence, rough notes; `decide` only on "record this" |
| `note <text>` | `spike.py note` | nothing |
| `variants <n> <q>` | `spike.py variants` → n worktrees, n capped `claude -p --model opus` runs | compares outputs as evidence into the log |
| `pivot <dir>` | `spike.py pivot` → closes direction with what it taught, marks superseded decisions, opens next | writes the learned line and names the superseded ids |
| `close` | `spike.py recover` (log + diff + commits + operator utterances from transcripts) then `spike.py close` | tags each recovered decision operator / code / open; writes tried / learned / thrown away |
| `handoff` | `spike.py handoff` → skeleton from state | fills prose; adds pre-registration only if a question became measurable |
| `status` | `spike.py status` | nothing |

## Hook

`SessionStart` with matcher `startup|resume|compact`. Reads stdin JSON, records
`session_id` + `transcript_path` into `.session.json` and the open spike's
`sessions[]`, and emits `additionalContext`: the open spike's question, current
direction, box spent, open decisions and the questions parked for the next
boundary. Nothing when no spike is open. Verified live under `claude -p`.

## Handoff format

Fixed headings so a downstream tool can parse it without knowing the plugin:
`Question`, `Status`, `Decisions` (table: id, decision, settled by, evidence,
superseded by), `Open questions`, `Pointers` (branch, base, head, commits,
transcripts), `Pre-registration` (arms, runs, pass rule, cost bound; present only
when measurable), `Thrown away`.

## Defaults I could not ground in the brief

| decision | default | why |
|---|---|---|
| plugin / command name | `spike`, skills invoked as `/spike:start` etc. | plugin skills are namespaced by the CLI; `/spike start` as one skill with sub-parsing would be `/spike:spike start` |
| branch vs worktree on start | branch in place; `--worktree` opt-in | the operator's shell stays put; variants are where isolation pays |
| spend metering | spawn costs summed from `total_cost_usd`; the interactive session's own cost is not metered | the plugin cannot read the live session's bill; elapsed hours are metered |
| variant permissions | `acceptEdits` + Bash allowed, in the arm's own worktree, `--max-budget-usd` per arm | arms that cannot run tests produce weak evidence; overridable with `--tools` |
| forcing compaction in the test | `--autocompact 100000` plus a padding read, falling back to `/compact` if it works headless | no documented deterministic trigger |
| state store | JSON + markdown, Python 3 stdlib, no jq | one interpreter present everywhere |
