# Task 114

Intent: port S2 basket detection onto the studio core: the PQL document its OperationSpec composition implies, fn.lab.basket.* Calculations, the LAB basket sprite, and a fixture drawn to the S2 knobs
Starting point: d4c51885da95f2fcc8f379a79dcf030f7f77810b (land(task-113): run the LAB's own S1 PrincipleComponentRender.yaml on the studio core, and land the port's map and findings as Parts)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks pyto/research
Candidate: 9 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/s2.js
- A  src/lab/source/basket-sprite.json
- M  src/lab/store/lab.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- A  src/lab/store/records/S2.json
- A  tests/lab-s2.test.js

```
src/lab/fixtures.js               |  22 +-
 src/lab/map.js                    |  14 +-
 src/lab/s2.js                     | 183 ++++++++
 src/lab/source/basket-sprite.json |  73 +++
 src/lab/store/lab.json            | 944 +++++++++++++++++++++++++++++++-------
 src/lab/store/records/S0.json     |  30 ++
 src/lab/store/records/S1.json     | 452 +++++++++++-------
 src/lab/store/records/S2.json     | 633 +++++++++++++++++++++++++
 tests/lab-s2.test.js              |  92 ++++
 9 files changed, 2101 insertions(+), 342 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.brgIkukLWO) (evidence/check_all.txt)
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
