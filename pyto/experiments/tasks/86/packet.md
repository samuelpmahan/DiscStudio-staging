# Task 86

Intent: brain/data time series Calculations fn.brain.data.*: rolling mean/var/min/max/sum, differencing and integration, simple and Holt exponential smoothing, additive and multiplicative seasonal decomposition, autocorrelation and partial autocorrelation, and an AR(p) fit by least squares with forecasts; py and np backends, numpy/scipy named as the reference
Starting point: 2afe2e2c966463615fc97b119ad41c0728e9f19f (board: **started** `task-85`: brain/data dataframe-like Calculations fn.brain.d)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 4 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/data/test_timeseries.py
- A  pyto/experiments/brain/data/timeseries.py
- A  pyto/experiments/brain/data/timeseries_cases.py
- M  pyto/experiments/brain/records/ml.regression.json

```
pyto/experiments/brain/data/test_timeseries.py    | 259 ++++++++++++
 pyto/experiments/brain/data/timeseries.py         | 461 ++++++++++++++++++++++
 pyto/experiments/brain/data/timeseries_cases.py   | 228 +++++++++++
 pyto/experiments/brain/records/ml.regression.json |  24 +-
 4 files changed, 960 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.agOdzWXmEZ) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               256  OK
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
