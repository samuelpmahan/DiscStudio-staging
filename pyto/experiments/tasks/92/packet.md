# Task 92

Intent: brain/stats and brain/data build the Parts: every oracle, benchmark, dataset, result and record this vertical owns, persisted to store/stats.json and store/data.json, the two tournaments (OLS normal equations against householder QR against numpy lstsq, and group-by aggregation py against np) with their criteria written down before any judging and scored by a referee that built neither, the findings, and the map Parts px.exp.brain.map.stats and px.exp.brain.map.data
Starting point: 804252504b559b1eee36c062ea00a9a5781ddb87 (land(task-91): brain harness (and the one line of ml/parts.py that is the same bug): a Store writes its store and records into a temporary directory unless it is an explicit record run (Store(commit=True), or BRAIN_RECORDS=commit), so no test can rewrite a tracked run record - a wall-clock duration inside a committed file leaves MAIN dirty and land.sh then refuses the NEXT landing, for whoever lands next rather than for whoever wrote it; reading is unchanged, load_store() still reads the committed store)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: 11 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/brain/data/build.py
- A  pyto/experiments/brain/data/referee.py
- A  pyto/experiments/brain/data/test_build.py
- A  pyto/experiments/brain/records/data.pipeline.json
- A  pyto/experiments/brain/records/stats.analysis.json
- A  pyto/experiments/brain/stats/build.py
- A  pyto/experiments/brain/stats/referee.py
- M  pyto/experiments/brain/stats/regression.py
- A  pyto/experiments/brain/stats/test_build.py
- A  pyto/experiments/brain/store/data.json
- A  pyto/experiments/brain/store/stats.json

```
pyto/experiments/brain/data/build.py               |   319 +
 pyto/experiments/brain/data/referee.py             |    53 +
 pyto/experiments/brain/data/test_build.py          |   185 +
 pyto/experiments/brain/records/data.pipeline.json  |   625 ++
 pyto/experiments/brain/records/stats.analysis.json |  1355 +++
 pyto/experiments/brain/stats/build.py              |   356 +
 pyto/experiments/brain/stats/referee.py            |   106 +
 pyto/experiments/brain/stats/regression.py         |    11 +-
 pyto/experiments/brain/stats/test_build.py         |   245 +
 pyto/experiments/brain/store/data.json             | 10110 +++++++++++++++++++
 pyto/experiments/brain/store/stats.json            |  6793 +++++++++++++
 11 files changed, 20157 insertions(+), 1 deletion(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.00YIyG8Xl0) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               374  OK
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
