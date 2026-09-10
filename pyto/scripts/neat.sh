#!/usr/bin/env bash
# neat: one MAIN, one EXP. The caveman version of landing (pyto/LANDING.md, first section).
#
#   neat new "<intent>" [--verify "<cmd>"] [--allow "<paths>"]   EXP/<id>: a copy of MAIN to work in
#   neat pack <id>            commit the work, write the packet and the hand-off, push exp/<id>
#   neat show <id>            print the hand-off (what a fresh agent gets)
#   neat drop <id> <path>...  put those files back to the starting point, repack
#   neat land <id>            merge into MAIN, verify, receipt, commit, push; EXP/<id> goes away
#   neat land <id> --from <url-or-remote-name> <branch> [--verify "<cmd>"] [--allow "<paths>"]   the same landing for a desk in another repository; --verify/--allow grade it with this repository's brief instead of the packet's
#   neat kill <id>            abandon: EXP/<id> goes away, nothing lands; exp/<id> is kept (nothing is deleted)
#   neat undo <id>            take a landed task back out of MAIN: revert, verify, receipt, push
#   neat update <id>          bring MAIN's newer commits into EXP/<id> (a conflict names the files and stops)
#   neat list                 every experiment and its state
#   neat selftest             build a scratch repo in a temp dir and run new, pack, land, undo there
#   neat walk [N | --page [out]]   the walk: the index of landings, one step as text, or the page (default ./walk.html)
#   neat diff <a.json> <b.json> --store <seed.json> --registry <module:attr> [--label-a T] [--label-b T]
#                             two PQL documents' difference, computed before it is shown: px.exp.blok.diff.<a>.<b>
#                             under pyto/experiments/review/diffs, with both documents' run records beside it
#
# The board says when a task starts (neat new) and when one is killed, not only when one lands, so the
# owner sees what is coming; those lines go through land.sh --note (commit and push, no receipt).
# MAIN is the clone itself. EXP/<id> is a git worktree on branch exp/<id> (ignored by git in MAIN).
# In a pyto repository (pyto/pyproject.toml is there) the copy gets its own .venv so the suite in
# EXP/<id> tests EXP/<id>'s kernel, not MAIN's, and the packet lives at pyto/experiments/tasks/<id>/;
# in any other repository there is no venv and the packet lives at .neat/tasks/<id>/. Either way the
# packet travels with the branch and lands with the candidate. IDs are plain numbers from 0.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
PY="$ROOT/pyto"
# The interpreter, in order: $PYTHON if set; the repository's own .venv (Linux or Windows layout);
# then python3 or python on PATH. A venv is what lets an isolated child (-I) import pyto on Windows,
# where a Store Python's editable install lands in the user site that -I ignores. The repository is
# wherever git says it is, so this works when the scripts do not sit in pyto/scripts/.
if [ -z "${PYTHON:-}" ]; then
  for _c in "$ROOT/.venv/bin/python" "$ROOT/.venv/Scripts/python.exe"; do
    [ -x "$_c" ] && PYTHON="$_c" && break
  done
fi
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
EXP="$ROOT/EXP"
if [ -f "$ROOT/pyto/pyproject.toml" ]; then
  PYTO_MODE=1
  TASKS="pyto/experiments/tasks"
  LAND_REL="pyto/experiments/landings/"
  BOARD_REL="pyto/BOARD.md"
else
  PYTO_MODE=0
  TASKS=".neat/tasks"
  LAND_REL=".neat/landings/"
  BOARD_REL=".neat/BOARD.md"
fi
BRANCH="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
# A remote spelling can carry a password (https://user:token@host/...); it is stripped everywhere it
# is printed: the hand-off page, and the board line of a landing that came from another repository.
strip_creds() { sed 's#https://[^@]*@#https://#'; }
URL="$(git -C "$ROOT" remote get-url origin 2>/dev/null | strip_creds || echo '<origin>')"
cmd="${1:-}"; shift || true

