# Task 133

Intent: vertical content: a 1080x1920 portrait canvas beside the 1920x1080 one, composed by the same fn.comparison.layout, plus a reusable frame preset (fill, safe area, title strip, sponsor lockup on the cards cascade's global tokens) materialized by the same fn.overlay.svg, and exports that honour the orientation
Starting point: 2487b379d17d28f07207414f51bdbe976958d8e1 (land(task-131): art assignment as a Calculation over the set, not a hash per item: fn.art.assign spreads first (a golden-ratio walk over the painter's families, every family used before any repeats) then groups (after coverage a disc takes the family of the disc it resembles, by mold), stable in the order the shelf holds its discs; px.art.assignment is a Part the card chain binds, an authored family still wins; four oracles as tests: coverage, spread, grouping, stability; the seed's twelve discs are assigned by it instead of by index)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py pyto/experiments/tasks
Candidate: 11 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  scripts/browser_test.py
- M  src/app.js
- M  src/domain.js
- A  src/frames.js
- M  src/media.js
- M  src/presentation.js
- M  src/runtime.js
- M  src/seed.js
- M  src/style.css
- M  tests/core.test.js
- M  tests/fixtures/serial-run-record.json

```
scripts/browser_test.py               |  39 +++++++
 src/app.js                            |  39 +++++--
 src/domain.js                         |  13 ++-
 src/frames.js                         |  97 ++++++++++++++++++
 src/media.js                          |   7 +-
 src/presentation.js                   |  77 ++++++++++----
 src/runtime.js                        |  15 ++-
 src/seed.js                           |   2 +-
 src/style.css                         |   2 +-
 tests/core.test.js                    |  47 ++++++++-
 tests/fixtures/serial-run-record.json | 185 ++++++++++++++++++++++++++++------
 11 files changed, 448 insertions(+), 75 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.xhi4yFgnlv) (evidence/check_all.txt)
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

{?} FrameIsPartOfTheLayout: the frame is a Part (`px.overlay.frame`) that `fn.comparison.layout` reads
and `fn.overlay.svg` draws, which means the canvas size lives in two places at once -- the layout's
`orientation` field and the frame Calculation's output. It works because the frame is composed first
and everything downstream takes its size from the frame's canvas, but a Part that is half layout input
and half drawing is a shape the kernel has no word for. A `Canvas` first-class Part that both read
would say it better.

{?} SponsorIsGlobalOnly: the frame's sponsor lockup reads `px.discstudio.cards.global.sponsor` and not
the effective cascade for the comparison's preset, so the broadcast preset's own `sponsor: 'CHAINSPOT'`
override shows on the cards but not in the frame's lockup until the global token is set. That is what
"drawing on the cards cascade's global tokens" says, and it is also the thing a person will ask about
first. The alternative -- a fourth cascade layer for the overlay itself -- is a bigger change than this
slice.

{?} FixtureIsByteForByte: `tests/fixtures/serial-run-record.json` is compared byte for byte, so every
task that adds one Tick to the comparison regenerates a 220 KB fixture. Two writers touching the
comparison in the same sprint conflict on that file and on nothing else. A fixture that asserted the
Tick names and the counters rather than every value would take the same kill and never conflict.
