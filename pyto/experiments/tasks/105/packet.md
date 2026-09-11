# Task 105

Intent: brain ml out-of-bag: a random forest scores itself on the rows each of its trees never saw, so a held-out number comes free with the fit; the bag each tree drew is recorded, oob_predict votes only the trees that missed a row, and the oob score is oracled against a real held-out split
Starting point: f8f15fa059e4aae8247fac2c52e7685806cf127c (board: **started** `task-104`: brain/stats and brain/data, closing two named st)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 6 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/ml/build.py
- M  pyto/experiments/brain/ml/calcs.py
- A  pyto/experiments/brain/ml/test_oob.py
- M  pyto/experiments/brain/ml/trees.py
- M  pyto/experiments/brain/records/ml.trees.json
- M  pyto/experiments/brain/store/ml.json

```
pyto/experiments/brain/ml/build.py           |   56 +-
 pyto/experiments/brain/ml/calcs.py           |    1 +
 pyto/experiments/brain/ml/test_oob.py        |   82 +
 pyto/experiments/brain/ml/trees.py           |   62 +
 pyto/experiments/brain/records/ml.trees.json | 3269 ++++++++++++++++++++++-
 pyto/experiments/brain/store/ml.json         | 3674 +++++++++++++++++++++++++-
 6 files changed, 7056 insertions(+), 88 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.z79hsbHSeU) (evidence/check_all.txt)
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

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
