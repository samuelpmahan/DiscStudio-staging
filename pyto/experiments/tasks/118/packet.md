# Task 118

Intent: the Course route: a capture becomes a course stage by stage on the record, with the canonical raster drawn once and each Stage's produce overlaid on it
Starting point: fba4b6ad76c521c1bdfb3e91f6534955ee83bfc6 (board: **started** `task-117`: S5 Course: the holes as a graph over the canonic)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/build.mjs scripts/serve.mjs pyto/experiments/tasks
Candidate: 5 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/browser_test.py
- M  scripts/serve.mjs
- M  src/app.js
- M  src/runtime.js
- M  src/style.css

```
scripts/browser_test.py |  59 +++++++++++++++-
 scripts/serve.mjs       |   4 +-
 src/app.js              | 178 ++++++++++++++++++++++++++++++++++++++++++++++--
 src/runtime.js          |   2 +-
 src/style.css           |  56 +++++++++++++++
 5 files changed, 287 insertions(+), 12 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.mAsd6DtoDa) (evidence/check_all.txt)
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

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
