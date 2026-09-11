# Task 127

Intent: S7 plays the holes S6 resolved: the course graph binds px.holes.straight and reports px.holes.unresolved as unplayed doglegs, a second pointing tee gives the round more than one leg, and the comparison with the straight-leg route is re-run on that binding
Starting point: 878f7a91d29db8f1b13ee8cabf4f58bb8ec01e56 (land(task-126): the port's map, honest after the renumbering: S4-S7 under ran, the stubs that S4 recovery actually retired removed, and what S7 still owes the straight holes written down as the next step with its for)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 28 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/fixtures.js
- M  src/lab/map.js
- M  src/lab/s7course.js
- M  src/lab/s7round.js
- M  src/lab/stage-sources.js
- M  src/lab/stages/S7.course.mmd
- M  src/lab/store/lab.json
- M  src/lab/store/records/HolesByNearestAnchor.invariants.json
- M  src/lab/store/records/HolesByNearestAnchor.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- M  src/lab/store/records/S2.json
- M  src/lab/store/records/S3.json
- M  src/lab/store/records/S3.quick-anno.json
- M  src/lab/store/records/S4.invariants.json
- M  src/lab/store/records/S4.json
- M  src/lab/store/records/S5.invariants.json
- M  src/lab/store/records/S5.json
- M  src/lab/store/records/S6.invariants.json
- M  src/lab/store/records/S6.json
- M  src/lab/store/records/S7.course.invariants.json
- M  src/lab/store/records/S7.course.json
- M  src/lab/store/records/S7.round.invariants.json
- M  src/lab/store/records/S7.round.json
- M  src/lab/store/records/S7.vs-straight.json
- M  src/lab/store/records/route-labfixture.json
- M  tests/lab-s7course.test.js
- M  tests/lab-s7round.test.js

```
src/lab/fixtures.js                                |   25 +-
 src/lab/map.js                                     |    7 +-
 src/lab/s7course.js                                |   67 +-
 src/lab/s7round.js                                 |   32 +-
 src/lab/stage-sources.js                           |    2 +-
 src/lab/stages/S7.course.mmd                       |    6 +-
 src/lab/store/lab.json                             | 2716 ++++++++++++++------
 .../records/HolesByNearestAnchor.invariants.json   |   24 +-
 src/lab/store/records/HolesByNearestAnchor.json    |  173 +-
 src/lab/store/records/S0.json                      |   56 +-
 src/lab/store/records/S1.json                      |  262 +-
 src/lab/store/records/S2.json                      |  150 +-
 src/lab/store/records/S3.json                      |  175 +-
 src/lab/store/records/S3.quick-anno.json           |   24 +-
 src/lab/store/records/S4.invariants.json           |    8 +-
 src/lab/store/records/S4.json                      |  162 +-
 src/lab/store/records/S5.invariants.json           |    4 +-
 src/lab/store/records/S5.json                      |  108 +-
 src/lab/store/records/S6.invariants.json           |    4 +-
 src/lab/store/records/S6.json                      |  115 +-
 src/lab/store/records/S7.course.invariants.json    |   45 +-
 src/lab/store/records/S7.course.json               |  267 +-
 src/lab/store/records/S7.round.invariants.json     |   12 +-
 src/lab/store/records/S7.round.json                |  606 +++--
 src/lab/store/records/S7.vs-straight.json          |   84 +-
 src/lab/store/records/route-labfixture.json        |  237 +-
 tests/lab-s7course.test.js                         |   70 +-
 tests/lab-s7round.test.js                          |   46 +-
 28 files changed, 3841 insertions(+), 1646 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.1HZzrrtDyC) (evidence/check_all.txt)
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
