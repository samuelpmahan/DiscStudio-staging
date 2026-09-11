# Task 79

Intent: the preset is the projection layer: the card cascade folds into the existing PxC composer (Component Editor) instead of a second page; global sits under each preset's own background, text, accent, radius, typeface and sponsor, a preset field set to inherit falls through to global, instances sit on top; The whole card section marks each field inherited or overridden with Reset to inherited, All cards is one more component tab with the four live previews and the global tokens, the #/cards route and the findings strip go away, and the seed presets keep their own looks
Starting point: 2d7934fe4661f5c934ee04296f5d9c693ac993c3 (land(task-78): card cascade editor as a PxC smoke test: four card projections (shelf, bag, single, competition) get cascading defaults global -> projection -> instance; each layer is a Part under px.discstudio.cards.*, fn.cards.effective and fn.cards.apply compose the effective card per projection inside the existing card chain, PQL prefix queries find overrides and inheritance, a recompose receipt says which edit recomposed which cards, and a three-pane editor (all cards, per-projection tabs, selected-card inspector) is retrofitted onto the existing surface; every friction is a proposal Part with its for, nothing is promoted)
Verify: npm test
Allow: src tests scripts/browser_test.py pyto/viewer/fixtures pyto/viewer/test pyto/experiments/cards pyto/experiments/tasks
Candidate: 15 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/experiments/cards/CONTRACT.md
- D  pyto/experiments/cards/FINDINGS.md
- A  pyto/experiments/cards/README.md
- M  pyto/viewer/fixtures/discstudio-display-card.json
- M  scripts/browser_test.py
- M  src/app.js
- D  src/cards-findings.js
- M  src/cards.js
- M  src/domain.js
- M  src/presentation.js
- M  src/runtime.js
- M  src/seed.js
- M  src/style.css
- M  tests/cards.test.js
- M  tests/fixtures/serial-run-record.json

```
pyto/experiments/cards/CONTRACT.md                |  303 +++---
 pyto/experiments/cards/FINDINGS.md                |   83 --
 pyto/experiments/cards/README.md                  |    7 +
 pyto/viewer/fixtures/discstudio-display-card.json | 1032 +++++++++++++++++----
 scripts/browser_test.py                           |   77 +-
 src/app.js                                        |  203 ++--
 src/cards-findings.js                             |   93 --
 src/cards.js                                      |  121 ++-
 src/domain.js                                     |   21 +-
 src/presentation.js                               |    9 +-
 src/runtime.js                                    |   37 +-
 src/seed.js                                       |    8 +-
 src/style.css                                     |   18 +-
 tests/cards.test.js                               |  154 +--
 tests/fixtures/serial-run-record.json             |   89 +-
 15 files changed, 1431 insertions(+), 824 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.o0HklUz26b) (evidence/check_all.txt)
    suite                         tests  status
    library                         435  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
