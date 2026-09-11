# Task 102

Intent: brain ml multiclass: softmax (multinomial) logistic regression beside the one-vs-rest one, and gradient boosting for classification on the logistic loss with its second-order step, each fit and predict a separate Calculation over a json-able model Part, oracled against scipy minimising the same cross-entropy and against the probabilities the fit itself recorded
Starting point: 206d6a1ffc475e272edf99244cfd6ba7e4270ffd (board: **killed** `task-88`: nothing landed; exp/88 is kept)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 5 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/ml/build.py
- M  pyto/experiments/brain/ml/calcs.py
- A  pyto/experiments/brain/ml/multiclass.py
- A  pyto/experiments/brain/ml/test_multiclass.py
- M  pyto/experiments/brain/store/ml.json

```
pyto/experiments/brain/ml/build.py           |  125 ++-
 pyto/experiments/brain/ml/calcs.py           |    9 +-
 pyto/experiments/brain/ml/multiclass.py      |  268 +++++++
 pyto/experiments/brain/ml/test_multiclass.py |  193 +++++
 pyto/experiments/brain/store/ml.json         | 1112 ++++++++++++++++++++++++--
 5 files changed, 1613 insertions(+), 94 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.K91tla6ao1) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               722  OK
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
