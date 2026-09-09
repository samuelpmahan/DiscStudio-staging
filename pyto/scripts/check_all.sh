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
# 18 pre-tournament + 8 (test_paint_families) + 11 (test_card_render), added when
# the art tournament promoted three families and two card renderers, + 24
# (test_art_registry) added when the owner directive registered every retained
# family and card renderer as a Calculation too (37 -> 61).
EXPECT_CONSUMER="${EXPECT_CONSUMER:-61}"
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
art_demo_rc=0
art_demo_out="$(cd "$PYTO" && python3 examples/art_registry_demo.py 2>&1)" || art_demo_rc=$?
printf '   $ python3 examples/art_registry_demo.py -> %s\n' "$(printf '%s' "$art_demo_out" | tail -1)"
if [ "$art_demo_rc" -ne 0 ]; then
    echo "-- examples/art_registry_demo.py: FAILED (exit $art_demo_rc)"; echo "$art_demo_out"; FAILED=1
elif ! printf '%s' "$art_demo_out" | grep -q '"sharedResult": "fn:render-art"'; then
    echo "-- examples/art_registry_demo.py: FAILED (sharedResult fn:render-art not printed)"; FAILED=1
fi
examples_ok=$([ "$example_rc" -eq 0 ] && [ "$fanout_rc" -eq 0 ] && [ "$art_demo_rc" -eq 0 ] \
    && [ "$basic_out" = "42" ] && echo OK || echo FAIL)
echo "-- examples: $examples_ok (3 scripts)"
SUMMARY+=("$(printf '%-28s %6s  %s' examples 3 "$examples_ok")")
echo

# 6. art registry index: regenerate ART-REGISTRY.md and require it to match
# what is already committed -- a stale index (art_registry.py or RESULTS.md
# changed and nobody regenerated the doc) fails the check.
ART_REGISTRY_MD="$PYTO/consumers/discstudio-card/ART-REGISTRY.md"
echo "== suite: art-registry-md  (cwd $PYTO/consumers/discstudio-card)"
gen_rc=0
gen_out="$(cd "$PYTO/consumers/discstudio-card" && python3 scripts/generate_art_registry_md.py 2>&1)" || gen_rc=$?
echo "   \$ python3 scripts/generate_art_registry_md.py -> $gen_out"
if [ "$gen_rc" -ne 0 ]; then
    echo "-- art-registry-md: FAILED (generator exited $gen_rc)"; FAILED=1; art_registry_ok=FAIL
elif ! (cd "$PYTO" && git diff --quiet -- "$ART_REGISTRY_MD"); then
    echo "-- art-registry-md: FAILED (ART-REGISTRY.md is stale -- regenerate and commit it)"
    (cd "$PYTO" && git diff --stat -- "$ART_REGISTRY_MD")
    FAILED=1; art_registry_ok=FAIL
else
    echo "-- art-registry-md: OK (regenerated, matches committed ART-REGISTRY.md)"
    art_registry_ok=OK
fi
SUMMARY+=("$(printf '%-28s %6s  %s' art-registry-md - "$art_registry_ok")")
echo

# 7. viewer suite: the Tick viewer is JavaScript ("JS is first class",
# research/ULTRACODE-WEEK.md Reframing 4), so its Node 22 tests are a suite here
# and not an optional extra. A missing node fails loudly with a named reason
# rather than passing silently.
EXPECT_VIEWER="${EXPECT_VIEWER:-77}"
echo "== suite: viewer  (cwd $PYTO/viewer)"
viewer_ok=FAIL
viewer_count="?"
if ! command -v node > /dev/null 2>&1; then
    echo "-- viewer: FAILED (node is not on PATH; the Tick viewer tests cannot run)"; FAILED=1
else
    echo "   \$ node --test test/*.test.mjs   ($(node --version))"
    viewer_log="$LOG_DIR/viewer.log"
    viewer_rc=0
    (cd "$PYTO/viewer" && node --test test/*.test.mjs) > "$viewer_log" 2>&1 || viewer_rc=$?
    cat "$viewer_log"
    viewer_count="$(grep -E '^# pass [0-9]+' "$viewer_log" | tail -1 | sed -E 's/^# pass ([0-9]+).*/\1/' || true)"
    viewer_count="${viewer_count:-?}"
    viewer_fail="$(grep -E '^# fail [0-9]+' "$viewer_log" | tail -1 | sed -E 's/^# fail ([0-9]+).*/\1/' || true)"
    if [ "$viewer_rc" -ne 0 ] || [ "${viewer_fail:-1}" != "0" ]; then
        echo "-- viewer: FAILED (exit $viewer_rc, passed $viewer_count, failed ${viewer_fail:-?})"; FAILED=1
    elif [ "$viewer_count" != "$EXPECT_VIEWER" ]; then
        echo "-- viewer: FAILED (expected exactly $EXPECT_VIEWER tests, got $viewer_count)"; FAILED=1
    else
        echo "-- viewer: OK (ran $viewer_count)"; viewer_ok=OK
    fi
fi
SUMMARY+=("$(printf '%-28s %6s  %s' viewer "$viewer_count" "$viewer_ok")")
echo

# 8. the record round trip: RECORD.md is a contract between two runtimes, so it
# is checked from both sides. viewer/test/record_schema.py is a Python
# validator written from RECORD.md independently of adapters.js; the suite runs
# every JavaScript adapter's output through it, and asserts the two validators
# refuse the same mutations at the same paths. It needs node (it drives the
# adapters), which the viewer suite above has already required.
EXPECT_RECORD_SCHEMA="${EXPECT_RECORD_SCHEMA:-19}"
run_suite viewer-record-schema "$PYTO/viewer" python3 -m unittest discover -s test -p 'test_*.py' -v
expect_count viewer-record-schema "$EXPECT_RECORD_SCHEMA"

echo "== per-suite counts"
printf '%-28s %6s  %s\n' suite tests status
for line in "${SUMMARY[@]}"; do echo "$line"; done
echo
if [ "$FAILED" -ne 0 ]; then
    echo "SOME SUITES FAILED (logs in $LOG_DIR)"
    exit 1
fi
echo "ALL SUITES PASSED"
