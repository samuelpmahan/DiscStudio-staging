# Task 120

Intent: your discs on the course the studio just built: S4 and S5 in the pipeline and on the raster, and an arrangement that stands the bag's DisplayCards at the holes
Starting point: 02b58d562a36b700f01e7cae00b3590a83325fdf (board: **started** `task-119`: S6 Round: a deterministic search over S5's walka)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/build.mjs scripts/serve.mjs pyto/experiments/tasks
Candidate: 8 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/browser_test.py
- M  src/app.js
- M  src/domain.js
- M  src/lab/stages.js
- M  src/presentation.js
- M  src/runtime.js
- M  src/style.css
- M  tests/lab-pipeline.test.js

```
scripts/browser_test.py    | 42 ++++++++++++++++++++++++++++----
 src/app.js                 | 56 ++++++++++++++++++++++++++++---------------
 src/domain.js              |  2 +-
 src/lab/stages.js          | 43 +++++++++++++++++++++++++++++++--
 src/presentation.js        | 57 ++++++++++++++++++++++++++++++++++++++++++-
 src/runtime.js             | 28 +++++++++++++++++++---
 src/style.css              |  6 +++++
 tests/lab-pipeline.test.js | 60 +++++++++++++++++++++++++++++++++++++++-------
 8 files changed, 254 insertions(+), 40 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.GA6LlJxV4Z) (evidence/check_all.txt)
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
