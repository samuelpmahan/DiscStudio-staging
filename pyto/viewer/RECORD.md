# Run record: the JSON both runtimes read and write

`pyto-run-record@1`. One document per executed PCR (or per PQL composition in the browser). In the
ELK reading (`pyto/research/ULTRACODE-WEEK.md`, Reframing 4) the PCR itself is Kibana: a
PrincipleComponentRender is the definition of what to show, per Tick, of the principal components of
a computation, exactly as its name says. This record is the data that render consumes, one document
per execution:
what ran, per Tick, what each Calculation read and wrote, how long it took, whether a Part was a
hit, and the value as material. It is produced by `pyto.materialize.run_record` in Python and by
the viewer's adapters from DiscStudio `px.receipt.<name>` records and ChessLab-shaped receipts in
JavaScript. It is a view for people and tools, never the program itself (stewardship: an
inspection receipt is derived from a program and a run).

The block below is abridged: two of the fifteen invocations of one run, and the `parts` rows those
two derive. It carries both binding spellings on purpose -- `split` binds a Part, `fit.all` binds
`split`'s result -- because that is the pair the `declared_consumes` rule turns on.

```json
{
  "schema": "pyto-run-record@1",
  "pcr": "grouped-ablation",
  "source": {"runtime": "pyto" | "discstudio" | "chesslab" | "wumpus", "version": "0.1.0", "commit": "<sha or null>"},
  "ticks": [
    {
      "index": 0,
      "name": "Prepare",
      "invocations": [
        {
          "id": "split",
          "calculation": {"address": "fn.ablation.split", "implementation_sha256": "<hex or null>",
                          "identity_scope": "runtime-function-body"},
          "inputs": {"raw": "px:scratch.ablation.raw"},
          "args": {"seed": 7},
          "into": "scratch.ablation.split",
          "declared_consumes": ["px:scratch.ablation.raw"],
          "actual_consumes": ["scratch.ablation.raw"],
          "actual_produces": ["scratch.ablation.split"],
          "writes": [{"address": "scratch.ablation.split", "kind": "new-address"}],
          "duration_ms": 3.921,
          "result_sha256": "<hex or null>",
          "hit": true,
          "value": {"kind": "json", "data": {"...": "..."}, "note": null}
        }
      ]
    },
    {
      "index": 1,
      "name": "Fit",
      "invocations": [
        {
          "id": "fit.all",
          "calculation": {"address": "fn.ablation.fit", "implementation_sha256": "<hex or null>",
                          "identity_scope": "runtime-function-body"},
          "inputs": {"split": "fn:split"},
          "args": {"variant": "all"},
          "into": "scratch.ablation.model.all",
          "declared_consumes": [],
          "actual_consumes": [],
          "actual_produces": ["scratch.ablation.model.all"],
          "writes": [{"address": "scratch.ablation.model.all", "kind": "new-address"}],
          "duration_ms": 5.663,
          "result_sha256": "<hex or null>",
          "hit": false,
          "value": {"kind": "json", "data": {"...": "..."}, "note": null}
        }
      ]
    }
  ],
  "parts": {
    "scratch.ablation.raw": {"written_by": null, "read_by": ["split"], "preexisting": true},
    "scratch.ablation.split": {"written_by": "split", "read_by": ["fit.all"], "preexisting": false},
    "scratch.ablation.model.all": {"written_by": "fit.all", "read_by": [], "preexisting": false}
  },
  "counters": {"invocations": 15, "hits": 2, "computed": 13, "wall_ms": 27.0}
}
```

## Field rules

- `inputs` is the complete binding map, in testimony spelling: one entry per bound parameter,
  `px:<address>` for a Part binding, `fn:<id>` for a result binding (the id of the invocation whose
  `into` published the value). It is the only field that carries every read the program declared.
- `declared_consumes` is the producing runtime's own declared Part reads and nothing else: exactly
  the `px:` bindings of `inputs`, in binding order. Every entry is spelled `px:<address>` and every
  entry appears in `inputs.values()` -- a strict rule, not a convention: both validators reject an
  `fn:` entry and an entry `inputs` does not carry, at the same path. It is therefore empty for an
  invocation whose every binding is an `fn:` result ref -- the common case in a fanned-out PCR: 13
  of the 15 invocations in the Day 1 evidence record
  (`experiments/grouped-ablation/evidence/run-1/record.json`), and `fit.all` above. In pyto that
  is literal -- `Receipt.declared_consumes` (`src/pyto/pcr.py:120`) is filled only from bindings
  whose source is a `Part` (`src/pyto/pcr.py:308-315`), and `materialize.py:416` prefixes each
  with `px:`. It is a second, narrower witness -- it says which reads went through the store --
  not a restatement of `inputs`.
