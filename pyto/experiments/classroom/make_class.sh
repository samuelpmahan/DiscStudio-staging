#!/usr/bin/env bash
# make_class.sh -- a class in a repo, built from nothing, in one run.
#
#   bash make_class.sh <dir>          build the class and one student's desk under <dir>
#   bash make_class.sh --selftest     build the whole thing under a temp dir and check it
#   bash make_class.sh --selftest <dir>   the same, under <dir>, and keep it
#
# What it builds under <dir>, and why each piece exists (pyto/questions.md,
# `{?} NeatLearning`: course = repo, assignment = a package brief, start = neat new,
# submit = neat pack, accepted = neat land, grade record = the landing receipt,
# gradebook = the Today log; and "private by default, sharing is a landing"):
#
#   seed/               the starting point both repositories are cut from. It exists
#                       because a landing is a merge: the class repo and the desk must
#                       share history or `neat land --from` has nothing to merge onto.
#                       It holds the two neat scripts, the brief, and the student's own
#                       little checks -- the starter kit.
#   class-origin.git    the class's remote, owned by the teacher.
#   class/              the class repo: the assignment package under
#                       assignments/scores/ (BRIEF.md, grader.sh, the teacher's grade.py
#                       and cold_reader.py, a reference solution) and, after the landing,
#                       submissions/<student>/.
#   desk-origin.git     the student's own remote. Private: nobody but the student and
#                       the teacher can fetch it.
#   desk/               the student's desk. Their MAIN, their tasks, their receipts.
#
# Then it plays both sides. The student runs neat on their desk: they start the
# homework (task 0), submit it, keep a page of their own questions (task 1: refused
# once at 1 of 2, then landed at 2 of 2), land and immediately undo a change (task 2),
# and start and kill one more (task 3). Nothing of that is visible to the class.
# The teacher then runs ONE command from the class repo:
#
#   neat land 0 --from <desk-origin> exp/0 \
#       --verify "bash assignments/scores/grader.sh" --allow "submissions/ada"
#
# which fetches the desk's branch, merges it under the one allowed path, grades it with
# the class's own verifier (not the desk's), and writes the score into the landing
# receipt and the class board. The desk is not touched by any of it.
#
# bash 3.2: no mapfile, no associative arrays, no ${var^^}. It has to run on the
# owner's mac as well as here.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTO="$(cd "$HERE/../.." && pwd)"
SCRIPTS="$PYTO/scripts"
STUDENTS="$PYTO/experiments/students"
VIEWER_TEST="$PYTO/viewer/test"
STUDENT="ada"

# The interpreter, by the same rule neat.sh and land.sh use: $PYTHON if set, then the
# repository's own .venv, then python3. It is exported because the class's grader runs
# as a verifier inside land.sh, three processes down, and must be the interpreter that
# can import pyto -- the student's record is replayed in a fresh process by grade.py.
if [ -z "${PYTHON:-}" ]; then
  for _c in "$PYTO/../.venv/bin/python" "$PYTO/../.venv/Scripts/python.exe"; do
    [ -x "$_c" ] && PYTHON="$_c" && break
  done
fi
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
export PYTHON

die() { echo "make_class: $*" >&2; exit 1; }
usage() { sed -n '3,6p' "${BASH_SOURCE[0]}" | sed 's/^#  *//'; exit 2; }
step() { echo; echo "=== $*"; }

configure() { # <repo>  -- a scratch repo needs a name to commit under
  git -C "$1" config user.email "class@example.invalid"
  git -C "$1" config user.name "neat class"
  # file:// pushes on some git builds print a push-negotiation warning that is not one
  git -C "$1" config push.negotiate false
}

# --- the files ------------------------------------------------------------------

