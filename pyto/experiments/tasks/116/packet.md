# Task 116

Intent: run the LAB Stages on the studio runtime: browser-safe lab modules, fn.lab.* Calculations registered in src/runtime.js, and runtime.lab.stage/pipeline as one composition per Stage with receipts
Starting point: c7f06cbe556cbbfc83fc7ad67ec0f0d3e172224a (board: **started** `task-115`: S4 Holes: assemble each hole from S1 badges, S2)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/build.mjs pyto/experiments/tasks
Candidate: 10 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/fixtures.js
- M  src/lab/lab.js
- M  src/lab/s0.js
- M  src/lab/s1.js
- M  src/lab/s2.js
- A  src/lab/source-data.js
- A  src/lab/stages.js
- M  src/runtime.js
- A  tests/lab-pipeline.test.js
- A  tests/lab-source-data.test.js

```
src/lab/fixtures.js           |   6 +-
 src/lab/lab.js                |  32 ++++++---
 src/lab/s0.js                 |   6 +-
 src/lab/s1.js                 |  10 ++-
 src/lab/s2.js                 |   6 +-
 src/lab/source-data.js        |  31 +++++++++
 src/lab/stages.js             | 150 ++++++++++++++++++++++++++++++++++++++++++
 src/runtime.js                | 141 ++++++++++++++++++++++++++++++++++++++-
 tests/lab-pipeline.test.js    | 127 +++++++++++++++++++++++++++++++++++
 tests/lab-source-data.test.js |  29 ++++++++
 10 files changed, 509 insertions(+), 29 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.JLsUamAXqD) (evidence/check_all.txt)
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
