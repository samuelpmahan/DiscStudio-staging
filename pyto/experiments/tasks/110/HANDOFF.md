# Task 110: brain/ml the kerchoo slice: the ml facade defaults to the plan instead of to py - ml/core.py's dispatch reads px.exp.brain.result.backend.plan when the caller names no engine, the plan is extended to the ml calcs that have bench Parts, py stays the reference and is still selectable by name - with knn_predict and softmax_fit re-benched and their rows appended to px.exp.brain.bench.kerchoo, and a finding for every ml calc that has no faster engine to choose

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
git fetch origin exp/110
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/110:pyto/experiments/tasks/110/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff f4e1996 origin/exp/110 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/ml the kerchoo slice: the ml facade defaults to the plan instead of to py - ml/core.py's dispatch reads px.exp.brain.result.backend.plan when the caller names no engine, the plan is extended to the ml calcs that have bench Parts, py stays the reference and is still selectable by name - with knn_predict and softmax_fit re-benched and their rows appended to px.exp.brain.bench.kerchoo, and a finding for every ml calc that has no faster engine to choose

## Starting point

7cc30b68d957e318209260f395a9594a0b613ae7 (land(task-109): brain: the blok generation lane, filed as a Part - proposal.brain.blok_generation, a seeded motif-patterned variation over the brain's Calculations through crisp vary, judged by the oracle Parts for correct, the benchmark Parts for fast and neat delta for cheap, with the winners' recurring motifs mined back into the motif set; and the same as a next entry on the backend map Part). MAIN may have moved since: `git log --oneline f4e1996..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/backend/choose.py
- M  pyto/experiments/brain/backend/kerchoo.py
- M  pyto/experiments/brain/ml/classify.py
- M  pyto/experiments/brain/ml/core.py
- M  pyto/experiments/brain/ml/distance.py
- M  pyto/experiments/brain/ml/linear.py
- M  pyto/experiments/brain/ml/metrics.py
- M  pyto/experiments/brain/ml/multiclass.py
- M  pyto/experiments/brain/ml/nnet.py
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/choose.py  |   41 +
 pyto/experiments/brain/backend/kerchoo.py |   51 +
 pyto/experiments/brain/ml/classify.py     |    4 +-
 pyto/experiments/brain/ml/core.py         |   54 +-
 pyto/experiments/brain/ml/distance.py     |    8 +-
 pyto/experiments/brain/ml/linear.py       |    2 +-
 pyto/experiments/brain/ml/metrics.py      |    2 +-
 pyto/experiments/brain/ml/multiclass.py   |    2 +-
 pyto/experiments/brain/ml/nnet.py         |    2 +-
 pyto/experiments/brain/store/backend.json | 1912 ++++++++++++++++++-----------
 10 files changed, 1365 insertions(+), 713 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.HfDzfxPcN6) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               756  OK
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

{?} both runs are in the packet: the copy's venv and python 3.12.3 / numpy 2.5.3 / scipy 1.18.1 at
experiments/tasks/110/evidence/verify-python312-numpy253.txt. 756 tests, OK in both, every oracle
passing except the three deliberate py_gram_unguarded ones.
{?} `core.backend_of({})` is still "py". A calculation opts into the plan by passing its own
benchmark name - `core.backend_of(args, calc="knn_predict")` - so the change is visible at each
call site rather than hidden in the default, and the ml vertical's existing test that pins
backend_of({}) == "py" still says something true.
{?} six ml calcs are wired: knn_predict, softmax_fit, linreg_fit, logreg_fit, silhouette,
lasso_fit. logreg_fit's fastest recorded name is `newton-np`, which is not in the engine list its
facade validates, so the chooser ignores it and logreg_fit stays on py - that is
proposal.brain.backend.a_plan_may_only_name_an_engine_the_facade_has, with ml.pairwise, ml.tree_fit
and ml.kmeans in the same shape. The plan naming an engine a facade cannot run is ignored, never
obeyed, so a stale plan can only cost speed and never correctness.
{?} the plan now carries `by_calc` for 47 calcs across stats, data and ml, keyed "<vertical>.<calc>".
Their size tokens are each vertical's own words and cannot be turned into an element count the way
the backend's can, so what is recorded is the engine fastest at the largest recorded case and the
spread it won by - a facade with no size to reason about still gets the right default, but it
cannot switch engine with n the way the backend ops do.
{?} the kerchoo Part now has 12 rows. `before` is read out of the committed benchmark Parts;
`after` is the minimum of five runs on this machine.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 110 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 110`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-110): brain/ml the kerchoo slice: the ml facade defaults to the plan instead of to py - ml/core.py's dispatch reads px.exp.brain.result.backend.plan when the caller names no engine, the plan is extended to the ml calcs that have bench Parts, py stays the reference and is still selectable by name - with knn_predict and softmax_fit re-benched and their rows appended to px.exp.brain.bench.kerchoo, and a finding for every ml calc that has no faster engine to choose`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
