# Task 114

Intent: port S2 (baskets) and S3 (visible tees) onto the studio core as the documents their OperationSpecs declare, with the Python analogue's ring balance as S3's oracle, and redefine pathfinding on the Stage outputs: the round in badge order, tee to basket to the next tee
Starting point: d4c51885da95f2fcc8f379a79dcf030f7f77810b (land(task-113): run the LAB's own S1 PrincipleComponentRender.yaml on the studio core, and land the port's map and findings as Parts)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks pyto/research
Candidate: 17 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/route.js
- A  src/lab/s2.js
- A  src/lab/s3.js
- A  src/lab/source/basket-sprite.json
- M  src/lab/store/lab.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- A  src/lab/store/records/S2.json
- A  src/lab/store/records/S3.json
- A  src/lab/store/records/S3.quick-anno.json
- A  src/lab/store/records/route-labfixture.json
- A  tests/lab-route.test.js
- M  tests/lab-s1.test.js
- A  tests/lab-s2.test.js
- A  tests/lab-s3.test.js

```
src/lab/fixtures.js                         |   57 +-
 src/lab/map.js                              |   28 +-
 src/lab/route.js                            |  133 ++
 src/lab/s2.js                               |  226 +++
 src/lab/s3.js                               |  289 +++
 src/lab/source/basket-sprite.json           |   73 +
 src/lab/store/lab.json                      | 2801 +++++++++++++++++++++------
 src/lab/store/records/S0.json               |   68 +-
 src/lab/store/records/S1.json               | 1122 ++++++-----
 src/lab/store/records/S2.json               |  733 +++++++
 src/lab/store/records/S3.json               |  646 ++++++
 src/lab/store/records/S3.quick-anno.json    |  165 ++
 src/lab/store/records/route-labfixture.json |  593 ++++++
 tests/lab-route.test.js                     |  105 +
 tests/lab-s1.test.js                        |    4 +-
 tests/lab-s2.test.js                        |   92 +
 tests/lab-s3.test.js                        |   95 +
 17 files changed, 6162 insertions(+), 1068 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.2a4xTDSfID) (evidence/check_all.txt)
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
