export const meta = {
  name: 'scout-ahead-prior-art-horde',
  description: 'Deep research horde: find prior art for a spike/exploration-mode Claude Code plugin (Oct 2026), refute each claim cross-family, synthesize bearings',
  phases: [
    { title: 'Search', detail: 'five distinguished-researcher lenses, mixed Opus/Fable' },
    { title: 'Refute', detail: 'every claim re-opened by a skeptic on the other model family' },
    { title: 'Critic', detail: 'what is missing' },
    { title: 'Synthesize', detail: 'bearings report' },
  ],
}

const CLAIMS = {
  type: 'object',
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'project / plugin / paper / doc name' },
          url: { type: 'string', description: 'the one URL that proves the claim; must be a page you actually fetched' },
          what_it_is: { type: 'string', description: 'two sentences: what it is, who made it, when (date if known)' },
          overlap: { type: 'string', enum: ['direct', 'partial', 'adjacent', 'none'], description: 'direct = a spike/exploration-mode workflow with boxes/pivots/decision recovery/handoff; partial = covers one or two of those; adjacent = same ecosystem, different problem' },
          what_it_covers: { type: 'string', description: 'which of: time/dollar box, kill criteria, pivot with supersession, decision recovery after the fact, provenance (operator/code/open), handoff to spec-driven tools, parallel variants in worktrees with per-arm caps, compaction re-injection hook, transcript pointer for successors' },
          what_it_lacks: { type: 'string' },
          evidence: { type: 'string', description: 'a quoted line or two from the fetched page' },
          popularity: { type: 'string', description: 'stars/installs/mentions if seen, else "unknown"' },
        },
        required: ['name', 'url', 'what_it_is', 'overlap', 'what_it_covers', 'what_it_lacks', 'evidence', 'popularity'],
      },
    },
    search_log: { type: 'string', description: 'the queries you ran and the dead ends, briefly' },
    verdict_on_gap: { type: 'string', description: 'in your expert judgment: is the gap real? one paragraph' },
  },
  required: ['claims', 'search_log', 'verdict_on_gap'],
}

const VERDICT = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reason: { type: 'string' },
    corrected_overlap: { type: 'string', enum: ['direct', 'partial', 'adjacent', 'none'] },
    what_the_page_actually_says: { type: 'string' },
  },
  required: ['refuted', 'reason', 'corrected_overlap', 'what_the_page_actually_says'],
}

const CONTEXT = `Today is ${args.today}. We built a Claude Code plugin called scout-ahead (${args.github}, local checkout ${args.repo}). Read its README.md, docs/protocol.md and docs/handoff-format.md from the checkout before searching, so you know exactly what to look for. In short: a workflow for exploratory work where decisions are discovered by building — a question with a time+dollar box and kill criteria, cheap pivots that supersede earlier decisions, no questions to the human mid-build (parked and raised at boundaries), decisions recovered after the fact from the diff and transcript and tagged operator/code/open, a plain-markdown handoff to spec-driven tools with optional pre-registration, 2-4 variant arms in sibling git worktrees each a capped claude -p, and a SessionStart hook that re-injects the open spike after compaction. The brief we built from claimed "every workflow framework we found assumes the decisions come first" and that comparison sites "literally say use the agent alone for prototypes". The operator does not believe there is no prior art in the community ecosystem as of October 2026. Your job is to find it, or to establish with evidence that it is not there.

Tooling: use WebSearch in "extended" mode (load it with ToolSearch if deferred) and WebFetch to read every page you cite; you may also run read-only \`gh search repos\`, \`gh search code\`, \`gh api\` (gh is authenticated), and inspect the installed marketplaces on disk under ~/.claude/plugins/marketplaces/ (claude-plugins-official, second-shift, coderlm, forge-core, trailofbits) and the plugin-directory cache ~/.claude/plugins/plugin-directory-cache-v2.json. Cite only pages you fetched; never a URL from memory. Prefer 2026 material; note dates. Return up to 6 claims, strongest overlap first, and include "none found" claims only as a search_log note, not as a claim.`

