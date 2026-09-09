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

## Receipts as Parts

`PCR.run(pxc, observe=True)` writes each invocation's `Receipt` into the store as an ordinary Part at
`px.receipt.<pcr>.<tick>.<invocation-id>` -- the PCR name, the Tick name and the invocation id, under
the reserved `receipt` second segment (`pyto/src/pyto/address.py`), so a reader predicts every
receipt address from the PCR alone and PQL reads receipts like anything else
(`PQL.prefix("px.receipt.")`). The key is the invocation id, not the Calculation address, because one
Calculation runs many times in one Tick (`fit.all`, `fit.none`); with `observe=False` nothing is
written at all, and no Calculation may bind an address under `px.receipt.` as its `into` -- `PCR.calc`
and `Tick.calc` refuse it, so the segment is written by observation and by nothing else.

This record does not enumerate store slots and so carries no receipt rows: `ticks` comes from the
testimony and the receipts, and `parts` from the addresses those name. The one place
`pyto.materialize.run_record` reads the store is the `preexisting` fallback (when the caller did not
capture `set(pxc.addresses())` before the run), and it excludes the receipt addresses this run's own
observation wrote, exactly as it excludes the addresses the run produced.

## Adapters

| Source | Where the fields come from |
|---|---|
| pyto | `PcrRun.ticks` (ids, inputs, args, into), `PcrRun.receipts` — required, so `PCR.run(pxc, observe=True)` (calculation identity, declared and actual access, writes, duration, digest), `PcrRun.results` (values), the pre-run `PxC.addresses()` (preexisting Parts) |
| DiscStudio | `px.pql.<name>` (Ticks, Calculations with `call`, `with`, `args`, `into`, resolved `inputs`, `output`) and `px.receipt.<name>` (`trace[].reused`, `material`, `revision`, `computed`, `reused`) from `src/runtime.js` |
| ChessLab | `Receipt` from `src/lab/contract.ts`: `opId`, `frozenCalculations[]`, `declaredConsumes`, `declaredProduces`, `actualConsumes`, `actualProduces`, `writes`, `durationMs`; values are not retained, so `value.kind` is `omitted` |
| Wumpus | `executeTick` records: `inputs[]`/`outputs[]` with values, `calculations[]`, `writes`, `durationMs` |
