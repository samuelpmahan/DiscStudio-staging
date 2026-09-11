# Task 85

Intent: brain/data dataframe-like Calculations fn.brain.data.* over the columns/rows dataset shape: select project filter group-by with aggregates join pivot sort window/rolling and missing-value handling, with py and np backends where the shape pays, dataset Parts px.exp.brain.data.* and oc.brain.data.load that reads csv and json through the effects handle's read_text
Starting point: a062b00304448f1ab5750910d79d5597bea6d725 (board: **started** `task-84`: brain/stats distributions and hypothesis tests as)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 8 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/data/__init__.py
- A  pyto/experiments/brain/data/datasets.py
- A  pyto/experiments/brain/data/frame.py
- A  pyto/experiments/brain/data/frame_cases.py
- A  pyto/experiments/brain/data/table.py
- A  pyto/experiments/brain/data/test_datasets.py
- A  pyto/experiments/brain/data/test_frame.py
- M  pyto/experiments/brain/records/ml.regression.json

```
pyto/experiments/brain/data/__init__.py           |   0
 pyto/experiments/brain/data/datasets.py           | 195 ++++++++
 pyto/experiments/brain/data/frame.py              | 569 ++++++++++++++++++++++
 pyto/experiments/brain/data/frame_cases.py        | 307 ++++++++++++
 pyto/experiments/brain/data/table.py              |  69 +++
 pyto/experiments/brain/data/test_datasets.py      | 110 +++++
 pyto/experiments/brain/data/test_frame.py         | 315 ++++++++++++
 pyto/experiments/brain/records/ml.regression.json |  24 +-
 8 files changed, 1577 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.5kcPXS2rZH) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               218  OK
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
