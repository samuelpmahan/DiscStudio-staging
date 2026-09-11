# Task 93

Intent: brain/backend the evidence and the tournaments: four more ops on the facade (norm, cholesky, inv, trace), an oracle Part per engine per case against the named numpy or scipy reference and a benchmark Part per engine at three sizes for all sixteen, three tournaments whose criteria are written into the bracket Part before anything is judged and whose judge is a function of the recorded oracle and benchmark Parts and the candidate's own source (a guarded pure-python pairwise distance against numpy broadcasting and scipy.cdist; top-k by full sort, by heap and by argpartition; and how a large array sits in the store: nested lists against flat-plus-shape against base64 float64), the vertical's findings and its map Part, and the store and records they leave behind; harness.outline caps what an oracle Part keeps of a large value, which is what takes store/backend.json from ten megabytes to under four hundred kilobytes
Starting point: b6b531bd8cd680399f62eb643493c960997c36ef (land(task-89): brain ml trees: cart with gini/entropy/squared-error and two split searches (every midpoint by sorting, and equal-width histogram bins), a small bootstrapped random forest with seeded feature subsets, small gradient boosting on squared loss, learning curves as Parts, oracles against hand-built trees and scipy, and the split-search tournament with its criteria recorded before judging)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 27 files, see below
Evidence: suite exit 0, see below

## Candidate

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