const LENSES = [
  { key: 'plugin-archaeologist', model: 'opus', prompt: `You are a distinguished Claude Code ecosystem archaeologist: you know every marketplace, every awesome-list, every plugin-directory entry. Lens: Claude Code plugins, skills, slash-command packs and hooks that implement a spike / prototype / exploration / research / experiment mode, or any "decisions discovered by building" workflow. Search the official plugin directory, awesome-claude-code lists, GitHub (topics: claude-code-plugin, claude-code-skill, claude-plugins), the installed marketplaces on this machine, and the agentskills.io / skills ecosystem. Also look specifically for hooks that re-inject context on the SessionStart compact matcher (session memory / continuity plugins).` },
  { key: 'spec-driven-analyst', model: 'fable', prompt: `You are a distinguished analyst of spec-driven and agentic development frameworks (Spec Kit, Kiro, BMAD, Superpowers, Conductor, OpenSpec, Ralph loops, Claude Code's own plan mode, etc.). Lens: do any of these frameworks have an explicit prototype / spike / exploration / "throwaway" mode, a handoff from exploration into spec, or a decision log with provenance and supersession? Find the comparison sites / articles that say "use the agent alone for prototypes" or equivalent, and any that contradict it. Quote them.` },
  { key: 'parallel-variants-researcher', model: 'opus', prompt: `You are a distinguished researcher of multi-agent experimentation tooling. Lens: tools that run 2-4 variants of the same question side by side in separate git worktrees with per-run budget caps and compare the results as evidence — Claude Code worktree/parallel-agent tools (Conductor, Crystal, claude-squad, vibe-kanban, Claude Code's own --worktree / EnterWorktree / agent teams), "best-of-N" or "tournament" prototyping plugins, and any pre-registration / experiment-tracking practice for agent runs. Also look for dollar-cap guards (--max-budget-usd wrappers).` },
  { key: 'research-mode-scholar', model: 'fable', prompt: `You are a distinguished scholar of AI-assisted research workflows and lab notebooks. Lens: tools and plugins for research spikes — lab-notebook / running-log skills, "decision records recovered from transcripts", ADR generators that mine chat history, successor handoff / session-continuity systems that hand the raw transcript to the next session, and papers or posts measuring how much context survives compaction. Include Anthropic's own docs and blog posts on long-running agents, context editing, memory tools and compaction from 2025-2026.` },
  { key: 'pre-mortem-contrarian', model: 'opus', prompt: `You are a distinguished contrarian running a pre-mortem: assume scout-ahead is redundant and find what makes it so. Lens: features built INTO Claude Code by October 2026 that already cover it (session forking, --worktree, agent teams, plan mode, auto-memory, /compact hooks, checkpoints, budget flags), Anthropic's official guidance on prototyping, and the most-installed plugins whose feature set subsumes it. Also check whether "decisions discovered by building" / "exploratory programming with agents" is an established practice with a name we missed (e.g. tracer bullets, walking skeletons, spike solutions in XP, "vibe coding" guides) that already has tooling.` },
]

phase('Search')
log('5 lenses out, mixed Opus/Fable; each claim will be refuted on the other family')

const results = await pipeline(
  LENSES,
  l => agent(`${CONTEXT}\n\nLENS: ${l.prompt}`, { label: `search:${l.key}`, phase: 'Search', model: l.model, schema: CLAIMS, effort: 'high' }),
  (r, l) => {
    if (!r) return null
    const other = l.model === 'opus' ? 'fable' : 'opus'
    log(`${l.key}: ${r.claims.length} claims → refuting on ${other}`)
    return parallel(r.claims.map(c => () =>
      agent(`You are a skeptic. A researcher claims the following is prior art for scout-ahead (${args.github}; read README.md and docs/protocol.md at ${args.repo} first, so you know what "overlap" means).\n\nClaim: ${JSON.stringify(c, null, 2)}\n\nRe-open the URL with WebFetch (and the repo's README / docs if it is a GitHub project; use gh api if the page is thin). Decide: is the stated overlap accurate? Default refuted=true if the page does not support the claim, if the overlap is overstated, if the project is abandoned/unmaintained in a way that matters, or if you cannot fetch it. Give the corrected overlap level and what the page actually says, with a quote.`,
        { label: `refute:${l.key}:${c.name.slice(0, 30)}`, phase: 'Refute', model: other, schema: VERDICT, effort: 'medium' })
        .then(v => ({ lens: l.key, claim: c, verdict: v }))
    )).then(vs => ({ lens: l.key, verdict_on_gap: r.verdict_on_gap, search_log: r.search_log, claims: vs.filter(Boolean) }))
  }
)

