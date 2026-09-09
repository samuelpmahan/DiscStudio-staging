#!/usr/bin/env bash
# Landing protocol, executable form. See pyto/LANDING.md.
#   pyto/scripts/land.sh <package> [--from <branch>] [--verify "<command>"] [--allow "<path> <path>..."] [--base <sha>] [--dry-run] [--message "<one line>"]
# --from: the candidate is a branch (a writer's prefixed copy of the tree, or an Astra hand-back).
#         It is merged into the working branch without committing; a conflict stops the landing
#         with nothing changed; the landing commit is the merge commit.
# --base: the commit the package started from. Checkpoint commits since then are part of the
#         candidate; the receipt lists every file changed since base, split into claimed (under
#         the allowed paths) and unclaimed (present, verified with the mixture, not this package's).
set -euo pipefail
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE" && git rev-parse --show-toplevel)"
if [ -f "$ROOT/pyto/pyproject.toml" ]; then
  PY="$ROOT/pyto"
  PYTO_MODE=1
else
  PY="$ROOT"
  PYTO_MODE=0
fi
cd "$ROOT"

PACKAGE="${1:-}"; shift || true
[ -n "$PACKAGE" ] || { echo "usage: land.sh <package> [--verify cmd] [--allow paths] [--base sha] [--dry-run] [--message line]" >&2; exit 2; }
VERIFY=""; ALLOW=""; DRY=0; MESSAGE=""; BASE=""; FROM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --verify) VERIFY="$2"; shift 2;;
    --allow) ALLOW="$2"; shift 2;;
    --base) BASE="$2"; shift 2;;
    --from) FROM="$2"; shift 2;;
    --dry-run) DRY=1; shift;;
    --message) MESSAGE="$2"; shift 2;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ID="${STAMP}-${PACKAGE//[^A-Za-z0-9._-]/_}"
if [ "$PYTO_MODE" -eq 1 ]; then
  LAND_DIR="$PY/experiments/landings"
  LAND_REL="pyto/experiments/landings/"
  BOARD="$PY/BOARD.md"
else
  LAND_DIR="$ROOT/.neat/landings"
  LAND_REL=".neat/landings/"
  BOARD="$ROOT/.neat/BOARD.md"
fi
WORK="$LAND_DIR/$ID"
BASE_SHA="$(git rev-parse "${BASE:-HEAD}")"
board() { # one plain line for the owner, newest first under "## Today" on pyto/BOARD.md
  "$PYTHON" - "$BOARD" "$1" "$PYTO_MODE" <<'PYEOF'
import sys, datetime
path, line, pyto_mode = sys.argv[1:4]
stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')
try:
    text = open(path).read()
except FileNotFoundError:
    if pyto_mode == '0':
        text = '# Neat Board\n\n## Today\n\nOne line per landing attempt, newest first, written by the landing script.\n'
    else:
        raise
marker = '## Today\n'
if marker not in text:
    if pyto_mode == '0':
        text = text.rstrip() + '\n\n' + marker + '\nOne line per landing attempt, newest first, written by the landing script.\n'
    else:
        text = text.replace('\n## Lane 1', '\n' + marker + '\nOne line per landing attempt, newest first, written by the landing script.\n\n\n## Lane 1', 1)
head, tail = text.split(marker, 1)
if '\n\n' in tail:
    intro, rest = tail.split('\n\n', 1)
    text = head + marker + intro + '\n\n- ' + stamp + ' ' + line + '\n' + rest
else:
    text = head + marker + tail.rstrip() + '\n\n- ' + stamp + ' ' + line + '\n'
open(path, 'w').write(text)
PYEOF
}
fail() { # reason
  if [ -n "$FROM" ] && git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then git merge --abort; fi
  board "**refused** \`$PACKAGE\`: $1"
  mkdir -p "$LAND_DIR/failed"
  "$PYTHON" - "$LAND_DIR/failed/$ID.json" "$PACKAGE" "$BASE_SHA" "$1" <<'EOF'
import json, sys, datetime
path, package, base, reason = sys.argv[1:5]
json.dump({"schema": "pyto-landing-receipt@1", "id": path.split('/')[-1][:-5], "package": package, "base_sha": base, "result": "failed", "reason": reason, "at": datetime.datetime.utcnow().isoformat() + "Z"}, open(path, "w"), indent=2)
EOF
  echo "LANDING FAILED: $1" >&2
  echo "failed receipt: $LAND_DIR/failed/$ID.json" >&2
  exit 1
}

# 0a. Two clones land into one branch (the owner's D:/ and the cloud), so MAIN must not be behind
#     origin: what the suites verify here must be what gets pushed.
UPSTREAM="$(git rev-parse --abbrev-ref HEAD)"
if git fetch -q origin "$UPSTREAM" 2>/dev/null && ! git merge-base --is-ancestor "origin/$UPSTREAM" HEAD 2>/dev/null; then
  fail "MAIN is behind origin/$UPSTREAM by $(git rev-list --count "HEAD..origin/$UPSTREAM") commit(s) (someone landed elsewhere); run: git pull --rebase origin $UPSTREAM  then land again"
