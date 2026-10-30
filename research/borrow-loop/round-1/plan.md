# Borrow loop, round 1: implementation plan

Input: `shortlist.json` (54 candidates C1–C54 in file order, 13 accepted judgments J1–J13). Every
"today" claim below was re-checked against `plugins/scout/scripts/scout.py`, the eight skills,
`docs/` and `tests/` on 2026-10-30, not taken from the candidate. Fourteen items survive; the
rest are merged into them or dropped (list at the end).

One premise was probed instead of assumed: C45 needs the operator's current turn to be in the
transcript jsonl before a tool call runs. In this session's own transcript the user record
(16:00:12.552Z) precedes the first assistant record (16:00:18.357Z), so interactively it is.
Headless `-p` is unverified; item 1's live check covers it.

Shared conventions for every item: new state keys are read with `.get(...)` so the committed
`scouting/*/state.json` files keep loading. Where an item changes a state shape (items 5, 10), a
normalization in `load()` upgrades the old shape. `HANDOFF_VERSION` stays 1 because every handoff
change is additive. Each borrow is appended to "What was borrowed" in `docs/prior-art.md`.

---

## Ranked list

### 1. Operator provenance is checked against what the operator actually typed

- **Mechanic.** The script, not the model, checks that an `operator` quote occurs verbatim in a
  human turn. Compaction summaries never count as human turns, slash-command arguments do, the
  quote travels without shell mangling, and the model cannot supersede an operator decision with
  its own.
- **Sources.** C43 (passbaton `human-turn.ts`), C45 (why-log `validate.py`), C9 (Pocock
  handoff: verbatim text goes as a file or stdin), C30 (Continuity frozen guard).
- **Change.** In `scripts/scout.py`:
  - `operator_utterances()`: skip records that carry `isCompactSummary` or
    `isVisibleInTranscriptOnly`, and skip text that starts with `This session is being continued`.
    When a text block starts with `<command-message>` or `<command-name>`, yield the stripped
    `<command-args>` content (skip it when empty) instead of dropping the block.
  - New helper `_text(v)`: returns `sys.stdin.read().rstrip("\n")` when `v == "-"`. Apply it to the
    positional text of `note`, `question` and `decide`, and to `--evidence`, `--learned` and
    `--verdict-note`. At most one argument per call may be `-`; die otherwise.
  - `cmd_decide`, for `--by operator`:
    - Evidence that names an existing file is a transcript pointer and is accepted.
    - Any other evidence is whitespace-normalized and must be at least 10 characters.
    - It must also be a substring of one `operator_utterances()` entry, searched across every
      `st["sessions"]` transcript plus the `.session.json` transcript.
    - On a miss, die: `quote not found verbatim in any recorded operator turn; quote one
      contiguous span exactly, pass the transcript path, or record it --by open --ask`. When no
      transcript is readable, die with that reason instead.
  - `cmd_decide`, for `--supersedes Dk` where Dk is `by: operator`: refuse unless the new decision
    is also `--by operator`. The die message says to record `--by open --ask "Dk said …; the code
    shows … — keep Dk?"` instead.
  - `cmd_pivot --supersedes`: list every operator decision it marks in the boundary printout.
  - Skills: `think` ("Recording a decision") and `close` step 2 pass operator words through a
    quoted heredoc: `decide "<text>" --by operator --evidence - <<'EOF'`. One line in `think`
    "Never": operator words never go inside double quotes.
- **Tests.**
  - `tests/test_scout.py::test_operator_quote_verified`. Uses a fixture transcript with:
    - one real turn;
    - one `isCompactSummary` record whose text contains "go with X";
    - one `<command-message>scout:think</command-message><command-args>record this: use the bypass</command-args>`
      line.
    It asserts all of the following:
    - A quote from the real turn passes.
    - The compaction-summary text dies.
    - The command-args text passes.
    - `yes` dies on length.
    - A quote containing `$HOME` and a backtick, fed through `--evidence -`, is stored byte-for-byte.
    - `--by code --supersedes D1` against an operator D1 dies.
  - Update `test_full_loop`: it currently uses `--evidence transcript`. Point it at a fixture
    transcript.
  - Extend `test_recover_reads_transcript` with the compaction-summary and command-args lines.
  - `tests/live.sh`: a new step, `/scout:think record this: coerce with float()`, followed by a
    check that `state.json` has a decision with `"by": "operator"`. This proves the headless
    flush, the envelope fix and the verification end to end.
