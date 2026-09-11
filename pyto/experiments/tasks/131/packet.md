# Task 131

Intent: art assignment as a Calculation over the set, not a hash per item: fn.art.assign spreads first (a golden-ratio walk over the painter's families, every family used before any repeats) then groups (after coverage a disc takes the family of the disc it resembles, by mold), stable in the order the shelf holds its discs; px.art.assignment is a Part the card chain binds, an authored family still wins; four oracles as tests: coverage, spread, grouping, stability; the seed's twelve discs are assigned by it instead of by index
Starting point: 88b933d8255ef20c2c98a8a9e25cf22f6602911b (land(task-130): every disc looked the same: the painter port (2026-09-09) replaced the per-disc hue with one fixed base and accent for every disc that has no authored art colours, so twelve discs painted one wind-rose in one grey-green; a disc's sample hue is its colours again (base and accent derived from sampleHue when artBase/artAccent are not authored, exactly the original prepareDiscArt's rule), the sanitised-colour test expects the disc's own defaults, and the two art-bearing fixtures are regenerated from the real runtime)
Verify: npm test
Allow: src tests pyto/viewer/fixtures pyto/experiments/tasks
Candidate: 8 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/viewer/fixtures/discstudio-display-card.json
- A  src/art.js
- M  src/presentation.js
- M  src/runtime.js
- M  src/seed.js
- A  tests/art.test.js
- M  tests/core.test.js
- M  tests/fixtures/serial-run-record.json

```
pyto/viewer/fixtures/discstudio-display-card.json | 264 ++++++++++++++--------
 src/art.js                                        |  66 ++++++
 src/presentation.js                               |   9 +-
 src/runtime.js                                    |  21 +-
 src/seed.js                                       |   4 +-
 tests/art.test.js                                 |  76 +++++++
 tests/core.test.js                                |  11 +-
 tests/fixtures/serial-run-record.json             | 159 ++++++-------
 8 files changed, 415 insertions(+), 195 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.dIxK2LW1dD) (evidence/check_all.txt)
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