fi

# 0b. A branch candidate: the main tree must be clean, then the branch is merged without committing.
if [ -n "$FROM" ]; then
  [ -z "$(git status --porcelain --untracked-files=all)" ] || fail "the tree is not clean; a branch can only land into a clean tree"
  git rev-parse -q --verify "$FROM^{commit}" >/dev/null || fail "no such branch: $FROM"
  [ -n "$BASE" ] || BASE_SHA="$(git merge-base HEAD "$FROM")"
  if ! git merge --no-commit --no-ff -q "$FROM" >/dev/null 2>&1; then
    fail "merge conflict with $FROM in: $(git diff --name-only --diff-filter=U | tr '\n' ' ')"
  fi
fi

# 1. Clean start: the dirty files are what this landing will commit; files committed since --base are
#    part of the candidate too (checkpoints never claim, landings do).
DIRTY="$(git status --porcelain --untracked-files=all | cut -c4- | sed 's/.* -> //' | grep -v "^$LAND_REL" || true)"
SINCE="$(git diff --name-only "$BASE_SHA" HEAD)"
CHANGED="$(printf '%s\n%s\n' "$SINCE" "$DIRTY" | grep -v '^$' | sort -u || true)"
[ -n "$CHANGED" ] || fail "nothing to land: the tree is clean and nothing changed since $BASE_SHA"

# 2. Scope. A dirty file outside the allowed paths stops the landing (it would be swept into this
#    commit). A file already committed since base but outside the paths is recorded as unclaimed.
in_scope() { # path -> 0 if under an allowed path
  local f="$1" a; [ -n "$ALLOW" ] || return 0
  for a in $ALLOW; do case "$f" in "$a"*) return 0;; esac; done; return 1
}
while IFS= read -r f; do
  [ -n "$f" ] || continue
  in_scope "$f" || fail "dirty file outside allowed paths: $f  (someone else's candidate; when its writer is done, park it with: git stash push -u -m parked -- $f  then land, then git stash pop)"
done <<< "$DIRTY"

# 3. Verify.
mkdir -p "$WORK"
VERIFY_EXIT=0
if [ -n "$VERIFY" ]; then
  echo "== verifier: $VERIFY"
  bash -c "$VERIFY" > "$WORK/verifier.txt" 2>&1 || VERIFY_EXIT=$?
  tail -20 "$WORK/verifier.txt"
  [ $VERIFY_EXIT -eq 0 ] || fail "verifier exited $VERIFY_EXIT (see $WORK/verifier.txt)"
fi
echo "== check_all"
CHECK_EXIT=0
if [ "$PYTO_MODE" -eq 1 ]; then
  bash "$PY/scripts/check_all.sh" > "$WORK/check_all.txt" 2>&1 || CHECK_EXIT=$?
  tail -12 "$WORK/check_all.txt"
  [ $CHECK_EXIT -eq 0 ] || fail "check_all exited $CHECK_EXIT (see $WORK/check_all.txt)"
else
  echo "== plain mode: packet verifier is the suite"
  : > "$WORK/check_all.txt"
fi

# 4. Record.
"$PYTHON" - "$WORK/receipt.json" "$ID" "$PACKAGE" "$BASE_SHA" "$VERIFY" "$WORK" "$DRY" "$ALLOW" "$CHANGED" "$PYTO_MODE" <<'EOF'
import json, sys, subprocess, hashlib, os, datetime
path, lid, package, base, verify, work, dry, allow, changed_list, pyto_mode = sys.argv[1:11]
allowed = allow.split()
root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
files = [f for f in changed_list.splitlines() if f.strip()]
def sha(p):
    try: return hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except Exception: return None
def entry(f):
    p = os.path.join(root, f)
    return {"path": f, "bytes": os.path.getsize(p) if os.path.exists(p) else None, "sha256": sha(p)}
files = [f for f in files if not f.startswith('pyto/experiments/landings/')]
claimed = [entry(f) for f in files if not allowed or any(f.startswith(a) for a in allowed)]
unclaimed = [entry(f) for f in files if allowed and not any(f.startswith(a) for a in allowed)]
counts = {}
for line in open(os.path.join(work, 'check_all.txt')):
    parts = line.split()
    if len(parts) >= 3 and parts[-1] == 'OK' and parts[-2].isdigit(): counts[' '.join(parts[:-2])] = int(parts[-2])
