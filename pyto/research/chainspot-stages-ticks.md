# What the ChainSpot LAB says a Tick is

Read on 2026-09-10 by a Sonnet agent from a read-only clone of `samuelpmahan/ChainSpot`, on the
lab tips the branch mining named (`research/chainspot-branch-mining.md`); the default branch has
none of it. Every claim cites `<sha>:<path>:<line>`. The owner's sentence that framed the reading:
"a Tick is when its Sequence of Calculations becomes Inspectable. It is our MINIMAL COMPARATIVE
UNIT." Nothing below is the owner's; it is the code, read.

## 1. Stages, and where a Stage's composition is written

- S0 = intake, "produce one cropped image for S1" (`43e6ea3:packages/alg/src/stages/S0/clean/S0.stage.yaml:6-7`).
- S1 = badge assembly and reading, candidate plate and digit glyphs (`43e6ea3:packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml:38`).
- S2 = basket detection (`43e6ea3:packages/alg/src/stages/S2/candidate/Basket.ts`).
- S3 = visible-Tee detection, "Construct visible Tee objects from exact accepted bright-component pixels" (`6309ff1:packages/alg/src/stages/S3/clean/index.ts:50`).

Production composition is YAML: `43e6ea3:packages/alg/src/stages/S0/clean/S0.pcr.yaml` and the S1
`PrincipleComponentRender.yaml` above. A Mermaid-authored source compiles to that YAML
(`b5a6ae0:packages/alg/src/stages/S0/exp/mermaid-pcr/compiler.ts:44`, from
`b5a6ae0:experiments/mermaid-s0-s1/S0.mmd`). A Python composition mirrors it for offline
investigation (`6309ff1:packages/quick_anno_py/chainspot_quick_anno/pcr.py:29`).

S0's Ticks in order (`43e6ea3:packages/alg/src/stages/S0/clean/S0.stage.yaml:7-11`):
`page_load_create_PxC` → `decode_selected_image_to_FullImage` → `crop_udisc_chrome_to_CroppedImage`
→ `cache_FullImage_last`. S1-exp's Ticks in order: `BlackMask`, `WhiteMask`, `BadgeAssembly`
(`43e6ea3:.../PrincipleComponentRender.yaml:3,20,38`).

## 2. Inside a Tick: chains; across Ticks: Parts

Tick `BlackMask` (`43e6ea3:.../PrincipleComponentRender.yaml:3-19`): `fn.s1.exp.maskComponents.selectHsvMask`
reads `px.s1.exp.maskComponents.part.croppedRaster` and writes `px.s1.exp.maskComponents.part.blackMask`;
then `fn.s1.exp.maskComponents.group8Connected` reads that same `blackMask` and writes
`blackComponents`. The output of line 12 feeds the input of line 15: a chain inside one Tick.

Tick `BadgeAssembly` (lines 38-86) chains five Calculations, `selectComponents → findRelated →
findRelated → findRelated → assemble`, each `into:` feeding the next `with:`. Its
`selectComponents` reads `px.s1.exp.maskComponents.part.blackComponents` (line 45) and `findRelated`
reads `...part.whiteComponents` (line 58): outputs of the earlier `BlackMask` and `WhiteMask`
Ticks, a dependency crossing a Tick boundary by Part.

The Python analogue, S3 (`6309ff1:experiments/quick-anno-python/s3.py:83-92`): Tick `AccountRings`
writes `Part('scratch.s3.ringLedger')`; Tick `CheckBalance` reads it as `ledger`. The checkpoint
says it: "S3 is the first Stage with something to compose, so the PCR has two Ticks and the second
consumes the first's published Part by result" (`6309ff1:experiments/quick-anno-python/S3_CHECKPOINT.md:84-85`).

So in the LAB a Tick is a sequence of dependent Calculations run in order, and a Stage is Ticks in
order joined by Parts. This is the reading pyto took back on 2026-09-10 (`questions.md`,
ChainsInsideATick) after the sprint had refused it (task 39); the LAB never held the other rule.

## 3. What becomes inspectable at a Tick boundary, and what "comparative" means

