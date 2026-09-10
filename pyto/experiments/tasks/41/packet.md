# Task 41

Intent: the px shell: a px command over records and stores: px ps, px ls, px cat, px diff, px laws, px receipts; PQL reads receipts as Parts; the store refuses writes under px.receipt except from a run; every command is a pure function of its inputs with byte-identical output tests
Starting point: 4474273d423e62ae84eb42f2f7a4a61a01cbf4e2 (board: **started** `task-40`: parallel you can see: the Tick viewer draws a Tic)
Verify: cd pyto && python3 -m unittest tests.test_px tests.test_pql tests.test_semantics tests.test_first_class
Allow: pyto/src/pyto/px.py pyto/src/pyto/pql.py pyto/src/pyto/core.py pyto/src/pyto/__init__.py pyto/pyproject.toml pyto/tests pyto/CHANGES.md pyto/experiments/tasks pyto/experiments/grouped-ablation/evidence
Candidate: 65 files, see below
Evidence: suite exit 0, see below

## What landed

Frontier add C ("The receipts are queryable", pyto/FRONTIER.md:45-58), in three pieces.

**`px`, a shell over run records** (`pyto/src/pyto/px.py`, registered as
`[project.scripts] px = "pyto.px:main"` and runnable as `python -m pyto.px`).  Six
commands over a `pyto-run-record@1` file:

| command | what it prints |
|---|---|
| `px ps <record> [--times]` | one line per invocation: tick, tick name, id, calculation address, `into` (one or several), `hit`/`computed`, and the recorded duration only under `--times` |
| `px ls <record> [prefix]` | every address the record knows -- preexisting, produced, and receipt addresses when a record lists them -- sorted, with its kind and who produced it |
| `px cat <record> <address>` | the produced Part's value as canonical JSON (sorted keys, two-space indent, RECORD.md), or `not carried` with the record's note |
| `px diff <a.json> <b.json>` | differences by invocation -- added, removed, digest changed, reads changed -- and exit 1 when there are any |
| `px laws <record> [--times]` | the node law and the loop law, delegated to `experiments/tick-laws/tick_laws.analyze_record`, with `tick_laws`' exit codes |
| `px receipts <record> [--tick NAME]` | the receipts as rows: declared reads beside actual, declared writes beside actual, both digests |

`px` imports no kernel runtime: it reads JSON plus two shared readers loaded by
path (`viewer/test/record_schema.py` for validation and `resolve_binding`/
`derive_part_index`, `experiments/tick-laws/tick_laws.py` for the laws), the way
`experiments/students/grade.py` loads the validator, but through an importlib
spec so `sys.path` is untouched.  A test asserts the absence of every
`from .pcr` / `from .core` / `from .pql` / `from .materialize` import.

Every command's output is a pure function of its inputs: no timestamps, no
absolute paths (`px laws` names the record's `pcr` where `tick_laws` echoes the
path it was handed; every error message names `Path(...).name` only), sorted
everywhere, and durations only when `--times` asks.  `tests/test_px.py` runs each
command in a **subprocess** on both committed records and compares stdout byte
for byte to 16 expected files under `tests/fixtures/px/`.

**PQL reads receipts** (`pyto/src/pyto/pql.py`).  `PQL.receipts(pxc, pcr=None,
tick=None)` is a thin layer over `PQL.prefix` whose docstring is the one place the
address scheme `px.receipt.<pcr>.<tick>.<invocation-id>` is spelled for a reader.
It narrows **by segment**, not by string prefix, so `pcr="count"` does not match a
PCR named `counted`, and `tick=` alone lands on the second segment rather than the
first.

**The store guards the receipt segment** (`pyto/src/pyto/core.py`).  `PxC.set`
now refuses an address under `px.receipt.` unless the write is the run's own.
`pcr.py` belongs to another team and was **not edited**, so the guard has three
ways in, in the order they are checked:

1. a module-level `pyto.core.receipt_writes_allowed()` context manager (re-entrant,
   restored on a raise) -- the explicit form, which a future `pcr.py` can adopt;
2. the calling frame's module being `pyto.core.RUN_MODULE` (`"pyto.pcr"`), which is
   why today's unedited `pcr.py:647` keeps working;
3. a keyword-only `PxC.set(..., _from_run=True)` -- the marker `PcrRun`'s observe
   branch would pass.

The rule is deterministic and consults only *who is calling*: nothing about
timing, ordering or the value.  A plain `pxc.set("px.receipt.x", ...)` from user
code raises `ValueError`, and `tests/test_receipts.py` (32 tests) passes
**unedited**.

## Regeneration

