"""Offline tests for scripts/scout.py: every command against a throwaway git repo."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent / "plugins" / "scout"
SCRIPT = PLUGIN / "scripts" / "scout.py"
HOOK = PLUGIN / "hooks" / "session-start.sh"


def sh(args, cwd, stdin=None, env=None, check=True):
    r = subprocess.run(args, cwd=cwd, text=True, input=stdin, capture_output=True, env=env)
    if check and r.returncode != 0:
        raise AssertionError(f"{args} failed ({r.returncode}): {r.stderr}")
    return r


class ScoutRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve()
        sh(["git", "init", "-q", "-b", "main"], self.repo)
        sh(["git", "config", "user.email", "t@example.invalid"], self.repo)
        sh(["git", "config", "user.name", "t"], self.repo)
        (self.repo / "a.txt").write_text("a\n")
        sh(["git", "add", "a.txt"], self.repo)
        sh(["git", "commit", "-q", "-m", "init"], self.repo)
        self.base = sh(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.fixtures = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()
        self.fixtures.cleanup()

    def transcript(self, name, records):
        tp = Path(self.fixtures.name).resolve() / name
        tp.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        return tp

    def add_session(self, slug, tp):
        st = self.state(slug)
        st["sessions"].append({"session_id": tp.stem, "transcript_path": str(tp)})
        (self.repo / "scouting" / slug / "state.json").write_text(json.dumps(st))

    def scout(self, *args, check=True, stdin=None):
        return sh([sys.executable, str(SCRIPT), *args], self.repo, stdin=stdin, check=check)

    def state(self, slug):
        return json.loads((self.repo / "scouting" / slug / "state.json").read_text())

    def stub_claude(self):
        """A `claude` on PATH that records argv and the stdin prompt in its cwd, writes a file there and prints a result json."""
        bindir = self.repo.parent / f"{self.repo.name}-bin"
        bindir.mkdir(exist_ok=True)
        stub = bindir / "claude"
        stub.write_text("""#!/usr/bin/env bash
