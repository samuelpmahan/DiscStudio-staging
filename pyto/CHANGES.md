# CHANGES.md: library seams of the ULTRACODE week

One entry per change to `pyto/src/pyto/`. Each entry names the day, the seam, the
tests that pinned the behaviour before and after, what it does *not* decide, and
the consumer-bytes statement. At most one library seam lands per day
(research/ULTRACODE-WEEK.md, "Execution policy"), so this file is also the count.

## Semantic flips

None. Every seam so far is additive: no existing field, default, exception, order
or serialized shape changed. A seam that changes what an existing program means
is recorded here first, with the consumer call sites it moves.

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
in-repo executable form of that check is the two tests above plus the 18 consumer
tests, which exercise the same call site.

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

**After.** The library suite is 64 tests: the 43 above plus 21 in
`tests/test_receipts.py`:

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

No other suite's *assertions* were changed by the seam, and all pass. Their counts
have since grown with the day's own experiment work (Lane C/D and fixer round 1),
so the numbers below are the ones `scripts/check_all.sh` printed on the last run of
this entry, not the pre-seam ones: `experiments/grouped-ablation` 151,
`experiments/s3-synthetic` 5, consumer 37, disc-stats 4, both examples. The 37
consumer tests are the 18 pre-tournament plus the 19 the art tournament added
(`scripts/check_all.sh:17-19`), none of them a change to a Day 1 assertion.

**No digest through `default=`** (research/ULTRACODE-WEEK.md critic gap 10).
`result_sha256` is `sha256(json.dumps(value, sort_keys=True, separators=(',', ':')))`
with no fallback serializer; `TypeError`/`ValueError` yields `None`. A value that
is not JSON therefore has no digest instead of a digest of its `repr`, which for
objects whose repr carries an address would be process-dependent and would show up
later as pyto-caused drift. Covered for a `set`, a `PxC`, and a dict with tuple
keys — the disc-stats result shape,
`consumers/discstudio-card/experiments/disc-stats/stats.py:34`
(`distinct_discs_by_mold -> dict[tuple[str, str], int]`).

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

**Not exported from `pyto/__init__.py`.** `Receipt`, `FrozenCalculation` and
`_TrackedPxC` are importable as `from pyto.pcr import ...` only — the same status
`Invocation` already has. The day's one library change is the seam in `pcr.py`; the
public surface moves when a consumer needs it, not before.

**Mutation check** (scratch only, applied to the imported module object at run
time, never to the repo): adding `default=str` to the result digest fails
`ResultDigest::test_non_json_value_yields_none` and `::test_tuple_keys_yield_none`
(2 of 2); collapsing `refinement` into `replacement` fails `WriteKinds::test_kinds`
(1 of 1); dropping `shadowed_inputs` fails
`ShadowedInputs::test_args_key_colliding_with_a_bound_input_is_recorded_not_raised`
(1 of 1).
