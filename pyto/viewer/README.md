# Tick viewer — Kibana for Ticks

A dependency-free browser page that shows, for one execution, **what each Calculation read and
wrote, per Tick, and the Part value as material**. That is the founding need: "nothing the
algorithm used to find a path was visible" (`../research/origin.md:8-9`), and the shape it must
show is the one that stuck — `PrincipleComponentRender -> Tick[]`, `Tick -> Calculation[]`, "each
Tick is where its Calculations become observable" (`origin.md:20-23`).

In the ELK reading (`../research/ULTRACODE-WEEK.md`, Reframing 4) the PCR *is* the render
definition, so this page is a PCR renderer, not a new dashboard concept. The document it renders is
`pyto-run-record@1`, specified in [`RECORD.md`](RECORD.md); `adapters.js` is that spec's executable
form and speaks it for four runtimes.

No npm packages, no CDN, no build step. Tests run under Node 22 with `node --test`.

## Files

| File | What it is |
|---|---|
| `tick-viewer.html` | the page: styles for both themes, toolbar, and a three-line module that calls `mount(document)` |
| `tick-viewer.js` | render functions (pure, `doc` always explicit) plus `mount` — the file picker, drag and drop, `?src=` and embedded-record wiring |
| `adapters.js` | `validate` plus the four `from*` adapters; no DOM |
| `embed.mjs` | `node embed.mjs record.json > page.html` — one self-contained file |
| `fixtures/*.json` | one document per runtime (see below) |
| `test/*.test.mjs` | 77 tests: schema, hit derivation, render safety, filter, embed |
| `test/record_schema.py` | a Python validator of RECORD.md, written independently of `adapters.js` |
| `test/test_record_schema.py` | 19 tests: every JavaScript adapter's output read back by that validator |
| `test/emit_adapter_records.mjs` | writes each adapter's output to a directory, for the Python suite |
| `test/validate_cases.mjs` | reports `adapters.js` verdicts on candidate records, for the Python suite |

## Opening it

**A file, or a drop.** Open `tick-viewer.html` directly (`file://` works), then pick a JSON file
with the toolbar control, or drag one anywhere onto the page.

**`?src=`.** Serve the directory and pass a same-origin path:

```sh
cd pyto/viewer && python3 -m http.server 8000
# then open
#   http://localhost:8000/tick-viewer.html?src=fixtures/pyto-grouped-ablation.json
#   http://localhost:8000/tick-viewer.html?src=fixtures/wumpus-belief-tick.json
```

`?src=` is same-origin only: a value carrying a scheme (`https:`, `data:`) or starting with `//` is
refused with a message instead of fetched. `file://` pages cannot fetch at all, which the page says
rather than failing silently.

**Embedded.** For a page that needs no server and no sibling files:

```sh
node embed.mjs fixtures/pyto-grouped-ablation.json > /tmp/tick.html   # or --out /tmp/tick.html
```

`embed.mjs` inlines `adapters.js` and `tick-viewer.js` into one module element and puts the record
in `<script type="application/json" id="record">`. It converts and **validates** the input first, so
a malformed record fails at build time, not in someone's browser. It accepts a
`pyto-run-record@1` document or any raw runtime document the adapters understand.

## What you see

- **One section per Tick, in record order**: index, name, invocation count, wall milliseconds (the
  sum of the durations the runtime recorded, or "no durations recorded").
- **One row per invocation**: id · calculation address · short `implementation_sha256` (full hash in
  the tooltip) · a `hit`/`computed` pill · duration; then `into`, the result digest, the identity
  scope, and the args.
- **Reads, declared beside actual.** One row per address with the declared binding and the observed
  read side by side. A divergence is highlighted and named — *declared, never read* or *read, never
  declared*. This is a conformance signal, not a crash: ChessLab's contract calls the two diverging
  "a conformance failure the gateway surfaces rather than silently accepting"
  (`../reference/lab/chesslab-lab/contract.ts:120-126`), and the fixture carries a real one.
  A `fn:` binding is shown as *result of `<invocation id>`*, since it never touches the store.
- **Writes with their kind**: `new-address`, `refinement`, `replacement`, or "kind not recorded".
- **The value as material**: `json` in a collapsible `<pre>`, `text` in a `<pre>`, `svg` through an
  `<img src="data:image/svg+xml;base64,…">`, `png-data-url` through an `<img>`, `omitted` as the
  note that says why.