printf '%s\\n' "$@" > argv.txt
cat > prompt.txt
mkdir -p .claude && echo x > .claude/settings.local.json
echo "built by $(basename "$PWD")" > VARIANT.md
echo built > out.txt
printf '{"type":"result","subtype":"success","total_cost_usd":0.25,"num_turns":3,"session_id":"stub","result":"done","permission_denials":[{"tool_name":"Bash"}]}'
""")
        stub.chmod(0o755)
        self.addCleanup(shutil.rmtree, bindir, ignore_errors=True)
        return dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}")

    def test_full_loop(self):
        out = self.scout("start", "Can the thing be done cheaply?", "--hours", "2", "--usd", "5", "--kill", "no path found").stdout
        self.assertIn("can-the-thing-be-done-cheaply", out)
        slug = "can-the-thing-be-done-cheaply"
        self.assertEqual(sh(["git", "branch", "--show-current"], self.repo).stdout.strip(), f"scout/{slug}")
        st = self.state(slug)
        self.assertEqual(st["base"], self.base)
        self.assertEqual(st["box"], {"hours": 2.0, "usd": 5.0})
        self.assertEqual((self.repo / "scouting" / ".current").read_text().strip(), slug)

        self.scout("note", "code: the caller lives in a.txt:1")
        self.scout("question", "is the cache shared?")
        self.scout("decide", "use the existing cache", "--by", "code", "--evidence", "a.txt:1")
        log = (self.repo / "scouting" / slug / "log.md").read_text()
        self.assertIn("code: the caller lives in a.txt:1", log)
        self.assertIn("question parked: is the cache shared?", log)
        self.assertIn("D1", (self.repo / "scouting" / slug / "decisions.md").read_text())

        out = self.scout("pivot", "bypass the cache", "--learned", "cache is per-process", "--evidence", "bench.txt:3", "--supersedes", "D1").stdout
        self.assertIn("direction 2 open", out)
        self.assertIn("boundary reached", out)
        st = self.state(slug)
        self.assertEqual(st["decisions"][0]["superseded_by"], 2)
        self.assertEqual(st["directions"][0]["learned"], "cache is per-process")
        self.assertIn("superseded by: direction 2", (self.repo / "scouting" / slug / "decisions.md").read_text())

        self.scout("answer", "Q1", "no, per process")
        tp = self.transcript("loop.jsonl", [{"type": "user", "message": {"content": "record this: ship the bypass"}}])
        self.scout("decide", "ship the bypass", "--by", "operator", "--evidence", str(tp))
        self.scout("decide", "cache eviction policy", "--by", "open")
        out = self.scout("close", "--outcome", "commit", "--tried", "cache, bypass", "--learned", "bypass wins", "--thrown-away", "cache branch").stdout
        self.assertIn("closed (commit)", out)
        self.assertFalse((self.repo / "scouting" / ".current").exists())
        self.assertEqual(self.scout("close", "--outcome", "kill", check=False).returncode, 2)

        self.scout("prereg", "--question", "bypass vs cache latency", "--arms", "bypass, cache", "--runs", "5",
                   "--pass-rule", "p50 under 10ms in 4 of 5", "--floor", "the cache arm unchanged scores p50 40ms, which fails", "--cost-usd", "3")
        out = self.scout("handoff", "--print").stdout
        for heading in ["## Question", "## Status", "## Decisions", "## Open questions", "## Pointers", "## Pre-registration", "## Thrown away"]:
            self.assertIn(heading, out)
        self.assertIn(f"| D2 | ship the bypass | operator | {tp} @ {self.base[:12]} |", out)
        self.assertIn(f"| D1 | use the existing cache | code, inferred | a.txt:1 @ {self.base[:12]} | direction 2 |", out)
        self.assertIn("- D3: cache eviction policy", out)
        self.assertIn("— learned: cache is per-process; turned on: bench.txt:3", out)
        self.assertIn(f"- `scout/{slug}` is evidence: re-run it, cite it, never merge it; what it proved is rebuilt under the receiving track's own rules.", out)
        self.assertIn("The box is what the scout spent, without tests, error handling or edge cases; it is not an estimate for the real build.", out)
        self.assertIn(f"- base: `{self.base}`", out)
        self.assertIn("p50 under 10ms", out)
        self.assertIn("cache branch", out)
        self.assertTrue((self.repo / "scouting" / slug / "handoff.md").exists())
        before = (self.repo / "scouting" / slug / "handoff.md").read_text()
        self.scout("spent", "--hours", "0.1")
        self.assertEqual(before, (self.repo / "scouting" / slug / "handoff.md").read_text(), "handoff is rendered only by the handoff command")
        self.assertIn("generated by scout from state.json", (self.repo / "scouting" / slug / "log.md").read_text())
        self.assertIn("generated by scout from state.json", (self.repo / "scouting" / slug / "decisions.md").read_text())

        out = self.scout("status", "-v").stdout
        self.assertIn("[closed, commit]", out)
        self.assertIn("decisions: 2 live, 1 open", out)

    def test_borrowed_rules(self):
        """Operator needs a quote; code carries proved/inferred; decisions supersede by id; open carries the ask;
        keep criteria; verdict and unknowns at close; handoff refuses to drop anything."""
        self.scout("start", "q rules", "--no-branch", "--keep", "p50 under 10ms", "--kill", "no path without isinstance")
        log = (self.repo / "scouting" / "q-rules" / "log.md").read_text()
        self.assertIn("Keep if: P1 p50 under 10ms.", log)
        r = self.scout("decide", "use X", "--by", "operator", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("needs --evidence", r.stderr)
        r = self.scout("decide", "use X", "--by", "open", "--proof", "proved", check=False)
        self.assertEqual(r.returncode, 2)
        r = self.scout("decide", "x", "--by", "code", "--proof", "proved", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("a proved decision needs the observation", r.stderr)
        self.scout("decide", "use X", "--by", "code", "--evidence", "a.txt:1")
        self.scout("decide", "use Y instead", "--by", "code", "--proof", "proved", "--evidence", "run output", "--supersedes", "D1")
        self.scout("decide", "eviction policy", "--by", "open", "--ask", "LRU or TTL?")
        st = self.state("q-rules")
        self.assertEqual(st["decisions"][0]["proof"], "inferred")
        self.assertEqual(st["decisions"][0]["superseded_by"], "D2")
        self.assertEqual(st["decisions"][1]["supersedes"], ["D1"])
        dec = (self.repo / "scouting" / "q-rules" / "decisions.md").read_text()
        self.assertIn("- settled by: code, inferred", dec)
        self.assertIn("- settled by: code, proved", dec)
        self.assertIn("- supersedes: D1", dec)
        self.assertIn("- superseded by: D2", dec)
        self.assertIn("- question to ask: LRU or TTL?", dec)
        self.scout("close", "--outcome", "kill", "--verdict", "conditional", "--verdict-note", "only if the cache is per process",
                   "--blast-radius", "every caller that assumes a shared cache",
                   "--unknown", "behaviour under concurrency", "--unknown", "cold start")
        log = (self.repo / "scouting" / "q-rules" / "log.md").read_text()
        self.assertIn("Verdict on the question: CONDITIONAL — only if the cache is per process", log)
        self.assertIn("- cold start", log)
        out = self.scout("handoff", "--print").stdout
        self.assertIn(f"| D1 | use X | code, inferred | a.txt:1 @ {self.base[:12]} | D2 |", out)
        self.assertIn("- D3: eviction policy — ask: LRU or TTL?", out)
        self.assertIn("## Still unknown", out)
        self.assertIn("- behaviour under concurrency", out)
        self.assertIn("Keep criteria: P1 p50 under 10ms.", out)
        self.assertIn("Criteria: none fired.", out)
        self.assertIn("Blast radius: every caller that assumes a shared cache", out)

    def test_handoff_cover_check(self):
        self.scout("start", "q cover", "--no-branch")
        self.scout("decide", "d one", "--by", "code", "--evidence", "x")
        st = self.state("q-cover")
        st["decisions"][0]["id"] = "D-odd id"
        (self.repo / "scouting" / "q-cover" / "state.json").write_text(json.dumps(st))
        self.assertEqual(self.scout("handoff", check=False).returncode, 0, "an unusual id still renders in the table")
        st["questions"].append({"text": "unrendered?", "at": "t", "direction": 1, "answered": None})
        (self.repo / "scouting" / "q-cover" / "state.json").write_text(json.dumps(st))
        self.assertEqual(self.scout("handoff", check=False).returncode, 0)
        # simulate a renderer regression: the open question list cannot show a question whose text is swallowed
        import subprocess as sp
        script = SCRIPT.read_text().replace('L.append(f"- {question_label(q)}")', 'pass')
        broken = self.repo / "broken.py"; broken.write_text(script)
        r = sp.run([sys.executable, str(broken), "handoff"], cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("handoff would drop: question: unrendered?", r.stderr)
        r = sp.run([sys.executable, str(broken), "handoff", "--no-check"], cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0)

    def test_verdict_requires_evidence(self):
        self.scout("start", "q verdict", "--no-branch", "--kill", "no path found", "--kill", "p50 over 50ms", "--keep", "one call site")
        refusals = [
            (["--verdict", "proven"], "needs at least one observed decision"),
            (["--verdict", "disproven", "--verdict-note", "the API has no hook"], "needs --verdict-note"),
            (["--verdict", "conditional", "--verdict-note", "only with one region"], "--blast-radius"),
            (["--verdict", "disproven", "--verdict-note", "no hook", "--repro", "make probe", "--blast-radius", "x"], "conditional verdict only"),
            (["--verdict", "unanswered", "--fired", "K9"], "no criterion K9"),
        ]
        self.scout("decide", "use the cache", "--by", "code", "--evidence", "a.txt:1")
        for extra, msg in refusals:
            r = self.scout("close", "--outcome", "kill", *extra, check=False)
            self.assertEqual(r.returncode, 2, extra)
            self.assertIn(msg, r.stderr)
            self.assertEqual(self.state("q-verdict")["status"], "open", "a refused close mutates nothing")
        self.scout("decide", "the cache holds", "--by", "code", "--proof", "proved", "--evidence", "x")
        self.scout("close", "--outcome", "commit", "--verdict", "proven", "--fired", "K1")
        out = self.scout("handoff", "--print").stdout
        self.assertIn("K1 no path found: fired", out)
        self.assertIn("K2 p50 over 50ms: did not fire", out)
        self.assertIn("P1 one call site: did not fire", out)
        self.assertNotIn("## Reproducing", out)

        self.scout("start", "q wall", "--no-branch")
        self.scout("close", "--outcome", "kill", "--verdict", "disproven", "--verdict-note", "the API has no hook",
                   "--repro", "python3 probe.py; look for 'no hook' on line 2")
        out = self.scout("handoff", "--print").stdout
        self.assertIn("## Reproducing\n\npython3 probe.py; look for 'no hook' on line 2\n", out)
        self.assertLess(out.index("## Pointers"), out.index("## Reproducing"))

    def test_stubs_survive_pivot(self):
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN))
        self.scout("start", "q stubs", "--no-branch")
        self.assertIn("S1 recorded", self.scout("stub", "payment API answers from a fixture").stdout)
        self.scout("pivot", "second direction", "--learned", "x")
        payload = json.dumps({"session_id": "s1", "transcript_path": "/nowhere/s1.jsonl", "cwd": str(self.repo), "source": "compact"})
        ctx = json.loads(sh(["bash", str(HOOK)], self.repo, stdin=payload, env=env).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Stubbed so far (re-read each against the question before any verdict): S1 payment API answers from a fixture", ctx)
        out = self.scout("handoff", "--print").stdout
        self.assertIn("## Still unknown\n\n- stubbed: S1 payment API answers from a fixture\n", out)
        self.assertIn("- S1 payment API answers from a fixture", self.scout("recover").stdout.split("## Open stubs")[1])
        self.assertIn("## Stubbed", (self.repo / "scouting" / "q-stubs" / "log.md").read_text())

        self.assertEqual(self.scout("unstub", "S9", "x", check=False).returncode, 2)
        self.scout("unstub", "S1", "pay.py:40 calls the sandbox")
        self.assertEqual(self.scout("unstub", "S1", "again", check=False).returncode, 2)
        out = self.scout("handoff", "--print").stdout
        self.assertNotIn("stubbed: S1", out.split("## Still unknown")[1])
        self.assertIn("→ unstubbed", (self.repo / "scouting" / "q-stubs" / "log.md").read_text())

        self.assertIn("S2 recorded", self.scout("stub", "auth is hard-coded").stdout)
        script = SCRIPT.read_text().replace('L.append(f"- stubbed: {sb[\'id\']} {sb[\'text\']}")', 'pass')
        broken = self.repo / "broken.py"; broken.write_text(script)
        r = subprocess.run([sys.executable, str(broken), "handoff"], cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("handoff would drop: stub S2", r.stderr)

    def test_operator_quote_verified(self):
        self.scout("start", "q quote", "--no-branch")
        real = "go with the bypass, but keep `$HOME/.cache` untouched"
        self.add_session("q-quote", self.transcript("s1.jsonl", [
            {"type": "user", "message": {"content": real}},
            {"type": "user", "isCompactSummary": True, "message": {"content": "Summary: the operator decided to go with X for the cache"}},
        ]))
        current = self.transcript("s2.jsonl", [
            {"type": "user", "message": {"content": [{"type": "text", "text":
                "<command-message>scout:think</command-message><command-args>record this: use the bypass</command-args>"}]}},
        ])
        (self.repo / "scouting" / ".session.json").write_text(json.dumps({"session_id": "s2", "transcript_path": str(current)}))

        self.scout("decide", "bypass the cache", "--by", "operator", "--evidence", "go with the bypass")
        r = self.scout("decide", "use X", "--by", "operator", "--evidence", "the operator decided to go with X", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("quote not found verbatim", r.stderr)
        self.scout("decide", "bypass", "--by", "operator", "--evidence", "use the bypass")
        r = self.scout("decide", "bypass", "--by", "operator", "--evidence", "yes", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("at least 10 characters", r.stderr)
        quote = "keep `$HOME/.cache` untouched"
        self.scout("decide", "leave the cache dir", "--by", "operator", "--evidence", "-", stdin=quote + "\n")
        self.assertEqual(self.state("q-quote")["decisions"][-1]["evidence"], quote)
        r = self.scout("decide", "-", "--by", "operator", "--evidence", "-", stdin=quote, check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("only one argument per call", r.stderr)

        r = self.scout("decide", "keep the cache", "--by", "code", "--evidence", "a.txt:1", "--supersedes", "D1", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("D1 was settled by the operator", r.stderr)
        self.assertIsNone(self.state("q-quote")["decisions"][0]["superseded_by"])

    def test_handoff_pointer_marks(self):
        self.scout("start", "q marks")
        branch = "scout/q-marks"
        self.add_session("q-marks", self.transcript("s1.jsonl", []))
        self.assertIn(f"- branch: `{branch}` (no commits past base)", self.scout("handoff", "--print").stdout)
        (self.repo / "a.txt").write_text("b\n")
        sh(["git", "commit", "-q", "-am", "change a"], self.repo)
        head = sh(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.scout("decide", "x", "--by", "code", "--evidence", "a.txt:1")
        out = self.scout("handoff", "--print").stdout
        self.assertIn(f"- branch: `{branch}` (not pushed)", out)
        self.assertIn(f"- transcript: {Path(self.fixtures.name).resolve() / 's1.jsonl'} (local to this machine)", out)
        self.assertIn(f"| a.txt:1 @ {head[:12]} |", out)

        sh(["git", "checkout", "-q", "main"], self.repo)
        sh(["git", "branch", "-q", "-D", branch], self.repo)
        r = self.scout("handoff", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn(f"scout branch that does not exist: {branch}", r.stderr)
        r = self.scout("handoff", "--no-check", "--print", check=False)
        self.assertEqual(r.returncode, 0)
        self.assertIn(f"- branch: `{branch}` (missing)", r.stdout)

    def test_slug_cuts_on_word_boundary(self):
        self.scout("start", "Can a hook re-inject the scout after compaction happens?", "--no-branch")
        slugs = [p.name for p in (self.repo / "scouting").iterdir() if p.is_dir()]
        self.assertEqual(slugs, ["can-a-hook-re-inject-the-scout-after"])

    def test_no_branch_and_duplicate(self):
        self.scout("start", "q one", "--no-branch")
        self.assertEqual(sh(["git", "branch", "--show-current"], self.repo).stdout.strip(), "main")
        r = self.scout("start", "q one", "--no-branch", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("already exists", r.stderr)

    def test_worktree_start(self):
        self.scout("start", "q wt", "--worktree")
        wt = self.repo.parent / f"{self.repo.name}-scout-worktrees" / "q-wt"
        try:
            self.assertTrue((wt / "scouting" / "q-wt" / "state.json").exists())
            self.assertEqual(sh(["git", "branch", "--show-current"], wt).stdout.strip(), "scout/q-wt")
            self.assertEqual(sh(["git", "branch", "--show-current"], self.repo).stdout.strip(), "main")
        finally:
            sh(["git", "worktree", "remove", "--force", str(wt)], self.repo, check=False)

    def test_box_warning(self):
        self.scout("start", "q box", "--hours", "1", "--usd", "1", "--no-branch")
        r = self.scout("spent", "--hours", "1.5")
        self.assertIn("BOX: 1.5/1h logged. Pivot or close.", r.stderr)
        r = self.scout("spent", "--usd", "0.5")
        self.assertNotIn("spawn-metered", r.stderr)
        r = self.scout("spent", "--usd", "0.5")
        self.assertIn("BOX: $1.00/$1 spawn-metered. Pivot or close.", r.stderr)
        status = self.scout("status").stdout
        self.assertLess(status.index("q-box"), status.index("    BOX: $1.00/$1 spawn-metered"))
        self.assertLess(status.index("    BOX: $1.00/$1 spawn-metered"), status.index("    box:"))

        self.scout("start", "q cal", "--hours", "0.0001", "--no-branch")
        time.sleep(0.5)
        r = self.scout("note", "still going")
        self.assertIn("BOX:", r.stderr)
        self.assertIn("on the calendar against a 0.0001h box (0.0h logged)", r.stderr)
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN))
        payload = json.dumps({"session_id": "s1", "transcript_path": "/nowhere/s1.jsonl", "cwd": str(self.repo), "source": "compact"})
        ctx = json.loads(sh(["bash", str(HOOK)], self.repo, stdin=payload, env=env).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(ctx.splitlines()[0].startswith("BOX:"), ctx)
        self.assertIn("Context was just compacted", ctx)

        self.scout("close", "--outcome", "kill")
        self.assertNotIn("BOX:", self.scout("status").stdout.split("q-cal")[1], "a closed scout has nothing to pivot or close")

    def test_variants_refused_past_box(self):
        self.scout("start", "q var box", "--usd", "1")
        r = self.scout("variants", "2", "--usd", "1", "--criterion", "c1", "--dry-run", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("run would exceed the box: $1.00 left; fewer arms, a lower --usd, or pivot/close", r.stderr)
        self.assertEqual(self.state("q-var-box")["variants"], [])

    def test_question_ids_and_assumptions(self):
        self.scout("start", "q ids", "--no-branch")
        self.assertIn("Q1 parked", self.scout("question", "is the cache shared?").stdout)
        self.scout("question", "which region?", "--assuming", "eu-west only")
        self.scout("question", "LRU or TTL?", "--assuming", "LRU")
        out = self.scout("answer", "Q1", "no, per process").stdout
        self.assertNotIn("assumed:", out)
        st = self.state("q-ids")
        self.assertEqual([q["id"] for q in st["questions"]], ["Q1", "Q2", "Q3"])
        self.assertEqual(st["questions"][1]["assuming"], "eu-west only")

        out = self.scout("answer", "2", "us-east as well").stdout
        self.assertIn("Q2 answered", out)
        self.assertIn("assumed: eu-west only (since ", out)
        self.assertIn("answered: us-east as well; if they differ, re-check the work since then", out)
        self.assertEqual(self.state("q-ids")["questions"][1]["answered"], "us-east as well")
        r = self.scout("answer", "Q2", "again", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("Q2 is already answered", r.stderr)
        r = self.scout("answer", "Q9", "x", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("no question Q9", r.stderr)

        out = self.scout("pivot", "next direction", "--learned", "x").stdout
        self.assertIn("  Q3: LRU or TTL? (proceeding on: LRU)", out)
        self.assertIn("- Q3: LRU or TTL? (proceeding on: LRU)\n", self.scout("handoff", "--print").stdout)
        self.assertIn("Parked questions (raise only at a pivot, a close, or when asked): Q3: LRU or TTL? (proceeding on: LRU)",
                      self.scout("context").stdout)
        log = (self.repo / "scouting" / "q-ids" / "log.md").read_text()
        self.assertIn("- [x] Q2: which region? (proceeding on: eu-west only) → us-east as well", log)

        st = self.state("q-ids")
        for q in st["questions"]:
            del q["id"]
        (self.repo / "scouting" / "q-ids" / "state.json").write_text(json.dumps(st))
        self.assertIn("      Q3: LRU or TTL? (proceeding on: LRU)", self.scout("status", "-v").stdout, "old state gets ids by position")
        self.assertIn("Q3 answered", self.scout("answer", "Q3", "LRU", "--scout", "q-ids").stdout)

    def test_stakes_rendered(self):
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN))
        self.scout("start", "q stakes", "--no-branch", "--stakes", "s")
        log = (self.repo / "scouting" / "q-stakes" / "log.md").read_text()
        self.assertIn("\nStakes: s\nOpened ", log)
        out = self.scout("handoff", "--print").stdout
        self.assertIn("Stakes: s", out.split("## Question")[1].split("## Status")[0])
        payload = json.dumps({"session_id": "s1", "transcript_path": "/nowhere/s1.jsonl", "cwd": str(self.repo), "source": "startup"})
        ctx = json.loads(sh(["bash", str(HOOK)], self.repo, stdin=payload, env=env).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Stakes: s", ctx)

    def test_hook_records_session_and_injects(self):
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN))
        payload = json.dumps({"session_id": "s1", "transcript_path": "/nowhere/s1.jsonl", "cwd": str(self.repo), "source": "startup", "hook_event_name": "SessionStart"})
        r = sh(["bash", str(HOOK)], self.repo, stdin=payload, env=env)
        self.assertEqual(r.stdout.strip(), "", "hook must stay silent when no scout is open")
        self.assertTrue((self.repo / "scouting" / ".session.json").exists())
        self.assertIn(".session.json", (self.repo / "scouting" / ".gitignore").read_text())

        self.scout("start", "Does it survive compaction?", "--no-branch", "--kill", "no injection in two runs")
        st = self.state("does-it-survive-compaction")
        self.assertEqual([s["session_id"] for s in st["sessions"]], ["s1"], "start adopts the session the hook recorded")
        self.scout("note", "first thread")
        self.scout("question", "is the window configurable?")
        self.scout("decide", "render md from state", "--by", "code", "--evidence", "scout.py:60")

        payload = json.dumps({"session_id": "s2", "transcript_path": "/nowhere/s2.jsonl", "cwd": str(self.repo), "source": "compact", "hook_event_name": "SessionStart"})
        r = sh(["bash", str(HOOK)], self.repo, stdin=payload, env=env)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("Context was just compacted", ctx)
        self.assertIn("Does it survive compaction?", ctx)
        self.assertIn("Current direction (1)", ctx)
        self.assertIn("first thread", ctx)
        self.assertIn("D1 render md from state [code, inferred]", ctx)
        self.assertIn("is the window configurable?", ctx)
        self.assertIn("Kill when: K1 no injection in two runs", ctx)
        self.assertNotIn("Tried and left", ctx)
        self.assertIn("/nowhere/s1.jsonl", ctx, "successor gets the previous session's raw transcript path")
        self.assertIn("/nowhere/s2.jsonl (this session)", ctx)
        st = self.state("does-it-survive-compaction")
        self.assertEqual([s["session_id"] for s in st["sessions"]], ["s1", "s2"])

        self.scout("pivot", "inject from a file", "--learned", "the window is fixed at 8k", "--evidence", "probe.log:12")
        payload = json.dumps({"session_id": "s3", "transcript_path": "/nowhere/s3.jsonl", "cwd": str(self.repo), "source": "compact", "hook_event_name": "SessionStart"})
        ctx = json.loads(sh(["bash", str(HOOK)], self.repo, stdin=payload, env=env).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Tried and left (do not reopen without new evidence):", ctx)
        self.assertIn("1. Does it survive compaction? — learned: the window is fixed at 8k [probe.log:12]", ctx)
        self.assertIn("Current direction (2): inject from a file", ctx)

        r = sh(["bash", str(HOOK)], self.repo, stdin="not json", env=env)
        self.assertEqual(r.returncode, 0)

    def test_recover_reads_transcript(self):
        self.scout("start", "q rec", "--no-branch")
        tp = self.repo / "fake.jsonl"
        lines = [
            {"type": "user", "message": {"role": "user", "content": "let's record this: go with the bypass"}, "timestamp": "2026-10-30T10:00:00Z"},
            {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "x"}]}},
            {"type": "user", "isMeta": True, "message": {"content": "meta"}},
            {"type": "assistant", "message": {"content": "no"}},
            {"type": "user", "message": {"content": [{"type": "text", "text": "and note the cost"}]}, "timestamp": "2026-10-30T10:01:00Z"},
            {"type": "user", "isCompactSummary": True, "message": {"content": "Summary: we decided to go with the cache"}},
            {"type": "user", "message": {"content": "This session is being continued from a previous conversation. go with the cache"}},
            {"type": "user", "message": {"content": "<command-message>scout:think</command-message><command-args>record this: use the bypass</command-args>"},
             "timestamp": "2026-10-30T10:02:00Z"},
            {"type": "user", "message": {"content": "<command-message>scout:status</command-message><command-args></command-args>"}},
        ]
        tp.write_text("\n".join(json.dumps(l) for l in lines) + "\nnot json\n")
        (self.repo / "b.txt").write_text("b\n")
        sh(["git", "add", "b.txt"], self.repo)
        sh(["git", "commit", "-q", "-m", "add b"], self.repo)
        st = self.state("q-rec")
        st["sessions"].append({"session_id": "x", "transcript_path": str(tp)})
        (self.repo / "scouting" / "q-rec" / "state.json").write_text(json.dumps(st))
        out = self.scout("recover").stdout
        self.assertIn("** let's record this: go with the bypass", out)
        self.assertIn("- 2026-10-30 10:01Z and note the cost", out)
        utts = out.split("## Operator utterances")[1].split("## Decisions already recorded")[0]
        self.assertNotIn("meta", utts)
        self.assertNotIn("go with the cache", utts)
        self.assertIn("- 2026-10-30 10:02Z ** record this: use the bypass", utts)
        self.assertNotIn("command-", utts)
        self.assertIn("add b", out)
        self.assertIn("b.txt", out)

    def test_variants_dry_run_and_bounds(self):
        self.scout("start", "q var", "--no-branch")
        r = self.scout("variants", "5", "--criterion", "c1", "--dry-run", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("2..4", r.stderr)
        (self.repo / "dirty.txt").write_text("x")
        r = self.scout("variants", "2", "--criterion", "c1", "--dry-run", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("dirty", r.stderr)
        (self.repo / "dirty.txt").unlink()
        sh(["git", "add", "-A"], self.repo)
        sh(["git", "commit", "-q", "-m", "scout state"], self.repo)
        r = self.scout("variants", "2", "--dry-run", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("criteria before launching", r.stderr)
        r = self.scout("variants", "3", "--arm", "A", "--arm", "B", "--criterion", "c1", "--dry-run", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--arm given 2 times for 3 arms", r.stderr)
        out = self.scout("variants", "3", "--dry-run", "--usd", "1.5", "--criterion", "p50 under 10ms").stdout
        self.assertEqual(out.count("would run arm"), 3)
        self.assertIn("cap $1.5", out)
        self.assertIn("criteria (fixed before launch): p50 under 10ms", out)

    def test_variants_with_stub_claude(self):
        """Arms run as separate processes in separate worktrees; a stub `claude` proves the plumbing.
        The scout itself is on a branch, so the arm branches must not nest under it."""
        env = self.stub_claude()
        self.scout("start", "q stub")
        sh(["git", "add", "-A"], self.repo)
        sh(["git", "commit", "-q", "-m", "scout state"], self.repo)
        r = subprocess.run([sys.executable, str(SCRIPT), "variants", "2", "--usd", "0.5", "--model", "opus",
                            "--arm", "A", "--arm", "B", "--criterion", "c1",
                            "--check", "test -f out.txt", "--check", "test -f nope"],
                           cwd=self.repo, text=True, capture_output=True, env=env)
        try:
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("| arm | approach | branch | cost | turns | files | status | c1 | c2 | denied |", r.stdout)
            self.assertIn("| v1 | A | `scout/q-stub-run1-v1` | $0.25 | 3 | 4 | success | pass | fail | 1 |", r.stdout)
            st = self.state("q-stub")
            run = st["variants"][0]
            self.assertEqual(run["criteria"], ["c1"])
            self.assertEqual(len(run["arms"]), 2)
            self.assertEqual(st["spent"]["usd"], 0.5)
            for a, approach in zip(run["arms"], ["A", "B"]):
                self.assertEqual(a["approach"], approach)
                self.assertTrue(a["commit"], "arm work is committed on its branch as a pointer")
                self.assertEqual([c["exit"] == 0 for c in a["checks"]], [True, False])
                self.assertEqual(a["denied"], 1)
                vdir = self.repo / "scouting" / "q-stub" / "variants" / "run-1" / f"v{a['i']}"
                self.assertIn(f"built by q-stub-run1-v{a['i']}", (vdir / "VARIANT.md").read_text())
                self.assertEqual(json.loads((vdir / "result.json").read_text())["total_cost_usd"], 0.25)
                self.assertIn("exit: 0", (vdir / "check-1.txt").read_text())
                self.assertIn("exit: 1", (vdir / "check-2.txt").read_text())
                self.assertIn("Bash", (vdir / "denials.txt").read_text())
                argv_text = (Path(a["worktree"]) / "argv.txt").read_text()
                argv = argv_text.split("\n")
                self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.5")
                self.assertEqual(argv[argv.index("--model") + 1], "opus")
                self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
                self.assertNotIn("You are arm", argv_text, "the prompt travels on stdin, never as a positional after a list flag")
                prompt = (Path(a["worktree"]) / "prompt.txt").read_text()
                self.assertIn("Do not read, list or search any other worktree", prompt)
                self.assertIn(f"Your approach: {approach}.", prompt)
                self.assertNotIn(f"Your approach: {'B' if approach == 'A' else 'A'}", prompt, "no arm is told another's approach")
                self.assertIn("You will be judged by: `test -f out.txt`; `test -f nope`.", prompt)
                tracked = sh(["git", "ls-tree", "-r", "--name-only", "HEAD"], Path(a["worktree"])).stdout
                self.assertNotIn(".claude/", tracked, "the CLI's own .claude/ dir stays out of the arm commit")
            log = (self.repo / "scouting" / "q-stub" / "log.md").read_text()
            self.assertIn("## Variants", log)
            self.assertIn("Criteria (fixed before launch): c1.", log)
            self.assertIn("| v2 | B | `scout/q-stub-run1-v2` |", log)
            self.assertIn("- variant run 1 arm v2 (B): `scout/q-stub-run1-v2`", self.scout("handoff", "--print").stdout)
        finally:
            for a in self.state("q-stub")["variants"][0]["arms"]:
                sh(["git", "worktree", "remove", "--force", a["worktree"]], self.repo, check=False)
            shutil.rmtree(self.repo.parent / f"{self.repo.name}-scout-worktrees", ignore_errors=True)

    def test_prereg_append_only(self):
        self.scout("start", "q prereg", "--no-branch")
        base = ["prereg", "--question", "lock vs none", "--arms", "lock, none", "--runs", "5", "--cost-usd", "0"]
        r = self.scout(*base, "--pass-rule", "10 of 10 kept", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--floor", r.stderr)
        self.assertIn("P1 pre-registered", self.scout(*base, "--pass-rule", "10 of 10 kept", "--floor", "no lock keeps 6 of 10").stdout)
        self.assertIn("P2 pre-registered", self.scout(*base, "--pass-rule", "moved rule", "--floor", "f").stdout)
        st = self.state("q-prereg")
        self.assertEqual([(p["id"], p["pass_rule"]) for p in st["prereg"]], [("R1", "10 of 10 kept"), ("R2", "moved rule")])
        self.scout("prereg-status", "R1", "failed", "--evidence", "x")
        r = self.scout("prereg-status", "R1", "passed", "--evidence", "y", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("R1 is already failed (x)", r.stderr)
        self.assertEqual(self.scout("prereg-status", "P9", "dropped", "--evidence", "z", check=False).returncode, 2)
        out = self.scout("handoff", "--print").stdout
        p1 = out.split("### R1\n")[1].split("### R2\n")[0]
        self.assertIn("- pass rule: 10 of 10 kept", p1)
        self.assertIn("- floor: no lock keeps 6 of 10", p1)
        self.assertIn("- status: failed (x)", p1)
        self.assertIn("- status: open", out.split("### R2\n")[1])
        self.assertIn("pre-registration R1 failed: x", (self.repo / "scouting" / "q-prereg" / "log.md").read_text())

        st = self.state("q-prereg")
        st["prereg"] = {"question": "old", "arms": "a, b", "runs": "1", "pass_rule": "r", "cost_usd": 0.0, "at": st["opened_at"]}
        (self.repo / "scouting" / "q-prereg" / "state.json").write_text(json.dumps(st))
        out = self.scout("handoff", "--print").stdout
        self.assertIn("### R1\n\n- question: old", out, "an old single registration becomes R1")
        self.assertIn("- status: open", out)

        script = SCRIPT.read_text().replace('L.append(f"### {p[\'id\']}")', 'pass')
        broken = self.repo / "broken.py"; broken.write_text(script)
        r = subprocess.run([sys.executable, str(broken), "handoff"], cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("handoff would drop: pre-registration R1", r.stderr)

    def test_coldread_with_stub_claude(self):
        env = self.stub_claude()
        self.scout("start", "q cold", "--no-branch", "--usd", "2")
        cold = lambda *a: subprocess.run([sys.executable, str(SCRIPT), "coldread", *a], cwd=self.repo, text=True, capture_output=True, env=env)
        r = cold()
        self.assertEqual(r.returncode, 2)
        self.assertIn("run `scout handoff` first", r.stderr)
        self.scout("handoff")
        r = cold()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("done", (self.repo / "scouting" / "q-cold" / "coldread.md").read_text())
        self.assertEqual(self.state("q-cold")["spent"]["usd"], 0.25)
        argv = (self.repo / "argv.txt").read_text().split("\n")
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.5")
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Read,Grep,Glob")
        self.assertNotIn("--permission-mode", argv, "the cold reader gets no edit permission")
        prompt = (self.repo / "prompt.txt").read_text()
        self.assertIn("Read scouting/q-cold/handoff.md.", prompt)
        self.assertIn("cold read: scouting/q-cold/coldread.md, $0.25", (self.repo / "scouting" / "q-cold" / "log.md").read_text())
        r = cold("--usd", "1.8")
        self.assertEqual(r.returncode, 2)
        self.assertIn("run would exceed the box: $1.75 left", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
