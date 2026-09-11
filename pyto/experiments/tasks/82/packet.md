# Task 82

Intent: brain/stats descriptive and correlation as Calculations fn.brain.stats.* over dataset Parts with py and np backends: mean, var, std, quantiles, median, skew, kurtosis, mode, covariance, pearson, spearman, kendall; each backend agrees with the other inside tolerance and with numpy/scipy as the named reference; unittest coverage per calculation and per backend
Starting point: c3a79b03eb17a08d77761ea438aba46fe4bfbc04 (board: **started** `task-81`: brain harness: experiments/brain shared harness ()
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 9 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/stats/__init__.py
- A  pyto/experiments/brain/stats/correlation.py
- A  pyto/experiments/brain/stats/correlation_cases.py
- A  pyto/experiments/brain/stats/descriptive.py
- A  pyto/experiments/brain/stats/descriptive_cases.py
- A  pyto/experiments/brain/stats/test_correlation.py
- A  pyto/experiments/brain/stats/test_descriptive.py
- A  pyto/experiments/brain/stats/test_tolerance.py
- A  pyto/experiments/brain/stats/tolerance.py

```
pyto/experiments/brain/stats/__init__.py          |   0
 pyto/experiments/brain/stats/correlation.py       | 183 ++++++++++++++++
 pyto/experiments/brain/stats/correlation_cases.py |  89 ++++++++
 pyto/experiments/brain/stats/descriptive.py       | 243 ++++++++++++++++++++++
 pyto/experiments/brain/stats/descriptive_cases.py | 141 +++++++++++++
 pyto/experiments/brain/stats/test_correlation.py  |  97 +++++++++
 pyto/experiments/brain/stats/test_descriptive.py  | 122 +++++++++++
 pyto/experiments/brain/stats/test_tolerance.py    |  29 +++
 pyto/experiments/brain/stats/tolerance.py         |  24 +++
 9 files changed, 928 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.PAchZ9aLoY) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