- **Why.** This is a measured defect, not a nicety. 32 of 36 compaction summaries pass today's
  filter, so `recover` can hand the close a model paraphrase as "operator" evidence. Meanwhile
  every `/scout:think record this …` line is dropped. The strongest provenance tag is currently
  the least checked one.

### 2. A verdict is refused without the evidence its kind requires, and the close records which criteria fired

- **Mechanic.** The four verdicts carry different evidence:
  - `proven` needs an observed decision.
  - `disproven` needs its wall and a command that reproduces it.
  - `conditional` needs the constraint and its blast radius.
  The close also states which pre-committed kill/keep criteria fired. A criterion that named the
  wrong observation point is honoured as written.
- **Sources.** C21 (GSD spike depth), J3/C2, J10, J2/C3 (prp-spike `spike-report.md`,
  `evidence.md`, `framing.md`).
- **Change.**
  - `scripts/scout.py`:
    - New helper `criteria_lines(st)` numbers the criteria K1.. (kill) and P1.. (keep). Use it in
      `render_log`, `render_handoff` Status and `context_text`; this replaces three copies of the
      `"; ".join` code.
    - `close` parser: add `--repro` ("command, run from the scout branch, and what to look at"),
      `--blast-radius`, and a repeatable `--fired K1|P2`.
    - `cmd_close` checks, all before any mutation:
      - `proven` with no live `code, proved` decision → die "a proven verdict needs at least one
        observed decision; record it, or use conditional/unanswered".
      - `disproven` without `--verdict-note` or without `--repro` → die.
      - `conditional` without `--verdict-note` or without `--blast-radius` → die.
      - `--blast-radius` with any other verdict → die.
      - an unknown `--fired` id → die.
    - Store `repro`, `blast_radius` and `fired` in `st["close"]`.
    - `render_handoff`:
      - Status gets one line per criterion, `K1 <text>: fired | did not fire`, or `Criteria: none
        fired.`
      - Status gets `Blast radius: …` when conditional.
      - A `## Reproducing` section goes between Pointers and Pre-registration when `repro` is set.
  - `skills/close/SKILL.md` step 4:
    - Update the command line.
    - Add one paragraph. A disproof states that the approach was credible and which alternatives
      were considered, and it gives the repro. A conditional states what depends on the current
      behaviour. A criterion is never widened at the close: the missed observation point goes in
      `--unknown`.
  - `docs/handoff-format.md`: add `## Reproducing` to Shape and Fields.
- **Tests.**
  - `test_verdict_requires_evidence`: each of the five refusals exits 2.
  - A `proven` close passes after `decide --by code --proof proved --evidence x`.
  - `--fired K1` renders `K1 …: fired` and `K2 …: did not fire`.
  - `## Reproducing` appears for disproven.
  - Update `test_borrowed_rules`: its conditional close gains `--blast-radius`.
- **Why.** Today `close` accepts any verdict with no evidence. The handoff reader therefore
  cannot tell "could not make it work" from "cannot work". It also cannot check the verdict
  against the criteria the scout fixed before building, which is the whole point of fixing them.

### 3. Stubs are recorded when they are made and re-read before the verdict

- **Mechanic.** Every fake is recorded as it is made, survives pivots and compaction, and is
  re-read against the question before the verdict. A stub of the part under test makes the
  verdict `unanswered`.
- **Sources.** J1/C1 (prp-spike "Track what got faked", "The stub that hid the hard part"). The
  "never mock the unknown part" sentence comes from J12.
- **Change.** As refined in J1:
  - `stub <text>` and `unstub <id> <evidence>` commands. Stub ids are S1.. and never shift (the
    same rule as item 5).
  - State key `st["stubs"]` and helper `open_stubs(st)`.
  - Render a `## Stubbed` section in `render_log`, and `- stubbed: …` lines under `## Still
    unknown` in `render_handoff`.
  - `context_text` gets one line: "Stubbed so far (re-read each against the question before any
    verdict)".
  - `cover_gaps` refuses a handoff that drops an open stub.
  - `cmd_recover` prints `## Open stubs`.
  - Skills:
    - `think` "How to answer": one bullet on recording stubs, plus the J12 sentence "never stub
      the part the question is about; blocked on access means `question`, not a mock".
    - `close` step 4: one sentence on re-reading the open stubs before choosing the verdict.
- **Tests.** `test_stubs_survive_pivot`:
  - stub, pivot, and check the hook payload and the handoff both carry the stub;
  - unstub, and check the stub leaves `## Still unknown`;
  - a renderer that swallows a stub makes `handoff` exit 2 (the same harness pattern as
    `test_handoff_cover_check`).
