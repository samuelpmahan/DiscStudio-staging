# Task 89

Intent: brain ml trees: cart with gini/entropy/squared-error and two split searches (every midpoint by sorting, and equal-width histogram bins), a small bootstrapped random forest with seeded feature subsets, small gradient boosting on squared loss, learning curves as Parts, oracles against hand-built trees and scipy, and the split-search tournament with its criteria recorded before judging
Starting point: a9f3476abcdca3c49000fb6ebc0092715cf5e958 (land(task-84): brain/stats distributions and hypothesis tests as Calculations fn.brain.stats.*: normal t chi2 binomial poisson pdf/pmf cdf ppf in pure python and scipy backends plus oc.brain.stats.sample through the effects handle's random; one-sample two-sample and paired t tests, chi-square test of independence and goodness of fit, one-way anova, mann-whitney u, shapiro-wilk; scipy.stats named as the reference for every one)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 23 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/ml/build.py
- M  pyto/experiments/brain/ml/calcs.py
- A  pyto/experiments/brain/ml/classify.py
- M  pyto/experiments/brain/ml/metrics.py
- A  pyto/experiments/brain/ml/nnet.py
- M  pyto/experiments/brain/ml/parts.py
- M  pyto/experiments/brain/ml/resample.py
- A  pyto/experiments/brain/ml/test_classify.py
- A  pyto/experiments/brain/ml/test_nnet.py
- M  pyto/experiments/brain/ml/test_store.py
- A  pyto/experiments/brain/ml/test_tournament.py
- A  pyto/experiments/brain/ml/test_trees.py
- A  pyto/experiments/brain/ml/test_unsup.py
- A  pyto/experiments/brain/ml/test_validate.py
- A  pyto/experiments/brain/ml/tournament.py
- A  pyto/experiments/brain/ml/trees.py
- A  pyto/experiments/brain/ml/unsup.py
- A  pyto/experiments/brain/ml/validate.py
- A  pyto/experiments/brain/records/ml.classification.json
- M  pyto/experiments/brain/records/ml.regression.json
- A  pyto/experiments/brain/records/ml.trees.json
- A  pyto/experiments/brain/records/ml.unsupervised.json
- M  pyto/experiments/brain/store/ml.json

```
pyto/experiments/brain/ml/build.py                 |   734 +-
 pyto/experiments/brain/ml/calcs.py                 |    35 +-
 pyto/experiments/brain/ml/classify.py              |   395 +
 pyto/experiments/brain/ml/metrics.py               |    23 +-
 pyto/experiments/brain/ml/nnet.py                  |   282 +
 pyto/experiments/brain/ml/parts.py                 |   325 +-
 pyto/experiments/brain/ml/resample.py              |    24 +-
 pyto/experiments/brain/ml/test_classify.py         |   231 +
 pyto/experiments/brain/ml/test_nnet.py             |   138 +
 pyto/experiments/brain/ml/test_store.py            |    47 +-
 pyto/experiments/brain/ml/test_tournament.py       |    71 +
 pyto/experiments/brain/ml/test_trees.py            |   219 +
 pyto/experiments/brain/ml/test_unsup.py            |   190 +
 pyto/experiments/brain/ml/test_validate.py         |    71 +
 pyto/experiments/brain/ml/tournament.py            |   330 +
 pyto/experiments/brain/ml/trees.py                 |   468 +
 pyto/experiments/brain/ml/unsup.py                 |   385 +
 pyto/experiments/brain/ml/validate.py              |    95 +
 .../brain/records/ml.classification.json           |  7201 +++
 pyto/experiments/brain/records/ml.regression.json  |    24 +-
 pyto/experiments/brain/records/ml.trees.json       | 13142 +++++
 .../experiments/brain/records/ml.unsupervised.json |  2937 ++
 pyto/experiments/brain/store/ml.json               | 51482 +++++++++++++++++--
 23 files changed, 73125 insertions(+), 5724 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.sRqh4A70Vc) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               481  OK
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
