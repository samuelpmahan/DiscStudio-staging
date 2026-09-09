#!/usr/bin/env bash
# neat: one MAIN, one EXP. The caveman version of landing (pyto/LANDING.md, first section).
#
#   neat new "<intent>" [--verify "<cmd>"] [--allow "<paths>"]   EXP/<id>: a copy of MAIN to work in
#   neat pack <id>            commit the work, write the packet and the hand-off, push exp/<id>
#   neat show <id>            print the hand-off (what a fresh agent gets)
#   neat drop <id> <path>...  put those files back to the starting point, repack
#   neat land <id>            merge into MAIN, verify, receipt, commit, push; EXP/<id> goes away
#   neat kill <id>            abandon: EXP/<id> and its branch go away, nothing lands
#   neat undo <id>            take a landed task back out of MAIN: revert, verify, receipt, push
#   neat list                 every experiment and its state
#
# MAIN is the clone itself. EXP/<id> is a git worktree on branch exp/<id> (ignored by git in MAIN),
# with its own .venv so the suite in EXP/<id> tests EXP/<id>'s kernel, not MAIN's. The packet lives
# inside the experiment at pyto/experiments/tasks/<id>/ so it travels with the branch and lands with
# the candidate. IDs are plain numbers from 0.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$PY/.." && pwd)"
# The interpreter, in order: $PYTHON if set; the repository's own .venv (Linux or Windows layout);
# then python3 or python on PATH. A venv is what lets an isolated child (-I) import pyto on Windows,
# where a Store Python's editable install lands in the user site that -I ignores.
_root_for_python="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -z "${PYTHON:-}" ]; then
  for _c in "$_root_for_python/.venv/bin/python" "$_root_for_python/.venv/Scripts/python.exe"; do
    [ -x "$_c" ] && PYTHON="$_c" && break
  done
fi
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
EXP="$ROOT/EXP"
TASKS="pyto/experiments/tasks"
BRANCH="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
URL="$(git -C "$ROOT" remote get-url origin 2>/dev/null | sed 's#https://[^@]*@#https://#' || echo '<origin>')"
cmd="${1:-}"; shift || true

die() { echo "neat: $*" >&2; exit 1; }
usage() { sed -n '4,12p' "${BASH_SOURCE[0]}" | sed 's/^#  *//'; exit 2; }
field() { # <name> <file>  -> the value after "<name>: "
  grep -m1 "^$1: " "$2" | sed "s/^$1: //"
}
next_id() { # the highest id seen anywhere: local copies, landed packets, and exp/* branches here or on origin
  local max=-1 d n
  git -C "$ROOT" fetch -q origin 'refs/heads/exp/*:refs/remotes/origin/exp/*' 2>/dev/null || true
  for d in "$EXP"/*/ "$ROOT/$TASKS"/*/; do
    [ -d "$d" ] || continue; n="$(basename "$d")"
    case "$n" in ''|*[!0-9]*) continue;; esac
    [ "$n" -gt "$max" ] && max="$n"
  done
  for n in $(git -C "$ROOT" for-each-ref --format='%(refname:short)' 'refs/heads/exp/*' 'refs/remotes/origin/exp/*' | sed 's#.*exp/##'); do
    case "$n" in ''|*[!0-9]*) continue;; esac
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
need_exp() { [ -d "$EXP/$1" ] || die "no experiment EXP/$1 (neat list)"; }

cmd_new() {
  local intent="${1:-}"; shift || true
  [ -n "$intent" ] || die 'new needs an intent: neat new "what you want"'
  local verify="none" allow="any"
  while [ $# -gt 0 ]; do case "$1" in --verify) verify="$2"; shift 2;; --allow) allow="$2"; shift 2;; *) die "unknown option $1";; esac; done
  local id base subject
  id="$(next_id)"; base="$(git -C "$ROOT" rev-parse HEAD)"; subject="$(git -C "$ROOT" log -1 --format=%s)"
  mkdir -p "$EXP"
  git -C "$ROOT" worktree add -q "$EXP/$id" -b "exp/$id" HEAD
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
  echo "Task $id: EXP/$id is a copy of MAIN at ${base:0:7}. Work there."
  echo "  making its python (EXP/$id/.venv) so the suite there tests that copy's kernel ..."
  "$PYTHON" -m venv --system-site-packages "$EXP/$id/.venv"
  "$(venv_python "$id")" -m pip install -q --no-build-isolation -e "$EXP/$id/pyto[drawing]" 2>&1 | grep -v "^$" | tail -2 || true
  case "$("$(venv_python "$id")" -c 'import pyto; print(pyto.__file__)' 2>/dev/null)" in
    "$EXP/$id/"*) echo "  its python imports pyto from EXP/$id";;
    *) die "EXP/$id/.venv does not import pyto from EXP/$id; the suite there would test MAIN's kernel. Fix the install before working.";;
  esac
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
  git -C "$wt" add -A
  git -C "$wt" commit -q -m "exp/$id: $intent" 2>/dev/null || true
  mkdir -p "$wt/$TASKS/$id/evidence"
  if [ "$verify" != "none" ]; then
    echo "== verify: $verify"
    vexit=0; (cd "$wt" && PYTHON="$vpy" bash -c "$verify") > "$wt/$TASKS/$id/evidence/verify.txt" 2>&1 || vexit=$?
    echo "   exit $vexit"
  fi
  echo "== suite in EXP/$id (python: $vpy)"
  cexit=0; (cd "$wt" && PYTHON="$vpy" bash "$wt/pyto/scripts/check_all.sh") > "$wt/$TASKS/$id/evidence/check_all.txt" 2>&1 || cexit=$?
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

