# CHANGES.md: library seams of the ULTRACODE week

One entry per change to `pyto/src/pyto/`. Each entry names the day, the seam, the
tests that pinned the behaviour before and after, what it does *not* decide, and
the consumer-bytes statement. At most one library seam lands per day
(research/ULTRACODE-WEEK.md, "Execution policy"), so this file is also the count.

## exp/39 (base 0debaf3): parallel Ticks, placement and budgets -- `PCR.run(pxc, observe=, parallel=, budget_ms=, clock=)` runs a Tick's invocations on a `ThreadPoolExecutor` of `min(len(tick), os.cpu_count())` workers and publishes their Parts in declared order only after the whole Tick (so the store never holds half a Tick), each `Receipt` gains a trailing `placement` (worker index, ms into the Tick, `None` when serial), `Tick.calc`/`PCR.calc` refuse the node law's two shorts at bind time naming both ids (a binding on a sibling's result, two siblings on one address), and `budget_ms` with an injectable `clock` stops the run at a Tick boundary with `PcrRun.stopped_after_tick`/`completed` saying where; the record gains the four optional `placement`/`latency_ms`/`parallel`/`budget` fields **only** for a parallel or budgeted run, so a serial record and the testimony consumers embed are byte for byte what they were (pinned by `tests/test_parallel.py`, `tests/test_budget.py`, `viewer/test/test_record_schema.py::PlacementAndBudget`).
## exp/41 (base 4474273): the store guards the receipt segment -- `PxC.set` refuses an address under `px.receipt.` unless the write is the run's own (a keyword-only `_from_run=True`, the module-level `pyto.core.receipt_writes_allowed()` context manager, or a calling frame inside `pyto.core.RUN_MODULE`, so `pcr.py` keeps working unedited), and `PQL.receipts(pxc, pcr=None, tick=None)` is the named, segment-wise layer over `PQL.prefix` that spells the address scheme once; reading a receipt (as an input or through PQL) is untouched, `tests/test_receipts.py` passes unedited, and the new `pyto/src/pyto/px.py` shell (`px ps|ls|cat|diff|laws|receipts`, registered as `px` in pyproject.toml) imports no kernel runtime at all -- it reads `pyto-run-record@1` JSON plus the two shared readers by path (pinned by `tests/test_pql.py` and `tests/test_px.py` against committed expected output in `tests/fixtures/px/`).

## exp/35: no library seam -- `experiments/students` check 4 now requires each Tick in the record to have a list line of its own under the hand-off's "One line per Tick" heading (`- **Name**`, `- Name:` or `- Name `) instead of matching the Tick name as a substring of the whole page, so deleting a step's bullet is caught even when the name survives in prose (the task 29 `MissingTickTestStillRemovesHistogram` gap); the missing-Tick test now removes the `Stats` bullet, file names keep the substring rule, `evidence/run-1` is untouched and `git diff -- pyto/src` is empty.

## exp/30 (base f1524b4): no library seam -- the last two single-`into` readers in `experiments/grouped-ablation` now handle a Calculation that publishes several Parts: `compare_local` maps every produce address to its writer and resolves `fn:<id>#<address>` bindings, and `pql_document` refuses a multi-produce invocation by name and addresses because the readPql grammar has one `into` string per Calculation (`src/core/exec.js:46`, `invokePql`'s single `pxc.set`); `git diff -- pyto/src` is empty and `test_second_experiment.py` pins both.

## exp/23 (base d13fcd1): no library seam -- `experiments/students` is the first student-facing experiment (a five-Tick homework over a class's scores, its committed `evidence/run-1`, a hand-off page, and `grade.py`'s four mechanical checks: record contract, fresh-process replay on the compared fields, receipt source digests against today's source, hand-off names every Tick and file); `git diff -- pyto/src` is empty and the plain-words explanation is left to a cold reader.

## exp/22 (base 76bc3d2): receipts are Parts -- `PCR.run(..., observe=True)` also writes each `Receipt` into the store at `px.receipt.<pcr>.<tick>.<invocation-id>`, `PCR.calc`/`Tick.calc` refuse a Calculation binding into `px.receipt.`, observe=False still writes nothing, and the testimony, the results and the `pyto-run-record@1` document are unchanged either way (`pcr.py`, `core.RECEIPT_PREFIX`, `materialize.run_record` preexisting fallback; pinned by `tests/test_receipts.py::ReceiptsAreParts` and `::ReceiptSegmentIsNotBindable`).

## Semantic flips

None. Every seam so far is additive: no existing field, default, exception, order
or serialized shape changed. A seam that changes what an existing program means
is recorded here first, with the consumer call sites it moves.

## exp/29: no library seam -- `experiments/students` now runs four Ticks, with `Stats` holding `mean` and `median` as parallel branches (both bind Parse's roster, neither reads the other); the hand-off replaces its false reason with the honest one (a receipt is per Calculation, so one Tick or two records the same reads; a Tick is a step), `evidence/run-1` is regenerated by `python homework.py --out evidence/run-1`, and `tick_laws.py` reports Stats as the one Tick whose work exceeds its latency; `git diff -- pyto/src` is empty.

## exp/26: no library seam — added `experiments/tick-laws`, a record-only checker for observed Tick node/loop laws and Tick-model work versus critical-path reporting; `pyto/src` is unchanged.

## Day 2 (base d9dded6): `PcrRun.receipts`, opt-in through `PCR.run(..., observe=True)`

**What landed.** `pyto/src/pyto/pcr.py` only:

- `FrozenCalculation(address, implementation_sha256, identity_scope, limitation)`
  — `implementation_sha256` is `sha256(inspect.getsource(callable))` when the
  runtime can show the source and `None` otherwise (a C builtin). The two honesty
  fields carry the transferred wording verbatim: `identity_scope
  = 'runtime-function-body'`, `limitation = 'called helpers, constants, templates,
  and assets are not covered'`.
- `Receipt(invocation_id, calculation, started_ms, duration_ms, declared_consumes,
  declared_produces, actual_consumes, actual_produces, writes, result_sha256,
  effective_arg_keys, shadowed_inputs)` — frozen; `writes` is a tuple of the
  existing `core.PxWrite` with kinds `new-address | refinement | replacement`.
- `_TrackedPxC`, a recording view of the PxC for the span of one invocation.
- `PcrRun.receipts: dict[str, Receipt] = field(default_factory=dict)`, trailing.
- `PCR.run(pxc, *, observe: bool = False)`; the observation branch runs only when
  `observe=True`.

**Transfer, not invention** (research/lab-transfer-ledger.md:35-41). `Receipt` is
the LAB Tick receipt: `reference/lab/chesslab-lab/contract.ts:127-141` (Receipt),
`contract.ts:60-68` (FrozenCalculation, including `identityScope`/`limitation`),
`contract.ts:71-74` (PxWriteTestimony kinds), `reference/lab/chesslab-lab/host.ts:33-36`
(how a receipt is assembled from tracked access). Timing and per-invocation
identity follow `reference/lab/wumpus-core/execute.js:10-47` (`executeTick`:
`startedAt`, `durationMs`, `actualConsumes`/`actualProduces` from the transaction).
`_TrackedPxC` is `/home/user/DiscStudio-staging/src/core/exec.js:22-33`
(`trackAccess`), including its write-kind rule at exec.js:28 — `new-address` when
the address did not exist, `refinement` when it existed and was declared as an
input of this invocation, `replacement` otherwise. No JS file was edited.

**Testimony bytes are unchanged.** `json.dumps([asdict(t) for t in run.ticks])` —
the expression consumers embed in `compositionEvidence` at
`consumers/discstudio-card/card_composition.py:177` and
`consumers/discstudio-card/app.py:53` — is byte-identical with `observe` on, with
`observe` off, and against the Day 1 bytes retained at
`experiments/grouped-ablation/evidence/run-1/testimony.json`.
`CalculationTestimony` and `TickTestimony` are untouched; `receipts` is a trailing
field on `PcrRun`, which no consumer serializes. The oracle is executable:
`tests/test_receipts.py::TestimonyBytesUnchanged::test_observe_on_and_off_produce_identical_tick_bytes`
and `::test_tick_bytes_equal_the_retained_day_1_testimony`. Checked once more from
outside the library, in scratch: `card_composition.execute_card` was run against a
copy of `pyto` at d9dded6 and against this tree, and
`json.dumps(evidence["composition"]["ticks"])` compared byte for byte -- equal. The
in-repo executable form of that check is the two tests above plus the consumer suite,
which exercises the same call site.