die() { echo "neat: $*" >&2; exit 1; }
usage() { sed -n '4,18p' "${BASH_SOURCE[0]}" | sed 's/^#  *//'; exit 2; }
field() { # <name> <file>  -> the value after "<name>: ", empty when the line is missing
  # (grep exits 1 on no match; under set -e -o pipefail that used to end the script with no message)
  { grep -m1 "^$1: " "$2" || true; } | sed "s/^$1: //"
}
next_id() { # the highest id seen anywhere: local copies, landed packets, and exp/* branches here or on origin
  local max=-1 d n
  git -C "$ROOT" fetch -q origin 'refs/heads/exp/*:refs/remotes/origin/exp/*' 2>/dev/null || true
  for d in "$EXP"/*/ "$ROOT/$TASKS"/*/; do
    [ -d "$d" ] || continue; n="$(basename "$d")"
    case "$n" in ''|*[!0-9]*) continue;; esac
    [ "$n" -gt "$max" ] && max="$n"
  done
  # landed tasks on origin's copy of this branch count too: another clone may have landed since we pulled
  for n in $(git -C "$ROOT" for-each-ref --format='%(refname:short)' 'refs/heads/exp/*' 'refs/remotes/origin/exp/*' | sed 's#.*exp/##') $(git -C "$ROOT" ls-tree --name-only "origin/$BRANCH:$TASKS" 2>/dev/null); do
    case "$n" in ''|*[!0-9]*) continue;; esac
    [ "$n" -gt "$max" ] && max="$n"
  done
  # landing receipts are never deleted, so an undone or killed task's number stays taken:
  # <stamp>-task-N/ and failed/<stamp>-task-N.json, and undo-task-N likewise
  for n in $(ls "$ROOT/$LAND_REL" "$ROOT/$LAND_REL/failed" 2>/dev/null | sed -n 's/.*-task-\([0-9][0-9]*\)\(\.json\)\{0,1\}$/\1/p'); do
    [ "$n" -gt "$max" ] && max="$n"
  done
  echo $((max + 1))
}
venv_python() { # <id>
  if [ -x "$EXP/$1/.venv/bin/python" ]; then echo "$EXP/$1/.venv/bin/python"
  elif [ -x "$EXP/$1/.venv/Scripts/python.exe" ]; then echo "$EXP/$1/.venv/Scripts/python.exe"
  else echo "$PYTHON"; fi
}
packet_of() { echo "$EXP/$1/$TASKS/$1/packet.md"; }
hostpath() { # Git Bash on Windows: pip and python want D:\... not /d/...; elsewhere the path is unchanged
  if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s\n' "$1"; fi
}
need_exp() { [ -d "$EXP/$1" ] || die "no experiment EXP/$1 (neat list)"; }
receipt_of() { # <package> -> the newest committed receipt for it, empty when there is none
  # Landing directories are <stamp>-<package>, and the stamp sorts the same way it ticks, so the
  # last glob match is the newest. The stamp is spelled out rather than globbed with * so that
  # task-0's receipts are not mixed up with undo-task-0's.
  local d last=""
  for d in "$ROOT/$LAND_REL"????????T??????Z-"$1"/; do
    [ -f "$d/receipt.json" ] && last="$d/receipt.json"
  done
  printf '%s\n' "$last"
}
score_of() { # <receipt path> -> "<passed>/<total>", or "-" when the verifier printed no score
  local f="${1:-}" p t
  [ -n "$f" ] && [ -f "$f" ] || { echo "-"; return 0; }
  p="$(sed -n 's/.*"passed"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$f" | head -n 1)"
  t="$(sed -n 's/.*"total"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$f" | head -n 1)"
  if [ -n "$p" ] && [ -n "$t" ]; then echo "$p/$t"; else echo "-"; fi
}
status_without_bookkeeping() { # MAIN's status minus the landing script's own leavings: receipts and the board
  local line path
  while IFS= read -r line; do
    path="${line:3}"; path="${path##* -> }"
    case "$path" in "$LAND_REL"*|"$BOARD_REL") continue;; esac
    printf '%s\n' "$line"
  done < <(git -C "$ROOT" status --porcelain --untracked-files=all)
}