const lenses = results.filter(Boolean)
const all = lenses.flatMap(x => x.claims)
const kept = all.filter(x => x.verdict && !x.verdict.refuted)
const dropped = all.filter(x => !x.verdict || x.verdict.refuted)
log(`${all.length} claims, ${kept.length} survived refutation, ${dropped.length} refuted or unverifiable`)

phase('Critic')
const critic = await agent(`${CONTEXT}\n\nYou are the completeness critic. Here is what five lenses found and what survived refutation:\n\nSURVIVED:\n${JSON.stringify(kept.map(k => ({ lens: k.lens, name: k.claim.name, url: k.claim.url, overlap: k.verdict.corrected_overlap, covers: k.claim.what_it_covers })), null, 2)}\n\nREFUTED:\n${JSON.stringify(dropped.map(k => ({ lens: k.lens, name: k.claim.name, url: k.claim.url, reason: k.verdict ? k.verdict.reason : 'unverifiable' })), null, 2)}\n\nSEARCH LOGS:\n${lenses.map(l => `[${l.lens}] ${l.search_log}`).join('\n\n')}\n\nAsk: which search modality was not run? Which obvious name or community (Reddit r/ClaudeAI, Hacker News, X, Discord, the Claude Code GitHub issues, YouTube, newsletters) was not consulted? Run up to 6 additional searches yourself to fill the biggest gap you see, fetch what you find, and return any NEW candidates with the same claim shape plus a one-paragraph note on what remains unsearched.`,
  { label: 'critic', phase: 'Critic', model: 'fable', schema: CLAIMS, effort: 'high' })

let criticKept = []
if (critic && critic.claims.length) {
  log(`critic found ${critic.claims.length} more; refuting on opus`)
  criticKept = (await parallel(critic.claims.map(c => () =>
    agent(`You are a skeptic. Claim of prior art for scout-ahead (${args.github}; read README.md and docs/protocol.md at ${args.repo} first): ${JSON.stringify(c, null, 2)}\n\nRe-open the URL with WebFetch. Default refuted=true if unsupported, overstated, or unfetchable. Give the corrected overlap and what the page actually says, with a quote.`,
      { label: `refute:critic:${c.name.slice(0, 30)}`, phase: 'Refute', model: 'opus', schema: VERDICT, effort: 'medium' })
      .then(v => ({ lens: 'critic', claim: c, verdict: v }))))).filter(Boolean).filter(x => x.verdict && !x.verdict.refuted)
}

phase('Synthesize')
const survivors = kept.concat(criticKept)
const report = await agent(`${CONTEXT}\n\nYou are the synthesizer writing a bearings report for the operator, who suspects prior art exists. Be blunt and evidence-first. Input: every claim that SURVIVED cross-family refutation (with the refuter's corrected overlap and quote), every REFUTED claim (with reason), each lens's verdict on the gap, and the critic's note on what remains unsearched.\n\nSURVIVORS:\n${JSON.stringify(survivors, null, 2)}\n\nREFUTED:\n${JSON.stringify(dropped.map(k => ({ lens: k.lens, claim: k.claim, verdict: k.verdict })), null, 2)}\n\nLENS VERDICTS:\n${lenses.map(l => `[${l.lens}] ${l.verdict_on_gap}`).join('\n\n')}\n\nCRITIC: ${critic ? critic.verdict_on_gap + '\n' + critic.search_log : '(none)'}\n\nWrite markdown with exactly these sections: 1) Bottom line (three sentences: is the gap real, what is the closest prior art, what scout-ahead should borrow or drop). 2) Prior art table: name | URL | overlap (direct/partial/adjacent) | covers | lacks | date/popularity — survivors only, strongest first. 3) Claims that did not survive, one line each with why. 4) Bearings: for each scout-ahead feature (box+kill, pivot/supersession, no-asking-mid-build, decision recovery with provenance, handoff format, variants in worktrees with caps, compaction hook, transcript pointer) say "novel", "exists in <name>", or "exists natively in Claude Code as <feature>", with the URL. 5) Recommendations: concrete, ranked, including anything we should rename, integrate with, or cite in the README. 6) What remains unsearched. Pointers only, no copying; quote at most two lines per source.`,
  { label: 'synthesize', phase: 'Synthesize', model: 'fable', effort: 'high' })

return { report, survivors: survivors.length, refuted: dropped.length, lenses: lenses.length }