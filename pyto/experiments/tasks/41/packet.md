# Task 41

Intent: the px shell: a px command over records and stores: px ps, px ls, px cat, px diff, px laws, px receipts; PQL reads receipts as Parts; the store refuses writes under px.receipt except from a run; every command is a pure function of its inputs with byte-identical output tests
Starting point: 4474273d423e62ae84eb42f2f7a4a61a01cbf4e2 (board: **started** `task-40`: parallel you can see: the Tick viewer draws a Tic)
Verify: cd pyto && python3 -m unittest tests.test_px tests.test_pql tests.test_semantics tests.test_first_class
Allow: pyto/src/pyto/px.py pyto/src/pyto/pql.py pyto/src/pyto/core.py pyto/src/pyto/__init__.py pyto/pyproject.toml pyto/tests pyto/CHANGES.md pyto/experiments/tasks pyto/experiments/grouped-ablation/evidence
Candidate: 62 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/CHANGES.md
- M  pyto/experiments/grouped-ablation/evidence/disc-stats-sidecar.json
- M  pyto/experiments/grouped-ablation/evidence/lf-source-drift.log
- M  pyto/experiments/grouped-ablation/evidence/replay/forged-record-refused.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-2-regroup.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-3-reinput.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-4-from-retained.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/digest-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/module-leak.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/registry-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/source-sha-mismatch.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/value-forged-rows.log
- M  pyto/experiments/grouped-ablation/evidence/run-1/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-1/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/mutating-baseline-refused-record.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/retained-tampered.json
- M  pyto/pyproject.toml
- M  pyto/src/pyto/core.py
- M  pyto/src/pyto/pql.py
- A  pyto/src/pyto/px.py
- A  pyto/tests/fixtures/px/cat-ablation-comparison.txt
- A  pyto/tests/fixtures/px/cat-students-mean.txt
- A  pyto/tests/fixtures/px/diff-students-flipped.txt
- A  pyto/tests/fixtures/px/diff-students-students.txt
- A  pyto/tests/fixtures/px/laws-ablation.txt
- A  pyto/tests/fixtures/px/laws-students.txt
- A  pyto/tests/fixtures/px/laws-times-students.txt
- A  pyto/tests/fixtures/px/ls-ablation-models.txt
- A  pyto/tests/fixtures/px/ls-ablation.txt
- A  pyto/tests/fixtures/px/ls-students.txt
- A  pyto/tests/fixtures/px/ps-ablation.txt
- A  pyto/tests/fixtures/px/ps-students.txt
- A  pyto/tests/fixtures/px/ps-times-students.txt
- A  pyto/tests/fixtures/px/receipts-ablation.txt
- A  pyto/tests/fixtures/px/receipts-students-stats.txt
- A  pyto/tests/fixtures/px/receipts-students.txt
- A  pyto/tests/test_pql.py
- A  pyto/tests/test_px.py

