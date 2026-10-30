"""Offline tests for scripts/scout.py: every command against a throwaway git repo."""
import json
import os
import subprocess
import sys
import tempfile
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

        out = self.scout("pivot", "bypass the cache", "--learned", "cache is per-process", "--supersedes", "D1").stdout
        self.assertIn("direction 2 open", out)
        self.assertIn("boundary reached", out)
        st = self.state(slug)
        self.assertEqual(st["decisions"][0]["superseded_by"], 2)
        self.assertEqual(st["directions"][0]["learned"], "cache is per-process")
        self.assertIn("superseded by: direction 2", (self.repo / "scouting" / slug / "decisions.md").read_text())

        self.scout("answer", "1", "no, per process")
        tp = self.transcript("loop.jsonl", [{"type": "user", "message": {"content": "record this: ship the bypass"}}])
        self.scout("decide", "ship the bypass", "--by", "operator", "--evidence", str(tp))
        self.scout("decide", "cache eviction policy", "--by", "open")
        out = self.scout("close", "--outcome", "commit", "--tried", "cache, bypass", "--learned", "bypass wins", "--thrown-away", "cache branch").stdout
        self.assertIn("closed (commit)", out)
        self.assertFalse((self.repo / "scouting" / ".current").exists())
        self.assertEqual(self.scout("close", "--outcome", "kill", check=False).returncode, 2)

        self.scout("prereg", "--question", "bypass vs cache latency", "--arms", "bypass, cache", "--runs", "5",
                   "--pass-rule", "p50 under 10ms in 4 of 5", "--cost-usd", "3")
        out = self.scout("handoff", "--print").stdout
        for heading in ["## Question", "## Status", "## Decisions", "## Open questions", "## Pointers", "## Pre-registration", "## Thrown away"]:
            self.assertIn(heading, out)
        self.assertIn(f"| D2 | ship the bypass | operator | {tp} @ {self.base[:12]} |", out)
        self.assertIn(f"| D1 | use the existing cache | code, inferred | a.txt:1 @ {self.base[:12]} | direction 2 |", out)
        self.assertIn("- D3: cache eviction policy", out)
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
        self.assertIn("Keep if: p50 under 10ms.", log)
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
                   "--unknown", "behaviour under concurrency", "--unknown", "cold start")
        log = (self.repo / "scouting" / "q-rules" / "log.md").read_text()
        self.assertIn("Verdict on the question: CONDITIONAL — only if the cache is per process", log)
        self.assertIn("- cold start", log)
        out = self.scout("handoff", "--print").stdout
        self.assertIn(f"| D1 | use X | code, inferred | a.txt:1 @ {self.base[:12]} | D2 |", out)
        self.assertIn("- D3: eviction policy — ask: LRU or TTL?", out)
        self.assertIn("## Still unknown", out)
        self.assertIn("- behaviour under concurrency", out)
        self.assertIn("Keep criteria: p50 under 10ms.", out)

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
        script = SCRIPT.read_text().replace('L.append(f"- {q[\'text\']}")', 'pass')
        broken = self.repo / "broken.py"; broken.write_text(script)
        r = sp.run([sys.executable, str(broken), "handoff"], cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("handoff would drop: question: unrendered?", r.stderr)
        r = sp.run([sys.executable, str(broken), "handoff", "--no-check"], cwd=self.repo, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0)

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
        self.assertIn("BOX: hours spent", r.stderr)
        r = self.scout("spent", "--usd", "0.5")
        self.assertNotIn("dollars", r.stderr)
        r = self.scout("spent", "--usd", "0.5")
        self.assertIn("BOX: dollars spent", r.stderr)

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
        self.assertIn("Kill when: no injection in two runs", ctx)
        self.assertIn("/nowhere/s1.jsonl", ctx, "successor gets the previous session's raw transcript path")
        self.assertIn("/nowhere/s2.jsonl (this session)", ctx)
        st = self.state("does-it-survive-compaction")
        self.assertEqual([s["session_id"] for s in st["sessions"]], ["s1", "s2"])

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
        r = self.scout("variants", "5", "--dry-run", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("2..4", r.stderr)
        (self.repo / "dirty.txt").write_text("x")
        r = self.scout("variants", "2", "--dry-run", check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("dirty", r.stderr)
        (self.repo / "dirty.txt").unlink()
        sh(["git", "add", "-A"], self.repo)
        sh(["git", "commit", "-q", "-m", "scout state"], self.repo)
        out = self.scout("variants", "3", "--dry-run", "--usd", "1.5").stdout
        self.assertEqual(out.count("would run arm"), 3)
        self.assertIn("cap $1.5", out)

    def test_variants_with_stub_claude(self):
        """Arms run as separate processes in separate worktrees; a stub `claude` proves the plumbing.
        The scout itself is on a branch, so the arm branches must not nest under it."""
        bindir = self.repo.parent / f"{self.repo.name}-bin"
        bindir.mkdir(exist_ok=True)
        stub = bindir / "claude"
        stub.write_text("""#!/usr/bin/env bash
# stub: record argv and the stdin prompt, write a file in the worktree, print a result json
printf '%s\\n' "$@" > argv.txt
cat > prompt.txt
mkdir -p .claude && echo x > .claude/settings.local.json
echo "built by $(basename "$PWD")" > VARIANT.md
echo built > out.txt
printf '{"type":"result","subtype":"success","total_cost_usd":0.25,"num_turns":3,"session_id":"stub","result":"done"}'
""")
        stub.chmod(0o755)
        self.scout("start", "q stub")
        sh(["git", "add", "-A"], self.repo)
        sh(["git", "commit", "-q", "-m", "scout state"], self.repo)
        env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}")
        r = subprocess.run([sys.executable, str(SCRIPT), "variants", "2", "--usd", "0.5", "--model", "opus"], cwd=self.repo, text=True, capture_output=True, env=env)
        try:
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("| v1 | scout/q-stub-run1-v1 | $0.25 | 3 | 4 | success |", r.stdout)
            st = self.state("q-stub")
            run = st["variants"][0]
            self.assertEqual(len(run["arms"]), 2)
            self.assertEqual(st["spent"]["usd"], 0.5)
            for a in run["arms"]:
                self.assertTrue(a["commit"], "arm work is committed on its branch as a pointer")
                vdir = self.repo / "scouting" / "q-stub" / "variants" / "run-1" / f"v{a['i']}"
                self.assertIn(f"built by q-stub-run1-v{a['i']}", (vdir / "VARIANT.md").read_text())
                self.assertEqual(json.loads((vdir / "result.json").read_text())["total_cost_usd"], 0.25)
                argv_text = (Path(a["worktree"]) / "argv.txt").read_text()
                argv = argv_text.split("\n")
                self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.5")
                self.assertEqual(argv[argv.index("--model") + 1], "opus")
                self.assertNotIn("You are arm", argv_text, "the prompt travels on stdin, never as a positional after a list flag")
                self.assertIn("Do not read, list or search any other worktree", (Path(a["worktree"]) / "prompt.txt").read_text())
                tracked = sh(["git", "ls-tree", "-r", "--name-only", "HEAD"], Path(a["worktree"])).stdout
                self.assertNotIn(".claude/", tracked, "the CLI's own .claude/ dir stays out of the arm commit")
            self.assertIn("## Variants", (self.repo / "scouting" / "q-stub" / "log.md").read_text())
            self.assertIn("variant run 1 arm v2", self.scout("handoff", "--print").stdout)
        finally:
            for a in self.state("q-stub")["variants"][0]["arms"]:
                sh(["git", "worktree", "remove", "--force", a["worktree"]], self.repo, check=False)
            import shutil
            shutil.rmtree(bindir, ignore_errors=True)
            shutil.rmtree(self.repo.parent / f"{self.repo.name}-scout-worktrees", ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