- **Why.** The failure most specific to spikes is mocking the question itself and calling it
  proven. Today stubs exist only as close-time recall in `--unknown`, and a stub made in
  direction 1 is gone after a pivot.

### 4. Closed directions and what turned them survive compaction and reach the handoff

- **Mechanic.** The session-start payload carries a "tried and left" guardrail: each closed
  direction with its learned line and the pointer to the evidence that turned it.
- **Sources.** C11 (agent-lab-kit HANDOFF "Failed (do not retry)"), C29 (Continuity rejected
  paths), C7 (HASH `ln-handoff` diagnostic evidence).
- **Change.** In `scripts/scout.py`:
  - `pivot` and `close` take `--evidence` (pointer), stored as `evidence` on the closing
    direction.
  - `context_text`: before `Current direction`, add `Tried and left (do not reopen without new
    evidence):` with one line per closed direction, `N. <text> — learned: <learned> [<evidence>]`.
  - `render_log`: show the evidence after `Learned:`.
  - `render_handoff` Pointers: the direction lines become `- direction N: <text> (opened …, closed
    …) — learned: <learned>; turned on: <evidence>`. The `- direction N:` prefix stays, so
    `cover_gaps` is unchanged.
  - `skills/pivot/SKILL.md` step 1: name the observation that ended the direction and pass it as
    `--evidence`.