**One consumer-served byte does move, by design.** The hard rule is scoped to the
tick payload, and the tick payload is unchanged; but the seam is `pcr.py`, and
`consumers/discstudio-card/app.py:33-36` computes `PYTO_SOURCE_SHA256` as the
sha256 of the source *files* of `pyto.core` and `pyto.pcr`, then embeds it in the
same `compositionEvidence` object at `app.py:52` that `app.py:170` serves to
clients. `PYTO_SOURCE_SHA256["pyto.pcr"]` therefore moves across this seam --
recompute both sides rather than trusting a literal:
`git show d9dded6:pyto/src/pyto/pcr.py | sha256sum` versus
`sha256sum pyto/src/pyto/pcr.py` (at the time of writing, `6280fe80...` ->
`64cd374a...`), and with it the sha256 of the whole `compositionEvidence` object
on the art path. That field exists to stamp the library version, so a moved value
is the field working, not a break -- but an owner auditing "the consumer-bytes
statement" against a live sandbox response would otherwise find a changed byte this
ledger did not name (fixer round 1, finding 8). `PYTO_SOURCE_SHA256["pyto.core"]`
does not move (`core.py` is untouched), the tick payload at `app.py:53` and
`card_composition.py:177` does not move, and `card_composition`'s own evidence does
not move end to end: `card_composition.py:174` hashes the source file of
`Calculation`, i.e. `pyto/core.py`, not `pcr.py`.

**Before.** At d9dded6, `PCR.run(pxc, observe=True)` raised
`TypeError: PCR.run() got an unexpected keyword argument 'observe'`, `PcrRun` had
no `receipts` attribute, and `from pyto.pcr import FrozenCalculation, Receipt`
raised `ImportError: cannot import name 'FrozenCalculation' from 'pyto.pcr'`
(the first run of the new suite, written before the field). The library suite was
43 tests: `tests/test_semantics.py` 31, `tests/test_first_class.py` 9,
`tests/test_graph.py` 3.

- `tests/test_semantics.py::PCRRunRulesTest::test_results_keyed_by_id_not_tick_and_rerun_replaces`
  asserted `dataclasses.fields(PcrRun) == ("pcr", "ticks", "results")`. This is the
  one Day 1 test the seam moved; it now asserts `fields[:3] == ("pcr", "ticks",
  "results")` (order and prefix unchanged), that the only addition is the trailing
  `receipts`, and that `run.receipts == {}` when `observe` is not passed. No other
  Day 1 assertion changed.

