# Task 107

Intent: brain/stats and brain/data close the night: the empirical cdf and its quantile inverse against scipy.stats.ecdf, and the two findings this vertical owes the backend vertical -- what stats and data each had to do by hand because the facade has no op for it, with the workaround taken and the op proposed
Starting point: 248fb102ae3ca440fed84d80fce22400f3846cc0 (board: **started** `task-106`: brain/backend the three findings the night itsel)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 9 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/data/build.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- M  pyto/experiments/brain/stats/summaries.py
- M  pyto/experiments/brain/stats/summaries_cases.py
- M  pyto/experiments/brain/stats/test_summaries.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   15 +
 pyto/experiments/brain/records/data.pipeline.json  |   10 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |   16 +
 pyto/experiments/brain/stats/summaries.py          |   48 +-
 pyto/experiments/brain/stats/summaries_cases.py    |   15 +
 pyto/experiments/brain/stats/test_summaries.py     |   30 +
 pyto/experiments/brain/store/data.json             |  234 ++---
 pyto/experiments/brain/store/stats.json            | 1020 ++++++++++++++------
 9 files changed, 992 insertions(+), 408 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.jvoV3GZ1ZH) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               756  OK
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

{?} Two stacks, both green (756 tests): evidence/verify-py312.txt is the whole brain suite on
python 3.12.3 + numpy 2.5.3 + scipy 1.18.1 as well as the copy's own venv.
{?} The two findings this adds are addressed to the BACKEND vertical and name what each of
these two verticals had to write by hand because the facade has no op for it:
proposal.brain.stats.the_linear_algebra_this_vertical_wrote_by_hand (four hand-written
decompositions inside one vertical) and
proposal.brain.data.the_signal_processing_this_vertical_does_not_have (convolve, correlate,
interpolate, rfft -- the four primitives every missing time-series calculation is missing).
Each says the workaround taken and the op proposed.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
