# Task 99

Intent: brain/stats and brain/data, the fourth wave: the robust summaries (trimmed mean, winsorised sample, median absolute deviation, geometric and harmonic mean, entropy and a histogram) against scipy; a third rolling engine that runs the whole window in one cumulative pass instead of one slice per point, entered as the candidates of a third tournament with its criteria written down first; exponentially weighted moving statistics and the cross-correlation of two series
Starting point: 1fcfbbd858898cf141f92b9080ac1df398258603 (board: **started** `task-98`: brain/backend and harness, portable across numpy)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 13 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/data/build.py
- M  pyto/experiments/brain/data/referee.py
- M  pyto/experiments/brain/data/test_timeseries.py
- M  pyto/experiments/brain/data/timeseries.py
- M  pyto/experiments/brain/data/timeseries_cases.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- A  pyto/experiments/brain/stats/summaries.py
- A  pyto/experiments/brain/stats/summaries_cases.py
- A  pyto/experiments/brain/stats/test_summaries.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   57 +
 pyto/experiments/brain/data/referee.py             |   20 +
 pyto/experiments/brain/data/test_timeseries.py     |   84 +-
 pyto/experiments/brain/data/timeseries.py          |  188 +-
 pyto/experiments/brain/data/timeseries_cases.py    |   99 +
 pyto/experiments/brain/records/data.pipeline.json  |   12 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |    3 +
 pyto/experiments/brain/stats/summaries.py          |  213 ++
 pyto/experiments/brain/stats/summaries_cases.py    |   92 +
 pyto/experiments/brain/stats/test_summaries.py     |  164 ++
 pyto/experiments/brain/store/data.json             | 3103 +++++++++++++++++++-
 pyto/experiments/brain/store/stats.json            | 1664 +++++++++--
 13 files changed, 5369 insertions(+), 342 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.ZOOCfqUEJ1) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               648  OK
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

{?} Two stacks, not one: evidence/verify-py312.txt is the same suite on python 3.12.3 + numpy
2.5.3 + scipy 1.18.1 as well as the copy's own venv. Every stats and data test passes on both.
The three failures that stack shows are in the backend and ml verticals and were already there.
{?} Three tournaments now, all re-runnable from the store: ols_solver (lstsq), group_by_aggregation
(npsort) and rolling_window (cumsum). The rolling bracket's winner is NOT the facade default and
the refinement note says why: cumsum has no whole-window form for min, max or median and refuses
them, so the default has to be the engine that answers every fn.
{?} Committed documents are canonicalised to twelve significant digits before saving, so a fresh
build on another BLAS saves the same document; the wall-clock fields of a benchmark Part are a
measurement of this machine and are not expected to reproduce.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
