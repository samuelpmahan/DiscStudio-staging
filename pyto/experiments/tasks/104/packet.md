# Task 104

Intent: brain/stats and brain/data, closing two named stubs: weighted least squares through the same three solvers the tournament judged, with the weights in the design rather than in a fourth solver, and its oracle against numpy.linalg.lstsq on the scaled design; and the as-of (rolling) join, the one join a time series actually wants, backward forward or nearest with a tolerance
Starting point: f33b9e5f3111932ccfd091bc8a2d723a7aafecb8 (board: **started** `task-103`: brain/backend six more primitives and the case t)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 12 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/data/build.py
- M  pyto/experiments/brain/data/shaping.py
- M  pyto/experiments/brain/data/shaping_cases.py
- M  pyto/experiments/brain/data/test_shaping.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- M  pyto/experiments/brain/stats/regression.py
- M  pyto/experiments/brain/stats/regression_cases.py
- M  pyto/experiments/brain/stats/test_regression.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   8 +-
 pyto/experiments/brain/data/shaping.py             |  94 ++-
 pyto/experiments/brain/data/shaping_cases.py       |  62 ++
 pyto/experiments/brain/data/test_shaping.py        |  63 +-
 pyto/experiments/brain/records/data.pipeline.json  |  10 +-
 pyto/experiments/brain/records/stats.analysis.json |  12 +-
 pyto/experiments/brain/stats/build.py              |  11 +-
 pyto/experiments/brain/stats/regression.py         |  62 +-
 pyto/experiments/brain/stats/regression_cases.py   |  34 +
 pyto/experiments/brain/stats/test_regression.py    |  43 +-
 pyto/experiments/brain/store/data.json             | 694 ++++++++++++++++----
 pyto/experiments/brain/store/stats.json            | 700 ++++++++++++---------
 12 files changed, 1360 insertions(+), 433 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.HrRt7liMWd) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               742  OK
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

{?} Two stacks, both green (736 tests): evidence/verify-py312.txt is the whole brain suite on
python 3.12.3 + numpy 2.5.3 + scipy 1.18.1 as well as the copy's own venv.
{?} Two named stubs close here, and the map says so: fn.brain.stats.ols_weighted and
fn.brain.data.rolling_join both come off px.exp.brain.map.stats/.data's stubbed list, and the
'next' entries that pointed at them now point at what is left behind them (a huber m-estimator
over the weighted fit; a calendar-aware index under the as-of join).
{?} The weights go into the DESIGN, not into a fourth solver: ols_weighted scales each row by
sqrt(w) and calls whichever of the three tournament solvers is named, so the bracket's answer
still holds for the weighted case and there is nothing new to judge.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
