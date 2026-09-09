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
          "hit": false,
          "value": {"kind": "json", "data": {"...": "..."}, "note": null}
        }
      ]
    }
  ],
  "parts": {
    "scratch.ablation.split": {"written_by": "split", "read_by": ["fit.all", "score.all"], "preexisting": false}
  },
  "counters": {"invocations": 15, "hits": 2, "computed": 13, "wall_ms": 27.0}
}
```

## Field rules

- `inputs` keeps the testimony spelling: `px:<address>` for a Part binding, `fn:<id>` for a result
  binding. `declared_consumes` repeats them in binding order. `actual_consumes` and
  `actual_produces` are bare addresses as observed on the store.
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

## Adapters

| Source | Where the fields come from |
|---|---|
| pyto | `PcrRun.ticks` (ids, inputs, args, into), `PcrRun.receipts` — required, so `PCR.run(pxc, observe=True)` (calculation identity, declared and actual access, writes, duration, digest), `PcrRun.results` (values), the pre-run `PxC.addresses()` (preexisting Parts) |
| DiscStudio | `px.pql.<name>` (Ticks, Calculations with `call`, `with`, `args`, `into`, resolved `inputs`, `output`) and `px.receipt.<name>` (`trace[].reused`, `material`, `revision`, `computed`, `reused`) from `src/runtime.js` |
| ChessLab | `Receipt` from `src/lab/contract.ts`: `opId`, `frozenCalculations[]`, `declaredConsumes`, `declaredProduces`, `actualConsumes`, `actualProduces`, `writes`, `durationMs`; values are not retained, so `value.kind` is `omitted` |
| Wumpus | `executeTick` records: `inputs[]`/`outputs[]` with values, `calculations[]`, `writes`, `durationMs` |