write_brief() { # <path>  -- the assignment, in a student's words
  cat > "$1" <<'BRIEF'
# Assignment: class scores

You are given one CSV table of a class's names and whole-number scores. Turn it into
a report: the class average, the middle score, a letter for every student, and a bar
chart of how many students got each letter.

Write it as a program of Ticks over a store of named values, the way pyto does it.
A Tick is a step: between two Ticks your program claims an order and a state of the
world in between; inside one Tick it claims none, so two calculations that do not
need each other belong in the same Tick.

## What to hand in

Under `submissions/<your name>/` on your own desk:

- `homework.py` -- the program.
- `HANDOFF.md` -- one page, written for somebody who will never see your code. It
  must give every Tick a list line of its own under a heading "One line per Tick",
  and it must name every file your homework is made of.
- `evidence/run-1/record.json` -- the run your program produced.
- `evidence/run-1/receipts.json` -- one receipt per calculation of that run.
- `evidence/run-1/tick-viewer.html` -- the same run as a page you can step through.
- `cold-reader.txt` -- what a cold reader wrote after being handed your HANDOFF.md
  and nothing else. Their answer travels with the submission so the grade can be
  redone from the repository alone.

## How to hand it in

Your desk is your own repository. Nobody sees it until you share, and sharing is a
landing:

    bash tools/neat.sh new "class scores" --allow "submissions/<your name>" \
        --verify "bash tools/check_submission.sh"
    ... write the work in EXP/<id>/submissions/<your name>/ ...
    bash tools/neat.sh pack <id>

`pack` runs your own check, writes the packet and the hand-off page, and pushes the
branch. Then tell the teacher the id.

## How it is graded

The teacher runs the class's verifier, not yours:

    bash assignments/scores/grader.sh

which is `grade.py`'s four mechanical checks (the record validates; a fresh process
replays it byte for byte; every calculation has a receipt whose fingerprint is
today's source; the hand-off gives every Tick a line and names every file) and then
`cold_reader.py`, which checks that the cold reader's answer names every Tick and
every file your page names. The four checks are the score in the receipt. The cold
read is the real grade, and a person makes it.

The caveat, first and last: identical fingerprints prove the same computation, not
the right answer.
BRIEF
}

write_seed_files() { # <seed dir>
  local seed="$1"
  printf 'EXP/\n' > "$seed/.gitignore"
  cat > "$seed/README.md" <<'SEED'
# The seed

The commit both the class repository and every student's desk are cut from.

It exists for one mechanical reason: sharing is a landing, a landing is a merge, and
a merge needs a common ancestor. The desk is a fork of this; the class repository is
this plus the assignment package. `neat land <id> --from <desk> exp/<id>` fetches the
desk's branch and merges it here, and the merge base is this commit.

Everything in `tools/` is the student's: the two neat scripts and the small checks
they run on themselves before handing anything in.
SEED
  mkdir -p "$seed/tools"
  cp "$SCRIPTS/neat.sh" "$seed/tools/neat.sh"
  cp "$SCRIPTS/land.sh" "$seed/tools/land.sh"
  write_brief "$seed/BRIEF.md"
  cat > "$seed/tools/check_submission.sh" <<'CHECK'
#!/usr/bin/env bash
# The student's own check, before anybody else sees it: is the submission complete?
# It prints a score line because a verifier may report one (pyto/LANDING.md, "The
# words"), and a score the student can see before handing in is the point of packing.
set -u
who="${1:-ada}"
d="submissions/$who"
n=0
for f in homework.py HANDOFF.md cold-reader.txt evidence/run-1/record.json \
         evidence/run-1/receipts.json evidence/run-1/tick-viewer.html; do
  if [ -f "$d/$f" ]; then n=$((n + 1)); else echo "missing: $d/$f"; fi
done
echo "score: $n of 6"
[ "$n" -eq 6 ]
CHECK
  cat > "$seed/tools/check_notes.sh" <<'CHECK'
#!/usr/bin/env bash
# A page of my own questions is worth having only if it holds questions, spelled the
# way the record spells them: one line each, starting with {?}.
set -u
f="notes/questions.md"
n=0
if [ -f "$f" ]; then n="$(grep -c '^{?} ' "$f" || true)"; fi
[ "$n" -gt 2 ] && n=2
echo "score: $n of 2"
[ "$n" -eq 2 ]
CHECK
  chmod +x "$seed/tools/neat.sh" "$seed/tools/land.sh" \
           "$seed/tools/check_submission.sh" "$seed/tools/check_notes.sh"
}

