#!/usr/bin/env bash
# One command: offline tests for the script and the hook, then the live claude -p run.
# SPIKE_SKIP_LIVE=1 skips the live part (no claude, or no budget).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
fail=0
echo "== plugin manifests"
claude plugin validate plugins/spike >/dev/null 2>&1 && echo "  ok   plugin.json" || { echo "  FAIL plugin.json"; fail=1; }
claude plugin validate . >/dev/null 2>&1 && echo "  ok   marketplace.json" || { echo "  FAIL marketplace.json"; fail=1; }
echo "== offline: script + hook"
python3 tests/test_spike.py 2>&1 | tail -3 | sed 's/^/  /'
[ "${PIPESTATUS[0]}" = 0 ] || fail=1
if [ "${SPIKE_SKIP_LIVE:-0}" = 1 ]; then
  echo "== live: skipped (SPIKE_SKIP_LIVE=1)"
else
  echo "== live: claude -p"
  bash tests/live.sh || fail=1
fi
[ "$fail" = 0 ] && echo "selftest: PASS" || echo "selftest: FAIL"
exit $fail
