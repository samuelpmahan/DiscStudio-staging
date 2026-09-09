#!/usr/bin/env bash
# check_land_refusals.sh: proves land.sh's early refusal paths hold their contract
# (pyto/LANDING.md:69-70, 116-117: "if it refuses, it says exactly why, and nothing
# has changed") without ever running check_all.sh or touching this repository.
#
# Builds a throwaway git repo under mktemp, copies land.sh into it (land.sh finds its
# own root from its own path, so it must live under <throwaway>/pyto/scripts to act on
# the throwaway tree instead of this one), and calls it three ways: no package name at
# all (usage, exit 2, no receipt); an unknown --from branch (refused, exit 1, a failed
# receipt, before any clean/scope check body runs the verifier); a dirty file outside
# --allow (refused, exit 1, a failed receipt, the file left exactly where it was).
# None of these paths ever reaches check_all.sh -- there isn't one in the throwaway
# repo, so if a refusal regressed into running it the failure would say so.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_ROOT="$(cd "$HERE/../.." && pwd)"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
mkdir -p "$REPO/pyto/scripts" "$REPO/pyto/experiments/landings"
cp "$HERE/land.sh" "$REPO/pyto/scripts/land.sh"
cat > "$REPO/pyto/BOARD.md" <<'EOF'
# Board

## Today

placeholder

## Lane 1
placeholder
EOF

before_real="$(git -C "$REAL_ROOT" status --porcelain --untracked-files=all)"

cd "$REPO"
git init -q
git config user.email test@example.com
git config user.name test
echo hello > tracked.txt
git add -A
git commit -q -m initial

fails=0
failed_count() { [ -d pyto/experiments/landings/failed ] && ls pyto/experiments/landings/failed | wc -l | tr -d ' ' || echo 0; }

# check <label> <expected exit> <must-contain text or ""> -- <cmd...>
check() {
  local label="$1" expect="$2" want="$3"; shift 3; shift # drop the --
  local out="$TMP/out-$label.txt" got=0
  "$@" >"$out" 2>&1 || got=$?
  if [ "$got" != "$expect" ]; then
    echo "FAIL $label: expected exit $expect, got $got"; cat "$out"; fails=$((fails + 1)); return
  fi
  if [ -n "$want" ] && ! grep -qF "$want" "$out"; then
    echo "FAIL $label: expected output to name \"$want\""; cat "$out"; fails=$((fails + 1)); return
  fi
  if grep -qi "check_all" "$out"; then
    echo "FAIL $label: reached check_all.sh (it does not exist in this throwaway repo)"; cat "$out"; fails=$((fails + 1)); return
  fi
  echo "ok  $label: exit $got"
}

# A refusal writes its board() line into the tracked BOARD.md before the receipt is
# written, leaving it modified-but-uncommitted; reset it after each check so the next
# refusal's scope check sees only the file that test introduces as dirty.
reset_board() { git checkout -q -- pyto/BOARD.md; }

# 1. No package name: usage line, exit 2, not a refusal so no receipt.
n0="$(failed_count)"
check no-args 2 "usage: land.sh" -- bash pyto/scripts/land.sh
[ "$(failed_count)" = "$n0" ] || { echo "FAIL no-args: a receipt was written for a bare usage error"; fails=$((fails + 1)); }

# 2. Unknown branch named with --from: refused, exit 1, a new failed receipt.
n1="$(failed_count)"
check unknown-branch 1 "no such branch: no-such-branch" -- bash pyto/scripts/land.sh unknownbranch --from no-such-branch
[ "$(failed_count)" -gt "$n1" ] || { echo "FAIL unknown-branch: no new failed receipt"; fails=$((fails + 1)); }
reset_board

# 3. Dirty file outside the allowed paths: refused, exit 1, a new failed receipt, the
#    file and the earlier commit both left exactly as they were.
echo intruder > outside.txt
n2="$(failed_count)"
check dirty-outside-allow 1 "dirty file outside allowed paths: outside.txt" -- bash pyto/scripts/land.sh dirtyoutside --allow onlypath/
[ "$(failed_count)" -gt "$n2" ] || { echo "FAIL dirty-outside-allow: no new failed receipt"; fails=$((fails + 1)); }
[ "$(cat outside.txt)" = "intruder" ] || { echo "FAIL dirty-outside-allow: the untracked file was disturbed"; fails=$((fails + 1)); }
[ -z "$(git status --porcelain -- tracked.txt)" ] || { echo "FAIL dirty-outside-allow: the committed file was touched"; fails=$((fails + 1)); }

latest="$(ls -t pyto/experiments/landings/failed/*.json | head -1)"
grep -q '"result": "failed"' "$latest" || { echo "FAIL: $latest is not a failed receipt"; fails=$((fails + 1)); }

after_real="$(git -C "$REAL_ROOT" status --porcelain --untracked-files=all)"
[ "$before_real" = "$after_real" ] || { echo "FAIL: the working tree this check started from changed"; fails=$((fails + 1)); }

if [ "$fails" -eq 0 ]; then
  echo "check_land_refusals: 3 refusal paths verified (usage, unknown branch, scope), no receipt for usage, check_all.sh never reached, starting tree untouched"
  exit 0
fi
echo "check_land_refusals: $fails check(s) failed"
exit 1