**After.** The library suite is the 43 Day 1 tests plus `tests/test_receipts.py`,
whose classes and test names are listed below (the count of the day is read off
`scripts/check_all.sh`'s table, not from this file -- see the note after the table):

| class | tests |
| --- | --- |
| `TestimonyBytesUnchanged` | `test_observe_on_and_off_produce_identical_tick_bytes`, `test_tick_bytes_equal_the_retained_day_1_testimony`, `test_experiment_path_is_inside_this_repository` |
| `ReceiptsAreOptional` | `test_receipts_empty_when_observe_is_false`, `test_receipts_keyed_by_invocation_id_when_observe_is_true`, `test_day_1_program_gets_one_receipt_per_invocation` |
| `FrozenCalculationIdentity` | `test_implementation_sha256_is_the_source_digest_and_is_stable`, `test_implementation_sha256_is_none_for_a_builtin`, `test_identity_scope_and_limitation_are_the_chesslab_honesty_fields` |
| `ResultDigest` | `test_json_value_digest_is_canonical_json`, `test_non_json_value_yields_none`, `test_tuple_keys_yield_none` |
| `WriteKinds` | `test_kinds`, `test_declared_and_actual_addresses`, `test_an_invocation_without_into_produces_nothing`, `test_a_result_ref_input_is_not_a_declared_consume` |
| `ShadowedInputs` | `test_args_key_colliding_with_a_bound_input_is_recorded_not_raised`, `test_no_collision_leaves_shadowed_inputs_empty` |
| `Timing` | `test_duration_is_non_negative_and_started_is_monotonic` |
| `ReceiptShape` | `test_receipt_is_frozen_and_json_serializable_after_asdict`, `test_registry_calculations_are_named_functions_not_lambdas` |

No other suite's *assertions* were changed by the seam, and all pass.

**Per-suite counts are not carried here as prose.** They grow with the day's own
experiment work and with concurrent lanes, and a literal in this file goes stale
without anything failing -- which is exactly what happened (fixer round 2, finding
9: this paragraph said "consumer 37" while the suite discovered 61). The authority is
the `== per-suite counts` table `scripts/check_all.sh` prints at the end of the run
whose exit code this entry quotes, retained verbatim as the day's run record at
`experiments/runs/day2/tests.txt` (experiments/CAPTURE.md, "How a day closes":
`tests.txt` must end with `ALL SUITES PASSED`). `scripts/check_all.sh` also pins the
two suites whose size is a kill criterion -- `EXPECT_CONSUMER` and
`EXPECT_DISC_STATS` at `scripts/check_all.sh:21-22` -- so a suite that silently
shrinks fails the gate rather than this file.

What is stable enough to state is *which* tests the seam added, and that is the table
above: no Day 1 assertion changed except the one named under **Before**.

**No digest through `default=`** (research/ULTRACODE-WEEK.md critic gap 10).
`result_sha256` is `sha256(json.dumps(value, sort_keys=True, separators=(',', ':')))`
with no fallback serializer; `TypeError`/`ValueError` yields `None`. A value that
is not JSON therefore has no digest instead of a digest of its `repr`, which for
objects whose repr carries an address would be process-dependent and would show up
later as pyto-caused drift. Covered for a `set` and a `PxC` by
`ResultDigest::test_non_json_value_yields_none`, which is the mutation-sensitive
guard on the no-`default=` decision.

The dict-with-tuple-keys case — the disc-stats result shape,
`consumers/discstudio-card/experiments/disc-stats/stats.py:34`
(`distinct_discs_by_mold -> dict[tuple[str, str], int]`) — is covered by
`ResultDigest::test_tuple_keys_yield_none`, but that test is a **characterization of
json's key rule**, not evidence about `default=`: the encoder rejects keys that are
not `str|int|float|bool|None` before any `default=` hook is reached, so the test
passes with and without the fallback serializer. It pins that this shape yields
`None` here; the mutant that does kill it is a seam that stringifies keys before
dumping (see "Mutation check" below). Naming it as gap-10 `default=` evidence was an
overstatement (fixer round 2, finding 8).

**What this seam is not** (research/ULTRACODE-WEEK.md critic gap 14, and
`docs/PYTHON-LAB-STEWARDSHIP.md:62`, quoted in the gap as `stewardship:53`: "No
Pyto implementation starts until the consumer fixture establishes the calculation
boundaries and the owner confirms which presentation/config values are external
inputs versus calculation results").

- It records digests and durations of what `PCR.run` already did. It classifies no
  value as an external input versus a calculation result, so it makes no part of
  the `{?} ExternalInputBoundary` decision the precondition reserves for the owner.
- It is **not the replay seam**. Nothing here retains a program, resolves a
  calculation address, or rebuilds anything: retention and replay stay
  experiment-local (`experiments/grouped-ablation/`), per
  `docs/PYTHON-LAB-STEWARDSHIP.md:39` — retained data must not pickle lambdas or
  claim to contain executable Python code. A `Receipt` holds strings, floats and
  digests only; `test_receipt_is_frozen_and_json_serializable_after_asdict` asserts
  the serialized form contains no `lambda` and no `<function`.
- It is an observation of what `PCR.run` did on each invocation's behalf, not of
  the callable. `PCR.run` resolves bindings and calls the Calculation with a plain
  args mapping, so a body that closed over a PxC and touched it directly is
  invisible to `actual_consumes`/`actual_produces`/`writes`. The `Receipt`
  docstring says so at the point of use.
- `started_ms` and `duration_ms` come from `time.perf_counter()`: monotonic, with
  an arbitrary origin. `started_ms` orders invocations within one process; it is
  not a wall-clock time and must not be retained as one.
- Deferred, recorded as open rather than silently omitted
  (research/ULTRACODE-WEEK.md critic gap 19, `{?} Telemetry`): sequence-ordered
  read/write receipts across a whole run, and a failed-run `PcrRun` instead of a
  raise. A failing invocation still raises and returns no `PcrRun`, so it produces
  no receipts either. `{?} ShadowRule` also stays open
  (research/lab-transfer-ledger.md:65-67): an `args` key that collides with a bound
  input still overrides silently; the receipt now *records* the collision in
  `shadowed_inputs`, and `pcr.py` still does not raise.

**Fixer round 1 decisions that belong in this ledger** (the rest are
experiment-local and cited in `experiments/grouped-ablation/`).

- *Provider identity is carried, and comparing it is the caller's job.*
  `docs/PYTHON-LAB-STEWARDSHIP.md:36-37` asks a record to carry "the Pyto
  distribution version and calculation-provider identity needed to reject an
  incompatible replay". `retain.provider_identity` carries it; `retain.replay`
  deliberately does **not** compare it, because the LF-source-drift probe replays
  under a deliberately different library copy and must not be refused. The
  comparison now exists as `retain.verify_provider(record, registry)` -- reporting
  only, it raises nothing -- and the fresh-process replay child asserts on it and
  prints the accept/mismatch line into
  `experiments/grouped-ablation/evidence/replay/fresh-process.log`. The docstring
  that used to claim replay already compared has been corrected. No library change
  was needed for any of this: `retain.py` is experiment-local.
- *A predicted number was refuted by measurement and is recorded, not quietly
  dropped.* `research/ULTRACODE-WEEK.md` Day 2 predicts "no single drop exceeds
  +0.9 RMSE because each group holds at most two planted weights". The
  cross-cutting regroup measures a largest |delta vs baseline| of 1.5415 against
  run-1's 1.5896, so the bound is refuted while the *comparison* between the two
  groupings (the regroup does not concentrate more planted weight into one group:
  largest planted |w| per group is 2.0 in both) holds. Both numbers, and the
  per-group planted weights they rest on, are computed at run time by
  `run_regrouped.py` and written into
  `experiments/grouped-ablation/evidence/run-2-regroup/interpretation.md`; the
  values quoted here are that file's, not literals the ledger maintains.

**Fixer round 2 decisions that belong in this ledger** (the rest are
experiment-local and cited in `experiments/grouped-ablation/`). **No library change
was made in this round**: the day's one seam is the `pcr.py` change above, and
`src/pyto/` is untouched by everything below.

- *Regeneration order: run-1 first, then runs 2-4.* Lane C's `ms_saved` /
  `ms_saved_by_invocation` are durations read out of `evidence/run-1/receipts.json`
  (`second_experiment.py:230-248`), so regenerating run-1 alone leaves all three
  dependent ledgers quoting a duration that appears in no retained file -- which had
  happened, and nothing failed, because the suite only ever compared runs it
  regenerated itself into temp dirs. Runs 2-4 have been regenerated after the
  committed run-1, and
  `test_second_experiment.py::CommittedEvidenceResolvesToCommittedRunOne` now reads
  the **committed** evidence and fails if the two drift apart, naming the command to
  re-run (fixer round 2, findings 7 and 12).
- *`child failed checks: []` is not a verdict.*
  `replay.run_fresh_process_replay` now ends its log with one terminal `VERDICT:`
  line folding the child's own four checks together with the four the parent makes
  (module sources, leaked modules, comparison rows, result digests), and the tests
  assert on that line. Two forgeries reach the child cleanly and are refused only in
  the parent: a value-forged record with recomputed digests, and a registry-forged
  record whose provider block is byte-identical to the honest one. Each of the five
  refusals now has a test that trips exactly it; the mutation matrix over them kills
  1 of 58 per mutant with a clean baseline (fixer round 2, findings 2, 3 and 4).
- *`retain.provider_identity` is module-granular, and now says so.* It digests the
  *module source file* of a Calculation's callable, so an address pointing at a
  different function of the same module carries an identical provider block. The
  limitation is stated in its docstring the way
  `pyto.pcr.FrozenCalculation.limitation` states its own; a per-function digest
  (`implementation_sha256`, `pcr.py:152-160`) would close it and is recorded as open
  in `experiments/grouped-ablation/evidence/OPEN-FINDINGS.md`, because it changes the
  provider shape in every retained record.
- *The aliasing hole is closed on both sides.* `retain.replay` already deep-copied
  externals; `retain.from_program` now deep-copies `args` too (`retain.py:297`),
  because `PCR.calc` keeps only a shallow `dict(args or {})` (`pcr.py:56`) and a
  Calculation mutating a nested arg in place therefore rewrote the caller's retained
  record in memory. Pinned by
  `test_replay.py::ReplayDoesNotMutateTheRecord::test_a_calculation_that_mutates_its_args_in_place_leaves_the_record_alone`
  (fixer round 2, finding 5).
- *The tamper report's independence flag can now be False.* It compared the caller's
  `record` against itself; it now compares the copy actually handed to the baseline
  replay, before and after (fixer round 2, finding 4).
- *The cross-verification gate covers lane C.* `replay.cross_verify_lane_c_runs()`
  replays run-2/3/4's retained records in fresh processes against their own committed
  `comparison.json`, `testimony.json` and `retained.json["results"]`, leaving
  `evidence/replay/fresh-process-run-*.log` (fixer round 2, finding 13).

**Not exported from `pyto/__init__.py`.** `Receipt`, `FrozenCalculation` and
`_TrackedPxC` are importable as `from pyto.pcr import ...` only — the same status
`Invocation` already has. The day's one library change is the seam in `pcr.py`; the
public surface moves when a consumer needs it, not before.

**Mutation check** (scratch only: `src/pyto` is copied out, mutated there, and put
on `PYTHONPATH`; the repo is never written). Re-run whenever this paragraph is
edited -- the counts below are what the runs printed, not what the change was
expected to do.

- Adding `default=str` to the result digest fails
  `ResultDigest::test_non_json_value_yields_none` and **not**
  `::test_tuple_keys_yield_none` -- **1 of 2**. An earlier version of this paragraph
  claimed 2 of 2 (fixer round 2, finding 8). The survivor is structural, not luck:
  json's `default=` hook is consulted only for a non-serializable *value*, and a dict
  with tuple *keys* raises `TypeError: keys must be str, int, float, bool or None`
  inside the encoder before any hook runs.
- The mutant that does kill `::test_tuple_keys_yield_none` is stringifying keys
  first: `json.dumps({str(k): v for k, v in value.items()} if isinstance(value, dict)
  else value, ...)` -- **1 of 1**, and it leaves `::test_non_json_value_yields_none`
  passing. The two tests guard two different decisions; neither mutant reaches both.
- Collapsing `refinement` into `replacement` fails `WriteKinds::test_kinds` (1 of 1).
- Dropping `shadowed_inputs` fails
  `ShadowedInputs::test_args_key_colliding_with_a_bound_input_is_recorded_not_raised`
  (1 of 1).

**Fixer round 3 decisions that belong in this ledger** (the rest are
experiment-local and cited in `experiments/grouped-ablation/`). **No library change
was made in this round either**: `src/pyto/` is untouched by everything below, and
`json.dumps([asdict(t) for t in run.ticks])` is unchanged because `pcr.py` is
unchanged -- now also asserted through the replay path
(`test_replay.py::ReplayObserveSeam::test_testimony_bytes_are_identical_with_observe_on_and_off`).

- *Verification never rewrites committed evidence.* Running the suite used to
  rewrite thirteen tracked files under `evidence/`, because
  `replay.ensure_retained_record` wrote `evidence/run-1/retained.json` and every
  check logged into `evidence/replay/`, `evidence/tamper/` and so on. Every writer
  in `replay.py` now takes the path it writes to and defaults to a fresh temp
  directory; `ensure_retained_record` rebuilds into a temp dir and compares against
  the committed record as an **oracle**, returning the committed bytes. The
  committed tree is written only by the run scripts and by `python3
  experiments/grouped-ablation/replay.py --force`, which refuses a non-empty
  destination without `--force` the way `run.py` always has (`replay.OWNED_EVIDENCE`).
  The refusal logs and the two `evidence/tamper/mutating-baseline-*` files, which
  used to exist only because a test wrote them, are now produced by `replay.main`
  (`replay.run_refusal`, `replay.run_forged_record_refusal`).
  `test_replay.py::CheckAllLeavesTheTreeClean` runs the two evidence-writing suites
  in a child interpreter and asserts `git status --porcelain` for `evidence/` is
  unchanged (round 3, finding 1).
- *The replay child observes.* The fresh-process child now calls
  `retain.replay(record, REGISTRY, observe=True)` and reports
  `Receipt.result_sha256` per invocation. The parent asserts three files agree --
  the child's receipt digests, `record["results"]`, and the committed
  `receipts.json` `result_sha256` -- and logs both comparisons; either inequality is
  its own `VERDICT: refused` reason (round 3, finding 2).
- *The module-leak check reads the whole table.* It used to subtract the child's
  `sys.modules` *before* its first import, so anything a site hook had already
  pulled in was invisible. It is now computed over the child's full `sys.modules`
  minus an explicitly enumerated startup-resident set
  (`replay._STARTUP_RESIDENT_MODULES = {__main__, _distutils_hack, sitecustomize}`)
  plus the stdlib and the four modules the replay may reach; and `pyto`,
  `calculations`, `features` and `retain` are asserted **absent** from
  `sys_modules_before` (round 3, finding 3).
- *`input_parts_changed` is computed, not declared.* Each Day 2 script used to hand
  `second_experiment.saved_work` a literal list naming what its author believed the
  run had changed, so the field agreed with the script's intent by construction. It
  is now derived from the two records' external digests
  (`second_experiment.input_parts_changed`), and `saved_work` no longer accepts the
  keyword at all. run-4 consequently reports both halves of its boundary move
  (`input.ablation.rows` dropped, `scratch.ablation.split` added) where the literal
  named only the addition -- recorded as `{?} InputPartsChangedScope` in
  `pyto/questions.md` (round 3, finding 4).
- *`receipts.json` is deterministic apart from two fields.* `Determinism` only
  asserted that the file's TEXT differs across two regenerations, which one changed
  millisecond satisfies. `test_second_experiment.py::ReceiptsDeterminism` parses
  both, drops `started_ms` and `duration_ms` per receipt, requires the remainder
  equal, and requires at least one timing to differ so the equality is not
  trivially met by a frozen clock (round 3, finding 5).
- *`retained.json` and `receipts.json` are one measurement at two moments.*
  `retain.retain_run`'s docstring now says why: `pcr.py:334-336` publishes the value
  a Calculation returned into `run.results[id]` as the very same object,
  `pyto.pcr._result_sha256` digests it as the invocation returns and
  `retain.digest_of` digests that alias after the run, both over the same canonical
  JSON with no `default=`. An inequality means the object was mutated in between.
  `test_second_experiment.py::RetainedDigestsEqualReceiptDigests` asserts the
  equality per id for all four committed runs (round 3, finding 6).
- *Outputs are not code, for the `-dirty` stamp.* `run.evidence_excludes` excludes
  the whole `evidence/` tree from the dirt judgement in `run.py`,
  `second_experiment.py` and `replay.py`, where each previously excluded only the
  one directory it was writing -- so regenerating run-2 after run-1 saw run-1's
  fresh output as dirt. Uncommitted edits to producing code still stamp `-dirty`.
  Recorded as `{?} EvidenceDirtiness` in `pyto/questions.md`; the "Close it by"
  block in `evidence/OPEN-FINDINGS.md` is rewritten to match and now lists
  exhaustively which fields of which files a regeneration may change (round 3,
  finding 7).


## Day 3 (base 83422cf): `pyto/src/pyto/materialize.py`, a Tick materializer

**What landed.** One new module, `pyto/src/pyto/materialize.py`. No existing library
file changed: `pcr.py`, `core.py`, `pql.py`, `graph.py` and `neon.py` are byte-identical
to their state at 83422cf, and `pyto/__init__.py` is untouched, so the module is reached
as `from pyto.materialize import run_record` (the same status `pyto.pcr.Receipt` has).

- `run_record(run, pxc, *, preexisting=None, pcr_name=None, source=None,
  value_cap_bytes=262144, array_cap=200) -> dict` — the `pyto-run-record@1` document of
  pyto/viewer/RECORD.md: ticks joined to receipts by invocation id (grouping and order
  from `PcrRun.ticks`, `index` from position), Calculation identity from the receipt's
  `FrozenCalculation`, `hit` from the `px:` bindings, values from `PcrRun.results`, plus
  the derived `parts` map and `counters`. It requires `observe=True` and raises
  `ValueError` on a receipt-less run (see fixer round 2 below: the null-filled document it
  used to emit instead was one no reader of the shared schema would take).
- `render_value(value, *, value_cap_bytes, array_cap) -> {kind, data, note}` — the value
  dispatch: `png-data-url` (a PIL image through an in-memory PNG), `svg` (a string
  opening an SVG document, carried verbatim), `text`, `json` (arrays over the cap cut to
  their first `array_cap` entries with a note), `omitted` (with a note carrying the size
  and digest, or why the value is not serializable).
- `write_record(record, path)` — sorted keys, two-space indent, LF, trailing newline
  (RECORD.md:67).
- `tick_sheets(record, out_dir, *, cols=2)` — one neon PNG per Tick through
  `neon.panel`/`neon.sheet`: a text panel per invocation carrying the annotation anchor
  `(pcr, tick, invocation id, part address)`, the reads, the writes, the duration, the
  hit and the first lines of the value, plus an image panel for image values.

**What it is a transfer of.** Nothing in another runtime: this is the gap
`research/tick-observability-ledger.md:60-85` records as absent in *both* directions
("no function in `pyto/src/pyto/` consumes a `PcrRun`", "no Tick↔receipt join", "no value
in any serialized form"). The *output* is a transfer: the document is the shared record
format `pyto/viewer/RECORD.md`, which the JS runtime's adapters also emit, and the JS
runtime is the reference where the two could differ (ULTRACODE-WEEK.md, Reframing 4).
The panel vocabulary is `pyto/src/pyto/neon.py:161-190` unchanged.

**Testimony bytes are unchanged, and this is why the module could be additive.**
`run_record` only reads a `PcrRun`; it never constructs, mutates or re-serializes one.
`tests/test_materialize.py::TestimonyBytesUnchangedByMaterializing` is the oracle:
`json.dumps([asdict(t) for t in run.ticks])` before materializing equals the same
expression after `run_record` + `write_record` + `tick_sheets`. The Day 2 statement
therefore still holds unqualified — the bytes consumers embed in compositionEvidence
(consumers/discstudio-card/card_composition.py:177, app.py:53) never see this seam.

**Value blindness is where the record deliberately parts from the receipt.**
`Receipt.result_sha256` is one-way by construction (pcr.py:125) and `retained.json`
keeps `{invocation id: sha256|None}` (experiments/grouped-ablation/retain.py:28), so no
serialized artifact carried the values `PCR.run` was holding
(tick-observability-ledger.md:107-118). The record carries them, under two caps taken
from RECORD.md:63-64 rather than invented here: 256 KB per value and 200 array entries.
Over either cap the record says so in `note` with the size and the digest; it never
silently truncates.

**What this module does not decide.**

- *Not a cache and not a replay seam.* It reads a completed run. Reuse decisions,
  content addressing and the materials store are still `{?}` and still experiment-local.
- *Not a `hit` definition of its own.* It implements the JS reference rule verbatim
  (`viewer/adapters.js:244-249 deriveHit`, RECORD.md:55-56): a `px:` binding whose address
  was not produced by an earlier invocation of the same run. Reading `fn:<id>` is never a
  hit, which is why all twelve Day 1 fit/score invocations are `computed`, not hits — the
  declaration-order rewrite (pcr.py:112-116) is what makes them share one `split`.
  (`preexisting` was also ORed in until fixer round 2 below; it decides
  `parts[...].preexisting` and nothing else.)
- *Not a Part kind system.* `Part` still carries an address and nothing else
  (core.py:11-22, ledger gap 4); the dispatch is on the runtime type of the *value*, not
  on any new Part metadata, so no library type grew a field.
- *Not an SVG rasterizer.* `tick_sheets` writes an SVG value verbatim beside the sheet
  and draws a placeholder panel naming the file. Rasterizing needs a renderer pyto does
  not depend on; the harness or a browser does it.
- *Not a Tick identity.* `index` is the position in `PcrRun.ticks`, honestly derived, not
  a stable id assigned by the runtime (ledger gap 5 stays open).

**Pillow stays optional.** Importing `pyto.materialize` does not import PIL (`pyto.neon`
imports it at module level, so the import is deferred into the drawing functions). Without
Pillow the record is still produced, with any image value `omitted` and the note saying
why; `tick_sheets` raises `RuntimeError` naming the missing dependency rather than
writing half a sheet.

**Before.** At 83422cf, `import pyto.materialize` raised
`ModuleNotFoundError: No module named 'pyto.materialize'`, and no function anywhere in
`pyto/src/pyto/` took a `PcrRun` (the ledger's first missing item).

**After.** The library suite is Day 2's 64 tests plus `tests/test_materialize.py` (29):
93, all passing under `scripts/check_all.sh`, which pins no library count and needed no
edit. One test *helper* changed outside this file's scope and it is recorded here rather
than buried: `experiments/grouped-ablation/test_grouped_ablation.py::_snapshot` walked a
directory with a flat `os.listdir` and raised `IsADirectoryError` once
`evidence/run-1/ticks/` existed. It now recurses (`os.walk`), which keeps its assertion —
`run.py` leaves the tracked run-1 untouched — and extends it over the sheets. No
assertion, count or expectation of any existing test changed.

**Mutation check** (scratch only: `src/pyto` is copied out, mutated there, and put on
`PYTHONPATH`; the repository is never written). Counts are what the runs printed.

- Dropping the `fn:<id>` → writer's `into` edge from the `parts` map fails
  `DayOneRecord::test_parts_map_lists_the_twelve_fn_readers_of_the_split_part` and
  `HitLedger::test_an_address_produced_earlier_in_the_run_is_not_a_hit` — **2**. That edge
  is what makes `scratch.ablation.split` show its twelve readers (RECORD.md:44) even
  though every one of them binds it as `fn:split`.
- Reducing `hit` to `address in preexisting` (dropping "not produced earlier in this
  run") fails
  `HitLedger::test_a_part_no_invocation_produced_is_a_hit_even_with_an_empty_preexisting_set`
  — **1**. Without that test the clause was invisible, because a caller passing the true
  pre-run store gets the same answer either way. (The converse mutation — ORing
  `preexisting` back in, which is what the module actually shipped — is now caught by
  `HitLedger::test_re_reading_a_part_this_run_overwrote_is_not_a_hit_as_in_javascript`.)
- Removing the `str` branch, so a string falls through to `json`, fails four tests
  (`text`, `svg`, the XML prologue, and the SVG written beside the sheet) — **4**.
- Raising the array cap check from `> cap` to `> cap + 1000` fails **2** (the 1000-element
  list and the `array_cap` parameter).
- Digesting an omitted value through plain `repr` instead of the canonical repr fails
  **2**, one of them
  `ValueKinds::test_the_omitted_digest_is_the_same_in_a_process_with_a_different_hash_seed`,
  which runs three child processes under different `PYTHONHASHSEED` values. `repr(set)`
  order is salted per process, so the plain-`repr` digest would report two identical sets
  as different material — the process-dependent digest ULTRACODE-WEEK.md critic gap 10
  refuses.

### Day 3 round trip: the record is checked from both sides

Verification of the Day 3 seam, and the one place the two runtimes could have quietly
disagreed. `RECORD.md` is a contract between a Python producer and a JavaScript one, and
until now each side was checked only by itself: `pyto/tests/test_materialize.py` asserted
what Python wrote, `viewer/test/adapters.test.mjs` asserted what JavaScript wrote, and
the viewer's `pyto` fixture was hand-transcribed from `receipts.json` rather than being a
record either runtime had produced. Two producers and no shared reader is not a contract.

**The fixture is now the file, not a copy of the story it tells.**
`viewer/fixtures/pyto-grouped-ablation.json` is
`experiments/grouped-ablation/evidence/run-1/record.json` byte for byte, and
`adapters.test.mjs` compares the two files, so it cannot drift — the same property the
DiscStudio fixture already had by re-running `src/runtime.js`. The hand-written document
survives as `viewer/fixtures/pyto-value-kinds.json`, renamed, re-`pcr`'d
(`ablation.grouped.value-kinds`) and labelled synthetic in `viewer/README.md`: it is the
only thing that carries `svg`, `png-data-url`, `text` and `omitted` values, because
grouped-ablation run-1 materializes JSON and nothing else, and inventing four value kinds
into a record of a real run would have been the lie the fixture swap was meant to end.

The real record loads through `fromPytoRecord` unchanged, and renders: 4 Tick sections, 15
invocation rows, 0 script nodes. The render, filter, header, part-index and counter
assertions of `render.test.mjs` were re-pinned to run-1's actual numbers (15 / 2 / 13 over
4 Ticks) rather than the fixture's invented 11 / 2 / 9 over 6.

**The other direction now exists.** `viewer/test/record_schema.py` is a Python validator
of `pyto-run-record@1` transcribed from RECORD.md clause by clause, sharing no code with
`adapters.js` and importing nothing from `pyto`. `viewer/test/emit_adapter_records.mjs`
writes out every JavaScript adapter's output — pyto pass-through, both DiscStudio runs,
ChessLab, Wumpus — and `viewer/test/test_record_schema.py` (19 tests, the new
`viewer-record-schema` suite) reads them all back through it. Its key sets are **exact**
in both directions: RECORD.md:65 says missing fields are null and never invented, which
reads both ways, so a field an adapter drops and a field an adapter adds both fail.

All six adapter outputs pass. `parts` is re-derived a third time, in Python, from the
invocations alone and agrees with what JavaScript wrote for all six; counters recompute
from the Ticks for all six.

**Two differences found, and pinned rather than smoothed over.**

- `adapters.js` `validate` reads the fields it needs and accepts an unknown one: a record
  carrying `counters.misses` passes in JavaScript and fails in Python
  (`TheTwoValidatorsAgree::test_python_is_the_stricter_reader_only_where_RECORD_md_says_so`).
  So an invented field is caught by the round trip and by nothing else, which is the
  argument for the round trip. Not repaired in `adapters.js`: strictness there would
  reject a future record written to a later schema by a runtime that has not been updated,
  and RECORD.md gives no rule for that yet.
- A record re-serialized by JavaScript is equal to Python's file as parsed JSON but not as
  bytes. JSON has one number type, so an integral float inside a value payload is `0.0`
  from Python and `0` from JavaScript — one line of run-1's record
  (`delta_vs_baseline`). RECORD.md:67 fixes sorted keys and two-space indentation, not the
  spelling of a number, so neither side is wrong; the consequence is that nothing may key
  a digest on the record *file*, and
  `AdapterOutputs::test_the_round_trip_is_equal_as_JSON_and_not_promised_as_bytes` says so
  where it would otherwise be discovered by a broken digest.

**One asymmetry left standing on purpose.** `compare` binds `fn:score.*` and its
`actual_consumes` is empty, because a `fn:` result is served from the result cache and
never touches the store. The `parts` index resolves the `fn:` ref and lists `compare` as a
reader of `scratch.ablation.score.drop_g3`; the viewer's text filter, which matches what
the invocation *spells*, does not find `compare` under that address. Both readings are
correct and they differ; `render.test.mjs` now asserts both side by side rather than
letting a reader assume the filter and the index answer the same question.

**Counts.** `viewer` 73 → 77 (the byte-identity check, the four-Ticks-fifteen-rows render check, the value-kinds coverage check, and
the four value-kind schema cases moved onto the synthetic record); new suite
`viewer-record-schema` 19. `scripts/check_all.sh` pins both (`EXPECT_VIEWER`,
`EXPECT_RECORD_SCHEMA`). No Python library file changed; `materialize.py`, `pcr.py`,
`core.py`, `pql.py` and `graph.py` are untouched by this entry.

### Day 3 fixer round 1: record data is hostile until the reader says otherwise

Four defects found by review, all in the seam where *record data* becomes *reader
behaviour*. Nothing in `pcr.py`, `core.py`, `pql.py` or `graph.py` moved; the only library
file touched is `materialize.py`, and consumer testimony bytes are unchanged.

**A Part address is a string a record chose, so it can be `__proto__`.**
`derivePartIndex` built its index on a bare `{}` (`viewer/adapters.js:297-317`). For the
address `__proto__`, `parts[address] ??= {...}` reads `Object.prototype`, never assigns,
and hands it back as the row: `part.preexisting = true` then wrote onto the page's own
prototype chain — after which every fresh `{}` in the document reported
`preexisting: true` — and `part.read_by.includes(...)` threw a bare `TypeError` rather
than the `RecordSchemaError` the module promises. Reachable from every non-pyto adapter,
since all three go through `assemble` → `derivePartIndex`. The index is now built on
`Object.create(null)` with `hasOwnProperty` deciding existence
(`viewer/adapters.js:303-316`), and handed back with a spread, which copies by
`CreateDataProperty` and so yields the same own-property shape `JSON.parse` gives a
consumer reading the index off disk. `fromDiscStudioReceipt`'s `inputs` map got the same
treatment (`viewer/adapters.js:467,490`): a *binding name* of `__proto__` used to set the
prototype and drop the binding entirely.

**`png-data-url` named a kind but never checked the shape.** RECORD.md:60-61 says the data
*is* a `data:image/png;base64,...` string; `validateValue` only required a string, and
`tick-viewer.js` put it straight into an `<img src>`. A record could therefore make the
no-network viewer issue an arbitrary outbound request. Three places now agree on
`PNG_DATA_URL_PREFIX`: `viewer/adapters.js:26,124-130` rejects anything else with the
offending path; `viewer/adapters.js:264` classifies on the raw string rather than a
trimmed head, so `materialize` can never emit a block `validate` would refuse; and
`viewer/tick-viewer.js:116-131` re-checks at the render site and falls back to an
omitted-style note. The Python reader learned the same clause
(`viewer/test/record_schema.py:34,158-167`), and the case is in `TheTwoValidatorsAgree`
so the two runtimes cannot drift apart on it.

**A hit was claimed for a value that failed to load.**
`experiments/grouped-ablation/materials.py` incremented `hits` *before* `load_value()`,
so a truncated `<key>.json` recorded a hit and then raised: a caller that caught the
exception and recomputed was left with a ledger overstating reuse, in which
`hits + misses` no longer accounted for `requests`. The hit is now counted only after a
successful load, and a load failure degrades to the miss path
(`experiments/grouped-ablation/materials.py:227-241`) — the same honesty rule the module
already stated for a sidecar-only key. The sentinel is a private class, not `None`,
because `null` is a legal cached value.

**The two runtimes disagreed on a string that is already an image.**
`render_value` sent every `str` to `svg` or `text`, so a PNG data URL was `text` in Python
and `png-data-url` in JavaScript (`adapters.js:262-264`, pinned by
`adapters.test.mjs`): the same Part would show as a picture from a DiscStudio record and
as a wall of base64 from a pyto one. Resolved against the Python side, as "JS is first
class" requires: `src/pyto/materialize.py:49,156-172` now tests the raw string for the
PNG prefix between the svg and text branches, in JavaScript's order.

**Counts.** `viewer` 77 → 81 (hostile Part address, `validate` refusing a non-PNG
`png-data-url`, `materialize` never emitting one, and the render-site fallback);
`experiments/grouped-ablation` 228 → 230 (a corrupt value file recomputes; a stored
`null` is still a hit); `library` 93 → 94 (a PNG data URL string is `png-data-url`);
`viewer-record-schema` stays 19 with two new cases inside existing tests.
`scripts/check_all.sh:150-153` pins the viewer count. `bash pyto/scripts/check_all.sh`:
ALL SUITES PASSED.

### Day 3 fixer round 2: a value, an address or a name is data, and data must not be fatal

Five defects found by review. Round 1 was about record data reaching a *reader*; this
round is about record data reaching a *producer* — the same rule one step earlier, and
about one place where the two runtimes' records disagreed on the same input. Nothing in
`pcr.py`, `core.py`, `pql.py` or `graph.py` moved; the only library file touched is
`materialize.py`, and consumer testimony bytes are unchanged
(`TestimonyBytesUnchangedByMaterializing` still passes).

**A cyclic value took the whole record down, not one panel.** RECORD.md:62 assigns "not
serializable" to `omitted`, and the JS reference does exactly that
(`adapters.js:281-295`, `{kind:'omitted', note:'value is not JSON serializable:
Converting circular structure to JSON…'}`). `render_value` caught only
`(TypeError, ValueError)` and then digested the value through `_stable_repr`, which had
no cycle memo — unlike builtin `repr()`, whose answer for a self-referential dict is
`{'name': 'node', 'self': {...}}`. A cyclic Part value therefore raised `RecursionError`
out of `run_record` and *every* invocation's row was lost, not the offending one. Two
changes, both in `src/pyto/materialize.py`: `_stable_repr` carries an `id()` memo of the
containers on its recursion stack and marks a repeat the way `repr()` does
(`materialize.py:79-128`); the probe and the fallback are guarded by `except Exception`
(`materialize.py:222-244`, `_unserializable_note` at :130-145), which is what a 6000-deep
nesting needs too — `json.dumps` raises `RecursionError` there, which is neither
`TypeError` nor `ValueError`.

**`$&` in a Part value rewrote the standalone page.** `embed.mjs` inserted the record
block and the inlined bundle with `String.prototype.replace` and a replacement *string*
(`embed.mjs:63`), so `$&`, `` $` ``, `$'` and `$1` anywhere in a value, an address or a
`pcr` name were expanded as replacement patterns. A text Part holding the shell snippet
`printf $'%s\n' done` was enough: the record block no longer parsed, and in the `$'` case
the module bootstrap was left un-inlined, so the emitted file could never mount and
`readEmbeddedRecord` threw where `mount()` does not catch. The page's header comment
promises the opposite ("an invalid record fails at build time instead of in the browser").
Both replacements now pass a function, which is inserted literally
(`viewer/embed.mjs:63-71`); the bundle gets it too, because a future `$&` in `adapters.js`
would corrupt the inline module the same way. `embeddableJson`'s `<`/`>` escaping was
correct and unchanged — this was integrity, not injection.

**A `hit` was claimed where nothing was reused.** `materialize.py` ORed
`address in preexisting` into the hit test, which the JS reference `deriveHit` never
consults and which RECORD.md:55-56 excludes in its own parenthetical. An invocation that
read a Part *this same run had already overwritten* was reported `hit: true` in Python and
`hit: false` in JavaScript for the same program, while the value shown is the freshly
computed one. `validate()` cannot catch it — the counters stay self-consistent — so it was
silent. The rule is now `adapters.js:244-249` verbatim (`materialize.py:379-383`), pinned
from both sides: `tests/test_materialize.py::HitLedger::`
`test_re_reading_a_part_this_run_overwrote_is_not_a_hit_as_in_javascript` and
`viewer/test/adapters.test.mjs` ("deriveHit: an address this run overwrote is not a hit").
`preexisting` still decides `parts[...].preexisting`, and the Day 1 evidence record is
unchanged: `select` and `split` are still the two hits.

**A `png-data-url` whose payload will not decode aborted the sheet run.** RECORD.md:60-61
fixes the prefix, not the payload; `adapters.js` accepts such a value and the viewer
renders it as an `<img>` without complaint — `viewer/test/render.test.mjs:218` uses
`data:image/png;base64,iVBORw0KGgo=` as a fixture for exactly that. `_value_image` called
`Image.open(b64decode(...))` unguarded (`materialize.py:586-592`), so
`PIL.UnidentifiedImageError` (or `binascii.Error`) escaped `tick_sheets` and left a
half-written `ticks/` directory — the earlier Ticks' sheets on disk, the later ones
missing. The decode now degrades to `None` (`materialize.py:592-601`) and the invocation
keeps its text panel, which already names the value's kind and note: the same
degrade-don't-crash contract `render_value` honours.

**A receipt-less run emitted a document tagged with a schema it did not satisfy.** With
`observe=False`, `run_record` set `calculation.identity_scope`, `actual_consumes`,
`actual_produces` and `writes` to `null` and still wrote `"schema":
"pyto-run-record@1"`. RECORD.md marks its nullable fields explicitly (`"<hex or null>"`,
`"<sha or null>"`) and marks none of those four, so RECORD.md:65 does not license nulling
them — and both readers refuse the result at the same path
(`viewer/adapters.js:145,155-158`; `viewer/test/record_schema.py:181,190-193`). The old
test asserted the nulls without ever running the document through a reader, which is why
the suite was green. `run_record` now raises `ValueError` naming `observe=True` when any
invocation has no receipt (`materialize.py:322-337`); its one caller,
`experiments/grouped-ablation/materialize_run.py:107-112`, already passes `observe=True`,
so nothing downstream changes. The null-emitting branch is gone rather than dead. The
refusal is paired with a test that shows *why* it is a refusal — the four fields nulled
one at a time, each rejected by the independent Python validator at its own path — and a
new class, `ReadableByTheOtherRuntimesValidator`, runs the Day 1 record, a record of every
value kind (including the cyclic and undecodable-PNG cases above) and the committed
evidence file through `viewer/test/record_schema.py`, so this producer is checked by a
reader other than itself.

**Counts.** `library` 94 → 103 (`tests/test_materialize.py` 30 → 39: the cycle, the
repeated-but-not-cyclic container, the 6000-deep nesting, a cyclic value leaving the rest
of the record intact, the overwrite-then-read hit, the undecodable PNG leaving no
half-written directory, the receipt-less refusal, the shape it refuses, and the three
validator cases); `viewer` 81 → 83 (the `$&`/`` $` ``/`$'` record, and `deriveHit` on an
overwritten address). `scripts/check_all.sh:150-158` pins the viewer count and is updated;
no other expected count moved. `bash pyto/scripts/check_all.sh`: ALL SUITES PASSED
(library 103, experiments/grouped-ablation 230, experiments/s3-synthetic 5, consumer 61,
disc-stats 4, examples 3, art-registry-md, viewer 83, viewer-record-schema 19).

### Day 3 contract fix: `declared_consumes` is the Part reads, not a copy of `inputs`

`viewer/RECORD.md` said "`inputs` keeps the testimony spelling … `declared_consumes`
repeats them in binding order" (RECORD.md:52-54 before this change). No pyto record has
ever looked like that. `Receipt.declared_consumes` is filled only from bindings whose
source is a `Part` (`src/pyto/pcr.py:308-315`, the field at `pcr.py:120`), and
`materialize.py:416` does nothing to it but add the `px:` prefix — so in the committed
Day 1 evidence (`experiments/grouped-ablation/evidence/run-1/record.json`) 13 of the 15
invocations carry `declared_consumes: []`, because everything downstream of `split` binds
`fn:` result refs and declares no store read at all. Two independent readers already
behave as if the amended text were the rule: `viewer/adapters.js:385-390` and
`viewer/test/record_schema.py:290-299` both union `inputs.values()` with
`declared_consumes` before building the part index. The contract was the only thing out of
step, so the contract moved and no runtime code did — `pcr.py` and `materialize.py` are
untouched, and consumer testimony bytes are unchanged.

RECORD.md now states it in three clauses: `inputs` is the complete binding map in
testimony spelling; `declared_consumes` is the producing runtime's declared *Part* reads
only, the `px:` bindings in binding order, empty where every binding is an `fn:` ref; and
a part index must union the two and resolve each `fn:<id>` through that invocation's
`into`. The worked example carries a second invocation, `fit.all` in a second Tick, whose
one binding is `fn:split` — so the example itself shows the empty `declared_consumes` and
the empty `actual_consumes` that come with a result binding, and the `parts` rows shown
are the ones those two invocations derive.

`viewer/fixtures/pyto-value-kinds.json` was modelling the retired convention: six of its
eleven invocations listed `fn:` ids in `declared_consumes` (`fit.all`, `score.all`,
`fit.drop_g3`, `score.drop_g3`, `snapshot`, `table`). They are now `[]`. The derived part
index is unchanged — both readers were already taking those reads from `inputs` — so no
viewer expectation moved; the mutation cases that pin `declared_consumes` paths
(`viewer/test/adapters.test.mjs:392`, `viewer/test/test_record_schema.py:244,339`) point
at `select`, whose binding is a `px:` and stays.

Three tests in `tests/test_materialize.py`
(`DeclaredConsumesIsThePartSubsetOfInputs`): the committed run-1 bytes obey the rule for
all 15 invocations and the 13 empty ones are exactly the all-`fn:` invocations; a freshly
materialized Day 1 record obeys it too (mutant: `materialize.py:416` →
`declared_consumes = list(testimony.inputs.values())`, i.e. the old text — fails with 13
violations); and two `px:` bindings whose parameter names sort the other way keep binding
order (mutant: `sorted(...)` around the comprehension at `pcr.py:311-315` — fails with the
alphabetical answer). The first test's mutant is the evidence itself: giving `fit.all` a
`declared_consumes` of `["fn:split"]` in `evidence/run-1/record.json` fails it.

**Fix round 2 (verifier).** Four corrections to the above, none of which change what a
runtime emits:

- The rule is now *enforced*, not described. `declared_consumes` is exactly the `px:`
  bindings of `inputs`: both validators reject an `fn:` entry and an entry `inputs` does
  not carry, at the same path (`viewer/adapters.js:153-168`,
  `viewer/test/record_schema.py:188-199`). Without it, the six `fn:` entries deleted from
  `viewer/fixtures/pyto-value-kinds.json` validated cleanly and nothing stopped the drift
  returning. Two cases per validator table, one isolating each half of the rule
  (`viewer/test/test_record_schema.py:246-256,341-351`): `fit.all` binds `split` as
  `fn:split`, so an `fn:split` entry there *is* in `inputs.values()` and only the spelling
  rule refuses it, while `px:scratch.ablation.not_bound` is spelled right and only the
  subset rule refuses it. Each of the four checks, disabled one at a time, fails the
  `viewer-record-schema` suite. The suite is still 19 tests: the cases went into the two
  existing tables rather than into new methods.
- RECORD.md's own text said `declared_consumes` is a subset of `inputs.values()` and, two
  paragraphs later, that reading `inputs` alone loses a declared Part read recorded
  outside the binding map. Both cannot hold. The subset rule is the one that is true of
  every record in the tree and is now validated, so the second clause is gone: the union
  the two reference readers do is documented as a defence against a record that reached
  them without passing `validate`, not as a requirement.
- The RECORD.md edit inserted 54 lines above `## Field rules`, so every in-tree
  `RECORD.md:NN` citation below the insertion pointed at the wrong line. All of them in
  live code and live prose *outside the kernel* are renumbered against the amended file
  (`tests/test_materialize.py`, `questions.md`, `viewer/adapters.js`,
  `viewer/tick-viewer.js`, `viewer/README.md`, the five files under `viewer/test/`,
  `experiments/grouped-ablation/hits.py` and `materialize_run.py`). Three citation classes
  are deliberately left alone and listed here instead. (1) The twelve in
  `src/pyto/materialize.py:15,20,49,50,51,187,223,296,308,394,480,595`: renumbering them
  means editing `pyto/src`, and the day's hard rule keeps that tree clean — pinned by
  `experiments/grouped-ablation/test_materials.py:352`
  (`LibraryUntouched.test_git_status_is_clean_under_pyto_src`), which fails on the edit.
  (2) The dated entries earlier in this file. (3) The archived run records under
  `experiments/runs/day3/` and `experiments/landings/` (including the built
  `evidence/run-1/tick-viewer.html`), which quote RECORD.md as it stood when they were
  written. The union readers moved too and are
  cited at their new lines: `viewer/adapters.js:385-390` and
  `viewer/test/record_schema.py:290-299` (the earlier `adapters.js:327-336` named
  `capped()`, not the union).
- `evidence/run-6-cached/reuse-ledger.json` was regenerated from a throwaway worktree and
  baked that worktree's absolute paths into committed evidence — the only evidence file in
  the tree naming a directory that landing deletes. `run_cached.py`'s
  `resolve_in_fresh_process` now records `command` through `portable()`: a path inside the
  pyto root becomes `<pyto>/...` and anything else inside the checkout becomes
  `<checkout>/...` (so a sibling `.venv` reads `<checkout>/.venv/bin/python`, not a
  `<pyto>/../` path that climbs out of the root it names), a path outside the checkout is
  left exactly as it ran. Both
  spellings of each argument are tested, because `.venv/bin/python` is a symlink to the
  system interpreter and resolving first would hide the checkout path. Five tests in
  `experiments/grouped-ablation/test_run_cached.py`
  (`TheLedgerRecordsNoPathThatLandingWouldBreak`), each naming the one-line mutation it
  kills; the ledger on disk is asserted to contain no path under the checkout.

**Fix round 3 (verifier).** Three corrections to fix round 2, none of which change what a
runtime emits:

- `experiments/grouped-ablation/hits.py:14` cited `RECORD.md:83-105` for the `hit` rule,
  but 83 is where the `declared_consumes` bullet starts. The sentence is about `hit`, whose
  bullet is `viewer/RECORD.md:104-107`; the citation now reads that.
- The JavaScript half of the `declared_consumes` rule was pinned only by the Python
  cross-check suite: either branch of `viewer/adapters.js:162-167` could be deleted with
  `node --test viewer/test/*.test.mjs` still green. Two tests in
  `viewer/test/adapters.test.mjs` now isolate one branch each, the same way the
  `viewer-record-schema` tables do — `fn:split` on `fit.all` is in `inputs.values()`, so
  only the spelling rule can refuse it; `px:input.ablation.unbound` on `split` is spelled
  right, so only the subset rule can. Deleting either branch fails exactly its own test.
- `portable()` (`experiments/grouped-ablation/run_cached.py:176-200`) anchored everything
  under the checkout at the pyto root, so this worktree's sibling `.venv` came out
  `<pyto>/../.venv/bin/python` — a placeholder that climbs back out of the root it names.
  It now anchors at the containing root: `<pyto>/...` inside `pyto/`, `<checkout>/...`
  elsewhere in the checkout, untouched outside it. `evidence/run-6-cached/reuse-ledger.json:166`
  reads `<checkout>/.venv/bin/python`, which is what regenerating would now write; the rest
  of the ledger is byte-identical and still `json.dumps(sort_keys=True, indent=2)`.

**Counts.** `viewer-record-schema` stays 19 and `experiments/grouped-ablation` grows by
the five new `test_run_cached.py` tests (no pin, 240 total). `viewer` is 87 — 85 after fix
round 2, plus the two `declared_consumes` tests of round 3 — against a
`scripts/check_all.sh:160` pin of 83, which this pack may not edit; see the `{?}`
`ViewerPin` entry in `experiments/tasks/0/packet.md`. Runs green with
`EXPECT_VIEWER=87 bash pyto/scripts/check_all.sh`.

**Fix round 4 (verifier).** Two corrections, neither touching a runtime or a validator; the
round's blocker is a one-number pin this pack may not edit.

- `viewer/RECORD.md:41` — the worked example contradicted the contract two bullets down. The
  `split` invocation binds `px:scratch.ablation.raw`, and the example's own `parts` block
  (`viewer/RECORD.md:70`, added in fix round 2) says that address is `written_by: null,
  preexisting: true`. The `hit` rule (`viewer/RECORD.md:104-107`) makes exactly that shape a
  hit, and both implementations agree on it —
  `deriveHit(["px:scratch.ablation.raw"], new Set(), false)` is `true`
  (`viewer/adapters.js:258-265`) and `src/pyto/materialize.py:383` is the same predicate — as
  does the record the example abridges (`experiments/grouped-ablation/evidence/run-1/record.json`
  records `split` with `hit: true`). The example now reads `"hit": true`. `fit.all`'s
  `"hit": false` at `:63` is untouched and correct: its one binding is `fn:split`. The counters
  line at `:74` (`"hits": 2` of 15) was already right — `select` and `split` are the run's two
  hits — so nothing else in the block moves, and no line numbers shift.
- `tests/test_materialize.py:607` cited `RECORD.md:83-105` for the `hit` rule: the same
  off-by-a-bullet fix round 3 corrected in `hits.py:14` and missed here (83 starts the
  `declared_consumes` bullet). It now reads `RECORD.md:104-107`, matching `:646` in the same
  file. A grep of every live `RECORD.md:NN` citation outside `src/`, `experiments/runs/` and
  `experiments/landings/` finds no other bullet-range citation off its bullet.

**Counts.** Unchanged by this round: no test was added or removed, so `library` is 106,
`viewer` 87, `viewer-record-schema` 19, `experiments/grouped-ablation` 240. The
`scripts/check_all.sh:160` pin still reads 83 and this pack still may not edit that file, so
the unaltered `bash pyto/scripts/check_all.sh` ends `SOME SUITES FAILED` on that one line and
on nothing else; `EXPECT_VIEWER=87 bash pyto/scripts/check_all.sh` ends `ALL SUITES PASSED`.
See the `{?}` `ViewerPin` entries in `experiments/tasks/0/packet.md`.
## Day 3+ (base f2e0b8e): `pyto/src/pyto/mounts.py`, the world as a mount id

**A world is an id above an ordinary PxC, and it never enters an address.** Round four
put `disc`, `chess`, `wumpus`, `neat`, `tidy` inside the address as segments; ChainSpot had
already decided the other way and written a test for it — "The root is intentionally
external to PxC's semantic address space" (`43e6ea3:packages/alg/src/exec/mounts.ts:3-8`,
quoted at `research/chainspot-branch-mining.md:40-48`), with
`expect(dash.has('px.DashsTrack.s1.badges')).toBe(false)`
(`43e6ea3:tests/unit/pxcRootMounts.test.ts:6-18`, quoted at
`research/chainspot-branch-mining.md:56-65`). Section 6 item 1
(`research/chainspot-branch-mining.md:411`) ranks the port first and says the negative test
is the point: "it is what stops the LAB name from creeping into addresses".
`questions.md:407-411` (`{?} AddressRootIsAMount`) leans adopt, and the same entry's
earlier copy records that "Python has no mount type at all" and that the default taken is
`PartyMountType` — "build the Python mount type in round five, since nothing else prevents
collisions" (`questions.md:129,139-140`).

**`Mounts` is 89 lines and six methods plus a side map** (`src/pyto/mounts.py:37-89`):
`mount(root, pxc)`, `has(root)`, `get(root)`, `roots()` in insertion order, `entries()`,
and `slice(roots)` returning a new `Mounts` that shares the same PxC objects
(`mounts.py:70-77`) — a write through a slice is visible through the original, which is
the "cheap root-level slice; mounted PxCs themselves are shared" of
`43e6ea3:…/mounts.ts:11-22`. The human label lives beside the mounts, never in an address:
`set_label`/`label` (`mounts.py:79-89`), after
`43e6ea3:scripts/warm-dev-pxc-roots.mjs:46-48`. **No address rewriting happens anywhere** —
`mount` stores the object and writes nothing into it (`mounts.py:44-51`), `get` returns the
exact object (`mounts.py:56-60`) — so a value at `px.badges.px` is reached only as
`mounts.get(root).get("px.badges.px")`.

**Both errors are loud, as in the reference.** Re-mounting the *same* object is a no-op;
a *different* object under a mounted root raises `ValueError` naming the root
(`mounts.py:49-50`, after `43e6ea3:…/mounts.ts:32-34`), and a missing root raises
`KeyError` from `get`, `slice`, `set_label` and `label` rather than returning `None`
(`mounts.py:58-59,74,81-82,87-88`, after `43e6ea3:…/mounts.ts:40`). An empty or non-`str`
root is refused at `mount` (`mounts.py:46-47`), the way `Part` refuses an empty address
(`core.py:17-19`).

**The id is expected to be content-derived; `Mounts` does not compute it.** ChainSpot's
root is `sha256(WxH:sha256(rgba))` (`43e6ea3:packages/alg/src/exec/operations.ts:688,707`;
`questions.md:413-416`, `{?} RootIdIsContent`). `Mounts` accepts any non-empty string and
`tests/test_mounts.py:243-253` asserts `hashlib` never appears in the module, so the digest
stays the caller's job and this file has no opinion about how a world is named.

**Nothing in the kernel moved.** `core.py`, `pcr.py`, `pql.py`, `graph.py` and
`__init__.py` are untouched; the module is reached as `from pyto.mounts import Mounts`, the
status `pyto.address` and `pyto.materialize` have, and two tests pin that
(`tests/test_mounts.py:227-241`). `mounts.py` imports `PxC` only under `TYPE_CHECKING`
(`mounts.py:31-32`), so at runtime it depends on nothing.

**Counts.** `library` 120 → 141 (`tests/test_mounts.py`, 21 tests, 21 of 21 mutations
killed one at a time with the file restored after each: the prefix rewrite in `mount`, a
stray `px.mount.root` write, a copying `get`, the dropped `is not pxc` half of the guard,
the deleted already-mounted raise, the deleted empty-root guard, `get` degraded to
`.get(root)`, `has` returning `True`, `slice` skipping a missing root, the deleted
`set_label` guard, `sorted()` in `roots`, `entries` and `slice`, a deep-copying `slice`,
`sliced = self`, a `px.view.label` write in `set_label`, `label` falling back to the root,
the dropped label carry in `slice`, a `mounts` import added to `core.py`, a re-export added
to `__init__.py`, and a `hashlib` digest computed inside `mount`). No suite count is
pinned for `library` (`scripts/check_all.sh:86`), so that file is unchanged.
`bash pyto/scripts/check_all.sh`: ALL SUITES PASSED (library 141,
experiments/grouped-ablation 230, experiments/s3-synthetic 5, consumer 61, disc-stats 4,
examples 3, art-registry-md, viewer 83, viewer-record-schema 19).

## task 27 (base af0e30f): a Calculation can produce several Parts

`calc(..., into=[a, b])` publishes one Part per address from one invocation -- the Calculation
returns a mapping keyed by those addresses or a sequence in that order -- and one receipt lists
every produce, one write per address, `result_sha256` of the whole returned value as before plus
`produce_sha256` `{address: digest}` per published Part; a reference to such an invocation names
which produce it reads (`ref[address]`, testified `fn:<id>#<address>`) and a bare one is refused
at bind time and at resolve time; `into` may be an array in the record and both reference readers
resolve the new spelling (`viewer/RECORD.md`, `viewer/adapters.js`, `viewer/test/record_schema.py`);
one-address calls are byte for byte unchanged -- the record is identical and the receipt differs
only by the added field, pinned against `tests/fixtures/single_into_pre_change.json` generated
before the change -- and the grouped-ablation evidence was regenerated with the experiment's own
scripts (`run.py --force`, `run_regrouped.py`, `run_reinput.py`, `run_from_retained.py`,
`run_cached.py --force`, `replay.py --force`) because the receipts and pcr.py's pinned source
digest moved; no test expectation was edited by hand.
Then every other reader: `src/pyto/graph.py` (the authoring surface) and
`experiments/grouped-ablation/retain.py` (retain/replay) walk `produce_addresses()` instead of one
`into.address`, so `to_program`/`from_program` round-trip a multi-produce program and
`check_record` unions the produces rather than putting a list in a set; one test per file guards it.
`bash pyto/scripts/check_all.sh`: ALL SUITES PASSED (library 193,
experiments/cross-project 9, experiments/grouped-ablation 244, experiments/hiding-primitives 6,
experiments/s3-synthetic 5, experiments/students 10, consumer 61, disc-stats 4, examples 3,
art-registry-md, viewer 107, viewer-record-schema 24).