cmd_new() {
  local intent="${1:-}"; shift || true
  [ -n "$intent" ] || die 'new needs an intent: neat new "what you want"'
  local verify="none" allow="any"
  while [ $# -gt 0 ]; do case "$1" in --verify) verify="$2"; shift 2;; --allow) allow="$2"; shift 2;; *) die "unknown option $1";; esac; done
  local id base subject
  id="$(next_id)"; base="$(git -C "$ROOT" rev-parse HEAD)"; subject="$(git -C "$ROOT" log -1 --format=%s)"
  mkdir -p "$EXP"
  git -C "$ROOT" worktree add -q "$EXP/$id" -b "exp/$id" HEAD
  # Reserve the id everywhere at once: another clone computing its next id sees this branch on origin.
  git -C "$ROOT" push -q -u origin "exp/$id" 2>/dev/null && echo "  reserved exp/$id on origin" || echo "  (origin not reachable; the id is reserved only here until the first push)"
  mkdir -p "$EXP/$id/$TASKS/$id"
  cat > "$(packet_of "$id")" <<EOF
# Task $id

Intent: $intent
Starting point: $base ($subject)
Verify: $verify
Allow: $allow
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
\`{?} Label: description\`, and leaves the decision to the owner. Empty means nothing was unsure.)
EOF
  bash "$HERE/land.sh" --note "**started** \`task-$id\`: $intent (copy EXP/$id; it lands only on green, with a receipt, or is killed)"
  echo "Task $id: EXP/$id is a copy of MAIN at ${base:0:7}. Work there."
  if [ "$PYTO_MODE" -eq 1 ]; then
    echo "  making its python (EXP/$id/.venv) so the suite there tests that copy's kernel ..."
    "$PYTHON" -m venv --system-site-packages "$EXP/$id/.venv"
    "$(venv_python "$id")" -m pip install -q --no-build-isolation -e "$(hostpath "$EXP/$id/pyto")[drawing]" 2>&1 | grep -v "^$" | tail -2 || true
    if "$(venv_python "$id")" -c 'import os, sys, pyto; sys.exit(0 if os.path.realpath(pyto.__file__).startswith(os.path.realpath(sys.argv[1])) else 1)' "$(hostpath "$EXP/$id")" 2>/dev/null
    then echo "  its python imports pyto from EXP/$id"
    else die "EXP/$id/.venv does not import pyto from EXP/$id; the suite there would test MAIN's kernel. Fix the install before working."
    fi
  else
    echo "  plain repository: no venv or pip install"
  fi
  echo "  done. When the work is done: bash pyto/scripts/neat.sh pack $id"
}

write_packet_and_handoff() { # <id> <vexit|-> <cexit>  (evidence files already written)
  local id="$1" vexit="$2" cexit="$3" wt="$EXP/$1"
  "$PYTHON" - "$wt" "$id" "$TASKS" "$vexit" "$cexit" "$BRANCH" "$URL" <<'PYEOF'
import os, re, subprocess, sys
wt, tid, tasks, vexit, cexit, branch, url = sys.argv[1:8]
tdir = os.path.join(wt, tasks, tid); packet = os.path.join(tdir, 'packet.md')
text = open(packet, encoding='utf-8').read()
f = lambda name: re.search(r'^%s: (.*)$' % name, text, re.M).group(1)
intent, start, verify, allow = f('Intent'), f('Starting point'), f('Verify'), f('Allow')
base = start.split()[0]
unc = text.split('## Uncertain', 1)[1].strip() if '## Uncertain' in text else ''
git = lambda *a: subprocess.run(['git', '-C', wt, *a], capture_output=True, text=True).stdout
# After `neat update` merged MAIN into the copy, the candidate is what the copy adds beyond MAIN
# as it stands, never MAIN's own commits: diff from the merge base with the working branch.
merge_base = git('merge-base', 'HEAD', branch).strip() or base
base = merge_base
stat = git('diff', '--stat', base, 'HEAD', '--', '.', ':!' + tasks).strip()
names = [l for l in git('diff', '--name-status', base, 'HEAD', '--', '.', ':!' + tasks).splitlines() if l.strip()]
cand = '\n'.join('- ' + l.replace('\t', '  ') for l in names) or '- (nothing changed)'
counts = ''
try:
    lines = open(os.path.join(tdir, 'evidence', 'check_all.txt'), encoding='utf-8', errors='replace').read().splitlines()
    i = next((k for k, l in enumerate(lines) if l.startswith('suite ')), None)
    counts = '\n'.join('    ' + l for l in lines[i:i + 12]) if i is not None else '    ' + (lines[-1] if lines else '')
    last = next((l for l in reversed(lines) if l.strip()), '')
except FileNotFoundError:
    last = 'not run'
ver = 'none beyond the suite' if verify == 'none' else '`%s` exit %s (evidence/verify.txt)' % (verify, vexit)
evidence = ('- verify: %s\n- suite: `bash pyto/scripts/check_all.sh` exit %s, last line: %s (evidence/check_all.txt)\n%s' % (ver, cexit, last, counts))
new_packet = ('# Task %s\n\nIntent: %s\nStarting point: %s\nVerify: %s\nAllow: %s\nCandidate: %d files, see below\nEvidence: suite exit %s, see below\n\n## Candidate\n\n%s\n\n```\n%s\n```\n\n## Evidence\n\n%s\n\n## Uncertain\n\n%s\n'
              % (tid, intent, start, verify, allow, len(names), cexit, cand, stat or '(no diff)', evidence, unc))
open(packet, 'w', encoding='utf-8', newline='\n').write(new_packet)
handoff = f'''# Task {tid}: {intent}

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Stop here first (the owner's rule)

Read this page, `pyto/BOARD.md`, and the packet. No fourth file yet. Then write the one question
you would answer by reading another hundred thousand tokens of code, and ask the owner instead.
His answer is worth more than the reading: the last session that read everything first was
confidently wrong about half of it, and one sentence from him undid each wrong half. The answer
goes on `pyto/questions.md` verbatim, as `{{?}} Label: ...` with his words, so the next agent starts
one stupid question deeper. Only then read further and do the work below.

## Get the code (once)

```
git clone -b {branch} {url} DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/{tid}
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/{tid}:{tasks}/{tid}/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff {base[:7]} origin/exp/{tid} -- . ':!{tasks}'   # the candidate itself, as a diff
```

## Why this repository is worth twenty minutes

pyto is a Python transfer of a design the owner proved three times in JavaScript and TypeScript
(ChainSpot, ChessLab, EmbodiedWumpusWorld): a store of named values (PxC), pure functions over them
(Calculations), and a program that names which functions run in which order (a PCR, made of Ticks).
Every run leaves receipts: what each function read and wrote, how long it took, and a digest of its
source. From receipts you get three things for free: a cache (same inputs and digest, skip the call,
also across processes), a replay that verifies a shipped record in a fresh process, and a per-Tick
view of what the algorithm used. The founding need is the last one: the owner's course-map parser
had to fit five seconds on a phone, and nothing it used was visible. pyto is the workshop where that
visibility is designed before it is stripped for speed. JavaScript is first class; Python is where
the design is checked.

Do not take that from this page. In two minutes:

```
bash pyto/scripts/check_all.sh                                        # nine suites, ~600 tests
python pyto/experiments/grouped-ablation/run_cached.py --out /tmp/hit  # a miss, then two hits, one from a fresh process
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /tmp/hit/ticks.html
```

The tests were checked by mutation (each guards a specific line). The fixtures for the JavaScript
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{{?}} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

{intent}

## Starting point

{start}. MAIN may have moved since: `git log --oneline {base[:7]}..origin/{branch}` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

{cand}

```
{stat or '(no diff)'}
```

## Evidence

{evidence}

## Uncertain

{unc or '(nothing was marked unsure)'}

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop {tid} <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land {tid}`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-{tid}): {intent}`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
'''
open(os.path.join(tdir, 'HANDOFF.md'), 'w', encoding='utf-8', newline='\n').write(handoff)
print('packet: %s/packet.md  hand-off: %s/HANDOFF.md  candidate: %d files' % (os.path.relpath(tdir, wt), os.path.relpath(tdir, wt), len(names)))
PYEOF
}

cmd_pack() {
  local id="${1:-}"; [ -n "$id" ] || usage; need_exp "$id"
  local wt="$EXP/$id" packet vpy verify vexit=- cexit intent
  packet="$(packet_of "$id")"; vpy="$(venv_python "$id")"
  intent="$(field Intent "$packet")"; verify="$(field Verify "$packet")"
  [ -n "$intent" ] || die "task $id: the packet has no Intent line ($TASKS/$id/packet.md); the header above '## Uncertain' is neat's, restore it from the branch's first commit (git show \$(git -C \"$wt\" rev-list --max-parents=0 exp/$id | tail -1):$TASKS/$id/packet.md)"
  [ -n "$verify" ] || die "task $id: the packet has no Verify line ($TASKS/$id/packet.md); write one (a command that exits 0, or the word none) and pack again"
  git -C "$wt" add -A
  git -C "$wt" commit -q -m "exp/$id: $intent" 2>/dev/null || true
  mkdir -p "$wt/$TASKS/$id/evidence"
  if [ "$verify" != "none" ]; then
    echo "== verify: $verify"
    vexit=0; (cd "$wt" && PYTHON="$vpy" bash -c "$verify") > "$wt/$TASKS/$id/evidence/verify.txt" 2>&1 || vexit=$?
    echo "   exit $vexit"
  fi
  echo "== suite in EXP/$id (python: $vpy)"
  cexit=0
  if [ "$PYTO_MODE" -eq 1 ]; then
    (cd "$wt" && PYTHON="$vpy" bash "$wt/pyto/scripts/check_all.sh") > "$wt/$TASKS/$id/evidence/check_all.txt" 2>&1 || cexit=$?
  elif [ "$verify" = "none" ]; then
    echo "suite skipped (Verify: none)" > "$wt/$TASKS/$id/evidence/check_all.txt"
  else
    (cd "$wt" && PYTHON="$vpy" bash -c "$verify") > "$wt/$TASKS/$id/evidence/check_all.txt" 2>&1 || cexit=$?
  fi
  tail -12 "$wt/$TASKS/$id/evidence/check_all.txt" | sed 's/^/   /'
  write_packet_and_handoff "$id" "$vexit" "$cexit"
  git -C "$wt" add -A
  git -C "$wt" commit -q -m "exp/$id: packet (suite exit $cexit)" 2>/dev/null || true
  if git -C "$wt" push -q -u origin "exp/$id" 2>/dev/null; then echo "pushed exp/$id (a fresh agent anywhere can fetch it)"; else echo "not pushed (no remote reachable); the packet is committed on exp/$id"; fi
  echo "next: bash pyto/scripts/neat.sh show $id   |   bash pyto/scripts/neat.sh land $id"
}

cmd_show() {
  local id="${1:-}"; [ -n "$id" ] || usage
  if [ -f "$EXP/$id/$TASKS/$id/HANDOFF.md" ]; then cat "$EXP/$id/$TASKS/$id/HANDOFF.md"
  elif [ -f "$EXP/$id/$TASKS/$id/packet.md" ]; then cat "$EXP/$id/$TASKS/$id/packet.md"; echo; echo "(not packed yet: bash pyto/scripts/neat.sh pack $id)"
  elif [ -f "$ROOT/$TASKS/$id/HANDOFF.md" ]; then echo "(landed)"; cat "$ROOT/$TASKS/$id/HANDOFF.md"
  else die "no task $id"; fi
}

cmd_drop() {
  local id="${1:-}"; shift || true; [ -n "$id" ] && [ $# -gt 0 ] || usage; need_exp "$id"
  local wt="$EXP/$id" base p
  base="$(field 'Starting point' "$(packet_of "$id")" | cut -d' ' -f1)"
  for p in "$@"; do
    if git -C "$wt" cat-file -e "$base:$p" 2>/dev/null; then git -C "$wt" checkout -q "$base" -- "$p"; echo "back to the starting point: $p"
    else git -C "$wt" rm -q -f -- "$p" 2>/dev/null || rm -f "$wt/$p"; echo "removed (new in the candidate): $p"; fi
  done
  cmd_pack "$id"
}

drop_from_ref() { # the temporary ref a --from landing fetched into, on success and on refusal
  [ -n "${1:-}" ] || return 0
  git -C "$ROOT" update-ref -d "$1" 2>/dev/null || true
}

cmd_land() {
  local id="${1:-}"; [ -n "$id" ] || usage; shift || true
  local ref="exp/$id" packet base verify allow intent moved
  # `neat land <id> --from <url-or-remote-name> <branch>`: the desk lives in another repository (a
  # student's own repo; sharing is a landing into the class repo). Fetch that branch, land it from a
  # ref named by id, and touch nothing else there: the desk's branch is its owner's.
  local remote="" rbranch="" shown="" tmpref="" over_verify="" over_allow="" graded=0
  if [ "${1:-}" = "--from" ]; then
    remote="${2:-}"; rbranch="${3:-}"
    { [ -n "$remote" ] && [ -n "$rbranch" ]; } || die "land --from needs both a remote and a branch: neat land $id --from <url-or-remote-name> <branch>"
    shift 3
    # The landing repository may grade the desk with its own brief: --verify and --allow replace the
    # incoming packet's Verify and Allow for this landing (a class repo's tests are the real grade;
    # a desk's own Verify may name files only that desk has). The packet itself lands as it was.
    while [ $# -gt 0 ]; do
      case "$1" in
        --verify) over_verify="${2:-}"; [ -n "$over_verify" ] || die "land --verify needs a command: neat land $id --from <url-or-remote-name> <branch> --verify \"<cmd>\""; graded=1; shift 2;;
        --allow) over_allow="${2:-}"; [ -n "$over_allow" ] || die "land --allow needs one or more paths: neat land $id --from <url-or-remote-name> <branch> --allow \"<paths>\""; graded=1; shift 2;;
        *) break;;
      esac
    done
  fi
  [ $# -eq 0 ] || die "unknown option $1  (neat land <id> [--from <url-or-remote-name> <branch> [--verify \"<cmd>\"] [--allow \"<paths>\"]])"
  if [ -n "$remote" ]; then
    shown="$(printf '%s' "$remote" | strip_creds)"
    # refs/neat/from/<id>, never exp/<id>: task 0 here and task 0 on the desk are different tasks.
    tmpref="refs/neat/from/$id"
    git -C "$ROOT" fetch -q "$remote" "$rbranch" || die "cannot fetch $rbranch from $shown (a URL, a path, or a configured remote name; a path is read from $ROOT)"
    git -C "$ROOT" update-ref "$tmpref" "$(git -C "$ROOT" rev-parse FETCH_HEAD)"
    ref="$tmpref"
  elif ! git -C "$ROOT" rev-parse -q --verify "refs/heads/exp/$id" >/dev/null; then
    git -C "$ROOT" fetch -q origin "exp/$id" 2>/dev/null || die "no branch exp/$id here or on origin"
    ref="origin/exp/$id"
  fi
  packet="$(mktemp)"
  if ! git -C "$ROOT" show "$ref:$TASKS/$id/packet.md" > "$packet"; then
    drop_from_ref "$tmpref"
    [ -z "$remote" ] || die "$shown $rbranch was never packed: it carries no packet at $TASKS/$id/packet.md, and a shared desk must be packed first (on that desk: neat pack $id, which writes the packet and pushes the branch)"
    die "exp/$id carries no packet; run: neat pack $id"
  fi
  intent="$(field Intent "$packet")"; verify="$(field Verify "$packet")"; allow="$(field Allow "$packet")"
  base="$(field 'Starting point' "$packet" | cut -d' ' -f1)"
  [ -z "$over_verify" ] || verify="$over_verify"
  [ -z "$over_allow" ] || allow="$over_allow"
  echo "== land task $id: $intent"
  if [ -n "$remote" ]; then
    echo "   from $shown $rbranch (it started at ${base:0:7}, which may be a commit only that desk has); the candidate is merged onto MAIN as it is now and verified there"
    [ "$graded" -eq 0 ] || echo "   graded here: this repository's brief replaces the packet's (verify: $verify; allow: $allow)"
  else
    moved="$(git -C "$ROOT" rev-list --count "$base..HEAD")"
    echo "   MAIN moved $moved commit(s) since the task started; the candidate is merged onto MAIN as it is now and verified there"
  fi
  local args=("task-$id" --from "$ref" --message "$intent")
  if [ -n "$remote" ]; then
    if [ "$graded" -eq 0 ]; then args=("task-$id" --from "$ref" --message "$intent (from $shown $rbranch)")
    else args=("task-$id" --from "$ref" --message "$intent (from $shown $rbranch, graded here)"); fi
  fi
  [ "$verify" = "none" ] || args+=(--verify "$verify")
  [ "$allow" = "any" ] || args+=(--allow "$allow $TASKS/$id")
  if bash "$HERE/land.sh" "${args[@]}"; then
    drop_from_ref "$tmpref"
    if [ -n "$remote" ]; then
      echo "task $id landed from $shown $rbranch; its packet is at $TASKS/$id/ in MAIN. Nothing on that desk was deleted (unshare it here with: neat undo $id)"
    else
      rm -rf "$EXP/$id"
      git -C "$ROOT" push -q origin --delete "exp/$id" 2>/dev/null && echo "deleted origin/exp/$id" || true
      echo "task $id landed; its packet is at $TASKS/$id/ in MAIN"
    fi
  else
    drop_from_ref "$tmpref"
    [ -z "$remote" ] || { echo "task $id did not land (see the reason above); nothing was taken from $shown" >&2; exit 1; }
    echo "task $id did not land (see the reason above); EXP/$id is untouched" >&2; exit 1
  fi
}

cmd_kill() {
  local id="${1:-}"; [ -n "$id" ] || usage
  git -C "$ROOT" worktree remove --force "$EXP/$id" 2>/dev/null || true
  rm -rf "$EXP/$id"
  bash "$HERE/land.sh" --note "**killed** \`task-$id\`: nothing landed; exp/$id is kept"
  echo "task $id abandoned; nothing landed. exp/$id is kept (git branch -D exp/$id, and on origin: git push origin --delete exp/$id, when you're sure)"
}

cmd_undo() {
  local id="${1:-}"; [ -n "$id" ] || usage
  local sha intent parents
  sha="$(git -C "$ROOT" log --format=%H --grep="^land(task-$id): " -n 1)"
  [ -n "$sha" ] || die "no landing commit for task $id (git log --grep 'land(task-$id)')"
  [ -z "$(status_without_bookkeeping)" ] || die "MAIN is not clean; undo needs a clean tree"
  intent="$(git -C "$ROOT" log -1 --format=%s "$sha" | sed "s/^land(task-$id): //")"
  parents="$(git -C "$ROOT" rev-list --parents -n 1 "$sha" | wc -w)"
  echo "== undo task $id: $intent  (landing ${sha:0:7})"
  if [ "$parents" -gt 2 ]; then git -C "$ROOT" revert --no-commit -m 1 "$sha" >/dev/null 2>&1 || { git -C "$ROOT" revert --abort; die "the revert conflicts with later landings in: $(git -C "$ROOT" diff --name-only --diff-filter=U | tr '\n' ' ')"; }
  else git -C "$ROOT" revert --no-commit "$sha" >/dev/null 2>&1 || { git -C "$ROOT" revert --abort; die "the revert conflicts with later landings in: $(git -C "$ROOT" diff --name-only --diff-filter=U | tr '\n' ' ')"; }; fi
  git -C "$ROOT" reset -q  # leave the revert as ordinary dirty files for land.sh to claim
  if bash "$HERE/land.sh" "undo-task-$id" --message "undo task $id: $intent"; then
    echo "task $id is out of MAIN; its packet and landing stay in history (git log --grep 'task-$id')"
  else
    git -C "$ROOT" checkout -q -- . && git -C "$ROOT" clean -fdq -e "$LAND_REL"
    echo "undo of task $id did not land (see the reason above); MAIN is as it was" >&2; exit 1
  fi
}

cmd_update() {
  local id="${1:-}"; [ -n "$id" ] || usage; need_exp "$id"
  local wt="$EXP/$id" behind
  behind="$(git -C "$wt" rev-list --count "HEAD..$BRANCH")"
  [ "$behind" -gt 0 ] || { echo "EXP/$id already has everything on MAIN"; return 0; }
  echo "== update EXP/$id: MAIN has $behind newer commit(s)"
  if git -C "$wt" merge -q --no-edit "$BRANCH" >/dev/null 2>&1; then
    echo "merged; the suite in EXP/$id is worth a run before packing"
  else
    local files; files="$(git -C "$wt" diff --name-only --diff-filter=U | tr '\n' ' ')"
    git -C "$wt" merge --abort
    die "MAIN conflicts with EXP/$id in: $files  (regenerated evidence conflicts are re-made on the merged code, not merged by hand: merge in EXP/$id, regenerate, commit, then pack)"
  fi
}

cmd_selftest() {
  local tmp seed clone origin tools_dir out failures=0
  local desk_origin desk desk_tools from_receipt d
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/neat-selftest.XXXXXX")"
  origin="$tmp/origin.git"; seed="$tmp/seed"; clone="$tmp/clone"; tools_dir="$clone/tools"
  desk_origin="$tmp/desk-origin.git"; desk="$tmp/desk"; desk_tools="$desk/tools"
  git init -q --bare "$origin"
  git init -q "$seed"
  git -C "$seed" config user.email selftest@example.invalid
  git -C "$seed" config user.name selftest
  printf 'Verify: true\n' > "$seed/README.md"
  git -C "$seed" add README.md
  git -C "$seed" commit -q -m initial
  git -C "$seed" remote add origin "$origin"
  git -C "$seed" push -q -u origin HEAD
  git clone -q "$origin" "$clone"
  git -C "$clone" config user.email selftest@example.invalid
  git -C "$clone" config user.name selftest
  mkdir -p "$tools_dir"
  cp "$HERE/neat.sh" "$tools_dir/neat.sh"
  cp "$HERE/land.sh" "$tools_dir/land.sh"
  chmod +x "$tools_dir/neat.sh" "$tools_dir/land.sh"
  git -C "$clone" add tools
  git -C "$clone" commit -q -m "selftest tools"
  if bash "$tools_dir/neat.sh" new "selftest" --verify "echo score: 3 of 3" >"$tmp/new.txt" 2>&1; then :; else failures=$((failures + 1)); fi
  if [ -d "$clone/EXP/0" ] && [ -f "$clone/EXP/0/.neat/tasks/0/packet.md" ]; then
    echo "selftest new: pass"
  else
    echo "selftest new: FAIL"; failures=$((failures + 1))
  fi
  printf 'edit\n' > "$clone/EXP/0/edit.txt"
  if bash "$tools_dir/neat.sh" pack 0 >"$tmp/pack.txt" 2>&1; then :; else failures=$((failures + 1)); fi
  if grep -q '^## Candidate$' "$clone/EXP/0/.neat/tasks/0/packet.md" &&
     grep -q '^## Evidence$' "$clone/EXP/0/.neat/tasks/0/packet.md" &&
     grep -q '^## Uncertain$' "$clone/EXP/0/.neat/tasks/0/packet.md"; then
    echo "selftest packet sections: pass"
  else
    echo "selftest packet sections: FAIL"; failures=$((failures + 1))
  fi
  if bash "$tools_dir/neat.sh" land 0 >"$tmp/land.txt" 2>&1; then :; else failures=$((failures + 1)); fi
  if git -C "$clone" log --format=%s -n 20 | grep -q '^land(task-0): '; then
    echo "selftest landing commit: pass"
  else
    echo "selftest landing commit: FAIL"; failures=$((failures + 1))
  fi
  if ! git --git-dir="$origin" show-ref --verify --quiet refs/heads/exp/0; then
    echo "selftest origin branch removal: pass"
  else
    echo "selftest origin branch removal: FAIL"; failures=$((failures + 1))
  fi
  if grep -q '^## Today$' "$clone/.neat/BOARD.md" && grep -q 'task-0' "$clone/.neat/BOARD.md"; then
    echo "selftest board: pass"
  else
    echo "selftest board: FAIL"; failures=$((failures + 1))
  fi
  if grep -q '"passed": 3' "$clone"/.neat/landings/*-task-0/receipt.json 2>/dev/null && grep -q 'score 3/3' "$clone/.neat/BOARD.md"; then
    echo "selftest score: pass"
  else
    echo "selftest score: FAIL"; failures=$((failures + 1))
  fi
  if bash "$tools_dir/neat.sh" undo 0 >"$tmp/undo.txt" 2>&1; then :; else failures=$((failures + 1)); fi
  if [ ! -e "$clone/edit.txt" ] && [ -z "$(git -C "$clone" status --porcelain --untracked-files=all)" ]; then
    echo "selftest undo clean: pass"
  else
    echo "selftest undo clean: FAIL"; failures=$((failures + 1))
  fi
  # An undone task's number is never handed out again: the landing receipts keep it taken.
  bash "$tools_dir/neat.sh" new "again" --verify "true" --allow "again.txt" >"$tmp/again.txt" 2>&1 || failures=$((failures + 1))
  if [ -d "$clone/EXP/1" ] && [ ! -d "$clone/EXP/0" ]; then
    echo "selftest an undone id is not reused: pass"
  else
    echo "selftest an undone id is not reused: FAIL"; cat "$tmp/again.txt" | tail -3; failures=$((failures + 1))
  fi
  # A note addressed to the owner is an interrupt, and the board allows three reasons for one: an
  # untagged "**owner**" line is refused with exit 2 and writes nothing; a tagged one is an ordinary note.
  out=0; bash "$tools_dir/land.sh" --note "**owner** something" >"$tmp/note-untagged.txt" 2>&1 || out=$?
  if [ "$out" -eq 2 ] && ! grep -qF '**owner**' "$clone/.neat/BOARD.md"; then
    echo "selftest owner note without a reason: pass"
  else
    echo "selftest owner note without a reason: FAIL"; failures=$((failures + 1))
  fi
  if bash "$tools_dir/land.sh" --note "**owner** [asked] something" >"$tmp/note-asked.txt" 2>&1 &&
     grep -qF '**owner** [asked] something' "$clone/.neat/BOARD.md"; then
    echo "selftest owner note with a reason: pass"
  else
    echo "selftest owner note with a reason: FAIL"; failures=$((failures + 1))
  fi
  # A second repository: the student's desk, its own origin and clone, made from the same seed
  # commit so the two histories meet (a desk is normally a fork of the class repo). It packs its own
  # task 0 -- ids in two repos collide, that is the point -- and the class repo lands it with one
  # command: neat land 0 --from <the desk's origin> exp/0.
  git clone -q --bare "$seed" "$desk_origin"
  git clone -q "$desk_origin" "$desk"
  git -C "$desk" config user.email selftest@example.invalid
  git -C "$desk" config user.name selftest
  mkdir -p "$desk_tools"
  cp "$HERE/neat.sh" "$desk_tools/neat.sh"
  cp "$HERE/land.sh" "$desk_tools/land.sh"
  chmod +x "$desk_tools/neat.sh" "$desk_tools/land.sh"
  git -C "$desk" add tools
  git -C "$desk" commit -q -m "selftest tools"
  if bash "$desk_tools/neat.sh" new "shared desk" --verify true --allow desk.txt >"$tmp/desk-new.txt" 2>&1; then :; else failures=$((failures + 1)); fi
  printf 'desk\n' > "$desk/EXP/0/desk.txt"
  if bash "$desk_tools/neat.sh" pack 0 >"$tmp/desk-pack.txt" 2>&1; then :; else failures=$((failures + 1)); fi
  # The class repo grades the desk with its own brief: --verify replaces the packet's Verify line
  # (the desk asked for `true`; here it is the class's command, and its score is what the receipt keeps).
  if bash "$tools_dir/neat.sh" land 0 --from "$desk_origin" exp/0 --verify "echo score: 2 of 2" >"$tmp/land-from.txt" 2>&1; then :; else failures=$((failures + 1)); fi
  if [ -f "$clone/desk.txt" ] && [ -f "$clone/.neat/tasks/0/packet.md" ] &&
     grep -q '"path": "desk.txt"' "$clone"/.neat/landings/*/receipt.json; then
    echo "selftest land from a remote: pass"
  else
    echo "selftest land from a remote: FAIL"; failures=$((failures + 1))
  fi
  if grep -qF "(from $desk_origin exp/0, graded here)" "$clone/.neat/BOARD.md" &&
     ! git -C "$clone" show-ref --verify --quiet refs/neat/from/0; then
    echo "selftest remote board line and temporary ref: pass"
  else
    echo "selftest remote board line and temporary ref: FAIL"; failures=$((failures + 1))
  fi
  # The newest task-0 receipt is the one from the desk; the stamp is spelled out so the undo's
  # receipt (undo-task-0) is not mistaken for it.
  from_receipt=""
  for d in "$clone"/.neat/landings/????????T??????Z-task-0/; do
    if [ -f "$d/receipt.json" ]; then from_receipt="$d/receipt.json"; fi
  done
  if [ -n "$from_receipt" ] && grep -q '"passed": 2' "$from_receipt"; then
    echo "selftest remote desk graded here: pass"
  else
    echo "selftest remote desk graded here: FAIL"; failures=$((failures + 1))
  fi
  rm -rf "$tmp"
  [ "$failures" -eq 0 ]
}

cmd_walk() {
  # neat walk          -> the index, one line per landing on the board (walk.py --list)
  # neat walk N        -> step N as text, for an agent (walk.py --text N)
  # neat walk --page [out] -> the page, at out or ./walk.html in the current directory
  local walk="$ROOT/pyto/scripts/walk.py" out
  case "${1:-}" in
    "") "$PYTHON" "$walk" --list;;
    --page) out="${2:-walk.html}"; "$PYTHON" "$walk" --out "$out"; echo "the walk is at $out (open it; arrows step)";;
    --check) "$PYTHON" "$walk" --check;;
    *) case "$1" in *[!0-9]*) die "neat walk takes a step number, --page [out], or nothing: neat walk 55";; esac
       "$PYTHON" "$walk" --text "$1";;
  esac
}

cmd_diff() {
  # neat diff <a.json> <b.json> --store <seed.json> --registry <module:attr> [--label-a T] [--label-b T]
  # A thin forward to the Calculation itself (pyto/src/pyto/neat/diff.py); $PYTHON already has
  # pyto importable (this copy's own .venv, or PYTHONPATH), so no cwd or sys.path trick is needed here.
  "$PYTHON" -m pyto.neat.diff "$@"
}

cmd_list() {
  # A landed task's score is whatever its own landing receipt kept; an experiment that has not
  # landed has no receipt and so no score yet, which is the same "-" as a verifier that printed none.
  local d id packet base n state
  printf '%-4s %-8s %-6s %-6s %s\n' id state files score intent
  for d in "$EXP"/*/; do
    [ -d "$d" ] || continue; id="$(basename "$d")"; packet="$(packet_of "$id")"; [ -f "$packet" ] || continue
    base="$(field 'Starting point' "$packet" | cut -d' ' -f1)"
    n="$(git -C "$d" diff --name-only "$base" HEAD -- . ":!$TASKS" | wc -l | tr -d ' ')"
    [ -f "$d/$TASKS/$id/HANDOFF.md" ] && state=packed || state=open
    printf '%-4s %-8s %-6s %-6s %s\n' "$id" "$state" "$n" "-" "$(field Intent "$packet")"
  done
  for d in "$ROOT/$TASKS"/*/; do
    [ -f "$d/packet.md" ] || continue; id="$(basename "$d")"
    printf '%-4s %-8s %-6s %-6s %s\n' "$id" landed "-" "$(score_of "$(receipt_of "task-$id")")" "$(field Intent "$d/packet.md")"
  done
}

case "$cmd" in
  new) cmd_new "$@";; pack) cmd_pack "$@";; show) cmd_show "$@";; drop) cmd_drop "$@";;
  land) cmd_land "$@";; kill) cmd_kill "$@";; undo) cmd_undo "$@";; update) cmd_update "$@";;
  list) cmd_list "$@";; selftest) cmd_selftest "$@";; walk) cmd_walk "$@";; diff) cmd_diff "$@";; *) usage;;
esac
