# Task 78

Intent: card cascade editor as a PxC smoke test: four card projections (shelf, bag, single, competition) get cascading defaults global -> projection -> instance; each layer is a Part under px.discstudio.cards.*, fn.cards.effective and fn.cards.apply compose the effective card per projection inside the existing card chain, PQL prefix queries find overrides and inheritance, a recompose receipt says which edit recomposed which cards, and a three-pane editor (all cards, per-projection tabs, selected-card inspector) is retrofitted onto the existing surface; every friction is a proposal Part with its for, nothing is promoted
Starting point: d47cd064281b0014caa1fb85c5b922cc7a5b61ef (land(task-77): USE.md section 4 still teaches the rule the owner overturned: 'the Calculations of one Tick are parallel branches, so none of them may read another's produce'; it now says what the kernel does since task 57 (inside a Tick the Calculations are a sequence in declared order, a later one may bind an earlier sibling's result, a Tick with no sibling reads may run at once, a read of a later sibling and two siblings on one address are refused) with a chained Tick in the block and its printed output, and every other page that repeats the old sentence is corrected)
Verify: npm test
Allow: src tests scripts/browser_test.py index.html pyto/experiments/cards pyto/experiments/tasks
Candidate: 2 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/cards/CONTRACT.md
- A  pyto/experiments/cards/FINDINGS.md

```
pyto/experiments/cards/CONTRACT.md | 174 +++++++++++++++++++++++++++++++++++++
 pyto/experiments/cards/FINDINGS.md |  34 ++++++++
 2 files changed, 208 insertions(+)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.fkZJwSMgLn) (evidence/check_all.txt)
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
