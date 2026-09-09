# Day 3 completeness critic

Source list: `research/ULTRACODE-WEEK.md` Reframing 4's "Day 3: Kibana for Ticks" bullet
(plan lines 107-114), which supersedes the original Day 3 goal/deliverables paragraph (plan
lines 228-250: kernel-ablation, conventional-comparison, promotion — explicitly moved to Day 4's
second half by Reframing 4's last sentence, so their absence below is not a gap); the founding
need (`research/origin.md`) and `research/tick-observability-ledger.md` sections 3-4 (what the
materializer and the annotation anchor needed); the shared contract `pyto/viewer/RECORD.md`.
Compared against the working tree at HEAD and the three final-round lens verdicts in `verdicts/`.
This file lists deliverables not present, kill criteria that fired, and check_all state — kept as
open items, not dropped, per the Day 1/Day 2 completeness-critic precedent.

## Deliverables from Reframing 4's Day 3 bullet: present / absent

| deliverable | status | evidence |
| --- | --- | --- |
| Dependency-free browser page `pyto/viewer/tick-viewer.html`, Node 22 tests, no build | present | `pyto/viewer/tick-viewer.html` (no `<script src>` to any external host, no npm/CDN reference); `node --test test/*.test.mjs` runs under plain Node 22 (`node --version` = v22.22.2 in this environment), 83 tests, no build step. |
| Loads a PcrRun-with-receipts JSON and shows, per Tick, each Calculation with what it read, what it wrote, duration, result digest, hit or computed, and the Part values | present | `pyto/viewer/tick-viewer.js:306` `renderRecord`; per-invocation rows carry `inputs`/`declared_consumes` (reads), `writes`, `duration_ms`, `result_sha256`, `hit`, and the rendered `value` (text/JSON/SVG-as-`<img>`/png-data-url). Verified independently against the real record in the schema-round-trip lens (4 Tick sections, 15 invocation rows, 2 hits). See the schema-round-trip lens's blocker: `declared_consumes` itself does not carry every read RECORD.md says it should (13/15 invocations), so the viewer's reads column is complete only because it separately unions `inputs` (adapters.js:327-331) — the record's own `declared_consumes` field alone would under-report. |
| Same page reads DiscStudio's `px.receipt.<name>` records and ChessLab-shaped receipts | present | `pyto/viewer/adapters.js:449` `fromDiscStudioReceipt`, `:536` `fromChessLabReceipts`; a fourth, unplanned adapter is also present, `:592` `fromWumpusRecords` (Wumpus is not named in this bullet but RECORD.md's Adapters table documents it and the ledger's row 15/16 motivate it). Six fixtures exist under `viewer/fixtures/` covering all four `source.runtime` values; `viewer/test/emit_adapter_records.mjs` + `viewer/test/record_schema.py` round-trip every one through the independent Python validator. |
| Python side: a Tick materializer that emits that JSON from a `PcrRun` | present | `pyto/src/pyto/materialize.py` (new module, 661 lines; `run_record()` at materialize.py:281). Hard rule honored: `git diff 83422cf -- pyto/src/pyto/pcr.py pyto/src/pyto/core.py pyto/src/pyto/graph.py pyto/src/pyto/pql.py`, once line endings are normalized on both sides, shows **zero** real content change in core.py/graph.py/pql.py and exactly one two-line change in pcr.py (`_implementation_sha256` now normalizes CRLF to LF before hashing) — inherited from a separate, already-committed "Windows-safe by construction" line of work (commit `5915f9e`), not this day's own edit. `materialize.py` is the only Day-3 library addition, as the hard rule requires. |
| ... neon sheets for image Parts | present | `materialize.py` `tick_sheets()` (materialize.py:604 area) composites per-Tick PNGs through `pyto.neon`; `evidence/run-1/ticks/*.png` + `*.svg` exist on disk (`materialize_run.py`, run this record stage via `embed.mjs` against the same `record.json`). |
| The content-addressed materials store with hit counters, ported from ChainSpot, experiment-local | present | `pyto/experiments/grouped-ablation/materials.py` (250 lines, `MaterialsStore`, `material()`, `canonical()`/`sha()` transcribed from `reference/lab/chainspot-matrix/matrix/materials.ts:158-163,263-317`), `hits.py` (115 lines), `run_cached.py` (323 lines, the calling convention), `test_materials.py` (350 lines). Counters are `requests`/`hits`/`misses`/`writes`, matching `MatrixMaterialCounters`. Default root `~/.pyto/materials`, overridable by `PYTO_MATERIALS_DIR` — recorded as `{?} MaterialsLocation` per this record stage's questions.md addition. Stays experiment-local (`pyto/questions.md` `{?} PromotionScope`), as the week's refusals require. |
| Kernel ablation and the conventional cache comparison | **correctly absent — moved to Day 4** | Reframing 4's Day 3 bullet's last sentence: "Kernel ablation and the conventional cache comparison move to Day 4's second half." `pyto/experiments/kernel-ablation/`, `pyto/experiments/conventional-comparison/` and `pyto/experiments/promotion/` do not exist in the tree (`ls` returns nothing for all three); this is the plan working as re-written, not a gap. |

## Adjacent items named by the founding-need docs, checked for completeness

These are not bullet points of Reframing 4's Day 3 line itself, but are the motivating
material this record stage was pointed at (`research/origin.md`, `tick-observability-ledger.md`
§§3-4); listed here so the root stays complete rather than silently assumed satisfied.

| item | status | evidence |
| --- | --- | --- |
| §3's concrete missing-piece list (function consuming a `PcrRun`; Tick↔receipt join; a value channel; a Part-kind dispatch; a stable per-run Tick id; an entry point) | present, all six | `materialize.py`'s `run_record()` closes over `run.ticks`, `run.receipts`, `run.results` and the pre-run `PxC.addresses()` in one function (item 1); ticks are joined to receipts by invocation id inside that same function (item 2); `value.kind`/`value.data` is the new channel RECORD.md defines, not a widened `Receipt` (item 3, honoring pcr.py's byte-identity freeze); dispatch to `neon.panel`/`neon.crops` vs `json.dumps` happens by runtime type-sniffing the Python value, not a declared kind on `Part` (item 4 — `Part` itself is still kind-less, per `{?} StorageKinds`, unchanged this day); each Tick gets its `index` field in the record (item 5); `materialize_run.py` is the entry point (item 6). |
| §4's annotation anchor `(pcr, tick.name, invocation.id, part.address)` | anchor present; no annotation-writing UI built | `materialize.py:24` cites the anchor directly in its module docstring; `adapters.js:140` enforces invocation-id uniqueness ("ids anchor annotations and must be unique in a record") as a validation rule. No code writes or reads a note keyed to this anchor — §4 describes this as "what the grid convention gets right and stops short of" and proposes the extension, it does not list a Day 3 deliverable requiring it built, and Reframing 4's Day 3 bullet does not ask for it either. Recorded here as unbuilt-but-anchored, not as a gap against a stated deliverable. |

## Kill criteria checked

Reframing 4 does not add new Day-3-specific kill criteria beyond the plan's existing "Any day"
rules (research/ULTRACODE-WEEK.md "Kill criteria" section, lines 311-327).

- **"A library change that breaks any of the 18 consumer tests, disc-stats 4, examples..., or the
  Day 1 tests is reverted the same day"** — checked: `consumer` 61 OK, `disc-stats` 4 OK,
  `examples` 3 OK, all unchanged from their Day 2 counts. **Did not fire.**
- **"One seam per day, no compensating second change"** — checked and held: `materialize.py` is
  the one new module under `pyto/src`; no second file under `pyto/src` carries a real (non-EOL)
  change this day (see the table row above).
- **"A proposed change that ... edits the JS app (`src/*.js`, `index.html`) ... is out of scope"**
  — checked: `git diff 83422cf -- src index.html` outside `pyto/` is empty (this record stage's
  own `git diff` command is scoped to `-- pyto`, and the surrounding hard rules for this task
  independently forbid touching those paths; confirmed untouched).

## check_all.sh: currently RED, and why, isolated from Day 3's own work

`bash pyto/scripts/check_all.sh` exits 1: `experiments/grouped-ablation` reports **183** tests
with 25 failures and 7 errors (expected pin: 230, `scripts/check_all.sh` `EXPECT_*`). Every other
suite is green, including the two Day-3-owned suites (`library` 103, `viewer` 83,
`viewer-record-schema` 19).

**Root cause, isolated.** `experiments/grouped-ablation/test_replay.py`'s fresh-process /
tamper / determinism / hidden-state test classes all call
`replay.ensure_retained_record()`, which rebuilds `evidence/run-1/retained.json` fresh and
compares it byte-for-byte against the committed file. The rebuild now disagrees on exactly one
sub-object:

```
"provider": {"pyto": {"modules": {
  "core.py": "32a03183...c120"  (committed)  vs  "8133f980...fae" (fresh)
  "pcr.py":  "64cd374a...oacf"  (committed)  vs  "50accca6...2878" (fresh)
```

`retain._module_source_sha256` (`retain.py:396-407`) hashes the raw bytes of
`pyto/src/pyto/core.py`/`pcr.py` on disk. Those two files were renormalized from CRLF to LF (and
`pcr.py`'s `_implementation_sha256` gained a two-line CRLF-normalization fix) by the
already-committed `5915f9e` ("Windows-safe by construction: LF attribute for pyto, kernel files
renormalized, implementation digest ignores CRLF") — a real, intentional, already-landed change,
just not one this record stage made or that Day 3's brief asked for. Nobody has since run
`python3 experiments/grouped-ablation/replay.py --force` (the fix the tool's own `AssertionError`
message names) to bring the Day 2 evidence tree's recorded module hashes forward to match.
Verified in isolation: reverting `pyto/src/pyto/{__init__,core,graph,neon,pcr,pql}.py` and
`pyto/tests/test_{graph,receipts}.py` to their exact `HEAD` blobs (byte-for-byte, via
`git show HEAD:<path>`) and rerunning `check_all.sh` reproduces the identical 183/230 failure —
so this is not a working-tree artifact of this session, it is the committed state of the shared
branch at the time this record was taken.

**Why this record stage did not fix it.** `python3 experiments/grouped-ablation/replay.py
--force` would rewrite committed evidence across `run-1` through `run-4-from-retained` and the
disc-stats sidecar — files this day's hard rule does not license touching (Day 3's scope is
`pyto/src/pyto/materialize.py` and the viewer; the replay/evidence regeneration surface belongs
to Day 2's lane and to whichever session lands `5915f9e`'s follow-through). It also does not
touch `pcr.py`/`core.py`/`pql.py`/`graph.py` themselves, so fixing it would not violate the "do
not modify" hard rule, but regenerating four evidence directories' worth of committed digests is
a materially larger and more consequential action than a record-stage agent should take
unasked, on a branch multiple lines of work are landing to concurrently. Recorded as the
day's principal **blocker for committing** below rather than silently patched.

## Suite counts (from `tests.txt` in this directory, `bash pyto/scripts/check_all.sh`, this run)

| suite | tests | status |
| --- | --- | --- |
| library | 103 | OK |
| experiments/grouped-ablation | 183 (expected 230) | **FAIL** |
| experiments/s3-synthetic | 5 | OK |
| consumer | 61 | OK |
| disc-stats | 4 | OK |
| examples | 3 scripts | OK |
| art-registry-md | - | OK (regenerated, matches committed ART-REGISTRY.md) |
| viewer | 83 | OK |
| viewer-record-schema | 19 | OK |

`SOME SUITES FAILED` (`bash scripts/check_all.sh`, exit 1). The two suites this day actually owns
(`library`, at its pinned 103; `viewer` + `viewer-record-schema`, both at their pinned counts) are
green; the one red suite (`experiments/grouped-ablation`) is red for a Day-2-evidence /
cross-cutting-EOL reason unrelated to `materialize.py` or the viewer, isolated above.

## Blockers for committing

1. **`bash pyto/scripts/check_all.sh` exits non-zero.** Isolated to
   `experiments/grouped-ablation`'s replay/tamper/determinism suite, caused by evidence
   (`evidence/run-{1,2-regroup,3-reinput,4-from-retained}/retained.json`,
   `evidence/disc-stats-sidecar.json`) whose recorded `provider.pyto.modules` hashes predate the
   already-committed CRLF→LF renormalization of `core.py`/`pcr.py`. Not caused by this day's
   `materialize.py` or viewer work (both suites pass at their pinned counts). Fix is
   `python3 experiments/grouped-ablation/replay.py --force` re-run once, by whoever owns that
   evidence tree, followed by a `check_all.sh` re-run to confirm 230 again — deliberately left to
   the orchestrator/owner rather than done here, per the scope note above.
2. **The schema-round-trip and day3-verify lenses both found the same blocker**: `RECORD.md:52-54`
   states `declared_consumes` repeats every `inputs` binding in order, but pyto's own emitted
   record leaves it empty for every invocation whose binding is an `fn:` result ref (13 of 15
   invocations in `evidence/run-1/record.json`). This is a documentation/contract bug, not a
   behavior bug (both adapters already work around it correctly), but it means the contract file
   the hard rules say "both runtimes must speak exactly" currently describes neither runtime's
   real behavior for `fn:` bindings. See `verdicts/schema-round-trip.json` and
   `verdicts/day3-verify.json` for the two independently-arrived-at required fixes (they agree:
   amend RECORD.md rather than pcr.py, since pcr.py is the file this day may not touch).
3. **The adversarial-values lens found one real cross-runtime record-shape divergence**
   (RECORD.md:64's array-truncation rule: pyto truncates nested arrays, `adapters.js` truncates
   only the top level) and one honest-but-misleading ledger claim outside the viewer/materialize
   surface (`run_cached.py`'s `"hit (disk)"` string is asserted, not derived from the store's own
   counters). Neither blocks a commit of `materialize.py`/the viewer themselves, but both are
   contract- or ledger-integrity findings the owner should see before the materials store or
   RECORD.md's array rule get relied on elsewhere. See `verdicts/adversarial-values.json`.

None of items 2-3 touch `pcr.py`/`core.py`/`pql.py`/`graph.py`; all required fixes they name are
either to `RECORD.md` (data, not code) or to `materialize.py`/`adapters.js`/`run_cached.py`
(files this day's hard rule permits). Item 1 is the only blocker that keeps `check_all.sh` from
being green, and it is upstream of Day 3's own deliverables.