```
pyto/CHANGES.md                                    |   2 +
 .../evidence/disc-stats-sidecar.json               |   2 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |  10 +-
 .../evidence/replay/forged-record-refused.log      |  20 +-
 .../replay/fresh-process-run-2-regroup.log         |  20 +-
 .../replay/fresh-process-run-3-reinput.log         |  20 +-
 .../replay/fresh-process-run-4-from-retained.log   |  20 +-
 .../evidence/replay/fresh-process.log              |  22 +-
 .../evidence/replay/refusals/digest-forged.log     |  20 +-
 .../evidence/replay/refusals/module-leak.log       |  20 +-
 .../evidence/replay/refusals/registry-forged.log   |  20 +-
 .../replay/refusals/source-sha-mismatch.log        |  20 +-
 .../evidence/replay/refusals/value-forged-rows.log |  20 +-
 .../grouped-ablation/evidence/run-1/commit.txt     |   2 +-
 .../grouped-ablation/evidence/run-1/receipts.json  |  60 +--
 .../grouped-ablation/evidence/run-1/retained.json  |   4 +-
 .../evidence/run-1/saved-work.json                 |   8 +-
 .../grouped-ablation/evidence/run-1/timings.json   |   6 +-
 .../evidence/run-2-regroup/commit.txt              |   2 +-
 .../evidence/run-2-regroup/interpretation.md       |   2 +-
 .../evidence/run-2-regroup/receipts.json           |  44 +-
 .../evidence/run-2-regroup/retained.json           |   4 +-
 .../evidence/run-2-regroup/saved-work.json         |   4 +-
 .../evidence/run-2-regroup/timings.json            |   6 +-
 .../evidence/run-3-reinput/commit.txt              |   2 +-
 .../evidence/run-3-reinput/interpretation.md       |   2 +-
 .../evidence/run-3-reinput/receipts.json           |  60 +--
 .../evidence/run-3-reinput/retained.json           |   4 +-
 .../evidence/run-3-reinput/saved-work.json         |   4 +-
 .../evidence/run-3-reinput/timings.json            |   6 +-
 .../evidence/run-4-from-retained/commit.txt        |   2 +-
 .../evidence/run-4-from-retained/interpretation.md |   2 +-
 .../evidence/run-4-from-retained/receipts.json     |  56 +--
 .../evidence/run-4-from-retained/retained.json     |   4 +-
 .../evidence/run-4-from-retained/saved-work.json   |   4 +-
 .../evidence/run-4-from-retained/timings.json      |   2 +-
 .../evidence/run-6-cached/interpretation.md        |   6 +-
 .../evidence/run-6-cached/reuse-ledger.json        |  14 +-
 .../tamper/mutating-baseline-refused-record.json   |   4 +-
 .../evidence/tamper/retained-tampered.json         |   4 +-
 pyto/pyproject.toml                                |   3 +
 pyto/src/pyto/core.py                              |  80 +++-
 pyto/src/pyto/pql.py                               |  51 ++-
 pyto/src/pyto/px.py                                | 465 +++++++++++++++++++++
 pyto/tests/fixtures/px/cat-ablation-comparison.txt |  44 ++
 pyto/tests/fixtures/px/cat-students-mean.txt       |   5 +
 pyto/tests/fixtures/px/diff-students-flipped.txt   |   1 +
 pyto/tests/fixtures/px/diff-students-students.txt  |   1 +
 pyto/tests/fixtures/px/laws-ablation.txt           |   4 +
 pyto/tests/fixtures/px/laws-students.txt           |   4 +
 pyto/tests/fixtures/px/laws-times-students.txt     |   9 +
 pyto/tests/fixtures/px/ls-ablation-models.txt      |   7 +
 pyto/tests/fixtures/px/ls-ablation.txt             |  18 +
 pyto/tests/fixtures/px/ls-students.txt             |   7 +
 pyto/tests/fixtures/px/ps-ablation.txt             |  16 +
 pyto/tests/fixtures/px/ps-students.txt             |   6 +
 pyto/tests/fixtures/px/ps-times-students.txt       |   6 +
 pyto/tests/fixtures/px/receipts-ablation.txt       |  16 +
 pyto/tests/fixtures/px/receipts-students-stats.txt |   3 +
 pyto/tests/fixtures/px/receipts-students.txt       |   6 +
 pyto/tests/test_pql.py                             | 294 +++++++++++++
 pyto/tests/test_px.py                              | 431 +++++++++++++++++++
 62 files changed, 1740 insertions(+), 271 deletions(-)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_px tests.test_pql tests.test_semantics tests.test_first_class` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         248  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    248  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            10  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} ReceiptInputNotRefused: decided in code as it already stood -- only a declared `into` under `px.receipt.` is refused, so a receipt may be *bound as an input* and `PxC.set`'s new guard was deliberately not extended to reads (`tests/test_pql.py::ReceiptsAsInputsAndOnRerun::test_a_receipt_may_be_bound_as_an_input`); if the owner meant reads too, the guard moves from `into` to the whole binding map and `px receipts` output can never be fed back into a program.
{?} ReceiptRerunOverwrite: decided in code as it already stood -- a rerun of the same PCR against one store replaces each receipt Part in place, one address per invocation and only the last run's receipts survive (`::test_a_rerun_replaces_the_receipt_part_in_place` pins it so the change is visible when someone makes it). FRONTIER.md add C says "a rerun replaces, and the record keeps the run id"; the record has a `pcr` name and no run id, so the run-id half is not done and is the open part of this line.
{?} ReceiptNameSegments: left untouched, as the brief asked. `PQL.receipts` reads the address exactly as `receipt_address` writes it, so a PCR or Tick name carrying a dot shifts which segment `tick=` matches; the docstring says so rather than slugifying. `address.check` gained no reserved-segment-shape rule.
{?} ReceiptGuardIsFrameShaped: `PxC.set`'s guard recognises the run by the calling frame's module (`core.RUN_MODULE == "pyto.pcr"`) because `pcr.py` is another team's file and could not be edited to pass `_from_run=True`. It is deterministic and cheap, but it is a rule about *file layout*: split `pcr.py`, or file a receipt from a helper in another module, and the write is refused. The intended end state is `pcr.py` calling `set(..., _from_run=True)` or wrapping its observe branch in `receipt_writes_allowed()`, after which `RUN_MODULE` can be deleted; one line in `pcr.py`, whenever that team is willing.
{?} PxLawsPrintsNoPath: `px laws` does not delegate to `tick_laws.main`, because `tick_laws`' own text output echoes the path it was handed and no `px` command may print an absolute path. It calls `analyze_record` and renders the report itself, keeping `tick_laws`' exit codes (0 / 1) and its `LIMITATION` line verbatim. If the owner wants `px laws` to be exactly `tick_laws`' output, the fix belongs in `tick_laws._print_text` (print the record's `pcr`, not the path), which is outside this task's Allow line.
{?} PxReceiptsReadsTheRecordNotTheStore: `px receipts <record>` derives its rows from the record's invocations (`declared_consumes` / `actual_consumes` / `into` / `writes` / `result_sha256` / `implementation_sha256`), because a `pyto-run-record@1` document carries no receipt store rows at all (RECORD.md, "Receipts as Parts"). That makes it a witness of each `Receipt`, not the `Receipt` itself, and `produce_sha256` -- the per-produce digest that lives only on the `Receipt` -- cannot be shown. A `px receipts` over a live `PxC` (via `PQL.receipts`) would show it; that is a second command and no record format exists for it.
