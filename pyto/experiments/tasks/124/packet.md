# Task 124

Intent: S5 Tee->Badge and S6 straight holes: a tee's pointing end read off its own pixels, the ray cast at the badge it points at, and the basket found by continuing that ray past the badge -- three points on a line, with the badges whose ray finds nothing reported as doglegs
Starting point: 03dbfbd1684c30b15122698fd32498485674b182 (land(task-122): draw a Stage by the addresses it publishes, not by its number: the Course overlay becomes an address table, the searched round joins the pipeline, and the renumbered S4-S7 draw themselves as they land)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: 31 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/s5.js
- A  src/lab/s6.js
- M  src/lab/stage-sources.js
- A  src/lab/stages/S5.args.json
- A  src/lab/stages/S5.mmd
- A  src/lab/stages/S6.args.json
- A  src/lab/stages/S6.mmd
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
- A  src/lab/store/records/S5.invariants.json
- A  src/lab/store/records/S5.json
- A  src/lab/store/records/S6.invariants.json
- A  src/lab/store/records/S6.json
- M  src/lab/store/records/S7.course.invariants.json
- M  src/lab/store/records/S7.course.json
- M  src/lab/store/records/S7.round.invariants.json
- M  src/lab/store/records/S7.round.json
- M  src/lab/store/records/S7.vs-straight.json
- M  src/lab/store/records/route-labfixture.json
- A  tests/lab-s5.test.js
- A  tests/lab-s6.test.js

```
src/lab/fixtures.js                                |   44 +-
 src/lab/map.js                                     |   19 +-
 src/lab/s5.js                                      |  194 +
 src/lab/s6.js                                      |  175 +
 src/lab/stage-sources.js                           |    4 +
 src/lab/stages/S5.args.json                        |    4 +
 src/lab/stages/S5.mmd                              |   29 +
 src/lab/stages/S6.args.json                        |    3 +
 src/lab/stages/S6.mmd                              |   29 +
 src/lab/store/lab.json                             | 7576 +++++++++++++++-----
 .../records/HolesByNearestAnchor.invariants.json   |   32 +-
 src/lab/store/records/HolesByNearestAnchor.json    |  209 +-
 src/lab/store/records/S0.json                      |  102 +-
 src/lab/store/records/S1.json                      | 2822 ++++++--
 src/lab/store/records/S2.json                      |  242 +-
 src/lab/store/records/S3.json                      |  175 +-
 src/lab/store/records/S3.quick-anno.json           |   24 +-
 src/lab/store/records/S4.invariants.json           |   12 +-
 src/lab/store/records/S4.json                      | 1506 +++-
 src/lab/store/records/S5.invariants.json           |  107 +
 src/lab/store/records/S5.json                      |  609 ++
 src/lab/store/records/S6.invariants.json           |  127 +
 src/lab/store/records/S6.json                      |  415 ++
 src/lab/store/records/S7.course.invariants.json    |   28 +-
 src/lab/store/records/S7.course.json               |  172 +-
 src/lab/store/records/S7.round.invariants.json     |   24 +-
 src/lab/store/records/S7.round.json                |  562 +-
 src/lab/store/records/S7.vs-straight.json          |   53 +-
 src/lab/store/records/route-labfixture.json        |  203 +-
 tests/lab-s5.test.js                               |  110 +
 tests/lab-s6.test.js                               |  111 +
 31 files changed, 12813 insertions(+), 2909 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.RnYu9Thtmv) (evidence/check_all.txt)
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
