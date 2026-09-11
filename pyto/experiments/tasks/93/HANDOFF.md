# Task 93: brain/backend the evidence and the tournaments: four more ops on the facade (norm, cholesky, inv, trace), an oracle Part per engine per case against the named numpy or scipy reference and a benchmark Part per engine at three sizes for all sixteen, three tournaments whose criteria are written into the bracket Part before anything is judged and whose judge is a function of the recorded oracle and benchmark Parts and the candidate's own source (a guarded pure-python pairwise distance against numpy broadcasting and scipy.cdist; top-k by full sort, by heap and by argpartition; and how a large array sits in the store: nested lists against flat-plus-shape against base64 float64), the vertical's findings and its map Part, and the store and records they leave behind; harness.outline caps what an oracle Part keeps of a large value, which is what takes store/backend.json from ten megabytes to under four hundred kilobytes

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
git fetch origin exp/93
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/93:pyto/experiments/tasks/93/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 3e2ef2d origin/exp/93 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/backend the evidence and the tournaments: four more ops on the facade (norm, cholesky, inv, trace), an oracle Part per engine per case against the named numpy or scipy reference and a benchmark Part per engine at three sizes for all sixteen, three tournaments whose criteria are written into the bracket Part before anything is judged and whose judge is a function of the recorded oracle and benchmark Parts and the candidate's own source (a guarded pure-python pairwise distance against numpy broadcasting and scipy.cdist; top-k by full sort, by heap and by argpartition; and how a large array sits in the store: nested lists against flat-plus-shape against base64 float64), the vertical's findings and its map Part, and the store and records they leave behind; harness.outline caps what an oracle Part keeps of a large value, which is what takes store/backend.json from ten megabytes to under four hundred kilobytes

## Starting point

b6b531bd8cd680399f62eb643493c960997c36ef (land(task-89): brain ml trees: cart with gini/entropy/squared-error and two split searches (every midpoint by sorting, and equal-width histogram bins), a small bootstrapped random forest with seeded feature subsets, small gradient boosting on squared loss, learning curves as Parts, oracles against hand-built trees and scipy, and the split-search tournament with its criteria recorded before judging). MAIN may have moved since: `git log --oneline 3e2ef2d..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/experiments/brain/backend/cases.py
- A  pyto/experiments/brain/backend/evidence.py
- M  pyto/experiments/brain/backend/ops.py
- A  pyto/experiments/brain/backend/summary.py
- A  pyto/experiments/brain/backend/test_evidence.py
- M  pyto/experiments/brain/backend/test_ops.py
- A  pyto/experiments/brain/backend/test_tournament.py
- A  pyto/experiments/brain/backend/tournament.py
- M  pyto/experiments/brain/harness.py
- A  pyto/experiments/brain/records/brain_backend_argsort.json
- A  pyto/experiments/brain/records/brain_backend_cholesky.json
- A  pyto/experiments/brain/records/brain_backend_cumsum.json
- A  pyto/experiments/brain/records/brain_backend_eig.json
- A  pyto/experiments/brain/records/brain_backend_fft.json
- A  pyto/experiments/brain/records/brain_backend_histogram.json
- A  pyto/experiments/brain/records/brain_backend_inv.json
- A  pyto/experiments/brain/records/brain_backend_lstsq.json
- A  pyto/experiments/brain/records/brain_backend_matmul.json
- A  pyto/experiments/brain/records/brain_backend_norm.json
- A  pyto/experiments/brain/records/brain_backend_pairwise.json
- A  pyto/experiments/brain/records/brain_backend_select_k.json
- A  pyto/experiments/brain/records/brain_backend_solve.json
- A  pyto/experiments/brain/records/brain_backend_sort.json
- A  pyto/experiments/brain/records/brain_backend_svd.json
- A  pyto/experiments/brain/records/brain_backend_trace.json
- M  pyto/experiments/brain/store/backend.json
- M  pyto/experiments/brain/test_harness.py

```
pyto/experiments/brain/backend/cases.py            |    98 +-
 pyto/experiments/brain/backend/evidence.py         |   138 +
 pyto/experiments/brain/backend/ops.py              |   175 +-
 pyto/experiments/brain/backend/summary.py          |   193 +
 pyto/experiments/brain/backend/test_evidence.py    |    92 +
 pyto/experiments/brain/backend/test_ops.py         |    21 +-
 pyto/experiments/brain/backend/test_tournament.py  |   120 +
 pyto/experiments/brain/backend/tournament.py       |   372 +
 pyto/experiments/brain/harness.py                  |    52 +-
 .../brain/records/brain_backend_argsort.json       |   190 +
 .../brain/records/brain_backend_cholesky.json      |   328 +
 .../brain/records/brain_backend_cumsum.json        |   358 +
 .../brain/records/brain_backend_eig.json           |   340 +
 .../brain/records/brain_backend_fft.json           |   562 +
 .../brain/records/brain_backend_histogram.json     |   244 +
 .../brain/records/brain_backend_inv.json           |   328 +
 .../brain/records/brain_backend_lstsq.json         |   205 +
 .../brain/records/brain_backend_matmul.json        |   310 +
 .../brain/records/brain_backend_norm.json          |   589 +
 .../brain/records/brain_backend_pairwise.json      |  1192 ++
 .../brain/records/brain_backend_select_k.json      |   385 +
 .../brain/records/brain_backend_solve.json         |   202 +
 .../brain/records/brain_backend_sort.json          |   694 +
 .../brain/records/brain_backend_svd.json           |   178 +
 .../brain/records/brain_backend_trace.json         |   163 +
 pyto/experiments/brain/store/backend.json          | 18295 ++++++++++++++++++-
 pyto/experiments/brain/test_harness.py             |    32 +
 27 files changed, 25677 insertions(+), 179 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.Ai3rWiRV8e) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               503  OK
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