The grouped-ablation evidence pins the kernel modules' source digests (`core.py`
and `pql.py` appear in every `retained.json` provider block), so changing either
turns that suite red until the evidence is rebuilt.  It was regenerated here.
Another team's landing will move MAIN, so **this must be rerun after `neat
update`** -- from `EXP/41/pyto` with the copy's venv active
(`source ../.venv/bin/activate`), in this order:

```sh
cd pyto
source ../.venv/bin/activate
python3 experiments/grouped-ablation/run.py               --out evidence/run-1              --force
python3 experiments/grouped-ablation/run_regrouped.py     --out evidence/run-2-regroup      --force
python3 experiments/grouped-ablation/run_reinput.py       --out evidence/run-3-reinput      --force
python3 experiments/grouped-ablation/run_from_retained.py --out evidence/run-4-from-retained --force
python3 experiments/grouped-ablation/run_cached.py --force
python3 experiments/grouped-ablation/replay.py --force
```

`--out` is not optional on the first four: without it `run.py` writes to a fresh
temporary directory and leaves the tracked evidence alone (which is the point of
that default), and the other three refuse a non-empty destination.  `run-1`'s
`record.json` -- one of the two records every `px` test reads -- is byte-identical
across the regeneration; only `commit.txt`, `timings.json`, `saved-work.json`,
`receipts.json` (durations) and the `retained.json` provider digests move.  No
test expectation and no `px` fixture was edited for it.

## Mutation checks

Three claims, each mutated and the named test watched to fail, then restored
(`git status` clean afterwards):

1. `src/pyto/core.py:144` -- delete the `if address.startswith(RECEIPT_PREFIX) and
   not _from_run:` guard in `PxC.set`.  3 failures in `tests/test_pql.py`, first
   `ReceiptWritesAreTheRunS::test_user_code_cannot_forge_a_receipt`
   ("ValueError not raised").
2. `src/pyto/px.py:349` -- `print(f"pcr: {record['pcr']}")` -> `print(f"pcr: {args.record}")`
   in `cmd_laws`.  4 failures in `tests/test_px.py`: the three `laws` fixtures and
   `test_laws_prints_no_path`.  This is the line that keeps an absolute path out
   of `px laws`.
3. `src/pyto/pql.py:75` -- index `PQL.receipts`' `wanted` from 0 over the given
   segments instead of by segment position.  1 failure,
   `PqlReceipts::test_tick_narrows_on_the_second_segment_with_or_without_a_pcr`:
   a lone `tick=` would match the PCR name's segment instead of the Tick's.

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
- A  pyto/experiments/tasks/41/evidence/check_all.txt
- A  pyto/experiments/tasks/41/evidence/verify.txt
- A  pyto/experiments/tasks/41/packet.md
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

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_px tests.test_pql tests.test_semantics tests.test_first_class` exit 0 (evidence/verify.txt)
    Ran 95 tests in 3.012s
    
    OK
- the six commands' first line of stdout on the students record (`experiments/students/evidence/run-1/record.json`), copied from the committed fixtures:
    ```
    $ px ps            TICK  TICK-NAME  ID         CALCULATION            INTO                   STATE
    $ px ls            ADDRESS                 KIND  PRODUCED-BY
    $ px cat ... mean  {
    $ px diff (self)   no differences
    $ px laws          LIMITATION: reads are every input binding: px: bindings are store reads, fn: bindings are result...
    $ px receipts      TICK  ID         DECLARED-READS             ACTUAL-READS            DECLARED-WRITES        ACTUA...
    ```
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
    viewer                          107  OK
    viewer-record-schema             24  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} ReceiptInputNotRefused: decided in code as it already stood -- only a declared `into` under `px.receipt.` is refused, so a receipt may be *bound as an input* and `PxC.set`'s new guard was deliberately not extended to reads (`tests/test_pql.py::ReceiptsAsInputsAndOnRerun::test_a_receipt_may_be_bound_as_an_input`); if the owner meant reads too, the guard moves from `into` to the whole binding map and `px receipts` output can never be fed back into a program.
{?} ReceiptRerunOverwrite: decided in code as it already stood -- a rerun of the same PCR against one store replaces each receipt Part in place, one address per invocation and only the last run's receipts survive (`::test_a_rerun_replaces_the_receipt_part_in_place` pins it so the change is visible when someone makes it). FRONTIER.md add C says "a rerun replaces, and the record keeps the run id"; the record has a `pcr` name and no run id, so the run-id half is not done and is the open part of this line.
{?} ReceiptNameSegments: left untouched, as the brief asked. `PQL.receipts` reads the address exactly as `receipt_address` writes it, so a PCR or Tick name carrying a dot shifts which segment `tick=` matches; the docstring says so rather than slugifying. `address.check` gained no reserved-segment-shape rule.
{?} ReceiptGuardIsFrameShaped: `PxC.set`'s guard recognises the run by the calling frame's module (`core.RUN_MODULE == "pyto.pcr"`) because `pcr.py` is another team's file and could not be edited to pass `_from_run=True`. It is deterministic and cheap, but it is a rule about *file layout*: split `pcr.py`, or file a receipt from a helper in another module, and the write is refused. The intended end state is `pcr.py` calling `set(..., _from_run=True)` or wrapping its observe branch in `receipt_writes_allowed()`, after which `RUN_MODULE` can be deleted; one line in `pcr.py`, whenever that team is willing.
{?} PxLawsPrintsNoPath: `px laws` does not delegate to `tick_laws.main`, because `tick_laws`' own text output echoes the path it was handed and no `px` command may print an absolute path. It calls `analyze_record` and renders the report itself, keeping `tick_laws`' exit codes (0 / 1) and its `LIMITATION` line verbatim. If the owner wants `px laws` to be exactly `tick_laws`' output, the fix belongs in `tick_laws._print_text` (print the record's `pcr`, not the path), which is outside this task's Allow line.
{?} PxReceiptsReadsTheRecordNotTheStore: `px receipts <record>` derives its rows from the record's invocations (`declared_consumes` / `actual_consumes` / `into` / `writes` / `result_sha256` / `implementation_sha256`), because a `pyto-run-record@1` document carries no receipt store rows at all (RECORD.md, "Receipts as Parts"). That makes it a witness of each `Receipt`, not the `Receipt` itself, and `produce_sha256` -- the per-produce digest that lives only on the `Receipt` -- cannot be shown. A `px receipts` over a live `PxC` (via `PQL.receipts`) would show it; that is a second command and no record format exists for it.
