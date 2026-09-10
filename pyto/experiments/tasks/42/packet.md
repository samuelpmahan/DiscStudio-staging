# Task 42

Intent: the studio speaks the whole record: the site's PQL grammar accepts several into per Calculation and runs it, the Inspect page lists the studio's own receipts through PQL, and an UndoStack Part gives every format undo in the browser with receipts
Starting point: 5fa1383cc7a8516f3ebbd561eb01252d8870ff4a (board: **started** `task-41`: the px shell: a px command over records and store)
Verify: npm test && node --test pyto/viewer/test/*.test.mjs && python3 scripts/browser_test.py --embedded
Allow: src tests scripts/browser_test.py scripts/review_checkpoint.mjs .neat/items pyto/experiments/grouped-ablation/pql_document.py pyto/experiments/grouped-ablation/test_second_experiment.py pyto/experiments/grouped-ablation/candidates pyto/CHANGES.md pyto/experiments/tasks
Candidate: 16 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  .neat/items/DS-STUDIO-02.json
- M  pyto/CHANGES.md
- M  pyto/experiments/grouped-ablation/candidates/README.md
- M  pyto/experiments/grouped-ablation/candidates/readpql_check.mjs
- M  pyto/experiments/grouped-ablation/pql_document.py
- M  pyto/experiments/grouped-ablation/test_second_experiment.py
- M  scripts/browser_test.py
- M  scripts/review_checkpoint.mjs
- M  src/app.js
- M  src/core/exec.js
- A  src/formats/receipt-list.js
- A  src/formats/undo.js
- M  src/review-data.js
- M  src/runtime.js
- M  src/style.css
- M  tests/core.test.js

```
.neat/items/DS-STUDIO-02.json                      |  12 ++
 pyto/CHANGES.md                                    |   1 +
 .../grouped-ablation/candidates/README.md          |   2 +-
 .../grouped-ablation/candidates/readpql_check.mjs  |  47 +++++--
 pyto/experiments/grouped-ablation/pql_document.py  |  93 +++++++++-----
 .../grouped-ablation/test_second_experiment.py     |  83 +++++++-----
 scripts/browser_test.py                            |  30 +++++
 scripts/review_checkpoint.mjs                      |   2 +-
 src/app.js                                         |  21 ++-
 src/core/exec.js                                   |  53 +++++++-
 src/formats/receipt-list.js                        |  50 ++++++++
 src/formats/undo.js                                |  35 +++++
 src/review-data.js                                 |   3 +-
 src/runtime.js                                     |  38 +++++-
 src/style.css                                      |   8 ++
 tests/core.test.js                                 | 142 +++++++++++++++++++++
 16 files changed, 531 insertions(+), 89 deletions(-)
```

## Evidence

- verify: `npm test && node --test pyto/viewer/test/*.test.mjs && python3 scripts/browser_test.py --embedded` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         248  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    249  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} RecordAdapterHasOneIntoPerInvocation: the record contract already allows an array `into` (RECORD.md:117-119; `requireInto` and `produceAddresses` in pyto/viewer/adapters.js handle it), but the DiscStudio reader in the same file does not -- `fromDiscStudioReceipt` writes `id: uniqueId(into)`, `actual_produces: [into]` and `writes: [{address: into}]`, so a composition with several `into` fails `validate()` on the id and on `actual_produces` being an array of arrays. pyto/viewer belongs to another team and is outside this task's allow list, so the studio's own multi-produce Calculation (`fn.studio.receipts`) is never run-recorded, and `fn.undo.pop` was split into a pop that restores the value at the address and an `fn.undo.settle` in a second Tick that shortens the stack, so `runRecord('studio-undo')` still validates. One pop publishing both Parts is the honest shape and is one adapter change away; the owner decides whether that change is asked of the viewer team.

{?} UndoIsScopedToTheWholeWorld: `px.undo.studio` records `px.studio.world` and every `dispatch` pushes it, so the Shelf card's Undo button reverses one command whatever it touched, and the sample workspace comes back exactly. The Part and the three Calculations are generic (`push(address, scope)`), so a per-format scope -- undo for the customizer alone, or per node -- is a caller's choice and nothing in the grammar forbids it; nothing yet uses one, and no `redo` exists (the popped value is dropped rather than moved to a forward stack).

{?} TheReceiptsQueryListsItsOwnReceipt: `fn.studio.receipts` writes `px.receipt.studio-receipts` after the query has read the board, so the first reading of the Inspect list does not list itself and every later one does. That is honest -- the query is over the record as it stood -- and it is what the browser check exercises by opening the panel twice, but it means the row count moves by one on the first open of a session. Suppressing the self-row would be a lie about what `px.receipt.*` holds; the owner decides whether the page should say so in words.

{?} PqlDocumentKeepsAStaleLineReference: `pql_document.to_pql_document`'s "has no 'into'" refusal still names `exec.js:46` because `test_retain.py` pins that exact token and is outside this task's allow list; the message now names `produces` at exec.js:50-57 beside it. Every other reference in that module was renumbered to today's exec.js. The tidy fix is one line in a file this task may not touch.

{?} NoSubagentToolInThisEnvironment: the packet asked for two Sonnet lanes spawned with the Agent tool; this session has no Agent/Task tool (only SendMessage to already-running peers), so both lanes were built here, in the order Lane A -> Lane B -> integration, on the same allow list. Nothing about the result depends on it, but the two-lane shape was not tested.