- **The two caps, applied in RECORD.md's order**: `materialize` (`adapters.js:254`) truncates first
  and measures second, so a long array of small entries survives as its first 200 entries rather
  than being dropped whole. `RECORD.md:113` ("arrays longer than 200 entries carry the first 200 and a note with the
  full length") states the 200-entry cap without qualifying it by depth,
  and `materialize` reads it that way: **every** array in the value is cut, nested ones included, so
  `{"rows": [0..999]}` keeps 200 rows and `{"a": {"b": [[0..299]]}}` keeps 200. One note covers them
  all — `N array(s) truncated to the first 200 entries; original lengths: [...]`, lengths sorted
  descending — which is the wording `../src/pyto/materialize.py:236-239` writes, byte for byte.
  Whether the value is JSON at all is decided on the whole value before anything is cut
  (`materialize.py:229-234`), so a cycle or an unserializable entry past the cap still reaches
  `omitted` instead of being sliced out of sight. A value over 256 KB *after* truncation becomes
  `omitted` carrying its size and digest. `test/adapters.test.mjs` pins all of this against
  expectations generated by `pyto.materialize.render_value` itself; until that fix JS truncated only
  a top-level array, so the same 1000-row Part was 200 rows in pyto and 1000 rows with note `null`
  in the browser (`../experiments/runs/day3/verdicts/adversarial-values.json:12`).
- **A Part index**: every address with the invocation that wrote it, the invocations that read it,
  and whether it preexisted the run. `derivePartIndex` reads an invocation's `inputs` (the complete
  binding map) as well as its `declared_consumes`, because pyto's `Receipt.declared_consumes`
  (`../src/pyto/pcr.py:120`) lists only Part addresses and omits `fn:` result refs; and a `fn:<id>`
  binding counts as a read of the Part that invocation wrote, since `pcr.py:112-116` rewrote a Part
  binding into that ResultRef and the value published at `into` is the same one. That is what makes
  the index answer "which invocations consume `scratch.ablation.split`" with all twelve fit/score
  invocations rather than with none. It never turns an invocation into a hit: only a `px:` binding
  does that.

### Filter

The filter box narrows invocation rows. It follows PQL's own two selectors
(`../src/pyto/pql.py:26-45`):

- `scratch.ablation.model.*` — trailing `*` is a **prefix** match, spelled the way `PQL.prefix`
  describes itself;
- anything else is a case-insensitive **substring**.

An invocation matches on its id, its Tick name, its calculation address, its `into`, its declared
and actual reads, and its write addresses. Ticks left with no rows disappear; the header reports
"filter …: N of M invocations, K of L ticks". The Part index is not filtered.

### Safety rules the tests hold

- Every node is built with `createElement` + `textContent`. `innerHTML` is never given record data,
  and nothing is `eval`'d.
- An `svg` value is **never** inlined as markup. It becomes the `src` of an `<img>`, so a value
  containing `<script>` or `onload=` produces no script element and no handler —
  `test/render.test.mjs` asserts a zero script count over a whole record of hostile SVG and checks
  the bytes survive the base64 round trip unchanged.
- Layout never scrolls sideways: wide tables and `<pre>` blocks scroll inside their own container.
- Both themes come from `prefers-color-scheme`; every colour is a token defined in both.

## Adapters

Each `from*` function returns a `pyto-run-record@1` and runs it through `validate`, which throws a
`RecordSchemaError` naming the offending path (`ticks[1].invocations[0].writes[0].kind: expected one
of "new-address", "refinement", "replacement", got "clobber"`).

```js
import { fromPytoRecord, fromDiscStudioReceipt, fromChessLabReceipts, fromWumpusRecords, validate } from './adapters.js';
```

| Adapter | Source | Notes |
|---|---|---|
| `fromPytoRecord(doc)` | `pyto.materialize.run_record` output (object or JSON text) | validating pass-through; the viewer never repairs a producer's record |
| `fromDiscStudioReceipt(pqlRun, receipt)` | `px.pql.<name>` + `px.receipt.<name>` from `../../src/runtime.js` | see below |
| `fromChessLabReceipts(receipts)` | `Receipt[]` per `../reference/lab/chesslab-lab/contract.ts:127-141` | values `omitted` — `Receipt` has no value field |
| `fromWumpusRecords(records)` | `executeTick` records, `../reference/lab/wumpus-core/execute.js:19-37` | values present, from each calculation's captured output |

**Hits.** One rule for all four, from `RECORD.md`: an invocation is a hit when it read a Part that
existed before this run (a `px:` binding whose address was not produced by an earlier invocation of
the same record), **or** when the runtime reports reuse. The owner's definition is deliberately
broad — "a hit is any Part or Calculation being used; do not over-define it"
(`../research/ULTRACODE-WEEK.md`, Reframing 4). For DiscStudio that means `trace[].reused === true`
from the memo ring (`../../src/runtime.js:17-19`) *or* a read of a Part seeded before `execute`.

**DiscStudio specifics.** `runtime.js` does not use `trackAccess`, so:

- there are no durations (`duration_ms` is `null`) and no function-body hash
  (`implementation_sha256` is `null`) — memo identity is `{ revision, inputs }` (`runtime.js:15`),
  so the identity scope is reported as `registered-address-and-revision:<n>`;
