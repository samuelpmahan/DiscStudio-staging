# Task 115

Intent: S4 Holes: assemble each hole from S1 badges, S2 baskets and S3 tees as a Stage with explicit invariants, and extend the lab fixture with a third badge and an obstacle region
Starting point: db7bf336ed1dc3af0441711c7a4f1c135063d2f9 (land(task-114): port S2 (baskets) and S3 (visible tees) onto the studio core as the documents their OperationSpecs declare, with the Python analogue's ring balance as S3's oracle, and redefine pathfinding on the Stage outputs: the round in badge order, tee to basket to the next tee)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 16 files, see below
Evidence: suite exit 1, see below

## Candidate

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/s4.js
- M  src/lab/source.js
- A  src/lab/stages/S4.args.json
- A  src/lab/stages/S4.mmd
- M  src/lab/store/lab.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- M  src/lab/store/records/S2.json
- M  src/lab/store/records/S3.json
- M  src/lab/store/records/S3.quick-anno.json
- A  src/lab/store/records/S4.invariants.json
- A  src/lab/store/records/S4.json
- M  src/lab/store/records/route-labfixture.json
- A  tests/lab-s4.test.js

```
src/lab/fixtures.js                         |   64 +-
 src/lab/map.js                              |   21 +-
 src/lab/s4.js                               |  229 ++
 src/lab/source.js                           |    9 +
 src/lab/stages/S4.args.json                 |    3 +
 src/lab/stages/S4.mmd                       |   31 +
 src/lab/store/lab.json                      | 4314 +++++++++++++++++++++------
 src/lab/store/records/S0.json               |   58 +-
 src/lab/store/records/S1.json               | 2854 +++++++++++++-----
 src/lab/store/records/S2.json               |  128 +-
 src/lab/store/records/S3.json               |  199 +-
 src/lab/store/records/S3.quick-anno.json    |   24 +-
 src/lab/store/records/S4.invariants.json    |  196 ++
 src/lab/store/records/S4.json               |  730 +++++
 src/lab/store/records/route-labfixture.json |   89 +-
 tests/lab-s4.test.js                        |  137 +
 16 files changed, 7404 insertions(+), 1682 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.GYczQsJxNP) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               756  FAIL
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