- **Tests.**
  - Extend `test_hook_records_session_and_injects`: pivot with `--learned` and `--evidence`, then
    assert that the compact payload contains `Tried and left` and the learned line.
  - Extend `test_full_loop`: assert that the handoff's direction 1 line carries `learned: cache is
    per-process`.
- **Why.** `context_text` today re-injects only the current direction. After a compaction in
  direction 3, the successor cannot see that directions 1 and 2 failed, or why. That gap is
  exactly what the hook exists to close.

### 5. Parked questions get stable ids and carry the assumption the build proceeds on

- **Mechanic.** A question that is not asked carries the default the work continues on. Ids
  never shift. Before parking, check whether an experiment or a reversible default settles it.
  At the boundary, ask openly, without steering.
- **Sources.** C22 (spikekit ids; the code-stub half is dropped), C17 (hordev "never block"),
  C40 (agent-kit), C53 (ultracode gate protocol), C23 (spikekit proceeding-on; the recommend half
  is dropped), C24 (spikekit triage), C46 (why-log non-leading asking; the assent clause is
  dropped).
- **Change.**
  - `scripts/scout.py`:
    - Questions get `id` Q1..Qn. `load()` back-fills ids by position for old state.
    - `question` takes `--assuming "<default being built on>"`, stored as `assuming`.
    - `answer` takes `Q3` (or `3`), meaning the id, not the position among open questions.
      Today's index shifts after every answer.
    - When the question had an assumption, `answer` prints `assumed: <x> (since <ts>); answered:
      <y>; if they differ, re-check the work since then`.
    - `cmd_pivot`, `status -v`, `render_log`, `context_text` and the handoff Open questions all
      print `Q2: <text> (proceeding on: <x>)`.
  - `skills/think/SKILL.md`, before the parking-lot instruction, one paragraph:
    - If a run on the scout branch could answer the question, run it and note the result.
    - If a cheap-to-reverse default is fine, take it and park the question with `--assuming`.
    - Park bare only what the operator alone can settle.
    `start` step 3 gets one line mirroring it.
  - `skills/pivot` step 3 and `skills/close` step 3: ask each question openly, with its pointer.
    Show the assumption as what was built, never as the likely answer, and accept "I don't know"
    (the question then stays open).
- **Tests.**
  - `test_question_ids_and_assumptions`: park three questions, answer Q1, and assert Q2 and Q3
    keep their ids. Answering Q2 with text different from its assumption prints `assumed:`. The
    pivot printout and the handoff carry `Q3: … (proceeding on: …)`.
  - Update `test_full_loop`, which runs `answer 1`.
- **Why.** This fixes a real usability bug: positional `answer` indexes shift, and the pivot
  boundary prints questions without numbers. It also closes the gap rule 2 creates. When the
  model may not ask, the default it builds on is today recorded nowhere until the close tries to
  recover it.

### 6. Variant arms take named approaches, and the criteria are stored before launch

- **Mechanic.** Each arm is told which position on the one axis it builds. The prompts are
  otherwise identical, and no arm sees another's approach. The comparison criteria are written
  into the run record before any arm spawns. One approach is the codebase's path of least
  resistance, as the baseline.
- **Sources.** C5 (HASH `ln-prototype` bets), C8 (Pocock "radically different variants"), C15
  (hordev racing-prototypes), C20 (GSD comparison arms), C13 (agent-lab-kit prereg refuses
  unfrozen predictions).
- **Change.**
  - `scripts/scout.py`:
    - `variants` takes a repeatable `--arm "<approach>"`. When given, it must appear exactly `n`
      times; `n` stays positional, which avoids argparse ambiguity with the optional question.
    - It also takes a repeatable `--criterion "<observable check>"`, which is required (die
      without it, `--dry-run` included, and the dry run prints the criteria).
    - `VARIANT_PROMPT` gains `Your approach: {approach}. The other arms take different positions
      on the same axis; do not converge on a middle ground.` only when `--arm` was given. No arm
      is told another's approach.
    - The run record stores `criteria` before `_run_arm` is first called. Each arm stores
      `approach`, or `sampled` when no `--arm` was given.
    - `render_log` adds `Criteria (fixed before launch): …` above the table and an `approach`
      column. The printed table matches, and so do the handoff arm Pointers lines.
  - `skills/variants/SKILL.md` step 1:
    - Write one `--arm` per position and the criteria as `--criterion`.
    - One position is the existing pattern in this codebase.
    - Update the step 2 command line.
- **Tests.**
  - `test_variants_with_stub_claude` gains `--arm A --arm B --criterion c1`. v1's `prompt.txt`
    contains `Your approach: A` and not `B`. The state run has `criteria == ["c1"]`, and the log
    carries the criteria line.
  - `test_variants_dry_run_and_bounds`: no `--criterion` exits 2, and `--arm` given twice with
    `n=3` exits 2.
- **Why.** The skill demands "differ on one axis", but the CLI cannot express an axis. The
  measured run-4 `prompt.md` files differ only in `v1`/`v2`, so the arms differ only by sampling.
  The criteria the skill says to write first are stored nowhere, so nothing shows they existed
  before the race.

### 7. The box rings where the model will see it, and a run that would exceed it is refused

- **Mechanic.** A breached box is the first line of every command's output, of the session-start
  payload and of `status`. Each breach says which clock rang. No new spawn may push the box past
  its dollars. "Spent" has three easily missed shapes.
- **Sources.** C34 (gamedev `prototype-fast` timer), C36 (antiagree "check the ledger" first),
  C50 (ultracode budget floor; the refusal is kept and the 15% floor dropped), J12 (prp-spike
  sizing).
- **Change.**
  - `scripts/scout.py`:
    - New helper `breaches(st)` returns lines such as `BOX: $5.10/$5 spawn-metered. Pivot or
      close.` It also fires on calendar hours past `box.hours`, labelled honestly: `BOX: 4.3h on
      the calendar against a 4h box (0.0h logged). Pivot or close.`
    - `warn_box` prints `breaches()` to stderr. Call it at the end of `note`, `question`,
      `decide`, `pivot`, `spent` and `variants`.
    - `context_text` puts the breach lines first, and `cmd_status` prints them under the scout
      line.
    - `cmd_variants`, before any worktree exists: when `box.usd` is set and `n * cap` exceeds the
      remaining dollars, die with `run would exceed the box: $X left; fewer arms, a lower --usd,
      or pivot/close`. The dry run prints the same check.
  - `skills/think/SKILL.md` "When the direction is spent":
    - A `BOX:` line in any output is the ring.
    - Append J12's paragraph: blocked on access → park, never mock; answered early → offer close
      now; growing past half the box with no verdict → pivot to the one falsifiable part.
- **Tests.**
  - Extend `test_box_warning`: start with `--hours 0.0001`, run `note`, and assert `BOX:` and
    `on the calendar` on stderr. Also assert the hook payload's first line starts with `BOX:`.
  - `start --usd 1` then `variants 2 --usd 1 --dry-run` exits 2 with `would exceed the box`.
- **Why.** Today the hours box never rings. `warn_box` compares only hours logged by hand, no
  skill tells anyone to log them, it runs only from `spent` and `variants`, and the box reaches
  the session-start payload as neutral data. The think skill's "when the box line says spent"
  rule has nothing to fire on.

### 8. The harness, not the arm, runs the check in every arm and surfaces permission refusals

- **Mechanic.**
  - An acceptance command is written once. The arm is told it will be judged by it, and the
    harness runs it in each arm's worktree after the arm finishes. The arm's own report counts
    only as a claim.
  - A denied tool call is surfaced instead of silently weakening an arm.
  - Measured differences are checked for sensitivity and for cross-arm warm caches.
- **Sources.** C16 (hordev judging and corroboration), C42 (agent-kit "run a child's result
  before presenting it"), C52 (ultracode `permission_denials`), J13 (prp-spike `evidence.md`).
- **Change.**
  - `scripts/scout.py`:
    - `variants --check "<cmd>"` (repeatable). The commands are appended to the arm prompt ("you
      will be judged by: …").
    - In `_finish_arm`, after the harness commit, each check runs with `bash -c`, cwd set to the
      arm worktree, under `--check-timeout` (default 300).
    - The exit code and the last 20 lines go to `v<i>/check-<k>.txt`, and the arm stores
      `checks: [{cmd, exit}]`.
    - `_finish_arm` reads `result.get("permission_denials") or []`, writes them to
      `v<i>/denials.txt` and stores `denied: <count>`.
    - The printed table and `render_log` gain one `c<k>` column per check (`pass`/`fail`) and a
      `denied` column.
  - `skills/variants/SKILL.md` step 3, four sentences:
    - VARIANT.md is a claim. A criterion counts only from the check output; where the two
      disagree, report both.
    - An arm with denials is not evidence against its approach. Name the refused command and the
      `--tools` value that would allow it.
    - Before trusting a measured difference, change the thing under test and see the number move.
      Name any cache or service one arm could have warmed for another.
    - When the criterion is taste, the note names who judged.
- **Tests.**
  - `test_variants_with_stub_claude`: add `--check "test -f out.txt" --check "test -f nope"` and
    assert columns `pass` and `fail` and both `check-<k>.txt` files.
  - The stub's result JSON gains `"permission_denials":[{"tool_name":"Bash"}]`. Assert `denied` =
    1 and `denials.txt` exists.
- **Why.** Today the table's `success` means only "the process ended", and the comparison reads
  each arm's self-report. `result.json` already carries `permission_denials` (verified on run 4),
  but nothing reads it, and with `--permission-prompts none` a denied test command looks like a
  weak arm.

### 9. Handoff pointers are checked and stamped

- **Mechanic.** Before the handoff counts a pointer as evidence, the pointer must resolve. Pointers
  that resolve only on this machine are labelled as such. Each decision records the commit its
  `file:line` was cited against.
- **Sources.** J7/C4 (prp-spike Phase 7, "Making the evidence followable"), C44 (passbaton
  decision index header; the commit stamp is kept and the free-text token resolver dropped).
- **Change.**
  - `scripts/scout.py`:
    - `branch_mark()` returns `(missing)`, `(no commits past base)` or `(not pushed)`, and
      `transcript_mark()` returns `(local to this machine)` or `(missing)`, both as J7 refined.
    - Apply both in `render_handoff`, to the scout branch, the arm branches and the transcript
      lines. The base text stays intact, so `live.sh`'s `^- transcript: .*$SID.jsonl` still
      matches.
    - `cmd_handoff` refuses only when the scout branch itself is missing, unless `--no-check` is
      given.
    - `cmd_decide` stores `at_commit = git rev-parse HEAD`, plus `dirty` when `git status
      --porcelain` is non-empty.
    - `render_decisions` and the handoff evidence cell render `<evidence> @ <sha12>[+dirty]`.
  - `skills/handoff/SKILL.md` step 3: the script marks branches and transcripts; push what the
    reader must follow; check the free-text evidence by hand.
- **Tests.**
  - `test_handoff_pointer_marks`:
    - `(not pushed)` on the branch line;
    - `(local to this machine)` on a transcript line;
    - after `git branch -D` the handoff exits 2, and exits 0 with `--no-check`;
    - the evidence cell carries `@ <sha12>`.
  - Update the exact-row assertions in `test_full_loop` and `test_borrowed_rules`.
- **Why.** `file:line` pointers cited in direction 1 drift as later directions rewrite the branch.
  Today's cover check verifies only that a branch name is printed, not that it exists. Pointers
  are the plugin's alternative to copies, and a pointer that does not resolve is worth less than
  a copy.

### 10. Pre-registrations are append-only, carry a floor, and record their outcome

- **Mechanic.** A registration cannot be overwritten after a result exists. It states what a
  do-nothing arm would score, so the test can fail, and how warmup and spread are handled. Only
  its status may change later.
- **Sources.** C35 (antiagree "make it stick"), C12 (agent-lab-kit `prereg_require_floor`), J13
  (prp-spike pass-rule spread).
- **Change.**
  - `scripts/scout.py`:
    - `st["prereg"]` becomes a list of `{id: P1.., …, floor, status: open, status_evidence}`.
      `load()` wraps an old dict as P1, so the committed `scouting/variants-command` still loads.
    - `prereg` appends a registration, never replaces one, and requires `--floor "<what an arm
      that changed nothing scores, and why that fails the rule>"`.
    - New `prereg-status <P-id> passed|failed|dropped --evidence "<run pointer>"` changes only
      that entry's status and logs a dated entry.
    - `render_handoff` prints every entry with `- floor:` and `- status:`.
    - `cover_gaps` requires each P-id.
  - `skills/handoff/SKILL.md` step 1 and `skills/variants/SKILL.md` step 4: the command line
    gains `--floor`. Add one sentence: the pass rule states the runs discarded as warmup and the
    spread tolerated.
  - `docs/handoff-format.md`: add the fields.
