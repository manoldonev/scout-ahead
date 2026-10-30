export const meta = {
  name: 'scout-ahead-borrow-round',
  description: 'One round of the borrow loop: deep-read every prior-art source against the current scout-ahead checkout, propose borrow candidates, judge each cross-family',
  phases: [
    { title: 'Read', detail: 'one deep reader per source, full source not README' },
    { title: 'Judge', detail: 'each candidate judged on the other model family, default reject' },
    { title: 'Rank', detail: 'dedupe and order what survived' },
  ],
}

const CANDIDATES = {
  type: 'object',
  properties: {
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          mechanic: { type: 'string', description: 'one sentence: the concrete thing the source does' },
          source_pointer: { type: 'string', description: 'repo path and, if possible, a line range or heading; a URL you fetched' },
          quote: { type: 'string', description: 'the one or two lines from the source that define it' },
          scout_ahead_today: { type: 'string', description: 'what scout-ahead does now at this point, with the file in the checkout (scripts/scout.py function, skills/<name>/SKILL.md, docs/*.md); say "nothing" if absent' },
          proposed_change: { type: 'string', description: 'the smallest concrete change: which file, what shape (a flag, a rendered line, a skill paragraph, a check in the script)' },
          kind: { type: 'string', enum: ['script', 'skill-text', 'docs', 'test', 'hook'] },
          value: { type: 'string', enum: ['high', 'medium', 'low'], description: 'how much a real scout would gain' },
          cost: { type: 'string', enum: ['small', 'medium', 'large'], description: 'implementation size' },
        },
        required: ['mechanic', 'source_pointer', 'quote', 'scout_ahead_today', 'proposed_change', 'kind', 'value', 'cost'],
      },
    },
    already_borrowed: { type: 'string', description: 'mechanics in this source that scout-ahead already has, briefly, so the next round does not re-propose them' },
    read_log: { type: 'string', description: 'which files you read in full, which you skimmed, which you could not fetch' },
  },
  required: ['candidates', 'already_borrowed', 'read_log'],
}

const VERDICT = {
  type: 'object',
  properties: {
    accept: { type: 'boolean' },
    reason: { type: 'string' },
    refined_change: { type: 'string', description: 'if accepted: the change restated precisely enough to implement without re-reading the source; name file, function or skill section' },
    conflicts_with: { type: 'string', description: 'any scout-ahead rule, existing mechanic or earlier borrow this would duplicate or contradict; empty if none' },
    priority: { type: 'integer', description: '1 = do first, 5 = do last; only meaningful when accepted' },
  },
  required: ['accept', 'reason', 'refined_change', 'conflicts_with', 'priority'],
}

const RULES = `scout-ahead's own rules, which a borrow must not break: explore code before deciding; no asking the human mid-build (park, raise at a boundary); curated not retrieved (nothing pulled in by similarity); decisions written at the end of a direction, recorded only on "record this" or recovered at close; pre-registration only once measurable and before the scored run; 2-4 variants, compared as evidence, never sharing drafts; every spawn has a dollar cap enforced by the CLI; no dependence on agent teams, credential pass-through, or surviving compaction without the hook; Opus for spawns; never write a customer/client/employer name; pointers not copies; state.json is the record and the markdown is rendered from it; "engineered enough", DRY, explicit over clever, no ticket archeology in code. Things already borrowed in earlier rounds are listed in ${args.repo}/docs/prior-art.md under "What was borrowed"; do not re-propose them.`

phase('Read')
log(`round ${args.round}: ${args.sources.length} sources`)

