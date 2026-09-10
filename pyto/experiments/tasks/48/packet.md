# Task 48

Intent: the JavaScript runtime speaks the same schedule: exec.js runs a Tick's Calculations concurrently when the node law holds and refuses sibling reads at read time, takes a budget that stops at a Tick boundary, and the studio's run record carries parallel, placement, latency_ms and budget exactly as the Python kernel writes them; testimony byte-identical serial versus parallel; the record adapter accepts an array into; the studio's Tick page shows a parallel Tick
Starting point: f48fb3568c948fc5b43eb7ed13971fad9b9c0805 (exp/47: next_id counts the landing receipts; an undone id is never reused)
Verify: npm test && node --test pyto/viewer/test/*.test.mjs && python3 scripts/browser_test.py --embedded
Allow: src tests scripts/browser_test.py scripts/review_checkpoint.mjs .neat/items pyto/viewer/adapters.js pyto/viewer/test/adapters.test.mjs pyto/viewer/RECORD.md pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} ParallelIsAsync: a Tick whose branches overlap can only be awaited, so `parallel: true` is `invokePqlAsync(doc, pxc, {parallel: true})` and the synchronous `invokePql(doc, pxc, {budgetMs, clock})` refuses it by name. Keeping one synchronous entry point is what leaves the studio's own path -- dispatch, card, scene, constraints, undo -- unchanged and its serial record byte for byte what it was; a budget needs no awaiting and works in both. Owner: say the word and `invokePql` returns a Promise always, and every caller in src/ and every browser check becomes async.
{?} PlacementInAOneBranchTick: a parallel run writes a placement for every invocation, including a Tick that holds one Calculation (worker 0, started_ms ~0), because the run, not the Tick, is what was parallel -- which is also what pyto.materialize does with `reports_schedule`. The other reading is that `isParallelTick` decides it (a Tick of one branch is not parallel and has no placement to report), which would make the field null for exactly the Ticks the viewer draws as a single card.
{?} StageGroupedSampleComposition: `runtime.sceneParallel` runs the sample composition as one Tick per stage (every card's Fields, then every card's Art, ...) instead of one Tick per card step, because that is the grouping the node law allows to overlap; the serial `scene()` still writes the fourteen one-Calculation Ticks the record review item names. Two shapes of the same composition now exist. Owner: if the grouped shape is the real one, `scene()` should use it too and the review item's "14 Ticks, 14 invocations" is rewritten.
{?} DiscStudioLatencyIsMeasured: a DiscStudio invocation has no `duration_ms` (runtime.js records reuse and material identity, never a duration), so a Tick's `latency_ms` here is exec.js's own measurement rather than the sum of its durations, and `tickLatencyMs`'s fallback cannot check it. A budgeted serial run therefore reports a real wall time where the Python kernel would report the sum; the injected clock is what makes it deterministic in tests.
