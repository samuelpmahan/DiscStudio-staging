# Task 43: a class in a repo and the desk that teaches the tutor: classroom/make_class.sh builds a class repo and a student desk repo under a temp dir, lands the desk into the class graded by the class's verifier with a score, records the cold reader's answer and checks it mechanically, and tutor.py renders a tutoring page as a pure function of the desk's receipts, byte-identical on rerun

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Stop here first (the owner's rule)

Read this page, `pyto/BOARD.md`, and the packet. No fourth file yet. Then write the one question
you would answer by reading another hundred thousand tokens of code, and ask the owner instead.
His answer is worth more than the reading: the last session that read everything first was
confidently wrong about half of it, and one sentence from him undid each wrong half. The answer
goes on `pyto/questions.md` verbatim, as `{?} Label: ...` with his words, so the next agent starts
one stupid question deeper. Only then read further and do the work below.

## Get the code (once)

```
git clone -b claude/os-sprint-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/43
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/43:pyto/experiments/tasks/43/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 2a91d15 origin/exp/43 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{?} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

a class in a repo and the desk that teaches the tutor: classroom/make_class.sh builds a class repo and a student desk repo under a temp dir, lands the desk into the class graded by the class's verifier with a score, records the cold reader's answer and checks it mechanically, and tutor.py renders a tutoring page as a pure function of the desk's receipts, byte-identical on rerun

## Starting point

9cc413bafb37b07508a5a4ec4fb91efc49eb1006 (board: **started** `task-42`: the studio speaks the whole record: the site's PQ). MAIN may have moved since: `git log --oneline 2a91d15..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- A  pyto/experiments/classroom/README.md
- A  pyto/experiments/classroom/cold-reader.txt
- A  pyto/experiments/classroom/cold_reader.py
- A  pyto/experiments/classroom/make_class.sh
- A  pyto/experiments/classroom/test_classroom.py
- A  pyto/experiments/classroom/tutor.py
- M  pyto/scripts/check_all.sh

```
pyto/CHANGES.md                              |   1 +
 pyto/experiments/classroom/README.md         |  51 +++
 pyto/experiments/classroom/cold-reader.txt   |  36 ++
 pyto/experiments/classroom/cold_reader.py    | 159 ++++++++
 pyto/experiments/classroom/make_class.sh     | 578 +++++++++++++++++++++++++++
 pyto/experiments/classroom/test_classroom.py | 270 +++++++++++++
 pyto/experiments/classroom/tutor.py          | 518 ++++++++++++++++++++++++
 pyto/scripts/check_all.sh                    |   6 +-
 8 files changed, 1618 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `cd pyto/experiments/classroom && python3 -m unittest discover -s . -p 'test_*.py' && bash make_class.sh --selftest` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         248  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    249  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} ClassScore: the brief asks the grader for both `score: N of 4` with a landing receipt of `"passed": 4` AND a combined `score: N of M` over grade.py's four checks plus the cold reader's names (`e.g. score: 8 of 8`). Only one of those can be the receipt's score: land.sh keeps the LAST line matching `^score: [0-9]+ of [0-9]+` (land.sh, `SCORE_LINE="$(tr -d '\r' < "$WORK/verifier.txt" | grep -E '^score: [0-9]+ of [0-9]+' | tail -n 1 ...)`). Taken: the four mechanical checks are the landing's score (receipt `"passed": 4`, board `score 4/4`, as the brief's own selftest assertions ask), and the cold reader's count rides in the same verifier output as `cold reader: 13 of 13 named` with an explicit `combined: 17 of 17` line beside it. A single combined number would make the two halves one figure and lose which half failed, and the two halves are not the same kind of thing: one is a rubric, one is a floor under a human read. The owner decides whether the receipt should carry the combined total instead.
{?} ColdReaderFileCount: `cold_reader.py` counts every file the hand-off *names* (nine, including `tick_laws.py`, which the students page names in prose), while `grade.py` check 4 counts every file that is actually *beside* the hand-off (eight). So the two totals differ by one on the same page and both are right about different questions. Taken: the cold reader is checked against the page, because the page is all the reader was given. If the owner wants one number, check 4's directory listing is the one that cannot be padded by mentioning a file.
{?} ColdReaderAnswerLives: the canned cold-reader answer is committed inside `submissions/<student>/cold-reader.txt`, so the grade can be redone from the class repository alone; the grader leaves it out of the graded copy because grade.py check 4 asks the hand-off to account for every file beside it. That puts the reader's answer in the student's own submission, which the student could read before writing the page. The alternative is a teacher-only path outside the allowed paths, which no landing can write.
{?} DeskSeed: `neat land --from` is a merge, so the class repo and the desk must share a commit; make_class.sh cuts both from one seed, which puts the student's `tools/` and `BRIEF.md` at the class root too. A real class would fork the class repo into each desk instead, and then the seed is the assignment package itself. Not decided here because it changes what a desk starts with.
{?} NeatUndoFreesTheId: after `neat undo <id>` the id is handed out again by the next `neat new` (`next_id()` scans EXP dirs, landed packets and exp/* branches, and an undone landing leaves none of the three), so a fourth task on the desk came back as task 2 and collided with the undone one. Worked around in make_class.sh by reading the id back out of what `neat new` printed and by killing before undoing (a killed task keeps its branch, so its id stays taken). The line is `neat.sh:next_id()`; not fixed here because neat.sh is not in this task's allowed paths.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 43 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 43`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-43): a class in a repo and the desk that teaches the tutor: classroom/make_class.sh builds a class repo and a student desk repo under a temp dir, lands the desk into the class graded by the class's verifier with a score, records the cold reader's answer and checks it mechanically, and tutor.py renders a tutoring page as a pure function of the desk's receipts, byte-identical on rerun`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
