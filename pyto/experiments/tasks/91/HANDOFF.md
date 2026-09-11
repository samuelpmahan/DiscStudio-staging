# Task 91: brain harness (and the one line of ml/parts.py that is the same bug): a Store writes its store and records into a temporary directory unless it is an explicit record run (Store(commit=True), or BRAIN_RECORDS=commit), so no test can rewrite a tracked run record - a wall-clock duration inside a committed file leaves MAIN dirty and land.sh then refuses the NEXT landing, for whoever lands next rather than for whoever wrote it; reading is unchanged, load_store() still reads the committed store

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
git fetch origin exp/91
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/91:pyto/experiments/tasks/91/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 6cadc5d origin/exp/91 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain harness (and the one line of ml/parts.py that is the same bug): a Store writes its store and records into a temporary directory unless it is an explicit record run (Store(commit=True), or BRAIN_RECORDS=commit), so no test can rewrite a tracked run record - a wall-clock duration inside a committed file leaves MAIN dirty and land.sh then refuses the NEXT landing, for whoever lands next rather than for whoever wrote it; reading is unchanged, load_store() still reads the committed store

## Starting point

a4db7c65fe9b7376574412a3cc13f298f0e16663 (land(task-85): brain/data dataframe-like Calculations fn.brain.data.* over the columns/rows dataset shape: select project filter group-by with aggregates join pivot sort window/rolling and missing-value handling, with py and np backends where the shape pays, dataset Parts px.exp.brain.data.* and oc.brain.data.load that reads csv and json through the effects handle's read_text). MAIN may have moved since: `git log --oneline 6cadc5d..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/harness.py
- M  pyto/experiments/brain/ml/build.py
- M  pyto/experiments/brain/ml/parts.py
- M  pyto/experiments/brain/test_harness.py

```
pyto/experiments/brain/harness.py      | 61 ++++++++++++++++++++++++++++++----
 pyto/experiments/brain/ml/build.py     |  4 ++-
 pyto/experiments/brain/ml/parts.py     | 23 +++++++++++--
 pyto/experiments/brain/test_harness.py | 52 +++++++++++++++++++++++++++++
 4 files changed, 130 insertions(+), 10 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.Wr1fblvI3z) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               314  OK
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

{?} this task changes three files in pyto/experiments/brain: harness.py (the shared Store), and
ml/parts.py + ml/build.py, which are the ml vertical's own separate Store. Crossing that boundary
was not the plan. The reason: pyto/experiments/brain/ml/parts.py `Store.run` wrote its run record
into the tracked records/ unconditionally, so `build.build(save=False)` - which the ml tests call -
rewrote records/ml.regression.json on every suite run, including the check_all that land.sh runs on
MAIN inside a landing. land.sh then stops at step 5 with "the tree changed while the suites ran".
That refused five landings tonight across three verticals (tasks 85, 87 twice, 88 twice), including
the ml vertical's own, and no vertical could land anything until it was fixed. The change is the
same one the harness gets and preserves the explicit run: `python -m experiments.brain.ml.build`
still writes the committed record (build(save=True) passes commit=True); a test writes a tempdir.
{?} reading and writing now default to different places: `load_store()` still reads the committed
`store/`, `save()` and `run()` write a temporary directory unless Store(commit=True) or
BRAIN_RECORDS=commit. That asymmetry is deliberate - a vertical must see the others' Parts without
being able to overwrite the repository from a test - but `Store().save("backend")` now returns a
path under /tmp and nothing warns. The path is returned; read it rather than assuming.
{?} ml/parts.py `save()` is left alone: it writes store/ml.json unconditionally, and only
build(save=True) calls it, so no test rewrites it today. If a test ever calls it, it will dirty
MAIN the same way.
{?} BRAIN_RECORDS is read at Store construction, not cached at import, so a test may set and unset
it around a block. An explicit commit= flag beats the environment either way.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 91 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 91`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-91): brain harness (and the one line of ml/parts.py that is the same bug): a Store writes its store and records into a temporary directory unless it is an explicit record run (Store(commit=True), or BRAIN_RECORDS=commit), so no test can rewrite a tracked run record - a wall-clock duration inside a committed file leaves MAIN dirty and land.sh then refuses the NEXT landing, for whoever lands next rather than for whoever wrote it; reading is unchanged, load_store() still reads the committed store`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