receipt = {"schema": "pyto-landing-receipt@1", "id": lid, "package": package, "base_sha": base, "result": "verified",
           "verifier": {"command": verify or None, "exit": 0 if verify else None, "output_sha256": sha(os.path.join(work, 'verifier.txt')) if verify else None},
           "check_all": {"exit": 0, "output_sha256": sha(os.path.join(work, 'check_all.txt')), "counts": counts},
           "claimed": claimed, "unclaimed": unclaimed, "landed_by": os.environ.get('PYTO_LANDER', 'session'), "at": datetime.datetime.utcnow().isoformat() + 'Z',
           "result_sha": None, "note": "result_sha is filled by the next landing; a receipt cannot contain its own commit"}
if pyto_mode == '0':
    receipt['check_all'] = None
    receipt['note'] = 'plain mode: suite is the packet Verify command' if verify else 'plain mode: no verification command was requested'
json.dump(receipt, open(path, 'w'), indent=2)
# fill the previous landing's result_sha (the commit that carried its receipt)
land_dir = os.path.dirname(work)
prev = sorted(d for d in os.listdir(land_dir) if os.path.isdir(os.path.join(land_dir, d)) and d != os.path.basename(work) and d != 'failed')
if prev and dry != '1':
    p = os.path.join(land_dir, prev[-1], 'receipt.json')
    if os.path.exists(p):
        r = json.load(open(p))
        if r.get('result_sha') is None:
            r['result_sha'] = subprocess.run(['git', 'log', '-1', '--format=%H', '--', p], capture_output=True, text=True).stdout.strip() or None
            json.dump(r, open(p, 'w'), indent=2)
print(json.dumps({k: receipt[k] for k in ('id', 'package', 'base_sha', 'result')} | {"claimed": len(claimed), "unclaimed": len(unclaimed)}))
EOF

if [ $DRY -eq 1 ]; then
  echo "== dry run: would commit $(printf '%s\n' "$DIRTY" | grep -c . || true) dirty files and the receipt as land($PACKAGE)"; rm -rf "$WORK"
  if [ -n "$FROM" ]; then git merge --abort; fi
  exit 0
fi

# 5. Commit and push. Only the files that were dirty at the start; if the tree moved meanwhile, stop.
NOW="$(git status --porcelain --untracked-files=all | cut -c4- | sed 's/.* -> //' | grep -v "^$LAND_REL" || true)"
if [ "$(printf '%s\n' "$NOW" | grep -v '^$' | sort -u)" != "$(printf '%s\n' "$DIRTY" | grep -v '^$' | sort -u)" ]; then
  delta="$(diff <(printf '%s\n' "$DIRTY" | grep -v '^$' | sort -u) <(printf '%s\n' "$NOW" | grep -v '^$' | sort -u) | grep '^[<>]' | sed 's/^</ gone:/; s/^>/ new:/' | tr '\n' ' ')"
  fail "the tree changed while the suites ran (someone is writing); nothing committed. Changed:$delta"
fi
while IFS= read -r f; do [ -n "$f" ] && git add -A -- "$f"; done <<< "$DIRTY"
git add -A -- "$LAND_DIR"
LINE="${MESSAGE:-verified candidate}"
board "**landed** \`$PACKAGE\`: $LINE ($(printf '%s\n' "$CHANGED" | grep -c . || true) files since ${BASE_SHA:0:7}, suites green, receipt $ID)"
git add -A -- "$BOARD"
if [ "$PYTO_MODE" -eq 1 ]; then
  RECEIPT_LABEL="pyto/experiments/landings/$ID/receipt.json"
else
  RECEIPT_LABEL=".neat/landings/$ID/receipt.json"
fi
git commit -q -m "land($PACKAGE): $LINE

Landing receipt: $RECEIPT_LABEL

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014pqrhfQfjpSAYTvH8j3y93"
if ! git push -q -u origin "$UPSTREAM" 2>/dev/null; then
  echo "LANDED LOCALLY $(git rev-parse --short HEAD) $PACKAGE, but the push was rejected: someone landed on origin while the suites ran." >&2
  echo "Run: git pull --rebase origin $UPSTREAM && bash pyto/scripts/check_all.sh && git push -u origin $UPSTREAM   (the receipt's base is what was verified here; the rebased result is verified by that check_all)" >&2
  exit 1
fi
echo "LANDED $(git rev-parse --short HEAD) $PACKAGE"
if [ -n "$FROM" ]; then
  wt="$(git worktree list --porcelain | awk -v b="refs/heads/$FROM" '$1=="worktree"{w=$2} $1=="branch"&&$2==b{print w}')"
  [ -z "$wt" ] || { git worktree remove --force "$wt" && echo "removed copy $wt"; }
  case "$FROM" in
    origin/*) echo "remote branch stays until you run: git push origin --delete ${FROM#origin/}";;
    *) git branch -d "$FROM" >/dev/null 2>&1 && echo "deleted local branch $FROM" || true;;
  esac
fi
