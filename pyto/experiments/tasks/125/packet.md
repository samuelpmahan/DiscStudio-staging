# Task 125

Intent: what the Stages asked of the studio's PxC that it could not say: the sprint's frictions as proposal.studio.* Parts, and the last Stages wired as they land
Starting point: 4d316a53db95c6a2a6d49cc1bda5c97315f3ae88 (board: **started** `task-124`: S5 Tee->Badge and S6 straight holes: a tee's poi)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/build.mjs scripts/serve.mjs pyto/experiments/tasks
Candidate: 7 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/browser_test.py
- M  src/app.js
- M  src/lab/stages.js
- A  src/proposals.js
- M  src/runtime.js
- M  src/style.css
- M  tests/lab-pipeline.test.js

```
scripts/browser_test.py    | 22 +++++++------
 src/app.js                 |  3 +-
 src/lab/stages.js          | 64 ++++++++++++++++++++++++++++++-------
 src/proposals.js           | 80 ++++++++++++++++++++++++++++++++++++++++++++++
 src/runtime.js             | 14 +++++---
 src/style.css              |  2 +-
 tests/lab-pipeline.test.js | 79 ++++++++++++++++++++++++++++++++++++---------
 7 files changed, 222 insertions(+), 42 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.JyF6f7iWRe) (evidence/check_all.txt)
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