const results = await pipeline(
  args.sources,
  src => agent(`You are a distinguished reader of agent-workflow tooling. Round ${args.round} of a borrow loop for the scout-ahead plugin.

First read the CURRENT scout-ahead checkout at ${args.repo}: README.md, DESIGN.md, docs/protocol.md, docs/handoff-format.md, docs/prior-art.md (especially "What was borrowed" and "Not borrowed"), plugins/scout/scripts/scout.py in full, every plugins/scout/skills/*/SKILL.md, plugins/scout/hooks/. You must know exactly what it does today, or your candidates will be duplicates.

Then read the SOURCE in full, not its README: ${src.name} — repo ${src.repo || '(search, see paths)'} — ${src.paths}. Use \`gh api repos/<owner>/<repo>/git/trees/<default-branch>?recursive=1\` to list files and \`gh api repos/<owner>/<repo>/contents/<path>\` (base64) or WebFetch raw.githubusercontent.com to read them. Read templates, scripts and hooks, not only prose.

Return every concrete mechanic in the source that scout-ahead lacks and that a real exploratory scout would gain from, as candidates. Be specific: a flag, a rendered line, a check, a skill paragraph, a hook behavior. Skip anything already borrowed, anything that is the source's own pipeline glue (its spec stages, its tracker integration), and anything that breaks these rules: ${RULES}

Zero candidates is a valid answer. List what is already borrowed so the next round skips it.`,
    { label: `read:${src.name}`, phase: 'Read', model: 'opus', schema: CANDIDATES, effort: 'high' }),
  (r, src) => {
    if (!r) return null
    log(`${src.name}: ${r.candidates.length} candidates → judging on fable`)
    return parallel(r.candidates.map(c => () =>
      agent(`You are the judge of a borrow loop for the scout-ahead plugin at ${args.repo}. Read README.md, docs/protocol.md, docs/prior-art.md and plugins/scout/scripts/scout.py and the relevant plugins/scout/skills/*/SKILL.md first.

Source: ${src.name} (${src.repo}). Candidate:
${JSON.stringify(c, null, 2)}

Decide whether scout-ahead should borrow it. Default accept=false. Accept only when ALL hold: it is not already present (check the code and skills, not the candidate's claim); it serves exploratory work where decisions are discovered by building; it does not break any rule in: ${RULES}; it is "engineered enough" (a flag, a line, a check, a paragraph), not a subsystem; and a real scout would be measurably better off. Reject duplicates of earlier borrows, the source's own pipeline glue, anything that adds a dialog, retrieval, or a second record beside state.json. If you accept, restate the change precisely enough to implement without re-reading the source. If you can verify the quote by fetching the source, do; if the quote does not hold, reject.`,
        { label: `judge:${src.name}:${c.mechanic.slice(0, 28)}`, phase: 'Judge', model: 'fable', schema: VERDICT, effort: 'medium' })
        .then(v => ({ source: src.name, candidate: c, verdict: v }))
    )).then(vs => ({ source: src.name, already_borrowed: r.already_borrowed, read_log: r.read_log, judged: vs.filter(Boolean) }))
  }
)

const read = results.filter(Boolean)
const all = read.flatMap(x => x.judged)
const accepted = all.filter(x => x.verdict && x.verdict.accept)
const rejected = all.filter(x => !x.verdict || !x.verdict.accept)
log(`${all.length} candidates, ${accepted.length} accepted, ${rejected.length} rejected`)

phase('Rank')
let plan = null
if (accepted.length) {
  plan = await agent(`You are the implementation planner for round ${args.round} of the scout-ahead borrow loop (checkout ${args.repo}; read plugins/scout/scripts/scout.py and the skills before planning). Here are the accepted candidates with the judges' refined changes:

${JSON.stringify(accepted.map(a => ({ source: a.source, mechanic: a.candidate.mechanic, kind: a.candidate.kind, value: a.candidate.value, cost: a.candidate.cost, refined_change: a.verdict.refined_change, conflicts_with: a.verdict.conflicts_with, priority: a.verdict.priority })), null, 2)}

Dedupe candidates that are the same mechanic from different sources (keep one, name all sources). Drop any pair that contradict each other, saying which you kept and why. Order by value then cost. Return markdown: a numbered list, each item: the mechanic in one line; sources; the exact change (file, function or skill section, shape); the test that would prove it (tests/test_scout.py or tests/live.sh); one line on why it earns its place. Then a short "Deferred" list of accepted items you judge not worth doing this round and why.`,
    { label: 'plan', phase: 'Rank', model: 'fable', effort: 'high' })
}

return {
  round: args.round,
  sources_read: read.length,
  candidates: all.length,
  accepted: accepted.length,
  plan,
  accepted_raw: accepted.map(a => ({ source: a.source, mechanic: a.candidate.mechanic, change: a.verdict.refined_change })),
  rejected_brief: rejected.map(r => ({ source: r.source, mechanic: r.candidate.mechanic, why: r.verdict ? r.verdict.reason.slice(0, 160) : 'unjudged' })),
  already_borrowed: read.map(r => ({ source: r.source, already: r.already_borrowed })),
}