- **Tests.**
  - `test_prereg_append_only`:
    - `prereg` without `--floor` exits 2;
    - a second `prereg` leaves P1's pass rule unchanged;
    - `prereg-status P1 failed --evidence x` renders `status: failed (x)`.
  - `test_full_loop`'s `prereg` call gains `--floor`.
- **Why.** Today a second `prereg` silently overwrites the first, so the pass rule can be moved
  after a result. That defeats rule 5. The one real registration
  (`scouting/variants-command/handoff.md`) has no way to say it was never run.

### 11. The handoff states how to read the branch and the box

- **Mechanic.** The scout branch is evidence: it is re-run and cited, never merged. A `commit`
  outcome authorizes a rebuild under the receiving track's rules. The box is what the scout spent
  without tests, error handling or edge cases, and is not an estimate.
- **Sources.** C10 (Pocock `prototype` rule 6), C33 (gamedev `prototype-fast` "keep authorizes a
  rewrite"; one fixed line instead of a `--code` flag), J9 (prp-spike Effort line).
- **Change.**
  - `scripts/scout.py`, `render_handoff`:
    - Under the Pointers branch line, the fixed line ``- `scout/<slug>` is evidence: re-run it,
      cite it, never merge it; what it proved is rebuilt under the receiving track's own rules.``
    - In Status, after the box line, the fixed line `The box is what the scout spent, without
      tests, error handling or edge cases; it is not an estimate for the real build.`
  - `skills/close/SKILL.md` step 4: redefine `commit` as "carries the decisions and the branch
    forward as evidence; the branch is never merged". On a `proven` verdict, `--unknown` names the
    parts of a real build the scout did not touch.
  - `docs/handoff-format.md` "How a spec-driven tool reads it": two bullets.
- **Tests.** In `test_full_loop`, assert both fixed lines in `handoff --print`.
- **Why.** `commit` "carries the branch forward" currently reads as "merge the prototype", and a
  box line with no caveat reads as a sizing. Both are standard spike-to-production failures, and
  both cost two constant lines to prevent.

### 12. `start` frames a question worth asking, with falsifiable criteria and its gates probed

- **Mechanic.**
  - The scout records the decision waiting on the answer, and refuses to open a scout whose yes
    and no lead to the same next action.
  - Criteria are observations, not adjectives. At least one of them is plausible, and an unknown
    threshold becomes a baseline finding.
  - Platform gates (credentials, entitlements, toolchain versions) are probed with one command
    each before the design depends on them.
- **Sources.** J5 (prp-spike `framing.md` both-outcomes check), J11 (prp-spike `framing.md`
  adjective-to-threshold), C19 (hordev rapid-spec "probe platform gates").
- **Change.**
  - `scripts/scout.py`: `start --stakes "<decision waiting; what yes changes; what no changes>"`,
    stored as `st["stakes"]`. It renders as a `Stakes:` line in `render_log` after the title,
    under `## Question` in `render_handoff`, and in `context_text`.
  - `skills/start/SKILL.md`:
    - Step 1: the J5 paragraph on stakes and stopping without opening, and the J11 paragraph on
      the shape of a criterion.
    - Step 2: the C19 paragraph. Probe each gate with one command and record it as `note "gate:
      <x>: <command> -> <result>"`. A missing gate hits a kill criterion or becomes the first
      direction; it is never a parked question.
  - `docs/protocol.md` rule 1: add one clause on stakes.
- **Tests.** `test_stakes_rendered`: `start --stakes s` renders `Stakes: s` in `log.md`, in
  handoff `## Question`, and in the hook payload.
- **Why.** "Explore the code first" is rule 1, but nothing today checks that the question is
  load-bearing or that its criteria can fail. The cheapest kill observation is often a missing
  gate, and the current start skill never looks for one.

### 13. What counts as a decision, and what counts as `proved`

- **Mechanic.** A decision is one choice between alternatives that were live at one seam. Framing
  and standing instructions from the operator are operator decisions. A passing check proves a
  claim only if it was seen to fail without the mechanism, and only at the seat where it was
  observed.
- **Sources.** C6 (HASH `ln-spec` unit-of-record smell checks), C31 (Continuity capture criteria;
  skill text only), C14 (agent-lab-kit claim-guard), C18 (hordev negative control; as a rule, not
  a flag), J6 (prp-spike seat; inside the evidence, not a flag).
- **Change.**
  - `scripts/scout.py` `cmd_decide`: `--proof proved` without `--evidence` dies with "a proved
    decision needs the observation: the command and its output, the revert run, file:line". That
    is the only script change.
  - `skills/close/SKILL.md` step 2, one paragraph:
    - Do not record helper names, file layout or steps under an already-recorded decision.
    - New evidence on an existing decision is a `--supersedes`.
    - Framing ("Y is the real bottleneck") and standing instructions ("never touch X") are
      `operator`, quoted, never `open`. Default to recording nothing.
    - `proved` requires having seen the check fail with the mechanism reverted or stubbed. The
      evidence names that run and the seat (process, layer and mode) it was observed from.
      Otherwise the decision is `inferred`.
  - `skills/think/SKILL.md` "Recording a decision": the same proved clause in one sentence.
  - `docs/protocol.md` rule 4: one clause.
- **Tests.** In `test_borrowed_rules`, `decide x --by code --proof proved` with no evidence exits
  2.
- **Why.** `proved` is the label a successor trusts most. Today a passing test that would also
  pass with the change reverted earns it, and a recovery pass at the close floods the table with
  implementation mechanics that the handoff-format treats as the downstream interview.

### 14. The handoff gets a cold read by a fresh, capped agent before it ships

- **Mechanic.** A fresh agent that cannot talk to the author reads only the handoff and reports
  just the questions where a wrong guess would change the plan, ranked. The author sorts each
  question into one of three piles: answered by the record, the scout's minor call, or the
  operator's. There is one round.
- **Sources.** C54 (superpowers brainstorming builder-check), C26 (spikekit `spike-wrap` hand
  off).
- **Change.**
  - `scripts/scout.py`:
    - New helper `_claude_cmd(model, cap, tools)` builds the `claude -p … --max-budget-usd …
      --permission-prompts none --no-session-persistence` argv. `_run_arm` uses it too (DRY).
    - New `coldread [--usd 0.5] [--model opus]` refuses without an existing `handoff.md` and
      passes item 7's box check.
    - It spawns in the repository root with `--allowedTools "Read,Grep,Glob"`. The adapted
      builder-check prompt goes on stdin and names only the handoff path.
    - It writes `scouting/<slug>/coldread.md`, adds `total_cost_usd` to `spent.usd`, and logs an
      entry. `cover_gaps` is untouched, because `coldread.md` is a pointer, not a handoff section.
  - `skills/handoff/SKILL.md` step 3 becomes: run `coldread`, then sort each question:
    - answered by the record or the code → fix the record with `decide`/`answer`/`note` and
      regenerate;
    - minor → record it as the scout's call;
    - the operator's → `question` or `decide --by open --ask`.
    The final message lists the operator's pile, most important first.
- **Tests.**
  - `test_coldread_with_stub_claude` reuses the stub from the variants test:
    - `coldread` before `handoff` exits 2;
    - after `handoff`, `coldread.md` holds the stub's `result`;
    - `spent.usd` rose by the stub's cost;
    - the argv carries `--max-budget-usd 0.5` and `--allowedTools Read,Grep,Glob`.
  - Optionally, `tests/live.sh` runs `/scout:handoff` and checks that `coldread.md` exists.
- **Why.** The handoff's only semantic check today is the author re-reading their own record, and
  that is the read least able to notice an unstated assumption. One capped Opus spawn costs
  cents, and it tests the one thing a handoff exists to do: let a stranger proceed without
  re-asking.

---

## Dropped

Merged candidates are listed under their item above. Everything else is listed here.

- **C8, convergence warning** (same file set ⇒ "converged"): two arms answering one question
  usually touch the same files. The signal is noise.
- **C22, `TODO(scout: Qn)` code stubs and the git-grep check:** a second channel next to
  `state.json`. The ids are kept (item 5).
- **C23, `--recommend` on parked questions:** conflicts with C46. A recommendation offered at the
  boundary is the plausible guess the operator then ratifies. The neutral "proceeding on" stays.
- **C46, "assent to a proposal is `code, inferred`":** that applies to why-log's recall setting.
  At a scout boundary the operator is deciding now, and the verified-quote rule (item 1) already
  governs provenance.
- **C25, `scout next`:** a `note` already carries the next step, and the last five entries are
  re-injected. A dedicated field is one more thing to drift.
- **C27, `variants --setup` and port offsets:** speculative. No measured run needed setup. Add it
  when a scout hits it.
- **C28, mandatory `--because` on supersede:** the replacing decision's row carries its evidence.
  A direction-level supersession now renders the direction's learned line in the handoff
  (item 4).
- **C31, widened recover regex** (`never|always|must|only…`): it would flag nearly every line. Its
  real content, how framing and instructions are classified, is in item 13.
- **C32, assistant-text "choices" extraction:** the passbaton prior art shows regex decision
  extraction failing 146 of 146 times. Silent mid-build choices now get recorded as they happen
  (item 5, `--assuming`).
- **C37, blind second-opinion spawn:** a second judging spawn type. Item 2 makes the verdict carry
  its evidence, the close already re-runs inferred decisions, and item 14 tests the spawn pattern
  first.
- **C51, adversary spawn:** dropped for the same reason as C37. Revisit if cold reads show
  verdicts getting through unchallenged.
- **C38, `claude plugin eval` cases:** this is measurement work, not a mechanic. Queue it as
  `docs/measured.md` "What to measure next" item 3 (decision-recovery accuracy), with its own
  budget.
- **C39, one-way-door tag:** it reverses the handoff contract ("operator decisions are not
  re-asked") for a class the scout cannot reliably classify. Defer until a real scout hands off a
  persisted format.
- **C41, `SCOUT:` code markers:** a duplicate channel for stubs. Item 3 records stubs in state and
  renders them.
- **C44, resolving `path:line` tokens parsed from free-text evidence:** clever, and it breaks on
  any phrasing. The commit stamp is kept (item 9).
- **C47 / C48 / C49, fixture freeze, fixture-author exposure, eval.json scoring:** scored-run
  machinery that belongs to the downstream scored track. The scout registers the run and does not
  run it (rule 5, `docs/handoff-format.md`).
- **C50, 15% drain floor:** an arbitrary fraction from a swarm scheduler. The refusal of a run
  that would exceed the box is kept (item 7).
- **C18, `--falsify` flag; J6, `--seat` flag:** both live as rules inside the required `proved`
  evidence (item 13), with no new schema.
- **C3 / J2, as a separate item:** folded into item 2.
- **J3, `--unlocks` and `--cheaper-option`:** optional prose that fits in `--verdict-note`. Only
  blast radius is required (item 2).
- **J4, `start --conditional` criteria:** a third pre-committed list. Kill and keep already fix
  both ends before the build, and the conditional middle is priced at the close (item 2).
- **J8, `close --under-test` versions:** marginal over the `--repro` command and `--unknown`.
  Add it if a verdict is ever found stale because a version moved.
- **C16, renaming the table's `status` column:** once a check column exists, `success` is no
  longer read as "answered" (item 8).

## Effort

About 160–190 tool calls in one session. All fourteen items converge on `scout.py`, so they
should run sequentially, not as parallel agents.

- Items 1, 2, 5, 6, 8, 9, 10 and 14 each touch the script, one to three skills, a doc and the
  tests, at roughly 12–15 calls each.
- Items 3, 4, 7, 11, 12 and 13 are smaller, at roughly 6–10 calls each.
- About 15 calls go to `docs/prior-art.md` "What was borrowed", README rows and `docs/protocol.md`
  clauses.
- About 10 go to test runs and fixes, then one `./selftest.sh` with the live part. That run costs
  about $1–2 on sonnet, plus the new `record this` step.

Commit in four groups so a red selftest bisects cleanly:

1. provenance (items 1, 9, 13);
2. close and verdict (items 2, 3, 4, 11);
3. loop ergonomics (items 5, 7, 12);
4. variants and spawns (items 6, 8, 10, 14).
