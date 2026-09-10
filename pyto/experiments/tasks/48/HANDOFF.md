# Task 48: the JavaScript runtime speaks the same schedule: exec.js runs a Tick's Calculations concurrently when the node law holds and refuses sibling reads at read time, takes a budget that stops at a Tick boundary, and the studio's run record carries parallel, placement, latency_ms and budget exactly as the Python kernel writes them; testimony byte-identical serial versus parallel; the record adapter accepts an array into; the studio's Tick page shows a parallel Tick

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Stop here first (the owner's rule)

Read this page, `pyto/BOARD.md`, and the packet. No fourth file yet. Then write the one question
you would answer by reading another hundred thousand tokens of code, and ask the owner instead.
His answer is worth more than the reading: the last session that read everything first was
confidently wrong about half of it, and one sentence from him undid each wrong half. The answer
goes on `pyto/questions.md` verbatim, as `{?} Label: ...` with his words, so the next agent starts
one stupid question deeper. Only then read further and do the work below.

## Get the code (once)

```
git clone -b claude/os-sprint-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/48
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/48:pyto/experiments/tasks/48/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 9add98b origin/exp/48 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
```

## Why this repository is worth twenty minutes

pyto is a Python transfer of a design the owner proved three times in JavaScript and TypeScript
(ChainSpot, ChessLab, EmbodiedWumpusWorld): a store of named values (PxC), pure functions over them
(Calculations), and a program that names which functions run in which order (a PCR, made of Ticks).
Every run leaves receipts: what each function read and wrote, how long it took, and a digest of its
source. From receipts you get three things for free: a cache (same inputs and digest, skip the call,
also across processes), a replay that verifies a shipped record in a fresh process, and a per-Tick
view of what the algorithm used. The founding need is the last one: the owner's course-map parser
had to fit five seconds on a phone, and nothing it used was visible. pyto is the workshop where that
visibility is designed before it is stripped for speed. JavaScript is first class; Python is where
the design is checked.

Do not take that from this page. In two minutes:

```
bash pyto/scripts/check_all.sh                                        # nine suites, ~600 tests
python pyto/experiments/grouped-ablation/run_cached.py --out /tmp/hit  # a miss, then two hits, one from a fresh process
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /tmp/hit/ticks.html
```

The tests were checked by mutation (each guards a specific line). The fixtures for the JavaScript
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{?} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

the JavaScript runtime speaks the same schedule: exec.js runs a Tick's Calculations concurrently when the node law holds and refuses sibling reads at read time, takes a budget that stops at a Tick boundary, and the studio's run record carries parallel, placement, latency_ms and budget exactly as the Python kernel writes them; testimony byte-identical serial versus parallel; the record adapter accepts an array into; the studio's Tick page shows a parallel Tick

## Starting point

f48fb3568c948fc5b43eb7ed13971fad9b9c0805 (exp/47: next_id counts the landing receipts; an undone id is never reused). MAIN may have moved since: `git log --oneline 9add98b..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  .neat/items/DS-STUDIO-02.json
- M  pyto/CHANGES.md
- M  pyto/viewer/adapters.js
- M  pyto/viewer/test/adapters.test.mjs
- M  scripts/browser_test.py
- M  scripts/review_checkpoint.mjs
- M  src/app.js
- M  src/core/exec.js
- M  src/review-data.js
- M  src/runtime.js
- M  tests/core.test.js
- A  tests/fixtures/serial-run-record.json

```
.neat/items/DS-STUDIO-02.json         |    4 +-
 pyto/CHANGES.md                       |    1 +
 pyto/viewer/adapters.js               |   46 +-
 pyto/viewer/test/adapters.test.mjs    |   66 +
 scripts/browser_test.py               |   24 +
 scripts/review_checkpoint.mjs         |    2 +-
 src/app.js                            |    2 +-
 src/core/exec.js                      |  176 +-
 src/review-data.js                    |    4 +-
 src/runtime.js                        |   57 +-
 tests/core.test.js                    |  150 +-
 tests/fixtures/serial-run-record.json | 7058 +++++++++++++++++++++++++++++++++
 12 files changed, 7548 insertions(+), 42 deletions(-)
```

## Evidence

- verify: `npm test && node --test pyto/viewer/test/*.test.mjs && python3 scripts/browser_test.py --embedded` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.t7f3vPGTVt) (evidence/check_all.txt)
    suite                         tests  status
    library                         314  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} ParallelIsAsync: a Tick whose branches overlap can only be awaited, so `parallel: true` is `invokePqlAsync(doc, pxc, {parallel: true})` and the synchronous `invokePql(doc, pxc, {budgetMs, clock})` refuses it by name. Keeping one synchronous entry point is what leaves the studio's own path -- dispatch, card, scene, constraints, undo -- unchanged and its serial record byte for byte what it was; a budget needs no awaiting and works in both. Owner: say the word and `invokePql` returns a Promise always, and every caller in src/ and every browser check becomes async.
{?} PlacementInAOneBranchTick: a parallel run writes a placement for every invocation, including a Tick that holds one Calculation (worker 0, started_ms ~0), because the run, not the Tick, is what was parallel -- which is also what pyto.materialize does with `reports_schedule`. The other reading is that `isParallelTick` decides it (a Tick of one branch is not parallel and has no placement to report), which would make the field null for exactly the Ticks the viewer draws as a single card.
{?} StageGroupedSampleComposition: `runtime.sceneParallel` runs the sample composition as one Tick per stage (every card's Fields, then every card's Art, ...) instead of one Tick per card step, because that is the grouping the node law allows to overlap; the serial `scene()` still writes the fourteen one-Calculation Ticks the record review item names. Two shapes of the same composition now exist. Owner: if the grouped shape is the real one, `scene()` should use it too and the review item's "14 Ticks, 14 invocations" is rewritten.
{?} DiscStudioLatencyIsMeasured: a DiscStudio invocation has no `duration_ms` (runtime.js records reuse and material identity, never a duration), so a Tick's `latency_ms` here is exec.js's own measurement rather than the sum of its durations, and `tickLatencyMs`'s fallback cannot check it. A budgeted serial run therefore reports a real wall time where the Python kernel would report the sum; the injected clock is what makes it deterministic in tests.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 48 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 48`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-48): the JavaScript runtime speaks the same schedule: exec.js runs a Tick's Calculations concurrently when the node law holds and refuses sibling reads at read time, takes a budget that stops at a Tick boundary, and the studio's run record carries parallel, placement, latency_ms and budget exactly as the Python kernel writes them; testimony byte-identical serial versus parallel; the record adapter accepts an array into; the studio's Tick page shows a parallel Tick`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
