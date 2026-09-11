# Task 95

Intent: brain ml distances: the four calculations that each built their own n-by-n matrix (knn_predict, silhouette, kmeans, dbscan) route through fn.brain.backend.pairwise as one more backend, oracled against their own spelling and against scipy cdist, with the bracket that decides which spelling deserves the default; and exp/88 is killed, its candidate having landed inside task-89
Starting point: 7e1b03c57637f26460f09409557287ae158a6aba (board: **started** `task-94`: brain/stats and brain/data, the second wave: kolm)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 20 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/ml/build.py
- M  pyto/experiments/brain/ml/calcs.py
- M  pyto/experiments/brain/ml/classify.py
- M  pyto/experiments/brain/ml/core.py
- A  pyto/experiments/brain/ml/distance.py
- M  pyto/experiments/brain/ml/linear.py
- M  pyto/experiments/brain/ml/metrics.py
- M  pyto/experiments/brain/ml/nnet.py
- M  pyto/experiments/brain/ml/parts.py
- M  pyto/experiments/brain/ml/resample.py
- A  pyto/experiments/brain/ml/test_distance.py
- M  pyto/experiments/brain/ml/test_store.py
- M  pyto/experiments/brain/ml/tournament.py
- M  pyto/experiments/brain/ml/trees.py
- M  pyto/experiments/brain/ml/unsup.py
- M  pyto/experiments/brain/records/ml.classification.json
- M  pyto/experiments/brain/records/ml.regression.json
- M  pyto/experiments/brain/records/ml.trees.json
- M  pyto/experiments/brain/records/ml.unsupervised.json
- M  pyto/experiments/brain/store/ml.json

```
pyto/experiments/brain/ml/build.py                 |   115 +-
 pyto/experiments/brain/ml/calcs.py                 |     4 +-
 pyto/experiments/brain/ml/classify.py              |    39 +-
 pyto/experiments/brain/ml/core.py                  |    16 +-
 pyto/experiments/brain/ml/distance.py              |   146 +
 pyto/experiments/brain/ml/linear.py                |     8 +-
 pyto/experiments/brain/ml/metrics.py               |    28 +-
 pyto/experiments/brain/ml/nnet.py                  |    10 +-
 pyto/experiments/brain/ml/parts.py                 |   113 +-
 pyto/experiments/brain/ml/resample.py              |     6 +-
 pyto/experiments/brain/ml/test_distance.py         |   103 +
 pyto/experiments/brain/ml/test_store.py            |    44 +
 pyto/experiments/brain/ml/tournament.py            |   111 +-
 pyto/experiments/brain/ml/trees.py                 |    10 +-
 pyto/experiments/brain/ml/unsup.py                 |    42 +-
 .../brain/records/ml.classification.json           |  6246 +-
 pyto/experiments/brain/records/ml.regression.json  |  4712 +-
 pyto/experiments/brain/records/ml.trees.json       |  6200 +-
 .../experiments/brain/records/ml.unsupervised.json |  2092 +-
 pyto/experiments/brain/store/ml.json               | 64841 ++++++++++++++-----
 20 files changed, 59446 insertions(+), 25440 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.6viLawgIDg) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               665  OK
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

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
