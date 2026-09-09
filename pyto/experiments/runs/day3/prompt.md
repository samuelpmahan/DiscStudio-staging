# Day 3 brief (verbatim excerpts from research/ULTRACODE-WEEK.md, Reframing 4, at base 83422cf) plus the shared record contract

Copied by the record-stage agent per `pyto/experiments/CAPTURE.md`. Day 3 as originally planned
("Second experiment #2: ablate pyto itself by patch; conventional fair comparison; replay-gated
composition promotion with reversibility", plan lines 228-250) is superseded for Day 3 itself by
**Reframing 4** ("ELK, JS first class, hits are simple, grow it", plan lines 75-129): the owner's
answers restate the reference architecture as ELK (Logstash/Elasticsearch/Kibana), declare the PCR
itself to be Kibana, and re-plan Days 3-5 accordingly. The kernel ablation, conventional-comparison
and promotion deliverables move to Day 4's second half (Reframing 4, "Day 3" bullet, last sentence);
this record therefore covers "Day 3: Kibana for Ticks" as it now stands, not the original Day 3
goal/deliverables paragraph.

Section boundaries copied below: Reframing 4's "The reference architecture is ELK" and "JS is first
class" bullets (plan lines 86-99); the "Days 3 to 5, re-planned" Day 3 bullet and the week's failure
criterion (plan lines 105-129); the full text of `pyto/viewer/RECORD.md` (the shared
`pyto-run-record@1` contract both runtimes must speak exactly).

## Reframing 4 excerpts (research/ULTRACODE-WEEK.md lines 75-129)

The owner's answers to the open questions:

- **A hit is any Part or Calculation being used.** Do not over-define it. Receipts already record
  reads and calls, so a hit ledger is: Parts read that existed before the run, and Calculations
  called that were already registered. No perceptual matching, no course identity, unless a later
  experiment needs it.
- **PCRs in ChainSpot are Kibana** (owner, after the ELK answer): a PrincipleComponentRender is the
  render definition, per Tick, of a computation's principal components. The viewer is therefore a
  PCR renderer, not a new dashboard concept, and the run record is what it renders.
- **The reference architecture is ELK.** Lego-like ingestion and semantic composition, like
  Logstash: Calculations composing meaning onto Parts through PCR pipelines. Store what you want
  how you want, like Elasticsearch: PxC, with content addressing as the document identity and
  receipts as documents. Visibility, like Kibana: the missing third piece, and the founding need
  (`pyto/research/origin.md`). PQL is the query DSL of that store and is expected to grow toward
  it (selection by tick, by calculation, by digest), which supersedes the earlier "PQL untouched"
  refusal as a permanent rule; it stays untouched only through Day 2.
- **JS is first class** unless it cannot meet the 5000 ms budget, which the owner expects it can.
  Spinning up a new LAB ("I want to spin up ChessLab") should be natural in JS. Python (pyto) is
  the workshop that experiments on, replays, compares and visualizes the same records; it is not
  the runtime the browser depends on. Consequences: every retained record, receipt and material
  format is JSON that both runtimes read and write; the node-versus-Python parity check on the
  same PQL document is central, with JS as the reference semantics where the two differ; the
  Tick viewer is a dependency-free browser page that reads receipts JSON from any LAB.
- **Growth style: give a crystal an anchor and watch it grow.** The week provides anchors (the
  kernel, receipts, the shared record format, the viewer) and does not add prohibitions beyond the
  ones that protect existing consumers. Lists of refusals in this plan are read as "not this
  week", never as design limits.

### Days 3 to 5, re-planned

- **Day 3: Kibana for Ticks.** A dependency-free browser page (`pyto/viewer/tick-viewer.html`,
  Node 22 tests, no build) that loads a PcrRun-with-receipts JSON and shows, per Tick, each
  Calculation with what it read, what it wrote, duration, result digest, hit or computed, and the
  Part values (text, JSON, or a rendered image when the value is an SVG or a data URL); the same
  page reads DiscStudio's `px.receipt.<name>` records and ChessLab-shaped receipts. Python side:
  a Tick materializer that emits that JSON from a PcrRun (neon sheets for image Parts) and the
  content-addressed materials store with hit counters ported from ChainSpot, experiment-local.
  Kernel ablation and the conventional cache comparison move to Day 4's second half.
- **Day 4: JS and Python on one record.** The same PQL document executed by `src/core/exec.js`
  under node and by Python, receipts compared field by field, JS as reference; the DiscStudio
  fan-out fixture (art registry: 16 families, 8 renderers) rendered and viewed in the browser
  through the consumer's `app.py` and the Tick viewer, which is the owner's "test it in the
  browser" gate for the tournament. Replay-gated promotion of the fit-and-score composition.
- **Day 5: spin up a LAB.** A minimal new LAB scaffold ("give me a LAB") in JS with the kernel,
  a receipts JSON writer, and the Tick viewer wired, demonstrated by re-hosting one existing stage
  (ChessLab S0 or the disc-stats experiment) and producing a verified hit on a Part produced by
  another LAB through the shared store; SUBDUE and WebShaper comparison executed on the recorded
  graphs; wheel and returns as before.

Failure criterion for the week, proposed in the owner's absence and open to correction: the week
fails if it ends without a browser page in which a person can see, per Tick, what a Calculation
read and wrote, on receipts produced by both the JS runtime and pyto.

## The shared record contract: `pyto/viewer/RECORD.md` (verbatim)

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

(Note: the "Adapters" table's pyto row already reads "`PcrRun.receipts` — required, so
`PCR.run(pxc, observe=True)`", which is the corrected wording per `pyto/CHANGES.md`'s Day 3 entry —
the observe=False path now raises `ValueError` (`pyto/src/pyto/materialize.py:322-337`) rather than
emitting a document with nulled observed fields.)
