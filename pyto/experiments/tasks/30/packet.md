# Task 30

Intent: every reader handles several produces: compare_local.py and pql_document.py in grouped-ablation stop assuming one into per invocation; tests for both
Starting point: f1524b4ca3dcf6331f25f606934c412b8bde7627 (board: **started** `task-29`: students: Mean and Median run in one Tick as para)
Verify: cd pyto && python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'
Allow: pyto/experiments/grouped-ablation/compare_local.py pyto/experiments/grouped-ablation/pql_document.py pyto/experiments/grouped-ablation/test_grouped_ablation.py pyto/experiments/grouped-ablation/test_second_experiment.py pyto/experiments/grouped-ablation/evidence pyto/CHANGES.md pyto/experiments/tasks
Candidate: 4 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/CHANGES.md
- M  pyto/experiments/grouped-ablation/compare_local.py
- M  pyto/experiments/grouped-ablation/pql_document.py
- M  pyto/experiments/grouped-ablation/test_second_experiment.py

```
pyto/CHANGES.md                                    |   2 +
 pyto/experiments/grouped-ablation/compare_local.py |  79 +++++++++-
 pyto/experiments/grouped-ablation/pql_document.py  |  20 +++
 .../grouped-ablation/test_second_experiment.py     | 174 +++++++++++++++++++++
 4 files changed, 270 insertions(+), 5 deletions(-)
```

## Evidence

- verify: `cd pyto && python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         193  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             11  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} PqlMultiProduceIsRefused: `to_pql_document` REFUSES a multi-produce invocation instead of emitting one, naming the invocation (`<Tick>.<id>`) and every address it declared. The readPql grammar has one `into` per Calculation and reads it with `text(...)`, a nonempty string (`src/core/exec.js:46`), and `invokePql` writes exactly that one address (`pxc.set(calculation.into, output)`, exec.js:58) -- there is no place in the document for a second address and no rule by which the reader could split one result across two, so emitting the first address (or a JSON array the reader rejects at parse time) would be a document that says something false about the program. Widening the grammar was not this task's to do; if the owner wants the browser to run multi-produce Calculations, that is a change to exec.js and to `candidates/readpql_check.mjs`, and this refusal is the line it would replace.
{?} ConsumersOfOverlap: `consumers_of` now matches two `fn:` refs when they read a Part in common, not only when they are the same string -- a bare `fn:<id>` (every Part that invocation published) lists the ids that bind `fn:<id>#<address>` for any one of them, and a qualified ref lists only the readers of that one produce. Exact string equality still matches, so every one-address answer is unchanged; the alternative was to leave it literal, which reports "nothing consumes `stats`" for an invocation whose whole fan-out binds it by qualified spelling.
{?} PxWriterLastWins: `_writer_of` keeps the old "later declaration wins" rule when two invocations publish the same address, now per address rather than per `into` field. A multi-produce invocation can therefore be the writer of one address and not of another it also declared, if a later invocation republishes the second. Nothing here refuses a republished address; `PxWrite.kind` already reports it as a `replacement` (task 27 `{?} MultiWriteKinds`).
