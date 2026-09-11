# Task 94

Intent: brain/stats and brain/data, the second wave: kolmogorov-smirnov one and two sample, the wilcoxon signed-rank test and the p-value beside a pearson correlation, all with a pure-python tail (birnbaum-tingey, hodges, the limiting kolmogorov) that matches scipy exactly; a third group-by engine npsort that sorts once and reduces whole columns with numpy cumsum and reduceat, entered as the third candidate of the group-by bracket; melt as pivot's inverse and describe_table, the one place the data vertical calls the stats vertical
Starting point: 46cf6e2d4b003ccb641578962b981dcc04918151 (board: **started** `task-93`: brain/backend the evidence and the tournaments: f)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 18 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/brain/data/build.py
- M  pyto/experiments/brain/data/frame.py
- M  pyto/experiments/brain/data/frame_cases.py
- M  pyto/experiments/brain/data/referee.py
- A  pyto/experiments/brain/data/shaping.py
- A  pyto/experiments/brain/data/shaping_cases.py
- A  pyto/experiments/brain/data/sorted_groups.py
- M  pyto/experiments/brain/data/test_build.py
- M  pyto/experiments/brain/data/test_frame.py
- A  pyto/experiments/brain/data/test_shaping.py
- M  pyto/experiments/brain/records/data.pipeline.json
- M  pyto/experiments/brain/records/stats.analysis.json
- M  pyto/experiments/brain/stats/build.py
- A  pyto/experiments/brain/stats/nonparametric.py
- A  pyto/experiments/brain/stats/nonparametric_cases.py
- A  pyto/experiments/brain/stats/test_nonparametric.py
- M  pyto/experiments/brain/store/data.json
- M  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   72 +-
 pyto/experiments/brain/data/frame.py               |   42 +-
 pyto/experiments/brain/data/frame_cases.py         |   27 +-
 pyto/experiments/brain/data/referee.py             |    7 +-
 pyto/experiments/brain/data/shaping.py             |  107 +
 pyto/experiments/brain/data/shaping_cases.py       |  103 +
 pyto/experiments/brain/data/sorted_groups.py       |   87 +
 pyto/experiments/brain/data/test_build.py          |   33 +-
 pyto/experiments/brain/data/test_frame.py          |   34 +-
 pyto/experiments/brain/data/test_shaping.py        |  129 +
 pyto/experiments/brain/records/data.pipeline.json  |   12 +-
 pyto/experiments/brain/records/stats.analysis.json |   12 +-
 pyto/experiments/brain/stats/build.py              |   27 +-
 pyto/experiments/brain/stats/nonparametric.py      |  321 ++
 .../experiments/brain/stats/nonparametric_cases.py |  124 +
 pyto/experiments/brain/stats/test_nonparametric.py |  146 +
 pyto/experiments/brain/store/data.json             | 4290 ++++++++++++++------
 pyto/experiments/brain/store/stats.json            | 1132 +++++-
 18 files changed, 5298 insertions(+), 1407 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.LCRp2ZM7Ma) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               540  OK
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
