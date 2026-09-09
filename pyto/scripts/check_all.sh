#!/usr/bin/env bash
# check_all.sh v0 (Day 1): run every check the week guards, print per-suite
# counts, exit non-zero if any suite fails.
#
# Isolation rules (research/ULTRACODE-WEEK.md, critic gap 8; docs/worktree-workflow.md:17):
#   - the pyto root is resolved from this script's own path, never a relative cd;
#   - examples run with plain python3 (pyto comes from the installed package,
#     editable on Days 1-4, the wheel on Day 5), never PYTHONPATH=src;
#   - the only PYTHONPATH set anywhere below is `PYTHONPATH=.` for the disc-stats
#     suite, whitelisted as intra-directory (run_experiment.py names stats.py in cwd).
# Zero-count assertions use `! grep -q` (critic gap 18a).
set -euo pipefail

PYTO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${CHECK_ALL_LOG_DIR:-$(mktemp -d)}"
mkdir -p "$LOG_DIR"
EXPECT_CONSUMER="${EXPECT_CONSUMER:-18}"
EXPECT_DISC_STATS="${EXPECT_DISC_STATS:-4}"

echo "== check_all.sh v0"
echo "pyto root:    $PYTO"
echo "logs:         $LOG_DIR"
echo "python3:      $(command -v python3) ($(python3 --version 2>&1))"
echo "pyto module:  $(python3 -c 'import pyto; print(pyto.__file__)')"
echo

# Day 1 prerequisite: the consumer's tests write under data/ and the directory is gitignored.
mkdir -p "$PYTO/consumers/discstudio-card/data"

FAILED=0
SUMMARY=()

# count_from_log <log> -> N from the unittest "Ran N tests" line ("?" if absent)
count_from_log() {
    local n
    n="$(grep -E '^Ran [0-9]+ tests? in' "$1" | tail -1 | sed -E 's/^Ran ([0-9]+) tests?.*/\1/' || true)"
    printf '%s' "${n:-?}"
}

# run_suite <name> <workdir> <command...>
# Runs the command in <workdir>, prints its full log, records the count.
run_suite() {
    local name="$1" workdir="$2"; shift 2
    local log="$LOG_DIR/${name//\//_}.log" rc=0
    echo "== suite: $name  (cwd $workdir)"
    echo "   \$ $*"
    (cd "$workdir" && "$@") > "$log" 2>&1 || rc=$?
    cat "$log"
    local count; count="$(count_from_log "$log")"
    if [ "$rc" -ne 0 ]; then
        echo "-- $name: FAILED (exit $rc, ran $count)"; FAILED=1
    elif ! grep -q '^OK' "$log"; then
        echo "-- $name: FAILED (no OK line, ran $count)"; FAILED=1; rc=1
    elif grep -q '^Ran 0 tests' "$log"; then
        echo "-- $name: FAILED (ran 0 tests)"; FAILED=1; rc=1
    else
        echo "-- $name: OK (ran $count)"
    fi
    SUMMARY+=("$(printf '%-28s %6s  %s' "$name" "$count" "$([ "$rc" -eq 0 ] && echo OK || echo FAIL)")")
    echo
}

# expect_count <name> <expected> : pin a suite's count (kill criteria name 18 and 4)
expect_count() {
    local name="$1" expected="$2" log="$LOG_DIR/${1//\//_}.log"
    if ! grep -q "^Ran $expected tests in" "$log"; then
        echo "-- $name: FAILED (expected exactly $expected tests, got $(count_from_log "$log"))"; FAILED=1
    fi
}

# 1. library tests
run_suite library "$PYTO" python3 -m unittest discover -s tests -v

# 2. every experiments/<name>/ holding test_*.py (runs/ is a record, not a suite)
for dir in "$PYTO"/experiments/*/; do
    name="$(basename "$dir")"
    [ "$name" = "runs" ] && continue
    ls "$dir"/test_*.py > /dev/null 2>&1 || continue
    run_suite "experiments/$name" "$PYTO" python3 -m unittest discover -s "experiments/$name" -p 'test_*.py' -v
done

# 3. consumer tests (18)
run_suite consumer "$PYTO/consumers/discstudio-card" python3 -m unittest discover -s . -p 'test_*.py' -v
expect_count consumer "$EXPECT_CONSUMER"

# 4. disc-stats (4). PYTHONPATH=. whitelisted: intra-directory, names stats.py in cwd.
run_suite disc-stats "$PYTO/consumers/discstudio-card/experiments/disc-stats" \
    env PYTHONPATH=. python3 -m unittest discover -s . -p 'test_*.py' -v
expect_count disc-stats "$EXPECT_DISC_STATS"

# 5. examples with plain python3 (no PYTHONPATH): basic.py must print exactly 42
echo "== suite: examples  (cwd $PYTO)"
example_rc=0
basic_out="$(cd "$PYTO" && python3 examples/basic.py 2>&1)" || example_rc=$?
echo "   \$ python3 examples/basic.py -> ${basic_out}"
if [ "$example_rc" -ne 0 ] || [ "$basic_out" != "42" ]; then
    echo "-- examples/basic.py: FAILED (expected '42', got '${basic_out}', exit $example_rc)"; FAILED=1
fi
fanout_rc=0
fanout_out="$(cd "$PYTO" && python3 examples/shared_result_fanout.py 2>&1)" || fanout_rc=$?
printf '   $ python3 examples/shared_result_fanout.py -> %s\n' "$(printf '%s' "$fanout_out" | tail -1)"
if [ "$fanout_rc" -ne 0 ]; then
    echo "-- examples/shared_result_fanout.py: FAILED (exit $fanout_rc)"; echo "$fanout_out"; FAILED=1
elif ! printf '%s' "$fanout_out" | grep -q '"sharedResult": "fn:render-disc"'; then
    echo "-- examples/shared_result_fanout.py: FAILED (sharedResult fn:render-disc not printed)"; FAILED=1
fi
examples_ok=$([ "$example_rc" -eq 0 ] && [ "$fanout_rc" -eq 0 ] && [ "$basic_out" = "42" ] && echo OK || echo FAIL)
echo "-- examples: $examples_ok (2 scripts)"
SUMMARY+=("$(printf '%-28s %6s  %s' examples 2 "$examples_ok")")
echo

echo "== per-suite counts"
printf '%-28s %6s  %s\n' suite tests status
for line in "${SUMMARY[@]}"; do echo "$line"; done
echo
if [ "$FAILED" -ne 0 ]; then
    echo "SOME SUITES FAILED (logs in $LOG_DIR)"
    exit 1
fi
echo "ALL SUITES PASSED"