- Consequently a reader that wants every read reads `inputs.values()` and resolves each `fn:<id>`
  through that invocation's `into`; reading `declared_consumes` alone loses the result bindings.
  Because `declared_consumes` is a subset, unioning it in adds nothing to a conformant record;
  both reference readers union it anyway, defensively, so that a producer the validator never saw
  costs a duplicated edge rather than a lost one: `viewer/adapters.js:385-390` and
  `viewer/test/record_schema.py:290-299`. An `fn:` binding counts as a read of the address the
  named invocation wrote; it never makes a `hit`.
- `actual_consumes` and `actual_produces` are bare addresses as observed on the store. An `fn:`
  binding is served from the run's results, not from the store, so it leaves `actual_consumes`
  empty (`fit.all` above) -- another reason the part index cannot be built from the actuals alone.
- `hit` is true when the invocation read a Part that existed before this run (a `px:` binding whose
  address was not produced by an earlier invocation of the same run), or when the runtime reports
  reuse (`reused: true` in a DiscStudio trace). The owner's definition: any Part or Calculation being
  used is a hit.
- `value.kind` is one of `json` (data is the JSON value), `text` (data is a string), `svg` (data is
  the SVG document text; viewers render it as an image, never inline it as markup), `png-data-url`
  (data is a `data:image/png;base64,...` string produced by a materializer from an image Part), or
  `omitted` (data is null; `note` says why: not serializable, over the size cap, or the runtime did
  not retain values). Values over 256 KB are replaced by `omitted` with a note carrying the size and
  the digest; arrays longer than 200 entries carry the first 200 and a note with the full length.
- Missing fields are null, never invented. A runtime that does not record durations writes null.
- `parts` is derived from the invocations and is present for convenience only.
- Records are JSON with sorted keys and two-space indentation when written to disk.
- `into` is one address, an **array of addresses**, or null. A Calculation may publish several
  Parts from one pass (`{?} WhatIsATick`, owner 2026-09-10: "Obviously a Calculation can produce
  multiple parts"), and then `into` carries every address it declared, in declared order, while
  `actual_produces` and `writes` -- lists already -- carry one entry each per published address.
  One address is still spelled as the bare string it always was, so a one-address record is byte
  for byte what it was before multi-produce existed.
- An `fn:` binding on a producer that publishes several Parts names which one:
  `fn:<id>#<address>`. A reader resolves an `fn:` binding by taking the text after `fn:`, using it
  whole when it names an invocation in this record (the bare form, the producer's single published
  Part), and otherwise splitting at the **last** `#` into producer id and produce address -- the
  order that keeps an invocation id which itself carries a `#` resolvable. A bare `fn:<id>` on a
  producer of several Parts is what pyto's kernel refuses at bind time (`ResultRef` carries no
  produce, so `ref[address]`/`ref.part(address)` is how a program names one); a record that
  carries one anyway is read as a read of every Part that producer published. Both reference
  readers implement exactly this: `viewer/adapters.js` `parseBinding`/`derivePartIndex` and
  `viewer/test/record_schema.py` `resolve_binding`/`derive_part_index`.
- The record carries one `result_sha256` per invocation and no per-produce digest. The digest of
  each published Part is in the **Receipt** (`produce_sha256`, below), which is where a
  per-produce claim belongs; adding a field here would change the bytes of every record ever
  written, including the one-address records this change had to leave alone
  (`{?} RecordProduceDigest`).

## Placement and budget

Four optional fields say how a run was *scheduled* -- never what it was. **Absent means serial
and unbudgeted**, which is what every runtime that never heard of either writes, and what
`pyto.materialize.run_record` writes for a plain serial run: the four appear together, and only
when the run was parallel, was given a budget, or was stopped by one. A serial unbudgeted record
is therefore byte for byte the record it was before these existed
(`{?} ScheduleFieldsOptional`).

- per invocation, `"placement": {"worker": <int>, "started_ms": <float>}` or `null`. `worker` is
  the 0-based index of the pool thread that ran this invocation **within its Tick**; `started_ms`
  is the offset from the moment that Tick began, not a wall clock, so a reader draws the overlap
  without one. A serial run writes `null`: a Tick that ran on one thread has no placement to
  report. Placement is outside the compared and replayed fields for the same reason durations
  are -- it is the schedule, and the schedule is not the program.