- `result_sha256` carries the memo **material id** (`card.svg:406fa5de`), which is what that runtime
  content-addresses by;
- `writes[].kind` is derived with `exec.js:28`'s rule over what the record can see — *refinement*
  when the invocation also reads the address, *replacement* when an earlier invocation in the same
  record wrote it, *new-address* otherwise. The store's state before the run is not in the receipt,
  so the first write of an address in a run cannot be distinguished from a replacement of a Part
  that predated it;
- an invocation id is its `into` address (deduplicated with `#2` if ever repeated), because
  DiscStudio's PQL has no invocation ids;
- `presentation.js:69`'s `{ svg, width, height }` card wrapper is rendered as the SVG it is, with
  the dimensions kept in the value note.

**ChessLab and Wumpus specifics.** Both record access at Tick granularity, and both can bind more
than one Calculation per Tick. Each such Calculation becomes one invocation (`opId#0`, `opId#1`),
and every invocation of a Tick repeats that Tick's reads and writes — the record cannot say which of
them performed which read. A ChessLab receipt with an empty `frozenCalculations` yields one
invocation with a `null` address rather than an invented one.

## Fixtures

| File | Produced by |
|---|---|
| `pyto-grouped-ablation.json` | the file `pyto.materialize.run_record` wrote for grouped-ablation run-1, copied byte for byte from `../experiments/grouped-ablation/evidence/run-1/record.json`. `test/adapters.test.mjs` compares the two files, so the fixture cannot drift from the producer. 15 invocations over 4 Ticks; every value is `json`, because that is what the run materializes. |
| `pyto-value-kinds.json` | synthetic, and named as one: the same PCR shape carrying all five value kinds (`svg`, `png-data-url`, `text`, `omitted`, `json`) so the render and schema rules for the four kinds run-1 never produces are still exercised. Never presented as a record of a real run — its `pcr` is `ablation.grouped.value-kinds`. |
| `discstudio-display-card.json` | an actual node run of `../../src/runtime.js`: `createStudioRuntime(createSeed()).card('buzzz-mint','broadcast',ctx)` twice. `first` = everything computed, `second` = everything served from the memo ring. `test/adapters.test.mjs` re-runs the live runtime and asserts the adapter agrees with the fixture, so it cannot drift. |
| `chesslab-s0-s1.json` | hand-written to `contract.ts` and `host.ts:28-36`, with the S0/S1 slots and the declared/actual divergence from `debugger.test.ts:135-147`. |
| `wumpus-belief-tick.json` | an actual node run of `../reference/lab/wumpus-core/execute.js`: three `executeTick` calls (Sense, Believe, Render) on one board, the last producing an SVG belief grid. |

The two runtime-shaped fixtures (`{first, second}` / `{pql, receipt}`, `{receipts}`, `{records}`)
are raw runtime documents, not records — the page converts them on load through `coerceToRecord`,
which is also what `embed.mjs` uses.

## Tests

```sh
cd pyto/viewer && node --test test/*.test.mjs              # 77 tests, the "viewer" suite
cd pyto/viewer && python3 -m unittest discover -s test     # 19 tests, "viewer-record-schema"
bash ../scripts/check_all.sh                               # runs both as named suites
```

`test/render.test.mjs` uses a ~20-line document shim (`createElement` returns plain objects) and
walks the resulting tree. There is no jsdom and no dependency of any kind.

### The record is checked from both sides

RECORD.md is a contract between two runtimes, and a contract checked only by the side that wrote it
is not checked at all. So the round trip runs in both directions:

- **Python → JavaScript.** `test/adapters.test.mjs` loads the real `record.json` the Python
  materializer wrote, validates it, re-derives its `parts` index and its `hit` flags with
  `adapters.js`, and renders it through the document shim.
- **JavaScript → Python.** `test/emit_adapter_records.mjs` writes every adapter's output;
  `test/test_record_schema.py` reads them back through `record_schema.py`, a Python validator
  transcribed from RECORD.md clause by clause and deliberately not sharing code with `adapters.js`.
  Its key sets are *exact*: a field either side invents or omits fails there. The same suite feeds a
  list of mutated records to both validators and asserts they refuse the same ones at the same
  paths.

Two known differences are pinned by that suite rather than left to be discovered:

- `adapters.js` reads the fields it needs and lets an unknown one through; the Python validator
  rejects it. An invented field is caught on the Python side, which is why the round trip exists.
- A record re-serialized by JavaScript is equal to Python's file as parsed JSON but not always as
  bytes: JSON has one number type, so an integral float inside a value payload is `0.0` from Python
  and `0` from JavaScript. RECORD.md fixes sorted keys and two-space indentation, not the spelling
  of a number — so nothing may key a digest on the record file itself.