write_grader() { # <class dir>
  local class="$1"
  cat > "$class/assignments/scores/grader.sh" <<'GRADER'
#!/usr/bin/env bash
# The class's verifier: the one command the teacher hands to `neat land --verify`.
# It runs on the merged tree, so submissions/<student>/ is already in place.
#
# Two halves, and they are not the same kind of thing:
#   grade.py      four mechanical checks over the submitted run. This is the score in
#                 the landing receipt: "score: N of 4".
#   cold_reader.py  the reader's answer must name every Tick and every file the
#                 hand-off names. This is a floor under the cold read, not a grade.
# The exit code needs both. The receipt keeps the four checks, because a score that
# mixes a rubric with a word count cannot say which half failed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLASS="$(cd "$HERE/../.." && pwd)"
PY="${PYTHON:-python3}"
cd "$CLASS"

passed=0; checks=0; named=0; names=0; students=0; rc=0

for sub in submissions/*/; do
  [ -f "$sub/HANDOFF.md" ] || continue
  who="$(basename "$sub")"
  students=$((students + 1))
  echo "== $who"
  work="$(mktemp -d "${TMPDIR:-/tmp}/class-grade.XXXXXX")"
  # grade.py reads the directory it sits in: it imports homework.py from there, and
  # check 4 asks the hand-off to account for every file beside it. So the graded copy
  # is the submission plus the TEACHER's grade.py, standing where grade.py expects to
  # stand (pyto/experiments/<name>/) beside the validator it reads the record with.
  # cold-reader.txt is left out of that copy on purpose: it is the reader's answer,
  # not part of the program the hand-off has to account for.
  mkdir -p "$work/pyto/viewer/test" "$work/pyto/experiments/graded"
  cp "$HERE/record_schema.py" "$work/pyto/viewer/test/record_schema.py"
  cp "$HERE/grade.py" "$work/pyto/experiments/graded/grade.py"
  cp "$sub/homework.py" "$work/pyto/experiments/graded/homework.py"
  cp "$sub/HANDOFF.md" "$work/pyto/experiments/graded/HANDOFF.md"
  cp -R "$sub/evidence" "$work/pyto/experiments/graded/evidence"

  g=0
  "$PY" "$work/pyto/experiments/graded/grade.py" \
        --run "$work/pyto/experiments/graded/evidence/run-1" \
        --handoff "$work/pyto/experiments/graded/HANDOFF.md" \
        > "$work/grade.txt" 2> "$work/grade.err" || g=$?
  sed -n '1,/^--- for the cold reader ---$/p' "$work/grade.txt" | sed '$d'
  p="$(sed -n 's/^mechanical: \([0-9][0-9]*\) of \([0-9][0-9]*\) checks passed$/\1/p' "$work/grade.txt" | tail -n 1)"
  t="$(sed -n 's/^mechanical: \([0-9][0-9]*\) of \([0-9][0-9]*\) checks passed$/\2/p' "$work/grade.txt" | tail -n 1)"
  if [ -z "$p" ] || [ -z "$t" ]; then
    echo "grade.py printed no result for $who (exit $g):"
    tail -n 5 "$work/grade.err" | sed 's/^/    /'
    p=0; t=4; rc=1
  fi
  [ "$g" -eq 0 ] || rc=1
  passed=$((passed + p)); checks=$((checks + t))

  c=0
  "$PY" "$HERE/cold_reader.py" "$sub/HANDOFF.md" "$sub/cold-reader.txt" > "$work/cold.txt" 2>&1 || c=$?
  cat "$work/cold.txt"
  n="$(sed -n 's/^cold reader: \([0-9][0-9]*\) of \([0-9][0-9]*\) named$/\1/p' "$work/cold.txt" | tail -n 1)"
  m="$(sed -n 's/^cold reader: \([0-9][0-9]*\) of \([0-9][0-9]*\) named$/\2/p' "$work/cold.txt" | tail -n 1)"
  if [ -z "$n" ] || [ -z "$m" ]; then n=0; m=0; rc=1; fi
  [ "$c" -eq 0 ] || rc=1
  named=$((named + n)); names=$((names + m))
  rm -rf "$work"
  echo
done

if [ "$students" -eq 0 ]; then
  echo "no submission under submissions/: nothing to grade"
  exit 1
fi
echo "combined: $((passed + named)) of $((checks + names)) (grade.py's checks and the cold reader's names)"
echo "not mechanical, and the actual grade: whether the cold reader's answer is right."
echo "caveat: identical digests prove the same computation, not the right answer."
echo "score: $passed of $checks"
exit $rc
GRADER
  chmod +x "$class/assignments/scores/grader.sh"
}

# --- building the two repositories ----------------------------------------------

build_seed() { # <dir>
  local dir="$1"
  local seed="$1/seed"
  step "the seed: what the class and every desk are cut from"
  git init -q "$seed"
  configure "$seed"
  write_seed_files "$seed"
  git -C "$seed" add -A
  git -C "$seed" commit -q -m "the class seed: the neat scripts, the brief, the student's checks"
  git init -q --bare "$dir/class-origin.git"
  git -C "$seed" remote add origin "$dir/class-origin.git"
  git -C "$seed" push -q -u origin HEAD
  git clone -q --bare "$seed" "$dir/desk-origin.git"
  echo "  seed $(git -C "$seed" rev-parse --short HEAD); class-origin.git and desk-origin.git carry it"
}

build_class() { # <dir>
  local dir="$1"
  local class="$1/class"
  step "the class repository: the assignment package"
  git clone -q "$dir/class-origin.git" "$class"
  configure "$class"
  mkdir -p "$class/assignments/scores/reference/evidence/run-1"
  write_brief "$class/assignments/scores/BRIEF.md"
  write_grader "$class"
  cp "$STUDENTS/grade.py" "$class/assignments/scores/grade.py"
  cp "$HERE/cold_reader.py" "$class/assignments/scores/cold_reader.py"
  cp "$VIEWER_TEST/record_schema.py" "$class/assignments/scores/record_schema.py"
  # The reference solution: what the teacher's verifier encodes, written out so a
  # human can read it. grade.py has no reference of its own -- that is the caveat.
  cp "$STUDENTS/homework.py" "$class/assignments/scores/reference/homework.py"
  cp "$STUDENTS/HANDOFF.md" "$class/assignments/scores/reference/HANDOFF.md"
  cp "$STUDENTS/evidence/run-1/record.json" "$class/assignments/scores/reference/evidence/run-1/record.json"
  cp "$STUDENTS/evidence/run-1/receipts.json" "$class/assignments/scores/reference/evidence/run-1/receipts.json"
  cat > "$class/assignments/scores/reference/README.md" <<'REF'
# The reference

The worked answer this assignment is graded against, kept as files a person can read.

`grade.py` does not read it. Checks 1-4 are about whether the student's record is
honest about the program the student wrote -- the record validates, a fresh process
reproduces it, every calculation's fingerprint is today's source, and the hand-off
accounts for every Tick and every file. None of that needs a reference, and none of
it can tell you the answer is right.

That is the caveat the whole assignment is built around, so it is written here beside
the thing that would settle it: identical digests prove the same computation, not the
right answer. A verifier still needs a reference, and a teacher still has to read.
REF
  git -C "$class" add -A
  git -C "$class" commit -q -m "assignment: class scores (brief, grader, reference)"
  git -C "$class" push -q -u origin HEAD
  echo "  class/ at $(git -C "$class" rev-parse --short HEAD): assignments/scores/ is the package"
}

build_desk() { # <dir>
  local dir="$1"
  local desk="$1/desk"
  step "the desk: the student's own private repository"
  git clone -q "$dir/desk-origin.git" "$desk"
  configure "$desk"
  echo "  desk/ at $(git -C "$desk" rev-parse --short HEAD): the starter kit, and nothing of the class's"
}

# --- the student ----------------------------------------------------------------

new_task() { # <dir> <intent> [neat new options...] -> the id neat handed out
  # Never assume the id: neat hands out the next free one, and "free" moves as branches
  # land, are killed or are undone. The caller reads it back from what neat printed.
  local dir="$1"; shift
  local out id
  out="$dir/log-new-$$.txt"
  bash "$dir/desk/tools/neat.sh" new "$@" > "$out" 2>&1
  id="$(sed -n 's/^Task \([0-9][0-9]*\):.*/\1/p' "$out" | head -n 1)"
  [ -n "$id" ] || { cat "$out" >&2; echo "make_class: neat new printed no task id" >&2; exit 1; }
  mv "$out" "$dir/log-new-$id.txt"
  printf '%s\n' "$id"
}