- per Tick, `"latency_ms": <float>` or `null`: the wall time of the Tick from its first start to
  its last finish. A parallel run measures it; a serial run's is the sum of its own durations,
  which for a series of Calculations is the same number. Null when any invocation's duration is
  null. Both reference readers derive it the same way and fall back to the sum when the field is
  absent: `viewer/adapters.js tickLatencyMsFromRecord`, `viewer/test/record_schema.py
  tick_latency_ms`. `viewer/tick-viewer.js` exports a `tickLatencyMs` of its own whose
  fallback is the **longest branch** rather than the sum, because that is the critical
  path it draws; the two agree whenever the field is present, which is the only case a
  record decides (`{?} TwoLatencyFallbacks`).
- run level, `"parallel": <bool>`: true when the invocations of each Tick ran concurrently
  (`PCR.run(pxc, parallel=True)`).
- run level, `"budget": {"limit_ms": <float or null>, "stopped_after_tick": <tick name or null>,
  "completed": <bool>}`. The budget is checked at the Tick boundary and nowhere else, so a run
  that stops stops **between** two Ticks with everything before the seam published in full:
  `stopped_after_tick` names the last Tick that completed and `completed` is false. A completed
  run has `stopped_after_tick: null`; both validators refuse a record that claims both, and one
  whose `stopped_after_tick` names no Tick in the record.

`viewer/adapters.js runSchedule` and `viewer/test/record_schema.py run_schedule` read the pair
back with those defaults, so a reader asks one question of every record, old or new.

Work against latency is the number `{?} TicksAsCircuits` asked for: a Tick's work is the sum of
its `duration_ms`, its latency is `latency_ms`, and the ratio is what the parallel element bought.
The testimony itself is unchanged by any of this -- `ticks` in `PcrRun` carries no placement, no
latency and no budget, so a run's testimony bytes are identical serial versus parallel, and a
budgeted run's testimony is the byte-for-byte prefix of the unbudgeted run's.

## Effects

An **OperationalCalculation** -- a Calculation whose address starts with `oc.` -- is the only kind
that may perform an effect, and it may perform it only through the `Effects` handle the run gives
it (`pyto/src/pyto/effects.py`; `PCR.run(..., effects_root=...)` passes it as `args["effects"]`).
Five verbs: `write_text`, `read_text`, `now_ms`, `random`, `env`. Every call appends one entry to
that invocation's ledger, and the ledger is on the receipt and in this record, because the receipt
is the subject: an effect that is not recorded did not happen as far as this format is concerned.

Per invocation, `"effects": [<entry>, ...]`. **Optional, exactly like placement and budget**:
absent means the run performed none -- what every runtime that never heard of an `oc.` writes --
and a record that carries the field carries it on **every** invocation of the run, empty for every
pure `fn.` one (`{?} EffectsFieldOptional`). `pyto.materialize.run_record` writes it when the run
it describes ran an `oc.` Calculation or carries a ledger on any receipt, so a pure record is byte
for byte the record it was before effects existed.

Each entry is `{"kind", "args", "result", "result_sha256"}`:

- `kind` is one of `write_text`, `read_text`, `now_ms`, `random_seed`, `random`, `env`.
- `args` is the call as it was made: `{"path": "<relative path>"}` for `write_text` and
  `read_text`, `{"n": <int>}` for `random`, `{"name": "<variable>"}` for `env`, `{}` for `now_ms`
  and `random_seed`. **A path is always relative to the run's `effects_root` and never absolute**,
  so a ledger recorded in one checkout replays in another (and in a test's temporary directory);
  both validators refuse an absolute path and a `..` segment.
- `result` is the value that came back, kept so a replay can feed it back: the text for
  `read_text`, the milliseconds for `now_ms`, the integer seed for `random_seed`, the list of
  draws for `random`, the string or null for `env`. It is **null for `write_text`**, whose text is
  kept as a digest alone -- a ledger is not a copy of the file.
- `result_sha256` is the sha256 of the canonical JSON of the recorded value, by the same rule as
  `result_sha256` on the invocation (`pyto/src/pyto/pcr.py` `_result_sha256`), for every kind --
  for `write_text` it is the digest of the text that was written. One rule, so two digests are
  comparable without asking which kind wrote them.

`random`'s draws come from a seeded generator **whose seed is itself an effect**: the first
`random` of an invocation records a `random_seed` entry and then the draws, so the ledger carries
everything a replay needs and nothing it has to guess.

Replay reads this list back: `PCR.run(..., replay_effects={<invocation id>: <effects list>})`
gives each `oc` invocation a `ReplayEffects` handle, which returns the recorded reads, clocks,
seeds and draws **in order**, re-performs each `write_text` and refuses it when the text now
digests differently, and refuses any call that is not the next recorded entry, naming the kind and
the index. A replayed invocation's receipt therefore carries the same ledger the recorded one did,
which is what makes a receipt comparable byte for byte across a fresh process
(`pyto/tests/test_effects.py`).

The effects ledger is not an observation: `PCR.run` records it with `observe` off as well as on
(`PcrRun.effects`), and the testimony -- `ticks`, the bytes consumers embed -- carries none of it,
so a run's testimony is byte-identical with observation on and off, exactly as it is serial versus
parallel. An `oc.` inside a **parallel** Tick is refused unless the program passes
`allow_parallel_effects=True` (`{?} ParallelEffectsOptIn`).

`px effects <record> [--tick NAME]` prints one line per effect: tick, invocation, index, kind, the
path or argument summary, and the digest (`pyto/src/pyto/px.py`).

The JavaScript reader ignores keys it does not know, so a record carrying `effects` is read by
`viewer/adapters.js` exactly as it was before; teaching the viewer to *draw* effects is another
team's change to that file and is not made here.

## Receipts as Parts

`PCR.run(pxc, observe=True)` writes each invocation's `Receipt` into the store as an ordinary Part at
`px.receipt.<pcr>.<tick>.<invocation-id>` -- the PCR name, the Tick name and the invocation id, under
the reserved `receipt` second segment (`pyto/src/pyto/address.py`), so a reader predicts every
receipt address from the PCR alone and PQL reads receipts like anything else
(`PQL.prefix("px.receipt.")`). The key is the invocation id, not the Calculation address, because one
Calculation runs many times in one Tick (`fit.all`, `fit.none`); with `observe=False` nothing is
written at all, and no Calculation may bind an address under `px.receipt.` as its `into` -- `PCR.calc`
and `Tick.calc` refuse it, so the segment is written by observation and by nothing else.

A `Receipt` carries two digests, because one invocation may publish several Parts.
`result_sha256` is the digest of the whole value the Calculation returned -- unchanged, and for a
one-address invocation the returned value *is* the published Part. `produce_sha256` is
`{address: sha256 or null}`, one entry per published address in declared order, and for a
one-address invocation it is `{into: result_sha256}`. Both are canonical-JSON digests, so a value
that is not JSON has none rather than an unstable one (`pyto/src/pyto/pcr.py` `_result_sha256`).
The multi-produce return itself is the Calculation's: it returns a mapping keyed by the declared
addresses, or a sequence in the declared order, and anything else -- a missing key, an extra key,
a sequence of the wrong length -- publishes no Part at all (`{?} MultiReturnStrict`).

This record does not enumerate store slots and so carries no receipt rows: `ticks` comes from the
testimony and the receipts, and `parts` from the addresses those name. The one place
`pyto.materialize.run_record` reads the store is the `preexisting` fallback (when the caller did not
capture `set(pxc.addresses())` before the run), and it excludes the receipt addresses this run's own
observation wrote, exactly as it excludes the addresses the run produced.

## Adapters

| Source | Where the fields come from |
|---|---|
| pyto | `PcrRun.ticks` (ids, inputs, args, into -- one address or a list), `PcrRun.receipts` — required, so `PCR.run(pxc, observe=True)` (calculation identity, declared and actual access, writes, duration, digest), `PcrRun.results` (values), the pre-run `PxC.addresses()` (preexisting Parts) |
| DiscStudio | `px.pql.<name>` (Ticks, Calculations with `call`, `with`, `args`, `into`, resolved `inputs`, `output`) and `px.receipt.<name>` (`trace[].reused`, `material`, `revision`, `computed`, `reused`) from `src/runtime.js` |
| ChessLab | `Receipt` from `src/lab/contract.ts`: `opId`, `frozenCalculations[]`, `declaredConsumes`, `declaredProduces`, `actualConsumes`, `actualProduces`, `writes`, `durationMs`; values are not retained, so `value.kind` is `omitted` |
| Wumpus | `executeTick` records: `inputs[]`/`outputs[]` with values, `calculations[]`, `writes`, `durationMs` |
