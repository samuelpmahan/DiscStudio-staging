# Task 123

Intent: S4 Recovery: the objects the clean detectors lose to an overlap, found again from other evidence -- the LAB's own dark-plate recovery for badges, and the shell recovery and component fallback its S2 and S3 receipts mark NOT RUN -- published as px.recovered.* for the later Stages to read
Starting point: 88ca019fdd869010f3fdc122907069ab2d08be06 (land(task-121): renumber the invented Stages to the owner's S4-S7: the nearest-anchor hole assembly becomes the HolesByNearestAnchor fallback, the course graph and the A* round become S7 Pathfinding, and S4/S5/S6 are freed for recovery, the tee-to-badge ray and the straight holes)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 23 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/s4.js
- M  src/lab/stage-sources.js
- A  src/lab/stages/S4.args.json
- A  src/lab/stages/S4.mmd
- M  src/lab/store/lab.json
- M  src/lab/store/records/HolesByNearestAnchor.invariants.json
- M  src/lab/store/records/HolesByNearestAnchor.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- M  src/lab/store/records/S2.json
- M  src/lab/store/records/S3.json
- M  src/lab/store/records/S3.quick-anno.json
- A  src/lab/store/records/S4.invariants.json
- A  src/lab/store/records/S4.json
- M  src/lab/store/records/S7.course.invariants.json
- M  src/lab/store/records/S7.course.json
- M  src/lab/store/records/S7.round.invariants.json
- M  src/lab/store/records/S7.round.json
- M  src/lab/store/records/S7.vs-straight.json
- M  src/lab/store/records/route-labfixture.json
- A  tests/lab-s4.test.js

```
src/lab/fixtures.js                                |   50 +-
 src/lab/map.js                                     |   14 +-
 src/lab/s4.js                                      |  280 +
 src/lab/stage-sources.js                           |    2 +
 src/lab/stages/S4.args.json                        |   29 +
 src/lab/stages/S4.mmd                              |   50 +
 src/lab/store/lab.json                             | 9156 +++++++++++---------
 .../records/HolesByNearestAnchor.invariants.json   |   32 +-
 src/lab/store/records/HolesByNearestAnchor.json    |  217 +-
 src/lab/store/records/S0.json                      |   43 +-
 src/lab/store/records/S1.json                      | 2566 +++---
 src/lab/store/records/S2.json                      |  252 +-
 src/lab/store/records/S3.json                      |  175 +-
 src/lab/store/records/S3.quick-anno.json           |   24 +-
 src/lab/store/records/S4.invariants.json           |  164 +
 src/lab/store/records/S4.json                      | 3306 +++++++
 src/lab/store/records/S7.course.invariants.json    |   40 +-
 src/lab/store/records/S7.course.json               |  315 +-
 src/lab/store/records/S7.round.invariants.json     |   32 +-
 src/lab/store/records/S7.round.json                |  843 +-
 src/lab/store/records/S7.vs-straight.json          |   55 +-
 src/lab/store/records/route-labfixture.json        |  203 +-
 tests/lab-s4.test.js                               |  151 +
 23 files changed, 10632 insertions(+), 7367 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.YR8UYgZLrO) (evidence/check_all.txt)
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