cmd_land() {
  local id="${1:-}"; [ -n "$id" ] || usage
  local ref="exp/$id" packet base verify allow intent moved
  if ! git -C "$ROOT" rev-parse -q --verify "refs/heads/exp/$id" >/dev/null; then
    git -C "$ROOT" fetch -q origin "exp/$id" 2>/dev/null || die "no branch exp/$id here or on origin"
    ref="origin/exp/$id"
  fi
  packet="$(mktemp)"; git -C "$ROOT" show "$ref:$TASKS/$id/packet.md" > "$packet" || die "exp/$id carries no packet; run: neat pack $id"
  intent="$(field Intent "$packet")"; verify="$(field Verify "$packet")"; allow="$(field Allow "$packet")"
  base="$(field 'Starting point' "$packet" | cut -d' ' -f1)"
  moved="$(git -C "$ROOT" rev-list --count "$base..HEAD")"
  echo "== land task $id: $intent"
  echo "   MAIN moved $moved commit(s) since the task started; the candidate is merged onto MAIN as it is now and verified there"
  local args=("task-$id" --from "$ref" --message "$intent")
  [ "$verify" = "none" ] || args+=(--verify "$verify")
  [ "$allow" = "any" ] || args+=(--allow "$allow $TASKS/$id")
  if bash "$HERE/land.sh" "${args[@]}"; then
    rm -rf "$EXP/$id"
    git -C "$ROOT" push -q origin --delete "exp/$id" 2>/dev/null && echo "deleted origin/exp/$id" || true
    echo "task $id landed; its packet is at $TASKS/$id/ in MAIN"
  else
    echo "task $id did not land (see the reason above); EXP/$id is untouched" >&2; exit 1
  fi
}

cmd_kill() {
  local id="${1:-}"; [ -n "$id" ] || usage
  git -C "$ROOT" worktree remove --force "$EXP/$id" 2>/dev/null || true
  rm -rf "$EXP/$id"
  git -C "$ROOT" branch -D "exp/$id" >/dev/null 2>&1 || true
  git -C "$ROOT" push -q origin --delete "exp/$id" 2>/dev/null || true
  echo "task $id abandoned; nothing landed"
}

cmd_undo() {
  local id="${1:-}"; [ -n "$id" ] || usage
  local sha intent parents
  sha="$(git -C "$ROOT" log --format=%H --grep="^land(task-$id): " -n 1)"
  [ -n "$sha" ] || die "no landing commit for task $id (git log --grep 'land(task-$id)')"
  [ -z "$(git -C "$ROOT" status --porcelain --untracked-files=all | grep -v '^?? pyto/experiments/landings/')" ] || die "MAIN is not clean; undo needs a clean tree"
  intent="$(git -C "$ROOT" log -1 --format=%s "$sha" | sed "s/^land(task-$id): //")"
  parents="$(git -C "$ROOT" rev-list --parents -n 1 "$sha" | wc -w)"
  echo "== undo task $id: $intent  (landing ${sha:0:7})"
  if [ "$parents" -gt 2 ]; then git -C "$ROOT" revert --no-commit -m 1 "$sha" >/dev/null 2>&1 || { git -C "$ROOT" revert --abort; die "the revert conflicts with later landings in: $(git -C "$ROOT" diff --name-only --diff-filter=U | tr '\n' ' ')"; }
  else git -C "$ROOT" revert --no-commit "$sha" >/dev/null 2>&1 || { git -C "$ROOT" revert --abort; die "the revert conflicts with later landings in: $(git -C "$ROOT" diff --name-only --diff-filter=U | tr '\n' ' ')"; }; fi
  git -C "$ROOT" reset -q  # leave the revert as ordinary dirty files for land.sh to claim
  if bash "$HERE/land.sh" "undo-task-$id" --message "undo task $id: $intent"; then
    echo "task $id is out of MAIN; its packet and landing stay in history (git log --grep 'task-$id')"
  else
    git -C "$ROOT" checkout -q -- . && git -C "$ROOT" clean -fdq -e pyto/experiments/landings
    echo "undo of task $id did not land (see the reason above); MAIN is as it was" >&2; exit 1
  fi
}

cmd_list() {
  local d id packet base n state
  printf '%-4s %-8s %-6s %s\n' id state files intent
  for d in "$EXP"/*/; do
    [ -d "$d" ] || continue; id="$(basename "$d")"; packet="$(packet_of "$id")"; [ -f "$packet" ] || continue
    base="$(field 'Starting point' "$packet" | cut -d' ' -f1)"
    n="$(git -C "$d" diff --name-only "$base" HEAD -- . ":!$TASKS" | wc -l | tr -d ' ')"
    [ -f "$d/$TASKS/$id/HANDOFF.md" ] && state=packed || state=open
    printf '%-4s %-8s %-6s %s\n' "$id" "$state" "$n" "$(field Intent "$packet")"
  done
  for d in "$ROOT/$TASKS"/*/; do
    [ -f "$d/packet.md" ] || continue; id="$(basename "$d")"
    printf '%-4s %-8s %-6s %s\n' "$id" landed "-" "$(field Intent "$d/packet.md")"
  done
}

case "$cmd" in
  new) cmd_new "$@";; pack) cmd_pack "$@";; show) cmd_show "$@";; drop) cmd_drop "$@";;
  land) cmd_land "$@";; kill) cmd_kill "$@";; undo) cmd_undo "$@";; list) cmd_list "$@";; *) usage;;
esac
