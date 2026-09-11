# Task 88

Intent: brain ml classification: logistic regression (gradient descent and newton/irls, one-vs-rest), k nearest neighbours (classify and regress, euclidean/manhattan, uniform/distance weights), gaussian and multinomial naive bayes, each fit and predict a separate Calculation over a json-able model Part, with scipy oracles, tests and py/np benchmarks, and the ml vertical's parts writers rerouted through the landed shared harness
Starting point: 67a55fe152b388f79dedc76ba30193cb71c4fa8f (board: **started** `task-87`: brain/backend the facade: fn.brain.backend.<op> w)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 12 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/ml/build.py
- M  pyto/experiments/brain/ml/calcs.py
- A  pyto/experiments/brain/ml/classify.py
- M  pyto/experiments/brain/ml/metrics.py
- M  pyto/experiments/brain/ml/parts.py
- A  pyto/experiments/brain/ml/test_classify.py
- M  pyto/experiments/brain/ml/test_store.py
- A  pyto/experiments/brain/ml/test_tournament.py
- A  pyto/experiments/brain/ml/tournament.py
- A  pyto/experiments/brain/records/ml.classification.json
- M  pyto/experiments/brain/records/ml.regression.json
- M  pyto/experiments/brain/store/ml.json

```
pyto/experiments/brain/ml/build.py                 |   238 +-
 pyto/experiments/brain/ml/calcs.py                 |    12 +-
 pyto/experiments/brain/ml/classify.py              |   395 +
 pyto/experiments/brain/ml/metrics.py               |    23 +-
 pyto/experiments/brain/ml/parts.py                 |   291 +-
 pyto/experiments/brain/ml/test_classify.py         |   231 +
 pyto/experiments/brain/ml/test_store.py            |    49 +-
 pyto/experiments/brain/ml/test_tournament.py       |    75 +
 pyto/experiments/brain/ml/tournament.py            |   185 +
 .../brain/records/ml.classification.json           |  7201 +++++++
 pyto/experiments/brain/records/ml.regression.json  |    24 +-
 pyto/experiments/brain/store/ml.json               | 20040 ++++++++++++++++---
 12 files changed, 25465 insertions(+), 3299 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.lrvCEb6OJx) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               193  OK
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
