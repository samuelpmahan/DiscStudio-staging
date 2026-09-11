# Task 84

Intent: brain/stats distributions and hypothesis tests as Calculations fn.brain.stats.*: normal t chi2 binomial poisson pdf/pmf cdf ppf in pure python and scipy backends plus oc.brain.stats.sample through the effects handle's random; one-sample two-sample and paired t tests, chi-square test of independence and goodness of fit, one-way anova, mann-whitney u, shapiro-wilk; scipy.stats named as the reference for every one
Starting point: bc3f3bf9e25bd6149a98cd7640bbcf4d4ac1c09e (board: **started** `task-83`: brain ml foundation: the ml vertical's shared cor)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 9 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/records/ml.regression.json
- A  pyto/experiments/brain/stats/distributions.py
- A  pyto/experiments/brain/stats/distributions_cases.py
- A  pyto/experiments/brain/stats/hypothesis.py
- A  pyto/experiments/brain/stats/hypothesis_cases.py
- A  pyto/experiments/brain/stats/special.py
- A  pyto/experiments/brain/stats/test_distributions.py
- A  pyto/experiments/brain/stats/test_hypothesis.py
- A  pyto/experiments/brain/stats/test_special.py

```
pyto/experiments/brain/records/ml.regression.json  |  24 +-
 pyto/experiments/brain/stats/distributions.py      | 311 +++++++++++++++++
 .../experiments/brain/stats/distributions_cases.py |  84 +++++
 pyto/experiments/brain/stats/hypothesis.py         | 370 +++++++++++++++++++++
 pyto/experiments/brain/stats/hypothesis_cases.py   | 165 +++++++++
 pyto/experiments/brain/stats/special.py            | 189 +++++++++++
 pyto/experiments/brain/stats/test_distributions.py | 161 +++++++++
 pyto/experiments/brain/stats/test_hypothesis.py    | 127 +++++++
 pyto/experiments/brain/stats/test_special.py       |  53 +++
 9 files changed, 1472 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.4vqNevTSsh) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               158  OK
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
