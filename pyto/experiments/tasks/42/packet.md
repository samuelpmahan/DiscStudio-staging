# Task 42

Intent: the studio speaks the whole record: the site's PQL grammar accepts several into per Calculation and runs it, the Inspect page lists the studio's own receipts through PQL, and an UndoStack Part gives every format undo in the browser with receipts
Starting point: 5fa1383cc7a8516f3ebbd561eb01252d8870ff4a (board: **started** `task-41`: the px shell: a px command over records and store)
Verify: npm test && node --test pyto/viewer/test/*.test.mjs && python3 scripts/browser_test.py --embedded
Allow: src tests scripts/browser_test.py scripts/review_checkpoint.mjs .neat/items pyto/experiments/grouped-ablation/pql_document.py pyto/experiments/grouped-ablation/test_second_experiment.py pyto/experiments/grouped-ablation/candidates pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} RecordAdapterHasOneIntoPerInvocation: the record contract already allows an array `into` (RECORD.md:117-119; `requireInto` and `produceAddresses` in pyto/viewer/adapters.js handle it), but the DiscStudio reader in the same file does not -- `fromDiscStudioReceipt` writes `id: uniqueId(into)`, `actual_produces: [into]` and `writes: [{address: into}]`, so a composition with several `into` fails `validate()` on the id and on `actual_produces` being an array of arrays. pyto/viewer belongs to another team and is outside this task's allow list, so the studio's own multi-produce Calculation (`fn.studio.receipts`) is never run-recorded, and `fn.undo.pop` was split into a pop that restores the value at the address and an `fn.undo.settle` in a second Tick that shortens the stack, so `runRecord('studio-undo')` still validates. One pop publishing both Parts is the honest shape and is one adapter change away; the owner decides whether that change is asked of the viewer team.

{?} UndoIsScopedToTheWholeWorld: `px.undo.studio` records `px.studio.world` and every `dispatch` pushes it, so the Shelf card's Undo button reverses one command whatever it touched, and the sample workspace comes back exactly. The Part and the three Calculations are generic (`push(address, scope)`), so a per-format scope -- undo for the customizer alone, or per node -- is a caller's choice and nothing in the grammar forbids it; nothing yet uses one, and no `redo` exists (the popped value is dropped rather than moved to a forward stack).

{?} TheReceiptsQueryListsItsOwnReceipt: `fn.studio.receipts` writes `px.receipt.studio-receipts` after the query has read the board, so the first reading of the Inspect list does not list itself and every later one does. That is honest -- the query is over the record as it stood -- and it is what the browser check exercises by opening the panel twice, but it means the row count moves by one on the first open of a session. Suppressing the self-row would be a lie about what `px.receipt.*` holds; the owner decides whether the page should say so in words.

{?} PqlDocumentKeepsAStaleLineReference: `pql_document.to_pql_document`'s "has no 'into'" refusal still names `exec.js:46` because `test_retain.py` pins that exact token and is outside this task's allow list; the message now names `produces` at exec.js:50-57 beside it. Every other reference in that module was renumbered to today's exec.js. The tidy fix is one line in a file this task may not touch.

{?} NoSubagentToolInThisEnvironment: the packet asked for two Sonnet lanes spawned with the Agent tool; this session has no Agent/Task tool (only SendMessage to already-running peers), so both lanes were built here, in the order Lane A -> Lane B -> integration, on the same allow list. Nothing about the result depends on it, but the two-lane shape was not tested.
