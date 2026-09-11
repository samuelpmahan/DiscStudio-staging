# Task 90

Intent: brain/stats regression, intervals and effect sizes: OLS by three solvers that are the candidates of a tournament (normal equations, householder QR, numpy lstsq) behind one facade with standard errors, t and F, R2 and adjusted R2; ridge with the intercept unpenalised; logistic by IRLS and by gradient descent; t, welch, wilson and chi-square confidence intervals; oc.brain.stats.bootstrap that resamples through the effects handle so a record replays to the same interval; cohen's d, hedges' g, glass's delta, eta and omega squared, cramer's v and the rank-biserial correlation
Starting point: a9f3476abcdca3c49000fb6ebc0092715cf5e958 (land(task-84): brain/stats distributions and hypothesis tests as Calculations fn.brain.stats.*: normal t chi2 binomial poisson pdf/pmf cdf ppf in pure python and scipy backends plus oc.brain.stats.sample through the effects handle's random; one-sample two-sample and paired t tests, chi-square test of independence and goodness of fit, one-way anova, mann-whitney u, shapiro-wilk; scipy.stats named as the reference for every one)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 7 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/records/ml.regression.json
- A  pyto/experiments/brain/stats/intervals.py
- A  pyto/experiments/brain/stats/intervals_cases.py
- A  pyto/experiments/brain/stats/regression.py
- A  pyto/experiments/brain/stats/regression_cases.py
- A  pyto/experiments/brain/stats/test_intervals.py
- A  pyto/experiments/brain/stats/test_regression.py

```
pyto/experiments/brain/records/ml.regression.json |  24 +-
 pyto/experiments/brain/stats/intervals.py         | 295 +++++++++++++++++
 pyto/experiments/brain/stats/intervals_cases.py   | 187 +++++++++++
 pyto/experiments/brain/stats/regression.py        | 371 ++++++++++++++++++++++
 pyto/experiments/brain/stats/regression_cases.py  | 150 +++++++++
 pyto/experiments/brain/stats/test_intervals.py    | 175 ++++++++++
 pyto/experiments/brain/stats/test_regression.py   | 214 +++++++++++++
 7 files changed, 1404 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.LVGuUnOHKw) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               309  OK
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
