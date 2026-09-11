# Task 101

Intent: brain/stats and brain/data, the last wave: the robust simple regressions (theil-sen and siegel repeated medians) and the whole simple-regression verdict in one Calculation, all against scipy; and the three series transforms a pipeline still wants: percentage change, the expanding (whole-history) statistics on the same cumulative pass as the rolling ones, and linear interpolation over the holes
Starting point: c84c961a82c757bd0fa2f37a654b8108bac75ffb (board: **started** `task-100`: brain/backend the benchmark Parts are what decid)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 11 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/data/test_timeseries.py
- M  pyto/experiments/brain/data/timeseries.py
- M  pyto/experiments/brain/data/timeseries_cases.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- A  pyto/experiments/brain/stats/robust.py
- A  pyto/experiments/brain/stats/robust_cases.py
- A  pyto/experiments/brain/stats/test_robust.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/test_timeseries.py     |   66 +
 pyto/experiments/brain/data/timeseries.py          |   86 +-
 pyto/experiments/brain/data/timeseries_cases.py    |   75 +
 pyto/experiments/brain/records/data.pipeline.json  |   10 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |    9 +-
 pyto/experiments/brain/stats/robust.py             |  172 ++
 pyto/experiments/brain/stats/robust_cases.py       |  105 ++
 pyto/experiments/brain/stats/test_robust.py        |  136 ++
 pyto/experiments/brain/store/data.json             | 1860 +++++++++++++++++---
 pyto/experiments/brain/store/stats.json            | 1204 ++++++++++---
 11 files changed, 3184 insertions(+), 551 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.FQDOmdhHh7) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               701  OK
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

{?} Two stacks: evidence/verify-py312.txt is the whole brain suite on python 3.12.3 + numpy
2.5.3 + scipy 1.18.1 as well as the copy's own venv. Both are green (693 tests).
{?} fn.brain.data.expanding is fn.brain.data.rolling with the window set to the length of the
series, and nothing else: the same three engines, the same oracle shape, and the cumsum engine
is what turns an expanding statistic from O(n^2) into O(n).
{?} theil_sen reproduces scipy's confidence interval exactly, including the two rank indices
scipy takes from Sen (1968) equation 2.6 -- the interval is part of the oracle, not just the slope.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