uncertain() { # <packet path> <line...>  -- one {?} line, the habit the record is built on
  local packet="$1"; shift
  printf '%s\n' "$*" >> "$packet"
}

play_student() { # <dir>
  local dir="$1"
  local desk="$1/desk"
  local neat="$1/desk/tools/neat.sh"
  local sub t0 t1 t2 t3

  step "the student, task 0: the homework itself"
  # Task 0 goes first, before anything else on the desk: the branch it opens is what
  # the class will merge, so everything the desk does afterwards stays off it.
  t0="$(new_task "$dir" "class scores: four Ticks over a roster of twelve" \
        --verify "bash tools/check_submission.sh" --allow "submissions/$STUDENT")"
  [ "$t0" = "0" ] || die "the desk's first task came out as $t0, not 0"
  sub="$desk/EXP/$t0/submissions/$STUDENT"
  mkdir -p "$sub/evidence/run-1"
  cp "$STUDENTS/homework.py" "$sub/homework.py"
  cp "$STUDENTS/HANDOFF.md" "$sub/HANDOFF.md"
  cp "$STUDENTS/evidence/run-1/record.json" "$sub/evidence/run-1/record.json"
  cp "$STUDENTS/evidence/run-1/receipts.json" "$sub/evidence/run-1/receipts.json"
  cp "$STUDENTS/evidence/run-1/tick-viewer.html" "$sub/evidence/run-1/tick-viewer.html"
  cp "$HERE/cold-reader.txt" "$sub/cold-reader.txt"
  uncertain "$desk/EXP/$t0/.neat/tasks/$t0/packet.md" \
    '{?} Rounding: the mean is rounded to two decimals and the median is not; I could not decide which way to make the two agree.'
  uncertain "$desk/EXP/$t0/.neat/tasks/$t0/packet.md" \
    '{?} ColdReaderAnswer: the reader answered from my page alone and I kept their answer in the submission; I do not know whether the class wants it there or somewhere only the teacher can see.'
  bash "$neat" pack "$t0" > "$dir/log-pack-$t0.txt" 2>&1
  echo "  packed task $t0: $(grep -m1 '^score: ' "$desk/EXP/$t0/.neat/tasks/$t0/evidence/verify.txt")"

  step "the student, task 1: a page of my own questions (refused once, then landed)"
  t1="$(new_task "$dir" "a page of my own questions" \
        --verify "bash tools/check_notes.sh" --allow "notes")"
  mkdir -p "$desk/EXP/$t1/notes"
  cat > "$desk/EXP/$t1/notes/questions.md" <<'Q1'
# What I am unsure about

{?} Ticks: why is Stats one Tick and not two? Nothing I read says what a Tick is
Q1
  uncertain "$desk/EXP/$t1/.neat/tasks/$t1/packet.md" \
    '{?} OneQuestion: my own check wants two questions on the page and I only had one I could write down honestly.'
  bash "$neat" pack "$t1" > "$dir/log-pack-$t1-a.txt" 2>&1
  if bash "$neat" land "$t1" > "$dir/log-land-$t1-a.txt" 2>&1; then
    die "task $t1 landed on the first try; the desk's story needs the refusal (see $dir/log-land-$t1-a.txt)"
  fi
  echo "  refused, as it should be: $(grep -m1 -o 'score 1/2' "$desk/.neat/BOARD.md")"
  cat > "$desk/EXP/$t1/notes/questions.md" <<'Q2'
# What I am unsure about

{?} Ticks: why is Stats one Tick and not two? Nothing I read says what a Tick is
{?} Timings: the record keeps how long each calculation took, and the grader drops them
Q2
  bash "$neat" pack "$t1" > "$dir/log-pack-$t1-b.txt" 2>&1
  bash "$neat" land "$t1" > "$dir/log-land-$t1-b.txt" 2>&1
  echo "  landed task $t1: $(grep -m1 -o 'score 2/2' "$desk/.neat/BOARD.md")"

  step "the student, task 2: started and killed"
  # Before the undo, not after: a killed task keeps its branch, so its id stays taken.
  # An undone one does not, and the next `neat new` would hand the id out again.
  t2="$(new_task "$dir" "colour in the histogram")"
  bash "$neat" kill "$t2" > "$dir/log-kill-$t2.txt" 2>&1
  echo "  killed task $t2; nothing landed, exp/$t2 is kept"

  step "the student, task 3: landed, then taken straight back out"
  t3="$(new_task "$dir" "put the two questions in the order I asked them" \
        --verify "bash tools/check_notes.sh" --allow "notes")"
  cat > "$desk/EXP/$t3/notes/questions.md" <<'Q3'
# What I am unsure about

{?} Timings: the record keeps how long each calculation took, and the grader drops them
{?} Ticks: why is Stats one Tick and not two? Nothing I read says what a Tick is
Q3
  bash "$neat" pack "$t3" > "$dir/log-pack-$t3.txt" 2>&1
  bash "$neat" land "$t3" > "$dir/log-land-$t3.txt" 2>&1
  # Immediately: an undo reverts the landing commit, so it has to be the newest one or
  # the revert fights the board lines written since.
  bash "$neat" undo "$t3" > "$dir/log-undo-$t3.txt" 2>&1
  echo "  landed task $t3 and took it straight back out: $(grep -c "undo-task-$t3" "$desk/.neat/BOARD.md" | tr -d ' ') board line"
}

