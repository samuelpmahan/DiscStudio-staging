# Task 77: USE.md section 4 still teaches the rule the owner overturned: 'the Calculations of one Tick are parallel branches, so none of them may read another's produce'; it now says what the kernel does since task 57 (inside a Tick the Calculations are a sequence in declared order, a later one may bind an earlier sibling's result, a Tick with no sibling reads may run at once, a read of a later sibling and two siblings on one address are refused) with a chained Tick in the block and its printed output, and every other page that repeats the old sentence is corrected

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
git fetch origin exp/77
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/77:pyto/experiments/tasks/77/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff c34a4e8 origin/exp/77 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

USE.md section 4 still teaches the rule the owner overturned: 'the Calculations of one Tick are parallel branches, so none of them may read another's produce'; it now says what the kernel does since task 57 (inside a Tick the Calculations are a sequence in declared order, a later one may bind an earlier sibling's result, a Tick with no sibling reads may run at once, a read of a later sibling and two siblings on one address are refused) with a chained Tick in the block and its printed output, and every other page that repeats the old sentence is corrected

## Starting point

56f1bf6acc6f129d8dd3183f0ce44d81bc60a3e7 (land(task-76): a landing finishes on its own when a candidate deletes a file and starts ignoring it: land.sh step 5 staged each dirty path with git add -A, which is fatal for a deleted path that .gitignore now covers (task 75's landing passed every suite and died at the commit; finished by hand); the stage step now removes a deleted path from the index and adds the rest, and the selftest lands a candidate that deletes and ignores one file). MAIN may have moved since: `git log --oneline c34a4e8..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/USE.md

```
pyto/USE.md | 33 +++++++++++++++++++++------------
 1 file changed, 21 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_use && ! grep -rn 'parallel branches, so none of them' USE.md README.md research/START-HERE.md LANDING.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.EZOANQpHvP) (evidence/check_all.txt)
    suite                         tests  status
    library                         435  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 77 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 77`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-77): USE.md section 4 still teaches the rule the owner overturned: 'the Calculations of one Tick are parallel branches, so none of them may read another's produce'; it now says what the kernel does since task 57 (inside a Tick the Calculations are a sequence in declared order, a later one may bind an earlier sibling's result, a Tick with no sibling reads may run at once, a read of a later sibling and two siblings on one address are refused) with a chained Tick in the block and its printed output, and every other page that repeats the old sentence is corrected`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
