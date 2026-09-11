# Task 106: brain/backend the three findings the night itself produced, as Parts: the judge could not be another session (no route to a scoped worker existed, so every branch was written in one session and the judge is a pure function of the recorded oracle and benchmark Parts - weaker as independence, stronger as evidence, and the bracket says which it is), a copy that did not really merge claims MAIN's commits (neat update stops on a regenerated record, and bringing the copy forward by restoring that one file leaves MAIN's tip not an ancestor, so land.sh computes the candidate from the task's starting point and a verified receipt refuses), and a case that names its engines keeps the refusal in the record; plus the store and the map rebuilt over them

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
git fetch origin exp/106
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/106:pyto/experiments/tasks/106/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff dd7bd4b origin/exp/106 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/backend the three findings the night itself produced, as Parts: the judge could not be another session (no route to a scoped worker existed, so every branch was written in one session and the judge is a pure function of the recorded oracle and benchmark Parts - weaker as independence, stronger as evidence, and the bracket says which it is), a copy that did not really merge claims MAIN's commits (neat update stops on a regenerated record, and bringing the copy forward by restoring that one file leaves MAIN's tip not an ancestor, so land.sh computes the candidate from the task's starting point and a verified receipt refuses), and a case that names its engines keeps the refusal in the record; plus the store and the map rebuilt over them

## Starting point

254f751e28aea4736c0d4dd0d99dfc9325f1be52 (land(task-105): brain ml out-of-bag: a random forest scores itself on the rows each of its trees never saw, so a held-out number comes free with the fit; the bag each tree drew is recorded, oob_predict votes only the trees that missed a row, and the oob score is oracled against a real held-out split). MAIN may have moved since: `git log --oneline dd7bd4b..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/backend/summary.py
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/summary.py |   42 +
 pyto/experiments/brain/store/backend.json | 1499 +++++++++++++++--------------
 2 files changed, 801 insertions(+), 740 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.TOaE62bxLV) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               751  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

{?} both runs are in the packet: the copy's venv (python 3.11, numpy 2.4.6) through the Verify
line, and python 3.12.3 with numpy 2.5.3 and scipy 1.18.1 at
experiments/tasks/106/evidence/verify-python312-numpy253.txt. 751 tests, OK in both.
{?} `the_judge_could_not_be_another_session` is a finding about how this vertical's own evidence
was made, and it is written down because a reader a month from now cannot tell a mechanical judge
from an independent one by looking at the bracket's scores. Every bracket names its judge.
{?} `a_copy_that_did_not_really_merge_claims_mains_commits` is a finding about neat, not about the
brain. It is recorded here rather than fixed here: the brain verticals do not own pyto/scripts, and
the proposal (neat update should not report success unless MAIN's tip is an ancestor afterwards) is
a one-line check someone who does own it should make.
{?} nothing in this task changes a Calculation or an engine: the only source change is
backend/summary.py, and the store and records move because they were rebuilt over it. The brain
suite is unchanged in count except for what the new Parts add to the navigate tests.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 106 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 106`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-106): brain/backend the three findings the night itself produced, as Parts: the judge could not be another session (no route to a scoped worker existed, so every branch was written in one session and the judge is a pure function of the recorded oracle and benchmark Parts - weaker as independence, stronger as evidence, and the bracket says which it is), a copy that did not really merge claims MAIN's commits (neat update stops on a regenerated record, and bringing the copy forward by restoring that one file leaves MAIN's tip not an ancestor, so land.sh computes the candidate from the task's starting point and a verified receipt refuses), and a case that names its engines keeps the refusal in the record; plus the store and the map rebuilt over them`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
