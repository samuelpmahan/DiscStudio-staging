# Task 117

Intent: S5 Course: the holes as a graph over the canonical raster, with hole geometry, the obstacle map derived from px.remaining.afterBadges and the S1/S2/S3 masks, and the walkable cells a round can use
Starting point: 37d6b124284dce1c1716c1ef75a7e06693773948 (land(task-116): run the LAB Stages on the studio runtime: browser-safe lab modules, fn.lab.* Calculations registered in src/runtime.js, and runtime.lab.stage/pipeline as one composition per Stage with receipts)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 10 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/map.js
- M  src/lab/s4.js
- A  src/lab/s5.js
- A  src/lab/stage-sources.js
- A  src/lab/stages/S5.args.json
- A  src/lab/stages/S5.mmd
- M  src/lab/store/lab.json
- A  src/lab/store/records/S5.invariants.json
- A  src/lab/store/records/S5.json
- A  tests/lab-s5.test.js

```
src/lab/map.js                           |   11 +-
 src/lab/s4.js                            |   24 +-
 src/lab/s5.js                            |  275 ++
 src/lab/stage-sources.js                 |   33 +
 src/lab/stages/S5.args.json              |    4 +
 src/lab/stages/S5.mmd                    |   46 +
 src/lab/store/lab.json                   | 4238 +++++++++++++++++++++++++++++-
 src/lab/store/records/S5.invariants.json |  213 ++
 src/lab/store/records/S5.json            | 1184 +++++++++
 tests/lab-s5.test.js                     |  147 ++
 10 files changed, 6160 insertions(+), 15 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.myLkuDRsoY) (evidence/check_all.txt)
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