# --- the teacher ----------------------------------------------------------------

play_teacher() { # <dir>
  local dir="$1"
  local class="$1/class"
  step "the teacher: one command from the class repository"
  echo "  neat land 0 --from <desk-origin> exp/0 --verify \"bash assignments/scores/grader.sh\" --allow \"submissions/$STUDENT\""
  bash "$class/tools/neat.sh" land 0 --from "$dir/desk-origin.git" exp/0 \
      --verify "bash assignments/scores/grader.sh" \
      --allow "submissions/$STUDENT" > "$dir/log-land-class.txt" 2>&1 || {
        echo "the class landing failed; its log:" >&2
        cat "$dir/log-land-class.txt" >&2
        die "the class did not land the desk"
      }
  sed -n 's/^== /  /p;s/^score: /  score: /p;s/^cold reader: \([0-9]*\) of/  cold reader: \1 of/p' "$dir/log-land-class.txt" | head -20
}

class_board() { # <dir>  -- the Today lines of the class board, which is the gradebook
  local dir="$1"
  step "the class board, Today"
  "$PYTHON" - "$dir/class/.neat/BOARD.md" <<'PYEOF'
import sys
text = open(sys.argv[1], encoding='utf-8').read()
after = text.split('## Today', 1)[1] if '## Today' in text else ''
for line in after.splitlines():
    if line.startswith('- '):
        print(line)
PYEOF
}

