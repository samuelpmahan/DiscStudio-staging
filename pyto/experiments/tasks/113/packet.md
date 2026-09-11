# Task 113

Intent: run the LAB's own S1 PrincipleComponentRender.yaml on the studio core, and land the port's map and findings as Parts
Starting point: 938a8169c05b71d331e16d2febb98a0f5cb8438a (land(task-112): port ChainSpot's S0 and S1 stage documents to the studio's PxC core as fn.lab.* Calculations run through readPql/invokePql)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks pyto/research
Candidate: 8 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  src/lab/map.js
- A  src/lab/s1.js
- A  src/lab/store/lab.json
- A  src/lab/store/records/S0.json
- A  src/lab/store/records/S1.json
- A  src/lab/store/records/path-dashstrack-h1-h9.json
- A  tests/lab-map.test.js
- A  tests/lab-s1.test.js

```
src/lab/map.js                                   |   59 +
 src/lab/s1.js                                    |  280 ++
 src/lab/store/lab.json                           | 4509 ++++++++++++++++++++++
 src/lab/store/records/S0.json                    |  319 ++
 src/lab/store/records/S1.json                    | 4125 ++++++++++++++++++++
 src/lab/store/records/path-dashstrack-h1-h9.json |  886 +++++
 tests/lab-map.test.js                            |   41 +
 tests/lab-s1.test.js                             |   86 +
 8 files changed, 10305 insertions(+)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.9MfV2yQZYo) (evidence/check_all.txt)
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