`TickInspection.svelte` renders, per Tick: the exact PxC inputs (`tick.actualConsumes`,
`43e6ea3:src/lib/evidence-workbench/TickInspection.svelte:62`), the Calculation identities
(`frozenCalculations`, address plus the SHA-256 of the function body, line 73), the exact PxC
outputs (`tick.writes`, line 86), the Materializations emitted (line 101), and a "Residue/UNKNOWN"
section (line 123); hosted by `PcrInspectionHost.svelte:86`.

Comparison in the code:

- `b5a6ae0:packages/alg/src/stages/S0/exp/mermaid-pcr/compare.ts:73-110`, `compareMermaidS0Runs(legacy, generated)`:
  the legacy hand-written S0 against the Mermaid-generated S0, Tick by Tick, on canonical pixel
  bytes, badges, crop bounds, named calls and decode-count parity ("proof.ts independently executes
  legacy S0 and existing S1 YAML for comparison. It checks canonical bytes, crop proposal, decode
  count, direct reference identity...", `b5a6ae0:.../mermaid-pcr/README.md:41-42`).
- The Python neon sheet (`6309ff1:experiments/quick-anno-python/S3_CHECKPOINT.md:95-104`): nine
  panels comparing production's own receipt counts against the Python-derived ledger, plus
  per-object identity crops (panels 8-9), which caught three false Tee objects (Apple Maps chrome)
  and one wrongly voted-out real pad. Same run, two representations.

No comparison across courses or golden files was found on these tips. The comparative unit in the
code is the Tick's testimony: what it consumed, what it produced, which frozen Calculations ran,
compared between two implementations or two representations of the same Stage.

## 4. Runtime at the boundary

`43e6ea3:packages/alg/src/exec/gateway.ts:133-169` (async twin 185-215): one `Receipt` published
per Tick, sequentially, `for (const op of plan.ops) { ...; sink.putReceipt(receipt); }`. No
transaction and no rollback: the board is a mutable `Map` mutated in place each Tick
(`43e6ea3:packages/alg/src/exec/board.ts:52-60`); `fork()` is a snapshot for slicing and root
mounting (`board.ts:57`, `mounts.ts:29-41`), never used by the gateway for undo. No parallelism:
"Synchronous by design" (`gateway.ts:8`); the async variant "awaits asynchronous operations in list
order" (line 183). The receipt shape (`43e6ea3:packages/alg/src/exec/contract.ts:127-139`): `opId,
frozenCalculations[], startedAtMs, durationMs, declaredConsumes, declaredProduces, actualConsumes,
actualProduces, writes[]` (each write a `PxWriteTestimony`: new-address, refinement or
replacement), `probes[], artifacts[]`; and `TickTestimony = Receipt` (`contract.ts:144-148`).

Against pyto: pyto files one receipt per Calculation and keeps the Tick as the unit of order and
publication; the LAB files one receipt per Tick with the Calculations frozen inside it. That is the
`{?} TickEqualsReceipt` on the root, now with the LAB's side of it cited.

## 5. tidy's manifest

No `.tidy/manifest.json` exists on any of the four tips. All four carry `tidy.manifest.yaml` at the
repository root naming S0 to S3 with `version`, `clean` and `hash`
(`43e6ea3:tidy.manifest.yaml:2-5`: `S0: {version: 0.1.0, clean: packages/alg/src/stages/S0/clean,
hash: sha256:be3fcb...}`, the same shape for S1 to S3), with `tests/unit/tidy.test.ts`,
`scripts/tidy.mjs` and `tidy` beside it. The tidy scout (`research/tidy-delivery-freeze.md`) read
the standalone tidy repository, where the manifest is `.tidy/manifest.json` with no hashes; the LAB's
manifest carries a content hash per stage. The two are different tidies, or two versions of one.

## What this changes on the record

- ChainsInsideATick is confirmed by the oldest program: chains inside Ticks, Parts across them.
- "Minimal comparative unit" has a concrete referent: the Tick's testimony compared between two
  implementations of the same Stage (compare.ts) or two representations of the same run (the neon
  sheet). `px diff` over two records and `fn.neat.diff.candidates` are the same act in pyto.
- TickEqualsReceipt is a real difference between the LAB and pyto, not a naming choice.
- The tidy scout's manifest claim needs the LAB's `tidy.manifest.yaml` beside it.
