# Task 83

Intent: brain ml foundation: the ml vertical's shared core (backend dispatch py/np, matrix helpers, seeded generators, part/oracle/bench/record writers) plus linear regression closed form and gradient descent, ridge, regression metrics (mse/mae/r2) and seeded train-test split and k-fold, each a Calculation fn.brain.ml.<name> with oracle Parts, tests and benchmarks
Starting point: e6f06534cee445bb54fa685e40bb9f44228d8489 (board: **started** `task-82`: brain/stats descriptive and correlation as Calcul)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 15 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/ml/__init__.py
- A  pyto/experiments/brain/ml/build.py
- A  pyto/experiments/brain/ml/calcs.py
- A  pyto/experiments/brain/ml/core.py
- A  pyto/experiments/brain/ml/linear.py
- A  pyto/experiments/brain/ml/metrics.py
- A  pyto/experiments/brain/ml/parts.py
- A  pyto/experiments/brain/ml/resample.py
- A  pyto/experiments/brain/ml/test_core.py
- A  pyto/experiments/brain/ml/test_linear.py
- A  pyto/experiments/brain/ml/test_metrics.py
- A  pyto/experiments/brain/ml/test_resample.py
- A  pyto/experiments/brain/ml/test_store.py
- A  pyto/experiments/brain/records/ml.regression.json
- A  pyto/experiments/brain/store/ml.json

```
pyto/experiments/brain/ml/__init__.py             |    1 +
 pyto/experiments/brain/ml/build.py                |  359 ++
 pyto/experiments/brain/ml/calcs.py                |   62 +
 pyto/experiments/brain/ml/core.py                 |  236 +
 pyto/experiments/brain/ml/linear.py               |  175 +
 pyto/experiments/brain/ml/metrics.py              |  221 +
 pyto/experiments/brain/ml/parts.py                |  266 +
 pyto/experiments/brain/ml/resample.py             |  210 +
 pyto/experiments/brain/ml/test_core.py            |   75 +
 pyto/experiments/brain/ml/test_linear.py          |  121 +
 pyto/experiments/brain/ml/test_metrics.py         |  126 +
 pyto/experiments/brain/ml/test_resample.py        |  107 +
 pyto/experiments/brain/ml/test_store.py           |   83 +
 pyto/experiments/brain/records/ml.regression.json | 4128 ++++++++++++
 pyto/experiments/brain/store/ml.json              | 7141 +++++++++++++++++++++
 15 files changed, 13311 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.tRyrvlUMyB) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               117  OK
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