# --- the whole thing --------------------------------------------------------------

build() { # <dir>
  local dir="$1"
  mkdir -p "$dir"
  dir="$(cd "$dir" && pwd)"
  [ -e "$dir/class" ] && die "$dir already holds a class; give me an empty directory"
  build_seed "$dir"
  build_class "$dir"
  build_desk "$dir"
  play_student "$dir"
  play_teacher "$dir"
  class_board "$dir"
  echo
  echo "class:  $dir/class"
  echo "desk:   $dir/desk   (bash $PYTO/experiments/classroom/tutor.py $dir/desk > tutor.html)"
}

# --- the selftest -----------------------------------------------------------------

FAILURES=0
check() { # <name> <what happened: 0 good>
  if [ "$2" -eq 0 ]; then echo "selftest $1: pass"; else echo "selftest $1: FAIL"; FAILURES=$((FAILURES + 1)); fi
}

newest_receipt() { # <class dir> <package>  -- the newest committed receipt for a package
  local d last=""
  for d in "$1"/.neat/landings/????????T??????Z-"$2"/; do
    [ -f "$d/receipt.json" ] && last="$d/receipt.json"
  done
  printf '%s\n' "$last"
}

selftest() { # <dir>
  local dir="$1"
  local class desk receipt rc
  build "$dir"
  dir="$(cd "$dir" && pwd)"
  class="$dir/class"; desk="$dir/desk"
  step "selftest"
  receipt="$(newest_receipt "$class" task-0)"

  rc=1; [ -n "$receipt" ] && grep -q '"passed": 4' "$receipt" && rc=0
  check "the landing receipt scores the four checks (\"passed\": 4)" "$rc"

  rc=1; [ -n "$receipt" ] && grep -q '"total": 4' "$receipt" && rc=0
  check 'the landing receipt keeps the total ("total": 4)' "$rc"

  rc=1; grep -q 'score 4/4' "$class/.neat/BOARD.md" && rc=0
  check "the class board line says score 4/4" "$rc"

  rc=1; grep -q 'graded here' "$class/.neat/BOARD.md" && rc=0
  check "the class board line says graded here" "$rc"

  rc=1; grep -q "exp/0, graded here" "$class/.neat/BOARD.md" && rc=0
  check "the class board line names the desk's branch" "$rc"

  # The cold reader's count rides in the same verifier output the receipt digests.
  rc=1; grep -q '^cold reader: 13 of 13 named$' "$(dirname "$receipt")/verifier.txt" && rc=0
  check "the landing keeps the cold reader's score line" "$rc"

  rc=1; grep -q '^combined: 17 of 17 ' "$(dirname "$receipt")/verifier.txt" && rc=0
  check "the landing keeps the combined count" "$rc"

  # The desk is the student's. A landing reads its branch and touches nothing there.
  rc=0
  [ -n "$(git -C "$desk" status --porcelain --untracked-files=all)" ] && rc=1
  [ -e "$desk/assignments" ] && rc=1
  [ -e "$desk/submissions/$STUDENT" ] && rc=1
  git -C "$desk" show-ref --verify --quiet refs/heads/exp/0 || rc=1
  git --git-dir="$dir/desk-origin.git" show-ref --verify --quiet refs/heads/exp/0 || rc=1
  check "the desk is untouched (clean, no class files, exp/0 still there)" "$rc"

  # The submission is in the class repository, under the one allowed path.
  rc=0
  for f in homework.py HANDOFF.md cold-reader.txt evidence/run-1/record.json \
           evidence/run-1/receipts.json evidence/run-1/tick-viewer.html; do
    [ -f "$class/submissions/$STUDENT/$f" ] || rc=1
  done
  git -C "$class" ls-files --error-unmatch "submissions/$STUDENT/homework.py" > /dev/null 2>&1 || rc=1
  check "the class holds submissions/$STUDENT/ and it is committed" "$rc"

  # The desk's own record: a refusal at 1 of 2, then a landing at 2 of 2, then an undo.
  rc=0
  ls "$desk"/.neat/landings/failed/*.json > /dev/null 2>&1 || rc=1
  grep -q 'score 1/2' "$desk/.neat/BOARD.md" || rc=1
  grep -q 'score 2/2' "$desk/.neat/BOARD.md" || rc=1
  grep -q '\*\*landed\*\* `undo-task-' "$desk/.neat/BOARD.md" || rc=1
  grep -q '\*\*killed\*\*' "$desk/.neat/BOARD.md" || rc=1
  grep -q '\*\*refused\*\*' "$desk/.neat/BOARD.md" || rc=1
  check "the desk's record holds a refusal, a retry, an undo and a kill" "$rc"

  echo
  if [ "$FAILURES" -eq 0 ]; then
    echo "selftest: all checks passed"
  else
    echo "selftest: $FAILURES check(s) FAILED"
  fi
  [ "$FAILURES" -eq 0 ]
}

# --- arguments ---------------------------------------------------------------------

case "${1:-}" in
  --selftest)
    if [ -n "${2:-}" ]; then
      selftest "$2"
    else
      TMP="$(mktemp -d "${TMPDIR:-/tmp}/make-class.XXXXXX")"
      trap 'rm -rf "$TMP"' EXIT
      selftest "$TMP"
    fi
    ;;
  ''|-h|--help) usage;;
  -*) die "unknown option $1";;
  *) build "$1";;
esac