{?} the oracle value cap (harness.outline, 65536 bytes of json) changes what an oracle Part keeps,
not what it decides: the verdict is still computed on the full values. Before it, the three
pairwise tournaments alone put 6.5 MB of decimal text into store/backend.json (10 MB on disk);
after it the whole backend store is 460 KB. The cap is 64 KB rather than something tighter because the ml vertical delegates its oracle writer to this harness and its committed store holds Parts up to 59 KB; a tighter cap rewrote those and its store test went red. If a reader needs the full matrix back, it is not in
the Part - only its shape, digest and first numbers are.
{?} the judge in all three tournaments is `evidence`, a function that scores from the candidate's
own oracle Part, its benchmark Part at the largest size, and its source (lines, docstring). It did
not build any candidate, it cannot be talked into anything, and every score points at the Part it
came from. It is not a model judge: this session had no way to spawn one, and the bracket records
which judge scored it either way.
{?} three oracle Parts in the store are FAILING on purpose: pairwise_tournament.py_gram_unguarded_*.
They are the record of why the guarded gram expansion exists (the unguarded one is wrong in its
eighth digit where two points are close). `python -m experiments.brain.map` prints them under
"oracles: N (3 failed)", which reads as an alarm and is meant to.
{?} the sp engine of cumsum, sort, argsort, select_k and trace is numpy's: scipy has no distinct
call for these. It is said out loud in each docstring rather than dropped, so the oracle table
stays square (every op, every engine, one verdict).
{?} the committed store/backend.json and records/brain_backend_*.json hold wall-clock numbers, so
they differ byte for byte on every rebuild. Nothing regenerates them except an explicit record run
(BRAIN_RECORDS=commit python -m experiments.brain.backend.<module>); no test touches them.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 93 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 93`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-93): brain/backend the evidence and the tournaments: four more ops on the facade (norm, cholesky, inv, trace), an oracle Part per engine per case against the named numpy or scipy reference and a benchmark Part per engine at three sizes for all sixteen, three tournaments whose criteria are written into the bracket Part before anything is judged and whose judge is a function of the recorded oracle and benchmark Parts and the candidate's own source (a guarded pure-python pairwise distance against numpy broadcasting and scipy.cdist; top-k by full sort, by heap and by argpartition; and how a large array sits in the store: nested lists against flat-plus-shape against base64 float64), the vertical's findings and its map Part, and the store and records they leave behind; harness.outline caps what an oracle Part keeps of a large value, which is what takes store/backend.json from ten megabytes to under four hundred kilobytes`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
