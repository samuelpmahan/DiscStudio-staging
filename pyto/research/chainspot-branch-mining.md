<!-- Produced by the branch-mining workflow (wf_814798ac-137) on 2026-09-09: sixteen agents. Eleven
tips were mined; the synthesis below covers eight of them and names the rest as missing coverage
(three mined tips reached it too late to be folded in: f3ecab3, 116c984, 5433854; four agents failed
to return valid JSON after five tries: fa44a45, 52417a9, b9d05cd, 881c7e5). Per-tip findings as
returned are retained in chainspot-branch-mining.json. Nothing below is edited. -->

# ChainSpot branch mining — eight tips, read for pyto's round five

Mined 2026-09-09 against the read-only shallow clone at `/home/user/samuelpmahan/chainspot`. Every claim cites `<sha>:<path>:<line>`. Where a thing the brief asked about does not exist in a tip, it is recorded as **missing**, not inferred.

One structural fact first, because it changes how every citation below should be read: `packages/alg/src/exec/contract.ts` is **byte-identical (blob `62b5d75`) across all eight tips** — `5607611`, `8cdddec`, `43e6ea3`, `b5a6ae0`, `82f8fc9`, `5c87d48`, `6309ff1`, `19b9b92`. So is `src/lib/evidence-workbench/PcrInspectionHost.svelte` (blob `30ffdf2`) and `TickInspection.svelte` (blob `0bf6b00`). The production receipt shape, the artifact-kind union and the per-Tick viewer are **not branch experiments**; they are the stable substrate every branch was authored on top of. The branches are the moving parts around a fixed contract.

---

## 1. The tips

| sha | branches | what it is | date (author, local) | what it settled |
|---|---|---|---|---|
| `5607611` | `review/pxc-root-alignment-5607611`, `review/s1-pcr-5607611` | Checkpoint of the S1 YAML PCR composition, calculation variants and JS inspection. Base of the mounts tip: `git diff --name-status 5607611 43e6ea3` is exactly 8 added files, +395 lines, nothing modified except `packages/alg/src/exec/index.ts`. | 2026-09-06 21:01:21 | The **authored PCR file format**: `PrincipleComponentRender: S1` / `Ticks:` / per-Calculation `call` + `with` + `args` + `into` (`5607611:packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml:1-12`). Also settled that `px.*` Part addresses nest **stage → experiment → `part` → name** for scratch material (`…:7,12,19`). **Missing:** despite the branch name, no file in this tip contains a root/mount/alignment rule — `grep -i root` over its `*.md` returns only unrelated hits. The "alignment" is the YAML/JS composition agreeing, not an address-root decision. |
| `8cdddec` | `archive/duckdb-s1-38ca7ab` | Archive commit preserving the exact tree of local checkpoint `38ca7ab` (original tree `3afb0ae`): DuckDB-Wasm over a completed S1 PQL run, plus the Part inspector it drove. | 2026-09-06 22:42:06 | **Storage is judged by cold start, not query speed.** Commit message: *"Archived at Sam's request after the measured 5.79-second browser startup exceeded the five-second CV target. No replacement backend or further implementation is included."* (`git log -1 --format=%B 8cdddec`). Also settled the facade boundary and the reserved `px.view.*` segment (below). |
| `43e6ea3` | `lab/pxc-root-mounts` | The mounts model: `PxCRootMounts` + a warm-all-courses script + CI workflow + a same-number badge projection + a residue drilldown. | 2026-09-06 23:27:11 | **The root is external to the address space.** This is the single most load-bearing addressing decision in the whole clone. |
| `b5a6ae0` | `lab/s0-viewer`, `review/s0-s1-mermaid-b5a6ae0` | Two things at one tip: (a) Mermaid *as the authored PCR source*, compiled to YAML, with an isolated interpreter and a legacy-comparison proof; (b) the S0 viewer's build-time snapshot materializer. Explicitly **unrun**: *"Checkpoint state: written, unrun, unrendered. No parity or visual acceptance claim."* (`b5a6ae0:experiments/mermaid-s0-s1/HANDOFF.md:4`). | 2026-09-07 02:47:36 | **`px.` and `fn.` are the only legal roots, enforced by a parser at authoring time**, not just at construction time. And: the viewer never re-runs the stage; it reads a frozen snapshot. |
| `82f8fc9` | `task/quick-anno-s1-materialization` | First quick_anno Python checkpoint: `chainspot_quick_anno` core + S1 Badge-ownership transfer + 7-panel neon sheet. | 2026-09-07 03:59:49 | The **10-step delegate checklist** (`82f8fc9:experiments/quick-anno-python/S1_CHECKPOINT.md:109-122`) and **neon-first** as an acceptance rule (`…:101`). |
| `5c87d48` | `task/quick-anno-s2-materialization` | S2 Basket-family transfer; second use of the same pattern. | 2026-09-07 04:03:56 | *"S3 should be mostly mechanical for a Luna"* (`5c87d48:experiments/quick-anno-python/S2_VALIDATION.md:76`) — the pattern is a transfer procedure, not a one-off. Single-writer-per-address enforced (`5c87d48:packages/quick_anno_py/chainspot_quick_anno/pcr.py:119-123`). |
| `6309ff1` | `claude/lab-python-p8x0cf` | S3 visible-Tee transfer; first Tick-to-Tick composition; `neon.crops` added; `investigation.py` spine extracted. | 2026-09-07 10:10:14 UTC | **Identity precedes geometry**: *"a full-course panel proves where an object was accepted, never what it is"* (`6309ff1:packages/quick_anno_py/chainspot_quick_anno/neon.py:113-116`). And *"A count that matches expectation is not evidence, and a bounding box is not an identity"* (`6309ff1:experiments/quick-anno-python/DEV6_S3_SURVEY.md:174-175`). |
| `19b9b92` | `task/quick-anno-s3-materialization` | S3 materialization checkpoint with the survey folded in; the `graph.Pcr` authoring surface emitting literal PCR JSON keys. | 2026-09-07 13:56:47 | The **portable PCR export shape** as literal JSON keys: `{"PrincipleComponentRender": name, "Ticks": [...]}` (`19b9b92:packages/quick_anno_py/chainspot_quick_anno/graph.py:111`). And that a materialization can **refuse** a production result: 3 of 18 accepted Tee objects are iOS map-chrome false positives (`19b9b92:experiments/quick-anno-python/S3_VALIDATION.md`, `### HUH` heading). |

**Not mined (recorded as missing coverage):** `task/quick-anno-python-proof` `f3ecab3` (2026-09-07 03:33), `review/s1-ownership-fa44a45` `fa44a45` (the base the Mermaid proof names, `b5a6ae0:experiments/mermaid-s0-s1/HANDOFF.md:3`), `investigate/s1-badge-pixels-5607611` `52417a9`, `review/s1-digit-experimentation-116c984` `116c984`, `lab/arc-stage-seams-20260905` `5433854`, `lab/dashs-ternary-edge-pattern` `b9d05cd`, `lab/stage-aware-dev4` `881c7e5`.

**On `git diff --stat main <sha>`:** `main` is `b1f4c83` (2026-08-28, "Remove accidental connector scratch file") and every tip is a grafted root in this shallow fetch — `git show -s --format=%P` is empty for all eight and `git merge-base main <sha>` fails. So diffs against `main` are whole-tree comparisons and are not semantic. The one usable diff in the set is `5607611 → 43e6ea3`, which is a true parent-child pair.

---

## 2. ADDRESSING

### 2a. What the root-mounts tip decided, quoted

The decision is stated as a doc comment on the type itself:

> ```
> /**
>  * A root mounted above an ordinary PxC. The root is intentionally external
>  * to PxC's semantic address space: values remain px.* and calculations remain
>  * fn.* inside every mounted world.
>  */
> export type PxCRootId = string;
> ```
> — `43e6ea3:packages/alg/src/exec/mounts.ts:3-8`

The API is six methods and no rewriting:

> `/** Mount one already-materialized world beneath a root id (currently ImgID). */ mount(root, pxc)` … `/** Return the exact PxC mounted at root; no address rewriting occurs. */ get(root)` … `/** Stable insertion-order roots for wide/grouped projection. */ roots()` … `/** Make a cheap root-level slice; mounted PxCs themselves are shared. */ slice(roots)`
> — `43e6ea3:packages/alg/src/exec/mounts.ts:11-22`

The test asserts the *negative* — that the root never becomes a prefix:

> ```
> it('keeps ImgID outside the PxC address space', () => {
>   …
>   roots.mount('DashsTrack', dash);
>   roots.mount('NorthPark', north);
>   expect(roots.get('DashsTrack').get('px.s1.badges')).toEqual(['dash']);
>   expect(dash.has('px.DashsTrack.s1.badges')).toBe(false);
> ```
> — `43e6ea3:tests/unit/pxcRootMounts.test.ts:6-18`

Mounting is idempotent-or-loud, never silent:

> `if (current && current !== pxc) { throw new Error(\`PxC mounts: root '${root}' is already mounted.\`); }` — `43e6ea3:packages/alg/src/exec/mounts.ts:32-34`; and a missing root throws rather than returning undefined (`:40`).

**The root id is a content digest, not the course name.** The warm script mounts under `s0.fullImage.imageId` and keeps the human label in a *separate* map:

> `const root = s0.fullImage.imageId;` / `roots.mount(root, defaultResult.pxc);` / `labels.set(root, label);`
> — `43e6ea3:scripts/warm-dev-pxc-roots.mjs:46-48`

and `imageId` is `sha256HexSyncText(\`${image.width}x${image.height}:${sha256HexSync(rgba)}\`)` — `43e6ea3:packages/alg/src/exec/operations.ts:688,707`.

The report field names the semantics explicitly and asserts no rewriting happened:

> `rootSemantics: '<ImgID>/{px.*,fn.*}',` / `addressMutation: false,` — `43e6ea3:scripts/warm-dev-pxc-roots.mjs:69-70`, repeated verbatim in `43e6ea3:scripts/project-same-number-badges.mjs:44`.

And the payoff of keeping the root out of the address is stated as a comment on the cross-root query:

> `// Wide access proof: one semantic address, independently resolved in every mounted world.`
> — `43e6ea3:scripts/warm-dev-pxc-roots.mjs:60-64`

This is CI-guarded: the workflow runs `npx vitest run tests/unit/pxcRootMounts.test.ts` then `timeout --signal=TERM 55s node scripts/warm-dev-pxc-roots.mjs` on every push to the branch (`43e6ea3:.github/workflows/pxc-root-warm.yml:27-30`), against a 40 s target / 55 s hard watchdog for **all** dev courses (`43e6ea3:scripts/warm-dev-pxc-roots.mjs:9-15`).

### 2b. What the root-alignment tip decided

**Missing.** `5607611` carries no root, mount, namespace or alignment rule in any file. What it does settle is the *shape below* the root — the authored PCR YAML with fully-qualified `px.`/`fn.` addresses in `with`/`into`:

> ```
> - call: fn.s1.exp.maskComponents.selectHsvMask
>   with:
>     raster: px.s1.exp.maskComponents.part.croppedRaster
>   args: { polarity: black, valueMax: 45, alpha: ignored }
>   into: px.s1.exp.maskComponents.part.blackMask
> ```
> — `5607611:packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml:5-12`

### 2c. The prefix rules, everywhere they are actually enforced

Three independent enforcement points, in three languages, all agreeing:

1. **Authoring time (the Mermaid compiler).** Every node label must be `fn.*` or `px.*` or compilation fails:
   > `const kind = fnLabel(node[2]) ? 'fn' : node[2].startsWith('px.') ? 'px' : null;` / `if (!kind) fail(\`node '${node[1]}' must label fn.* or px.*.\`);`
   > — `b5a6ae0:packages/alg/src/stages/S0/exp/mermaid-pcr/compiler.ts:31-32`, duplicated at `:46-47`

   Plus structural rules that make the two roots *mean* something: `if (from.kind === 'px' && to.kind === 'px') fail('PxC-to-PxC edges require a Calculation.');` (`:73`), `if (to.kind === 'fn' && !edge.label) fail(\`input edge to '${to.id}' needs a named binding.\`);` (`:74`), `if (writers.has(to.label)) fail(\`multiple writers for '${to.label}'.\`);` (`:77`), and forward-dependency rejection (`:93`). Ticks are subgraphs named `Tick: <name>` (`:19,33`), the PCR is a subgraph named `PCR: <name>` (`:61`), and duplicate Tick names fail (`:63`).

2. **Construction time (Python).** `if not self.address.startswith("fn."): raise ValueError("Calculation address must start with 'fn.'")` — `82f8fc9:packages/quick_anno_py/chainspot_quick_anno/core.py:33-34`, unchanged at `5c87d48`, `6309ff1`, `19b9b92`. Part addresses get **no** equivalent: `if not self.address: raise ValueError("Part address must be non-empty")` — `82f8fc9:…/core.py:17-19`.

3. **Type level (TypeScript).** `readonly address: \`fn.${string}\`;` on both `PxFn` (`43e6ea3:packages/alg/src/exec/board.ts:19`) and `FrozenCalculation` (`43e6ea3:packages/alg/src/exec/contract.ts:62`). Part addresses are the open string `SlotRef`, and the openness is argued for:

   > *"Deliberately a plain string, not a closed enum: R2 requires operations at a finer grain than the existing engine units, so the slot namespace has to stay open (e.g. 'badgeStage.brightMask', 'badgeStage.components', 'assignment.scoring', 'assignment.selection') without this file growing every time a unit gets decomposed further."*
   > — `43e6ea3:packages/alg/src/exec/contract.ts:15-23`

**Note the internal disagreement:** the `SlotRef` examples in `contract.ts:19-22` (`'badgeStage.brightMask'`, `'assignment.scoring'`) carry **no `px.` prefix at all**. The `px.` prefix is a convention of the S0/S1 stage layer and the Python authoring layer, layered over a core that does not require it. The `board.ts` header says the same: it carries *"BOTH the classic unit-level slots ('stage', 'badges', 'measurement', …) and the new dotted sub-slots"* — `43e6ea3:packages/alg/src/exec/board.ts:1-8`.

### 2d. What the segments below the root actually discriminate

Full census of address roots across `43e6ea3`'s `*.ts`/`*.yaml`/`*.mjs`: only `px.` and `fn.` exist. (`run.`, `data.`, `view.` hits are all JS object properties, not addresses.)

The decisive pattern is in the S1 graph, where **public outputs drop the stage segment and scratch keeps it**:

| kind | address | cite |
|---|---|---|
| public, survives the stage | `px.course.canonicalPixels` | `b5a6ae0:experiments/mermaid-s0-s1/S1.mmd:2`; constant at `43e6ea3:packages/alg/src/stages/S0/clean/index.ts:17` |
| public | `px.badges.objects`, `px.badges.px`, `px.badges.muted` | `b5a6ae0:experiments/mermaid-s0-s1/S1.mmd:70,73,77` |
| public, names the *relation* not the stage | `px.remaining.afterBadges` | `b5a6ae0:…/S1.mmd:81` |
| scratch, stage+experiment scoped | `px.s1.exp.maskComponents.part.blackComponents` | `b5a6ae0:…/S1.mmd:42` |
| scratch | `px.s1.exp.badgeAssembly.plateBorders` | `b5a6ae0:…/S1.mmd:51` |
| model input | `px.s1.whiteDigits.model` | `b5a6ae0:…/S1.mmd:3` |
| source intake | `px.source.selectedInput`, `px.source.fullImage` | `43e6ea3:packages/alg/src/stages/S0/clean/index.ts:15-16` |
| **view state, reserved** | `px.view.partsInspector` | `8cdddec:src/lib/parts-inspector/PartInspector.svelte:21` |
| per-instance Part | `px.s1.exp.maskComponents.part.blackComponent-115` | `8cdddec:experiments/duckdb-inspection/receipt.json` (`part_key` rows) |

`px.badges.*` is exactly what lets S1 → S2 → S3 join with no stage in the address (`19b9b92:experiments/quick-anno-python/s1.py:33-35` reads `px.badges.objects` / `px.badges.px` / `px.badges.muted`; `19b9b92:…/s3.py:33-37` reads `px.tees.*` in the same shape). That is the connection the owner is asking for, already working.

The view root is enforced by a stated boundary rather than by code: *"Selection, visibility, isolation, and framing use `px.view.partsInspector`; those controls do not invoke Calculations."* — `8cdddec:experiments/parts-inspector/README.md:3-5`; and in the renderer, *"**Projection-only MaterializationView** — View Args never cross the production gateway"* — `43e6ea3:src/lib/evidence-workbench/PcrInspectionHost.svelte:90-92`.

The Python side adds a **third root that the TS side does not have**, unenforced: `scratch.*` for Python-derived investigation Parts —

> `rejected = Part("scratch.s3.rejectedCandidates")` / `summary = Part("scratch.s3.visibleTeeSummary")` — `19b9b92:experiments/quick-anno-python/s3.py:38-39`; also `Part("scratch.s1.ownershipSummary")` at `82f8fc9:experiments/quick-anno-python/s1.py:36` and `Part("scratch.s2.basketSummary")` at `5c87d48:experiments/quick-anno-python/s2.py:37`.

So ChainSpot has two answers to the same question — TS says "scratch is `px.<stage>.exp.*`", Python says "scratch is its own root `scratch.*`" — and neither validates it. That is the sharpest unresolved addressing conflict in the corpus.

Finally, the one place an address is **rewritten**, and it is a rewrite of the *binding*, never of the address: within one PCR, a Part bound as input is silently swapped for a ResultRef to that address's writer —

> `if isinstance(source, Part) and source.address in self._writers: source = ResultRef(self._writers[source.address])` — `6309ff1:packages/quick_anno_py/chainspot_quick_anno/pcr.py:113-116`

This is pyto's `{?} SilentRules` mechanism, present in ChainSpot two days before pyto raised it as a question, and silent there too.

### 2e. Proposed address tree for round five

The owner's rule — *the point is connection; a meaningless root is wasted log(N) potential* — is best served by ChainSpot's own answer, which is **not** "pick better first segments". It is: **the discriminator that varies fastest and carries the most connection is not a segment at all; it is the mount, and it is kept out of the address so that one address means one thing in every world.** `px.DashsTrack.s1.badges` is precisely the address ChainSpot wrote a test to prove it never creates (`43e6ea3:tests/unit/pxcRootMounts.test.ts:16-17`).

That reframes the log(N) argument. Putting the world name in the address spends a segment on a value that is constant for the whole tree you are querying — zero bits of discrimination inside a world, and it destroys the cross-world join, which is the entire connection. Keeping it as a mount spends zero segments and buys the wide query for free (`43e6ea3:scripts/warm-dev-pxc-roots.mjs:60-64`).

**Proposed shape:**

```
{?} Label                        provenance root; NOT an address (pyto/questions.md:1-8)
   │
<mount>                          outside the address space, content-derived where possible
   │                             ChainSpot: ImgID = sha256(WxH:sha256(rgba))
   │                             pyto:      imgid:<sha12> | neat:<repo> | chess:<gameid> | disc:<user>
   │                             human labels live in a side map, never in the address
   ├── fn.<domain>.<unit>.<op>            enforced prefix, three runtimes already agree
   ├── oc.<domain>.<effect>               effectful operations ({?} GuardEnforcement) — new, no ChainSpot precedent
   └── px.<second>…                       values
        ├── px.<domain-noun>.…           PUBLIC, stage-free, this is where connection lives
        │      px.badges.px  px.baskets.family  px.tees.px  px.course.canonicalPixels
        │      px.remaining.afterBadges
        ├── px.<stage>.exp.<experiment>.part.<name>   scratch, stage-scoped, disposable
        ├── px.view.<surface>            projection-only; never crosses the gateway
        ├── px.proposal.<domain-noun>.…  predicted transitions ({?} ProposalsNotFacts)
        └── px.run.<name>                per-run knobs/inputs (px.run.threshold, px.run.scoutThumbnail)
```

**What the root should be, and why.** The root of an *address* should stay `px.` / `fn.` (plus `oc.`), because that one bit is the only one three independent implementations already enforce and the only one a query language can rely on (`b5a6ae0:…/compiler.ts:31-32`; `82f8fc9:…/core.py:33-34`; `43e6ea3:…/contract.ts:62`). It is cheap and it is real. The root that must *carry connection* is the **mount**, and it should be **content-derived** — `imageId = sha256HexSyncText(\`${w}x${h}:${sha256HexSync(rgba)}\`)` (`43e6ea3:packages/alg/src/exec/operations.ts:688`) — because a content root makes "same material" and "same root" the same fact, which is what turns `{?} CrossProjectReuse` from a lookup problem into an identity check. `43e6ea3:packages/alg/src/stages/S0/clean/index.ts:245` already composes the two halves in an artifact id: `` `${S0_CROPPED_IMAGE_ADDRESS}.${output.imageId.slice(0, 12)}` `` — semantic address plus content root. That is the whole design in one line.

The **second segment** is where log(N) is actually spent well, and ChainSpot's rule is: **the second segment is the domain noun that outlives the stage that produced it.** `px.badges.px` is readable and joinable in S1, S2 and S3; `px.s1.exp.maskComponents.part.blackMask` is not meant to be. That is a discriminating segment because the set of domain nouns in a LAB is small and stable while the set of stages churns.

**Where pyto's current proposal agrees:**

- **`?`** — agrees, with a correction: it is the provenance root, and it must never be an address segment. ChainSpot has no equivalent construct anywhere in the clone (**missing**), which is exactly why it has two unreconciled scratch conventions (§2d) and no recorded decision about either.
- **`fn.<ns>`** — agrees, strongly. Three enforcement points, unchanged across all eight tips. Keep the `<ns>` shape too: ChainSpot's `fn.s1.exp.badgeAssembly.assemble` and `fn.quickAnno.s3.summarizeVisibleTees` (`19b9b92:experiments/quick-anno-python/s3.py:56`) both put the authoring context in the address, so a Calculation's provenance is readable without a registry.
- **`px`** — agrees, and is the only Part root ChainSpot's compiler will accept.
- **`scratch`** — agrees *conditionally*. It has real Python precedent (`19b9b92:…/s3.py:38-39`) and it discriminates the one thing a viewer most needs to filter on: production truth versus investigation output. But ChainSpot's TS side encodes the same distinction *inside* `px.` as `px.<stage>.exp.*` (`b5a6ae0:…/S1.mmd:37-57`). Adopt root-level `scratch.` only if it is enforced the way `fn.` is; an unenforced third root is how ChainSpot ended up with two.
- **`run`** — agrees as a *second* segment, not a root: `px.run.threshold` / `px.run.scoutThumbnail` already exist. As a root it duplicates what the mount and the receipt's `opId` (`43e6ea3:…/contract.ts:128`) already carry.

**Where it conflicts:**

- **`chess`, `wumpus`, `disc`, `neat`, `tidy`** — direct conflict with the mounts decision. These are worlds. Making them address segments is exactly `px.DashsTrack.s1.badges`, the address `43e6ea3:tests/unit/pxcRootMounts.test.ts:16-17` exists to assert is never created. They also fail the owner's own test: inside a chess LAB, every address begins `chess.`, so the segment discriminates nothing and is pure wasted log(N). Make them mount ids (`chess:<gameid>`), and `px.board.squares` then means the same thing in every game — which is the cross-project hit `{?} CrossProjectReuse` needs.
- **`material`** — conflict. ChainSpot's answer to "what kind of thing is this" is a **declared field on the artifact**, not an address prefix: `ArtifactKind = 'rgba' | 'mask' | 'scalarField' | 'orientationField' | 'componentSet' | 'candidateSet' | 'badgeEvidence' | 'm1Representation' | 'm2Representation' | 'polyline' | 'measurementTable'` (`43e6ea3:packages/alg/src/exec/contract.ts:77-88`) carried on `ArtifactRef {id, kind, sha256, uri, dims?}` (`:104-113`). A `material.` root would put the same fact in two places and would force the storage backend to be chosen by string-matching an address instead of by reading a declared kind. This is a live answer to `{?} StorageKinds`: **declared Part kind, not address prefix.**
- **`proposal`** — no ChainSpot precedent as a root (**missing**), but `px.view.*` is a working precedent for a reserved *second* segment that a gateway refuses to let cross into computation. `px.proposal.*` inherits that machinery for free; `proposal.*` as a root does not.

---

## 3. VIEWER

### What `lab/s0-viewer` built

A **build-time materializer**, not a live viewer. `prepareS0Viewer(routeRoot, assetRoot)` runs the frozen S0 once under Node, writes both rasters as PNGs, writes the raw canonical bytes, and generates a SvelteKit `+page.server.js` whose `load()` returns a literal JSON snapshot:

> `// Materialize the viewer's saved snapshot with the same frozen S0 as LAB.` / `// Browser view controls consume these outputs; they never rerun the stage.`
> — `b5a6ae0:scripts/prepare-s0-viewer.mjs:8-9`

The snapshot binds every panel to its **PxC address**, not to a filename:

> `return { label, filename, widthPx, heightPx, imageId: raster.imageId, address: index === 0 ? 'px.source.fullImage' : 'px.course.canonicalPixels' };` — `b5a6ae0:scripts/prepare-s0-viewer.mjs:19-20`

and it carries provenance and the contract source in-band: `const snapshot = { sourceSha, sourcePath, panels, crop: run.cropReceipt, receipt, contract: readFileSync('packages/alg/src/stages/S0/contract.ts', 'utf8') };` — `b5a6ae0:scripts/prepare-s0-viewer.mjs:25-26`. It seeds the browser's warm store with exact bytes: `writeFileSync(join(assetRoot, 'CroppedImage.rgba'), run.croppedImage.rgba);` with the comment *"Seed the browser's warm PxC with the exact S0 bytes, without image-decoder changes."* (`:23-24`).

The staging build **fails loudly** if any of it is missing: `for (const page of ['build/index.html', 'build/labui-s0/snapshot.json', 'build/labui-s0/CroppedImage.rgba', 'build/parts.html', 'build/lab.html', 'build/lab/pcr.html']) { if (!existsSync(resolve(page))) throw new Error(\`staging build omitted ${page}\`); }` — `b5a6ae0:scripts/build-staging.mjs:35-36`; and the asset dir is reserved: `if (existsSync(viewerAssets)) throw new Error('static/labui-s0 is reserved for generated S0 outputs');` (`:19-20`). Staging routes are overlaid into a temp tree and sheared away in a `finally` so *"the production build contains neither route nor its LAB code"* (`43e6ea3:src/lib/evidence-workbench/README.md:22-25`; `b5a6ae0:scripts/build-staging.mjs:16-18,39-40`).

### What the mermaid review built

Mermaid **is** the authored PCR. `compileMermaidPcr(mermaid, argsJson)` parses a restricted `flowchart TD` subset and emits `stringify({ PrincipleComponentRender: pcr, Ticks: ticks })` — `b5a6ae0:packages/alg/src/stages/S0/exp/mermaid-pcr/compiler.ts:102` — i.e. the identical shape to the hand-written YAML (`5607611:…/PrincipleComponentRender.yaml:1-2`) and to the Python exporter (`19b9b92:packages/quick_anno_py/chainspot_quick_anno/graph.py:111`). Declaration order is executable order: *"Declaration order is executable order; reject forward dependencies, including via PxC."* (`b5a6ae0:…/compiler.ts:58`), with Tick placement monotonic (`:82-86`) and unused functions rejected (`:98`).

The authored graphs are small and complete: S0 is 2 Ticks / 3 Calculations (`b5a6ae0:experiments/mermaid-s0-s1/S0.mmd:5-19`), S1 is 6 Ticks / 15 Calculations (`b5a6ae0:experiments/mermaid-s0-s1/S1.mmd:5-33`, edges `:36-81`). `S0.args.json` is `{}` (`b5a6ae0:experiments/mermaid-s0-s1/S0.args.json:1`) — args are keyed by node occurrence id and validated: `for (const id of Object.keys(args)) if (!positions.has(id)) fail(\`unknown argument occurrence '${id}'.\`);` (`compiler.ts:68`).

The runner and its limits are stated, not implied:

> *"runner.ts is an isolated experimental async interpreter over existing PxC.call; it is not integrated with shared PQL, Stage routing, browser inspection or S2. It records each actual call and its values by reference. Run records are returned, not published into PxC… Only explicit graph publications write result Parts to PxC."*
> — `b5a6ae0:packages/alg/src/stages/S0/exp/mermaid-pcr/README.md:31-36`

> *"CLI outputs: two generated YAMLs; readable receipt; actual-runs.v8 retaining typed arrays and shared references; baseline/generated canonical PNGs; separate exact owned/muted/remaining masks. Failure preserves the successful prefix and failing Calculation in failed-run.v8 plus readable failure.json… This is basic inspection, not a finished browser viewer."*
> — `b5a6ae0:…/README.md:47-51`

`proof.ts` independently re-executes legacy S0 and the existing S1 YAML and compares *"canonical bytes, crop proposal, decode count, direct reference identity, S1 bindings/args/output addresses, all S1 intermediate values and full public output values, including ownership declarations and pixel sets"* (`b5a6ae0:…/README.md:41-45`). The refine checklist is 14 unchecked boxes (`b5a6ae0:…/REFINE.md:7-24`) and the handoff refuses acceptance: *"Sam owns visual acceptance and the revised checklist. Publishing this checkpoint does not authorize landing it."* (`b5a6ae0:experiments/mermaid-s0-s1/HANDOFF.md:33-34`).

### What is shown per Tick

`TickInspection.svelte` (blob identical at every tip) renders exactly six sections for one Tick:

| section | fields | cite |
|---|---|---|
| header | `pcr.title`, `tick.opId`, `tick.durationMs.toFixed(3)` ms | `b5a6ae0:src/lib/evidence-workbench/TickInspection.svelte:31-38` |
| identity strip | Run Args identity (`pcr.paramsHash ?? 'UNKNOWN'`), Plan (`planFingerprint`), Run result (`runResultId`), then a line rendering `runResultIdentityScope` and `runResultIdentityLimitation` | `:40-56` |
| Exact PxC inputs | every `tick.actualConsumes` address; `[] — none read` when empty; a `Declared but unread:` warning when declared ≠ actual | `:59-68` |
| Calculation identity | per `frozenCalculation`: `address`, `identityScope` + `SHA-256 implementationHash`, and `Not transitive: {limitation}` | `:70-81` |
| Exact PxC outputs | every `tick.writes` address with its `kind`; `[] — nothing written`; `Declared but unwritten:` warning | `:83-97` |
| Materializations | per artifact `kind · id`, `SHA-256 sha256`, optional `w×h`; else *"No persisted Materialization at this boundary. PxC outputs remain inspectable by address."* | `:100-119` |
| Residue / UNKNOWN | per-line label/count/note; else *"UNKNOWN — this Tick establishes no molecule-specific residue account."* | `:122-133` |

The host wraps it with a pixel projection kept behind a firewall (`:86-95` of `PcrInspectionHost.svelte`), and the route is the delivery vehicle:

> *"`/lab/pcr` reuses the Storybook inspection molecules against the same materialized computation. It opens with the checked `DEFAULT_PCR_INSPECTION_PLAN` (Badge PCR, `badgeStage.masks`, badge 1, composed Materialization). The staging build fails loudly if the corpus is absent or any default PCR, Tick, or specimen identity has drifted."*
> — `43e6ea3:src/lib/evidence-workbench/README.md:27-30`

### What the Day 3 PCR render should copy, and avoid

**Copy — the six-section layout verbatim.** It is a finished, shipped answer to Reframing 4's Day 3 spec (`ULTRACODE-WEEK.md:107-113`) and its field list maps one-for-one onto pyto's `Receipt` (`pcr.py:95-128` per the ledger).

**Copy — UNKNOWN is a rendered value.** Four separate empty states are rendered rather than hidden (`TickInspection.svelte:63,92,117,131`), and `paramsHash ?? 'UNKNOWN'` (`:43`). A viewer that omits what it does not know is a viewer that lies about coverage.

**Copy — declared beside actual, not instead of.** The divergence is a visible warning, not a thrown error, in the viewer (`:65-67,94-96`), while being *"a conformance failure the gateway surfaces rather than silently accepting"* in the runtime (`43e6ea3:packages/alg/src/exec/contract.ts:121-125`). Two different jobs, two different responses.

**Copy — the limitation travels with the hash.** `identityScope: 'runtime-function-body'` and `limitation: 'called helpers, constants, templates, and assets are not covered'` are *typed fields on `FrozenCalculation`* (`43e6ea3:…/contract.ts:65-67`), rendered as `Not transitive:` (`TickInspection.svelte:77`). pyto's `{?} CacheInvalidation` raises the same caveat and leaves it in a side document. Put it in the receipt.

**Copy — the projection firewall.** *"View Args never cross the production gateway"* (`PcrInspectionHost.svelte:90-92`), and view state at a reserved `px.view.*` address whose controls *"do not invoke Calculations"* (`8cdddec:experiments/parts-inspector/README.md:5`).

**Copy — freeze at build, never re-run in the browser** (`b5a6ae0:scripts/prepare-s0-viewer.mjs:8-9`), and bind every panel to an address plus an `imageId` (`:19-20`).

**Copy — fail loud on drift** (`b5a6ae0:scripts/build-staging.mjs:35-36`; `43e6ea3:src/lib/evidence-workbench/README.md:30`).

**Avoid — Storybook/SvelteKit/Vite as the vehicle.** The whole surface needs `npm run build:staging`, a route overlay, a temp route tree, a private corpus checkout, and Storybook molecules (`b5a6ae0:scripts/build-staging.mjs:24-31`; `43e6ea3:src/lib/evidence-workbench/README.md:7-18`). Reframing 4 requires *"a dependency-free browser page (`pyto/viewer/tick-viewer.html`, Node 22 tests, no build)"* (`ULTRACODE-WEEK.md:107-108`). Copy the layout; leave the toolchain.

**Avoid — the split that ChainSpot never closed.** The value-bearing surface (the neon sheet) is Stage-keyed and PCR-blind — it is built straight from `snapshot.json`, never from `PcrRun` (`19b9b92:experiments/quick-anno-python/materialize_s3_neon.py:163` re-opens `snapshot['panels']['s3:CroppedImage']`; the Python PCR only writes `python-summary.json` at `19b9b92:…/s3.py:90-93`). The Tick-keyed surface (`TickInspection`, `PCR.mermaid()`) is structure-only and value-blind. Neither half alone answers origin.md's question. Day 3's render must be **one surface that is Tick-keyed and value-bearing**.

**Avoid — emitting an artifact nothing consumes.** *"Not part of the pattern's spine: nothing consumes the .mmd, and a two-node graph needs no diagram."* (`6309ff1:packages/quick_anno_py/chainspot_quick_anno/investigation.py:91-93`), and both call sites leave it commented out (`6309ff1:experiments/quick-anno-python/s3.py:104`). If the Day 3 page does not render the Mermaid, do not write it.

---

## 4. STORAGE — the DuckDB archive

### What was tried

DuckDB-Wasm **1.32.0**, reporting engine **v1.4.3**, as a **query layer over a completed run**, in the browser, driving the existing pixel inspector:

> *"The existing S1 YAML runs through the existing executor; DuckDB then queries its recorded results. A query row opens the original Parts in the interactive pixel inspector. This is a working browser integration, with a successful static staging build."*
> — `8cdddec:experiments/duckdb-inspection/REPORT.md:3`

Three derived tables from one S1 run (3 Ticks, 9 Calculations, 952 black components, 176 white, 18 plates, 934 rejected, 18 candidates, 0 incomplete — `REPORT.md:9-18`):

| table | rows | meaning | cite |
|---|---:|---|---|
| `results` | 2,163 | items in recorded Calculation outputs, **including rejections and intermediates** | `8cdddec:…/REPORT.md:24` |
| `parts` | 1,130 | 1,128 distinct components and two masks | `:25` |
| `result_parts` | 2,390 | result-to-Part occurrences **with their role paths** | `:26` |

Three preset queries, all executed for real: assembled candidates (18), rejected plates (934), Parts shared across candidates (0) — `:28-32`. Part keys in the result rows are full PxC addresses: `"part_key": "px.s1.exp.maskComponents.part.blackComponent-115"` (`8cdddec:experiments/duckdb-inspection/receipt.json`). Verified by 5 focused tests including *"actual DuckDB execution of all presets"* (`REPORT.md:66`) and a real-data smoke where *"every returned row resolved to an inspector target; every rejected reason and dimension matched its Calculation record"* (`:68`).

### Why it was archived

Not because it was wrong. Because of **cold start**:

> Commit message: *"Archived at Sam's request after the measured 5.79-second browser startup exceeded the five-second CV target. No replacement backend or further implementation is included."*

The numbers, verbatim:

> *"One final Node run measured S1 at **613 ms**, projection at **46 ms**, and database initialization plus table loading at **3.80 s**. Queries took **146 / 69 / 70 ms**. The browser preview measured startup at **5.79 s**, then **151 / 228 / 183 ms** for the three queries. These are single-run observations, not benchmarks."*
> — `8cdddec:experiments/duckdb-inspection/REPORT.md:71`

> *"The exception-handling Wasm asset is **34,242,586 bytes uncompressed**… DuckDB adds substantial startup weight for this small dataset. No CV speedup was attempted or demonstrated."*
> — `:73`

Machine-readable: `"databaseMs": 3802.124526`, `"executionMs": 613.154858`, `"projectionMs": 45.517…` (`8cdddec:experiments/duckdb-inspection/receipt.json`); `"startupSeconds": 5.79`, `"productionBrowserTested": false`, `"pagesDeployed": false` (`8cdddec:experiments/duckdb-inspection/browser-evidence.json`).

This is `{?} WarmupBudget` measured rather than argued (`pyto/questions.md:67-74`, which cites "5.3 s" — the archived receipt says **3.80 s Node init / 5.79 s browser startup**; the discrepancy should be reconciled or the questions.md figure corrected).

### What it implies for "storage as first class" and the opposite-of-S3 facade

**1. The facade discipline is already written down, and it is exactly the opposite-of-S3 thesis.** Four rules, quoted:

> - *"**PxC and PQL retain execution and original material.** No core store, registry, executor, or YAML edits were required."*
> - *"**Projection reads a completed run.** SQL holds scalar records and identity links; raw pixel buffers stay with the Parts."*
> - *"**Recorded geometry stays authoritative.** Bounding boxes come from existing `MeasuredPart` outputs, with `bbox_source_result` identifying a supplying result. The query layer does not reimplement geometric measurement. Missing recorded geometry is `NULL`."*
> - *"**The inspector resolves query identities back to recorded objects.** Querying and viewing do not modify CV results. The frontend can still inspect Parts if database startup fails."*
> — `8cdddec:experiments/duckdb-inspection/REPORT.md:55-59`

That last clause is the specification for the whole `{?} StorageKinds` design: **a specialized backend must be optional at runtime.** The raster kind stayed in its own store; the scalar/identity kind went to a relational backend; and the page still works when the relational backend fails to start. A backend that cannot be dropped is not a backend, it is a dependency.

**2. Kind, not prefix.** The archive did not select its backend by address prefix. `ArtifactKind` is a closed union of eleven kinds on a content-addressed `ArtifactRef {id, kind, sha256, uri, dims?}` where *"`uri` is sink-defined (a file:// path from the Node sink, an in-memory handle from a browser/collector sink) — the exec core never interprets it, only carries it through the receipt"* (`43e6ea3:packages/alg/src/exec/contract.ts:77-113`), and the backend is an **injected sink**. `{?} StorageKinds` asks "chosen by address prefix or a declared Part kind?" — ChainSpot has shipped the declared-kind answer, with dependency injection as the selection mechanism, and it has been byte-stable across all eight tips.

**3. Address reuse is the unsolved half, stated as a precondition:**

> *"This is deliberately a **single completed-run query surface**. It does not provide live subscriptions, cross-run versioning, a general SQL editor, arbitrary PxC enumeration, or execution optimization. It assumes the existing convention that recorded Part values are not subsequently mutated. Reusing an address for changed material would need versioned identity before treating this as a historical database."*
> — `8cdddec:experiments/duckdb-inspection/REPORT.md:61`

That is `{?} CacheInvalidation` restated as a storage requirement: **a historical store needs versioned identity at the address, which PxC does not have** (`PxC.set` classifies a write only as `"replacement"` vs `"new-address"`, never by hashing the value — `19b9b92:packages/quick_anno_py/chainspot_quick_anno/core.py:62-66`).

**4. The archive is a placement decision, not a rejection.** `{?} WarmupBudget` already says a backend that cannot warm inside the budget is *"not a backend for the runtime, only for the workshop"*. DuckDB's own guess agrees:

> *"the strongest next use is inspecting relationships and comparing experimental runs, where SQL joins and aggregation replace bespoke viewer filtering. The current three queries are small enough that ordinary JavaScript could handle them; they prove integration, not a necessity for DuckDB."*
> and *"keeping initialization lazy and reusing a database across several inspections will matter more initially than optimizing individual queries. The observed startup cost is much larger than query execution. Measure a repeated real workflow before deciding how far to commit to this backend."*
> — `8cdddec:experiments/duckdb-inspection/REPORT.md:106-108`

Under `{?} PerAppBudget` (per-application, not global), DuckDB is a legitimate **workshop** backend for pyto — comparing runs is exactly what pyto is for — and an illegitimate **ChainSpot runtime** backend. The archive should be read as evidence *for* the two-mount design, not against a relational kind.

**5. Contrast with what the quick_anno tips actually do for storage** — flat files named by a label slug: `` const file = `${stage}-${slug(panel.label)}.png`; … panels[`${stage}:${panel.label}`] = file; `` (`19b9b92:experiments/quick-anno-python/export_s3_snapshot.cjs:38-40`), re-opened by that string key in the materializer (`19b9b92:experiments/quick-anno-python/materialize_s3_neon.py:163`), versioned by string suffix `schema: 'chainspot-quick-anno-s3-snapshot@1'` (`19b9b92:…/export_s3_snapshot.cjs:60`), and never committed (`6309ff1:.gitignore`, added in that diff). Filename-as-address, with no kind and no digest. The DuckDB archive is strictly more advanced than anything on the Python side.

---

## 5. MATERIALIZATION and RECEIPTS — conventions to match

### Materializer conventions

1. **Neon first, as an acceptance rule.** *"The first subtle contact sheet was not sufficiently judgeable. The accepted investigation convention is **neon first**: make semantic differences unmistakable before making a render aesthetically subtle."* — `5c87d48:experiments/quick-anno-python/S1_VALIDATION.md:70`; restated at `82f8fc9:experiments/quick-anno-python/S1_CHECKPOINT.md:101`.

2. **Identity precedes geometry — per-object crops are mandatory, not optional.** *"panels 1-7 prove **where** each object was accepted and never **what** it is. Identity precedes geometry; a full-course panel cannot establish identity at course zoom."* — `6309ff1:experiments/quick-anno-python/S3_CHECKPOINT.md:110-112`; implemented as `neon.crops`, *"A contact strip of upscaled crops, one per box… This answers the second question."* — `6309ff1:packages/quick_anno_py/chainspot_quick_anno/neon.py:113-116`. The consequence, stated as a finding: *"A count that matches expectation is not evidence, and a bounding box is not an identity."* — `6309ff1:experiments/quick-anno-python/DEV6_S3_SURVEY.md:174-175`.

3. **Visually inspect before claiming success** — steps 7 and 8 of the checklist: *"7. materialize a **neon-first** visual correctness check; 8. visually inspect the materialization before claiming success;"* — `82f8fc9:experiments/quick-anno-python/S1_CHECKPOINT.md:109-122` (full 10 steps: prior Stage's PxC material in → smallest real snapshot → seed first-class Parts → name Calculations in a PCR → publish scratch Parts → query with PQL not ad-hoc state → neon-first → inspect → emit Mermaid/testimony → add convenience only after repeated friction).

4. **Verify the input by content, not by filename.** *"Input verified by content, not by filename: … sha256 e6616738640eee1d05d8cc2b59dd657f24b4a5a01dc2f68571b7e44c6f372b8a"* — `6309ff1:experiments/quick-anno-python/S3_VALIDATION.md:17-23`.

5. **Tag the snapshot schema, keep the producer's own receipt beside it.** `schema: 'chainspot-quick-anno-s1-snapshot@1'` plus `fs.writeFileSync(path.join(outDir, 's0.receipt.txt'), s0.receiptText + '\n'); fs.writeFileSync(path.join(outDir, 's1.receipt.txt'), s1.receiptText + '\n');` — `5c87d48:experiments/quick-anno-python/export_s1_snapshot.cjs:47-48,81-82`.

6. **Outputs are regenerated, never committed.** *"# quick_anno Python investigation outputs — regenerated by experiments/quick-anno-python/s<N>.py, never committed"* — `6309ff1:.gitignore`; *"Generated files land under `experiments/quick-anno-python/generated/` and are deliberately not checked in by this proof."* — `19b9b92:experiments/quick-anno-python/README.md`.

7. **The HUH convention when a materialization finds a real defect.** `### HUH — production-visible Tee set is not materially correct on this input` — `19b9b92:experiments/quick-anno-python/S3_VALIDATION.md`; expected vs encountered, exact pixel coordinates, PASS/FAIL per axis.

8. **Add nothing to the kernel to make a materialization readable.** *"No convenience was added to PxC/PQL/PCR. The repeated readability friction was handled in the S3 materializer itself by preserving source evidence and adding exact-pixel local-context crops; no new parallel telemetry or semantic store was introduced."* — `19b9b92:experiments/quick-anno-python/S3_VALIDATION.md` (closing paragraph).

9. **The spine as a reusable object.** *"Every quick_anno Stage investigation runs the same spine: real production Stage → smallest useful snapshot → first-class Python PxC Parts → bounded PCR Calculation → published scratch Part → PQL query → Mermaid view → neon-first correctness materialization"* — `6309ff1:packages/quick_anno_py/chainspot_quick_anno/investigation.py:3-8`, implemented as `StageInvestigation` (`:26-105`).

10. **Correctness as an accounting invariant, not eyeballed values.** S3's second Calculation asserts chained equalities so *"every enclosed ring left through exactly one named door"*, and `balanced: true` is the whole investigation's pass/fail signal, holding on all six Dev6 courses — `6309ff1:experiments/quick-anno-python/S3_CHECKPOINT.md:70-80`, `6309ff1:experiments/quick-anno-python/DEV6_S3_SURVEY.md:26-40`.

### Receipt conventions

The production `Receipt` is the target shape, and pyto's is already close:

```ts
export interface Receipt {
  readonly opId: string;
  readonly frozenCalculations: readonly FrozenCalculation[];
  readonly startedAtMs: number;
  readonly durationMs: number;
  readonly declaredConsumes: readonly SlotRef[];
  readonly declaredProduces: readonly SlotRef[];
  readonly actualConsumes: readonly SlotRef[];
  readonly actualProduces: readonly SlotRef[];
  /** Collision-visible PxC writes; replacements are never hidden as ordinary output. */
  readonly writes: readonly PxWriteTestimony[];
  readonly probes: readonly Probe[];
  readonly artifacts: readonly ArtifactRef[];
}
```
— `43e6ea3:packages/alg/src/exec/contract.ts:127-141`

Four conventions pyto does not yet match:

- **A Tick *is* a Receipt.** *"A Tick is the existing gateway Receipt understood as inspection testimony: exact addresses in, frozen calculations, exact addresses out. It adds no execution authority and deliberately has no run() method."* / `export type TickTestimony = Receipt;` — `43e6ea3:…/contract.ts:143-148`. This closes the ledger's gap #2 (no Tick↔receipt join) by construction, and `opId` (`:128`) is the stable per-run Tick id the ledger's gap #5 says nothing assigns.
- **Three write kinds, not two.** `'new-address' | 'refinement' | 'replacement'` — `43e6ea3:…/contract.ts:71-73`. Python has two: `kind = "replacement" if address in self._values else "new-address"` — `19b9b92:packages/quick_anno_py/chainspot_quick_anno/core.py:63-64`. `'refinement'` has no Python equivalent anywhere in the clone.
- **The identity limitation is a typed field.** `identityScope: 'runtime-function-body'` + `limitation: 'called helpers, constants, templates, and assets are not covered'` — `43e6ea3:…/contract.ts:65-67`. Machine-visible in every receipt, rendered in the viewer (`TickInspection.svelte:76-77`).
- **`Probe {name, value: number}`** — `43e6ea3:…/contract.ts:115-119` — a minimal named-numeric channel with no Python counterpart. Note the deliberate absence of anything larger: zero hits for "telemetry" anywhere in the quick_anno surface.

What the Python side has instead, and its exact deficit: `CalculationTestimony(id, calculation, inputs, args, into)` where `inputs` are `"px:<address>"` / `"fn:<calc_id>"` ref tags, never values — `6309ff1:packages/quick_anno_py/chainspot_quick_anno/pcr.py:59-65,149,157`; `TickTestimony(name, calculations)` and `PcrRun(pcr, ticks, results)` at `:68-78`. No digest, no duration, no receipt object, and **the values are live** — `results[invocation.id] = value` at `:162` — exactly as `tick-observability-ledger.md` §3 says of pyto's own `PcrRun.results`. Both runtimes hold every value in memory at the end of a run and neither renders it.

The two things ChainSpot calls "receipt" that are **not** the `Receipt` type, so pyto does not confuse them: (a) the TS stage's human-readable `receiptText` (`19b9b92:experiments/quick-anno-python/export_s3_snapshot.cjs:63-66,103`), an opaque string the Python side archives and never parses; (b) the "Receipt:" column in `docs/CLAIMS-LEDGER.md` (`6309ff1`, rows 31-35), an evidence-citation convention.

---

## 6. REUSABLE NOW — ranked, with tip and path

Ranked by (a) does it answer an open `{?}`, (b) is it a working artifact rather than a lesson, (c) can it land this week without a decision from the owner.

**1. `43e6ea3:packages/alg/src/exec/mounts.ts:1-53` + `43e6ea3:tests/unit/pxcRootMounts.test.ts:1-30` — the mounts model, 53 lines, no dependencies.** This is the answer to the addressing round and to `{?} PortableKernel`'s "namespaces as mount points". Port `mount/has/get/roots/entries/slice` and, critically, port the *negative* test (`:16-17`) — it is what stops the LAB name from creeping into addresses. Two mounts today, as `{?} PortableKernel` says: ChainSpot's raster material and neat's durable tickets.

**2. `43e6ea3:src/lib/evidence-workbench/TickInspection.svelte:30-134` — the six-section per-Tick layout, as a page spec for Day 3.** Read it as a specification, not as code to port; write the dependency-free HTML that Reframing 4 requires (`ULTRACODE-WEEK.md:107-108`) against pyto's `Receipt`. Carry the UNKNOWN discipline (`:63,92,117,131`) and the declared-beside-actual warnings (`:65-67,94-96`) exactly.

**3. `43e6ea3:packages/alg/src/exec/contract.ts:59-148` — four typed additions to pyto's Receipt.** In order of value: `identityScope`/`limitation` on the frozen calculation (`:65-67`, answers `{?} CacheInvalidation`'s machine-visibility half today), `ArtifactKind` + `ArtifactRef` (`:77-113`, the declared-kind answer to `{?} StorageKinds`), `'refinement'` as a third write kind (`:71-73`), `type TickTestimony = Receipt` (`:148`, closes ledger gap #2 — but see the {?} below, pyto's byte-identity guarantee may forbid it).

**4. `6309ff1:packages/quick_anno_py/chainspot_quick_anno/investigation.py:26-105` — the `StageInvestigation` spine as pyto's missing entry point.** Ledger gap #6 is "no entry point": `observe` defaults False and nothing runs a PCR and writes a sheet. This class is that entry point, already factored: export → build PxC/PCR → PQL → optional mermaid → materialize. Subclass by overriding the build step only.

**5. `82f8fc9:experiments/quick-anno-python/S1_CHECKPOINT.md:109-122` — the 10-step delegate checklist, verbatim, as pyto's per-surface transfer protocol.** Proven three times (S1, S2, S3) across `82f8fc9`, `5c87d48`, `6309ff1`, with an explicit claim that the third was mechanical (`5c87d48:…/S2_VALIDATION.md:76`). Costs nothing; it is a doc.

**6. `6309ff1:packages/quick_anno_py/chainspot_quick_anno/neon.py:32-192` — byte-diff against `pyto/src/pyto/neon.py:32-181`.** The ledger says pyto already has `dim/draw_boxes/paint_pixels/checkerboard/remaining/crops/panel/sheet`. The one function to verify pyto actually has is **`crops`** with its mark-the-subject-inside-the-tile behavior (`:133-145`), added specifically because full-panel boxes could not answer "what is this". If pyto lacks it, that is a same-day port.

**7. `b5a6ae0:scripts/prepare-s0-viewer.mjs:8-30` — build-time freeze, address-bound panels, provenance in-band.** ~30 lines. Three ideas to copy into pyto's Day 3 materializer: never re-run the computation to view it (`:8-9`), bind every panel to its Part address and `imageId` (`:19-20`), embed `sourceSha`/`sourcePath`/`contract` in the snapshot (`:25-26`). Add the reserved-output-dir and omitted-page guards from `b5a6ae0:scripts/build-staging.mjs:19-20,35-36`.

**8. `19b9b92:packages/quick_anno_py/chainspot_quick_anno/graph.py:89-111` — the literal PCR JSON keys as pyto's portable export format.** `{"PrincipleComponentRender": name, "Ticks": [{"name": ..., "Calculations": [...]}]}` (`:111`), identical to the YAML at `5607611:…/PrincipleComponentRender.yaml:1-2` and to the Mermaid compiler's output at `b5a6ae0:…/compiler.ts:102`. Three producers, one shape — this is the JSON both runtimes read that Reframing 4 requires. Also the concrete material for `{?} KernelMerge`.

**9. `8cdddec:experiments/duckdb-inspection/REPORT.md:55-59,61` — the storage responsibility boundary, five rules, as pyto's Day 3 materials-store contract.** Especially *"The frontend can still inspect Parts if database startup fails"* (`:59`) and the versioned-identity precondition (`:61`).

**10. `b5a6ae0:packages/alg/src/stages/S0/exp/mermaid-pcr/compiler.ts:58-102` — the compile-time rule set, as pyto's PCR validator.** Even without adopting Mermaid-as-source, the seven rules are the ones pyto's `{?} SilentRules` is about: px→px needs a Calculation (`:73`), unlabelled input edge fails (`:74`), publication edge cannot carry a label (`:76`), multiple writers fail (`:77`), forward dependency/cycle fails (`:93`), multiple publications from one Calculation fail (`:97`), unused function fails (`:98`). JS fails loud on every one.

**11. `19b9b92:experiments/quick-anno-python/S3_VALIDATION.md` (`### HUH` heading) — the failure-report format for pyto's own validation docs and `{?}` entries.** Expected vs encountered, exact coordinates, PASS/FAIL per axis rather than one verdict.

**12. `5c87d48:packages/quick_anno_py/tests/test_first_class.py:38-51` — the single-writer characterization test** (`PCR '<name>' has multiple writers for '<address>'`, `5c87d48:…/pcr.py:119-123`), as a Day 1 mutation-kill fixture.

---

## 7. Questions for the owner, as `{?}` entries

### {?} AddressRootIsAMount
ChainSpot decided the root that names a world is **external** to the address space, and wrote a test asserting `px.DashsTrack.s1.badges` is never created (`43e6ea3:packages/alg/src/exec/mounts.ts:3-8`; `43e6ea3:tests/unit/pxcRootMounts.test.ts:16-17`). pyto's round-four proposal puts `chess`, `wumpus`, `disc`, `neat`, `tidy` **inside** the address as segments. These cannot both be right. Should the LAB/world become a mount id (leaving `px.`/`fn.`/`oc.` as the only address roots), which is what makes `px.badges.px` mean the same thing in every world and makes `{?} CrossProjectReuse` an identity check rather than a lookup?
Status: open. Bites: the round-five address tree, `{?} PortableKernel`, `{?} CrossProjectReuse`, Day 5 cross-project hit.

### {?} RootIdIsContent
ChainSpot's mount root is `imageId = sha256(WxH:sha256(rgba))` (`43e6ea3:packages/alg/src/exec/operations.ts:688,707`), with the human course label kept in a **separate** map (`43e6ea3:scripts/warm-dev-pxc-roots.mjs:46-48`), and artifact ids composed as address + digest prefix (`43e6ea3:packages/alg/src/stages/S0/clean/index.ts:245`). Is "the root must carry connection" satisfied by a content digest — the most connective root available, since same-material implies same-root — with names living outside the address entirely? Or does the owner mean the root should be human-readable?
Status: open. Bites: `{?} CacheInvalidation`, the materials store, `px add <address>`.

### {?} ScratchRootConflict
ChainSpot answers "where does investigation output live" two incompatible ways: TS puts it inside `px.` as `px.<stage>.exp.<experiment>.part.<name>` (`b5a6ae0:experiments/mermaid-s0-s1/S1.mmd:37-57`), Python gives it a third root `scratch.*` (`19b9b92:experiments/quick-anno-python/s3.py:38-39`), and **neither is validated in code** — `Part.__post_init__` only checks non-empty (`82f8fc9:packages/quick_anno_py/chainspot_quick_anno/core.py:17-19`) while Calculations get a hard `fn.` check (`:33-34`). Should pyto pick one and enforce it the way `fn.` is enforced, before more surfaces accumulate more ad-hoc prefixes?
Status: open. Bites: `Part` validation, PQL prefix queries, the viewer's provenance filter.

### {?} MaterialIsAKindNotARoot
The round-four list has `material` as an address root. ChainSpot instead carries `kind` as a declared field on a content-addressed `ArtifactRef {id, kind, sha256, uri, dims?}` over a closed eleven-member `ArtifactKind` union, with the backend chosen by an injected sink and *"the exec core never interprets"* the uri (`43e6ea3:packages/alg/src/exec/contract.ts:77-113`). `{?} StorageKinds` asks "address prefix or declared Part kind?" — ChainSpot has shipped the declared-kind answer, byte-stable across all eight tips. Adopt it, and drop `material` as a root?
Status: open, leaning yes. Bites: `{?} StorageKinds`, Day 3 materials store, `Part` has no kind today.

### {?} DuckDBIsAWorkshopBackend
The archive measured 3.80 s Node init / **5.79 s** browser startup / 34,242,586-byte Wasm asset, against 69–228 ms queries (`8cdddec:experiments/duckdb-inspection/REPORT.md:71,73`). Under `{?} PerAppBudget` (per application) plus `{?} WarmupBudget` ("not a backend for the runtime, only for the workshop"), DuckDB is disqualified for ChainSpot and arguably ideal for pyto, whose whole job is comparing runs — which is also the archive's own guess (`REPORT.md:106`). Should the archive be un-archived **as a pyto workshop backend**, on the report's own five-rule facade (`:55-59`) with lazy init, rather than treated as a closed question?
Status: open. Also: `pyto/questions.md:69-70` records "5.3 s to warm"; the archived receipt says 3.80 s (Node) / 5.79 s (browser). Which figure is canonical?

### {?} TickEqualsReceipt
ChainSpot production declares `type TickTestimony = Receipt` with `opId` as the stable per-run Tick id (`43e6ea3:packages/alg/src/exec/contract.ts:143-148,128`), which would close ledger gap #2 (no Tick↔receipt join) and gap #5 (no Tick identity) structurally. pyto contractually freezes `PcrRun.ticks` byte-identical with `observe` on or off (`pcr.py:130-140` per the ledger), which appears to forbid the merge. Keep them separate and join in the materializer, or break the byte-identity guarantee?
Status: open. Bites: `{?} ObservationSeam`, Day 3 materializer, ledger gaps 2 and 5.

### {?} StorybookAsVehicle
ChainSpot's working per-Tick viewer is delivered through Storybook molecules on a staging-only SvelteKit route requiring `npm run build:staging`, a route overlay and a private corpus (`43e6ea3:src/lib/evidence-workbench/README.md:22-30`; `b5a6ae0:scripts/build-staging.mjs:24-36`). Reframing 4 specifies *"a dependency-free browser page… Node 22 tests, no build"*. Confirm: copy the six-section layout and the fail-loud/UNKNOWN discipline, discard the toolchain entirely?
Status: open, leaning yes. Bites: Day 3 `pyto/viewer/tick-viewer.html`.

### {?} SilentRewritePredatesPyto
The declaration-time rewrite of a Part binding into the producing invocation's ResultRef — the operation the week's thesis calls pyto's "one distinctive operation" — was already present and already silent in ChainSpot on 2026-09-07 (`6309ff1:packages/quick_anno_py/chainspot_quick_anno/pcr.py:113-116`), two days before `{?} SilentRules` was raised. Does knowing it is inherited rather than invented change the lean on whether it should raise loudly at declaration?
Status: open. Bites: `{?} SilentRules`, `{?} ShadowRule`.

### {?} UnrunProofsCount
The Mermaid PCR review is explicitly *"written, unrun, unrendered. No parity or visual acceptance claim"* with 14 unchecked refine boxes and *"Publishing this checkpoint does not authorize landing it"* (`b5a6ae0:experiments/mermaid-s0-s1/HANDOFF.md:4,33-34`; `b5a6ae0:packages/alg/src/stages/S0/exp/mermaid-pcr/REFINE.md:7-24`). Everything I cite from it is therefore a *design decision*, not a verified behavior. Is it acceptable to port `compiler.ts`'s seven rejection rules into pyto on the strength of the design alone, or must the proof be run in ChainSpot first?
Status: open. Bites: reusable item 10, `{?} KernelMerge`.

### {?} S3DefectOwnership
`19b9b92:experiments/quick-anno-python/S3_VALIDATION.md` reports a live correctness defect — 3 of 18 production-accepted Tee objects are iOS map-chrome false positives, with exact coordinates — and the branch's task boundary forbade fixing it. `6309ff1:experiments/quick-anno-python/DEV6_S3_SURVEY.md:64-66` names the cause: *"The family size vote is the only thing filtering them, and it is a size filter standing in for an identity filter. It has no notion of chrome, of occluders, or of what a tee is."* Is that tracked as a ChainSpot ticket anywhere, and does any pyto surface inherit it?
Status: open. Bites: whether the neon-sheet port carries a known-defect caveat.

### {?} MiningCoverage
Seven branch tips were not mined: `f3ecab3` (`task/quick-anno-python-proof`), `fa44a45` (`review/s1-ownership`, which is the base the Mermaid proof names at `b5a6ae0:experiments/mermaid-s0-s1/HANDOFF.md:3`), `52417a9`, `116c984`, `5433854`, `b9d05cd`, `881c7e5`. `fa44a45` in particular is the parent of the two tips this brief most depends on. Should it be mined before round five closes?
Status: open.

---

# Appendix: the four tips re-mined in plain text (2026-09-09, wf_ccf03ee0-338)

Returned as markdown after their first readers failed on JSON output. Unedited.

## fa44a45 (review/s1-ownership-fa44a45)

### What it is

`fa44a4505d9aafbf6d2d21a12400298edb7fa96d`, "Wire S1 white recognition and badge ownership through PCR," authored 2026-09-07T00:13:10-05:00 by Samuel Mahan, single branch `review/s1-ownership-fa44a45` (`git for-each-ref --contains fa44a45`). Like the eight mined tips, it is a grafted root — `git show -s --format=%P fa44a45` is empty — so `git diff --stat main fa44a45` is a whole-tree comparison, not a semantic diff, exactly the caveat section 1 already establishes.

New genealogy the synthesis didn't have: this tip **is** the base the Mermaid review names — `b5a6ae0:experiments/mermaid-s0-s1/HANDOFF.md:3` reads "Base: fa44a4505d9aafbf6d2d21a12400298edb7fa96d" — and it is also the direct completion of `5607611`'s stub. `5607611:packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml:87` ends the file with `# Partial S1: digit recognition and final Badge/muted/remaining outputs follow.`; `fa44a45`'s copy of the same file replaces that comment with the `WhiteDigitRecognition` and `BadgeOutputs` Ticks verbatim (`fa44a45:packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml:87-137`), committed 3h12m after `5607611` in the same timezone (`git log --date=iso-strict`: `5607611` 21:01:21-05:00, `fa44a45` 00:13:10-05:00). So the corpus's timeline is `5607611` (stub) → `fa44a45` (this tip, fills the stub) → `b5a6ae0` (Mermaid review built on `fa44a45`) → the quick_anno Python transfers, which is a tighter chain than section 1's table shows.

The tip's payload is `packages/alg/src/stages/S1/exp/badge-assembly/{stage,ownership,white-recognition,index}.ts` plus the completed `PrincipleComponentRender.yaml`, and a self-contained review artifact at `review/s1-ownership/{README.md,receipt.json,source.png,ownership.png}`.

### Addressing

Same two-root discipline as every other tip: only `px.` and `fn.` appear as address roots anywhere in `packages/alg`, `docs`, `experiments`, or `scripts` (`grep -rniE '\broot\b|\bmount' packages/alg/src/exec docs experiments` returns only filesystem/root-cause hits, never an address root). No mounts model exists yet — `packages/alg/src/exec/mounts.ts` and `tests/unit/pxcRootMounts.test.ts` are both absent from this tree (`git ls-tree fa44a45` returns nothing for either path) — so the mounts decision in `43e6ea3` postdates this checkpoint. There is also no `scratch.*` root: this tip is pure TypeScript, and `quick_anno_py` (where `scratch.*` first appears) does not exist here at all (`find fa44a45 -iname 'quick_anno*'` is empty).

What this tip adds to section 2d's census: it is the **origin** of the "public, stage-free" addresses the synthesis quotes from the later Mermaid file. `px.badges.objects`, `px.badges.px`, `px.badges.muted`, and `px.remaining.afterBadges` are written here first, by real TypeScript, not just diagrammed later:

> `into: px.badges.objects` … `into: px.badges.px` … `into: px.badges.muted` … `into: px.remaining.afterBadges`
> — `fa44a45:packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml:117,123,130,137`

`px.view.partsInspector` also already exists here, one commit earlier than the `8cdddec` archive the synthesis cites for the same address:

> `const viewAddress = 'px.view.partsInspector';`
> — `fa44a45:src/lib/parts-inspector/PartInspector.svelte:20`

### Viewer and PCR render

`packages/alg/src/exec/contract.ts`, `src/lib/evidence-workbench/PcrInspectionHost.svelte`, and `TickInspection.svelte` are present at the same blob hashes the synthesis found byte-identical across all eight mined tips (`62b5d75`, `30ffdf2`, `0bf6b00` respectively, via `git ls-tree fa44a45 -r`), extending the "stable substrate" claim to nine tips rather than eight — this checkpoint was authored on top of the same fixed contract and viewer, not before it.

The distinctive addition here is a viewer path neither Storybook nor DuckDB uses: a plain Node CJS script that runs the real production PCR, queries its completed `pxc` by address, and self-checks before rendering:

> `const badges=r.pxc.get('px.badges.objects'),owned=r.pxc.get('px.badges.px'),muted=r.pxc.get('px.badges.muted'),remaining=r.pxc.get('px.remaining.afterBadges');`
> `if(counts.some(n=>n!==1))throw Error('Pixel partition has an overlap or omission');`
> — `fa44a45:scripts/render-badge-ownership.cjs:10,12`

This is a working, minimal answer to the split section 2 (Viewer) calls out as unresolved — "the value-bearing surface is Stage-keyed and PCR-blind... the Tick-keyed surface is structure-only and value-blind." This script is neither: it runs the actual `createStage(yaml)` PCR, reads its Tick outputs by address, and renders per-badge crops with an exhaustiveness assertion, all in one file, no build step, no Storybook. It predates the "neon-first" quick_anno convention by about four hours and uses the same idea (cyan/pink pixel overlay, per-object crops, a border-exclusion bbox) without naming it.

### Storage

No specialized backend exists in this tip — `grep -rli duckdb` over the whole tree returns nothing. Storage is the in-memory `PxC` fork model already implicit in the stable contract: `stage.ts:39` calls `pxc.fork()` per variant, and results are read back with plain `pxc.get`/`pxc.set`. The experimental runner here (`invokePql`) does not use the `ArtifactRef`/`ArtifactKind` machinery in `contract.ts` at all — it carries raw values "held by reference rather than copied" (`fa44a45:packages/alg/src/exec/pql.ts:20-22`), with no `sha256`, no declared kind, no `uri`. So the declared-kind facade the synthesis credits to the DuckDB archive is present in the codebase at this commit but unused by this particular experimental path — a live example of `{?} StorageKinds`'s "backend chosen by kind" answer sitting beside code that ignores it entirely.

### Materialization and Ticks

The PQL shape here is exactly the authored-YAML format the synthesis documents (`call`/`with`/`args`/`into` inside named `Ticks`), confirmed at its origin:

> ```
> export interface PqlCalculation {
>   readonly call: `fn.${string}`;
>   readonly with: Readonly<Record<string, string>>;
>   readonly args: Readonly<Record<string, unknown>>;
>   readonly into: string;
> }
> export interface PqlTick { readonly name: string; readonly Calculations: readonly PqlCalculation[]; }
> ```
> — `fa44a45:packages/alg/src/exec/pql.ts:4-13`

The ABFeature run harness executes Default plus every registered feature as independent forks, and failure in one does not abort the others or discard earlier writes in that fork — direct, dated evidence for two open root questions:

> "Variant failures produce failed results and do not suppress later variants. Earlier writes in the failed fork remain available; partial Calculation records are not yet returned."
> — `fa44a45:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:13`

This answers `{?} TransactionalTick` in the negative for this lane (no rollback; a failed Tick's prior writes persist in its fork) and names `{?} PartialExecutionRecords` as an explicit open label rather than an oversight (`REVIEW.md:24`, `{PartialExecutionRecords}`).

### Receipts and telemetry

Three incompatible receipt shapes coexist in this one tip, unreconciled: (1) the stable, unused-here `Receipt` interface in `contract.ts` (typed, digest-bearing, byte-identical to every other tip); (2) the experimental `PqlRun`/`PqlTickRecord` shape, which is untyped-for-identity and reference-holding, with no digest, no duration, no kind (`pql.ts:18-31`); and (3) the review script's own ad hoc `receipt.json`, which has yet a third vocabulary (`rule`, `reviewMarginPx`, `owned`/`muted`/`remaining`/`total`, `perBadge`) with no `sha256` and no `opId`:

> `const receipt={rule:'outer-border-bbox',reviewMarginPx:8,marginPurpose:'view-only exterior context; not an ownership allowance',partition:'every raster pixel exactly once',source,executionMs:r.executionMs,owned:owned.pixels.length,...}`
> — `fa44a45:scripts/render-badge-ownership.cjs:16`

No `telemetry` concept exists in code anywhere in this tree (`grep -rli telemetry` hits only unrelated docs and `package-lock.json`). This is missing, recorded as such.

### Reusable now

The S1 badge-assembly module (`stage.ts`, `ownership.ts`, `white-recognition.ts`, the completed YAML) is a small, complete, real algorithm end to end — from raw raster to `px.badges.objects`/`px`/`muted`/`px.remaining.afterBadges` — with a working, dependency-light materializer script that queries by address and self-verifies a pixel partition before rendering. That combination (Tick-keyed execution, value-bearing render, address-driven query, no Storybook/DuckDB/build step) is closer to what pyto's Day 3 PCR render needs than either half the synthesis found split apart in the later tips.

### Quotes

- "PrincipleComponentRender.yaml owns the full experimental S1 order and arguments." — `fa44a45:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:7`
- "Variant failures produce failed results and do not suppress later variants. Earlier writes in the failed fork remain available; partial Calculation records are not yet returned." — `fa44a45:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:13`
- "View controls perform no CV calculations." — `fa44a45:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:14`
- "Refinement must preserve Badge identity, source coordinates, existing constituent Parts, and visibility of unexplained interior and exterior residue." — `fa44a45:review/s1-ownership/README.md:27-28`
- "S1 is not frozen or deployed." — `fa44a45:review/s1-ownership/README.md:38`
- "Actual input and output values, held by reference rather than copied." — `fa44a45:packages/alg/src/exec/pql.ts:21`
- `const viewAddress = 'px.view.partsInspector';` — `fa44a45:src/lib/parts-inspector/PartInspector.svelte:20`

### Questions for the owner

{?} ThreeReceiptShapes: This tip carries three unreconciled receipt vocabularies at once (typed `Receipt` in `contract.ts`, reference-holding `PqlRun`, ad hoc `receipt.json`). Should pyto commit to one shape now rather than let an experimental lane fork its own the way this one did?

{?} PartialWritesOnFailure: `REVIEW.md:13` shows a failed Tick's earlier writes staying visible in that fork, with partial Calculation records explicitly deferred. Does the owner want pyto's Tick semantics to keep partial writes on failure (this precedent) or roll the fork back — this is `{?} TransactionalTick` and `{?} PartialExecutionRecords` with concrete prior art now, not just an open label.

{?} MaterializerAsTemplate: `scripts/render-badge-ownership.cjs` is a full address-driven, self-checking, no-build viewer three hours older than "neon-first" and four commits older than DuckDB. Should this script's shape — plain script, query completed run by address, assert a partition invariant, then render — be the literal template for pyto's `viewer/tick-viewer.html`, ahead of copying layout from `TickInspection.svelte`?

{?} ScratchRootOrigin: `scratch.*` (first seen in `19b9b92`) has no ancestor in this tip at all — TS scratch material here stays under `px.s1.exp.*`. Was `scratch.*` a deliberate Python-side root decision or an incidental naming choice during the port? Bites section 2d's "sharpest unresolved addressing conflict."

## 52417a9 (investigate/s1-badge-pixels-5607611)

### What it is

An investigation-only commit, authored 2026-09-06 21:30:52 (`git log -1 --format=%B 52417a9`: "investigation: record S1 badge pixel findings across dev set"), branched from the same checkpoint the mining synthesis already covers as tip `5607611` — `52417a9:investigations/s1-badge-pixels/README.md:3` states "Base checkpoint: `56076112878edf4ac167d97c66f9f83082abe2b1`" and forbids touching the implementation branch: "Implementation continues on lab/s0-viewer... Do not merge or modify the implementation branch as part of this investigation." (`52417a9:investigations/s1-badge-pixels/README.md:4-5`). Its own commit metadata records a real parent, `135b2503a293ad97b1801972f4532e0ffd815ea3` (`git cat-file -p 52417a9`), which this shallow clone does not hold (`git cat-file -t 135b2503a293ad97b1801972f4532e0ffd815ea3` → "bad object") — a small correction to the synthesis's blanket claim that `%P` is empty for "all eight" tips: that was true only of the eight tips it mined, not of this ninth one, and `git diff --stat main 52417a9` (1,264 files, +155,539/-139,825) remains non-semantic for the same reason the synthesis names for the others.

The investigation asks one question: is the ~5–6% of pixels inside the S1 badge detector's footprint that no thresholded Part owns (`px.s1.exp.maskComponents.part.blackComponents` / `whiteComponents`, see below) recoverable material or noise. It ships three markdown documents, one PNG, and a Node probe script under a new corpus location, `investigations/s1-badge-pixels/` — a fourth top-level home for CV findings alongside the synthesis's `docs/`, `docs/orchestration/`, and `docs/handoffs/`.

### Addressing

Confirms the synthesis's §2b reading exactly: the S1 experimental PCR YAML this tip investigates is the identical file cited there, using `px.s1.exp.maskComponents.part.blackMask` / `px.s1.exp.badgeAssembly.badgeCandidates` and `fn.s1.exp.*` calls (`52417a9:packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml:1-12,44`).

It adds one addressing fact the synthesis missed for this line: a reserved second segment, `px.pql.<PrincipleComponentRender name>`, where the experimental PQL/PCR interpreter self-publishes its own execution record as an ordinary Part — `pxc.set(\`px.pql.${composition.PrincipleComponentRender}\`, run)` (`52417a9:packages/alg/src/exec/pql.ts:108`), and, for the ABFeature tournament wrapper, an array of per-variant records at `px.pql.<Name>.results` — `pxc.set(\`px.pql.${composition.PrincipleComponentRender}.results\`,results)` (`52417a9:packages/alg/src/exec/stage.ts:43`), stated in prose at `52417a9:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:12` and pinned by tests at `52417a9:tests/unit/pql.test.ts:24` and `52417a9:tests/unit/pql-stage.test.ts:22`. This sits alongside the synthesis's `px.view.*` finding as a second precedent for a reserved-but-unenforced `px.` second segment carrying execution history rather than production values — direct support for round-five's proposed `px.run.<name>` segment, and a small addition to the "two unreconciled scratch conventions" finding (synthesis §2d): counting `px.pql.*`, the corpus now has three places execution-derived material can land (`px.<stage>.exp.*` TS scratch, `scratch.*` Python root, `px.pql.*` run records), none cross-validated against the others.

No mount/root-external-to-address material appears anywhere in this tip — consistent with, not contradicting, the synthesis's "missing" finding for `5607611`, since this investigation was committed ~2 hours before `lab/pxc-root-mounts` (21:30:52 vs `43e6ea3` at 23:27:11).

### Viewer and PCR render

`TickInspection.svelte` and `PcrInspectionHost.svelte` are present and byte-identical to the other eight tips (blobs `0bf6b00`/`30ffdf2`, `git ls-tree 52417a9`), extending the mining preamble's "stable substrate" claim to a ninth tip. But this investigation does not use that shared surface. It ships its own private inspector instead: "One Node host replaces three experiment hosts... a standalone inspector; staging integration remains pending" and "The shared browser-safe JS renderer produces SVG from exact pixel membership... View controls perform no CV calculations" (`52417a9:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:5,10`). That is a third, independently-built inspection surface — distinct from both the shared evidence-workbench Svelte host and the Mermaid-driven S0 viewer the synthesis already names — reinforcing rather than resolving the synthesis's §3 "Avoid: the split ChainSpot never closed" finding.

The investigation's own probe script confirms that split at the code level: `dev-set-probe.mjs` walks `ok.run.ticks` / `tick.calculations` directly off the raw `PqlRun` object to find `badgeCandidates` (`52417a9:investigations/s1-badge-pixels/dev-set-probe.mjs:85-87`) rather than reading anything through a Receipt or a viewer — it had to hand-traverse Tick/Calculation records because no receipt-shaped surface exposed the value it needed.

### Storage

Nothing — no DuckDB, no `ArtifactKind` selection, recorded as missing rather than inferred. This precedes the DuckDB archive (`8cdddec`, committed 22:42:06) by about 70 minutes and by content, so its absence here is chronological, not a disagreement with that tip. The investigation's own outputs (`dev-set-report.json`, `DEV-SET-SUMMARY.md`) are generated to `dev-set-output/` and are not present in this tip's tree, extending the synthesis's "outputs regenerated, never committed" convention (§5 item 6) from the three quick_anno Python stages to a fourth, earlier TypeScript investigation line. Separately, `artifacts/custody-receipts/*.custody.receipt.txt` (`52417a9:artifacts/custody-receipts/DashsTrack.custody.receipt.txt`) is a chain-of-custody log for raw source images — a second, unrelated sense of "receipt" in this corpus that should not be conflated with `contract.ts`'s `Receipt` when transferring vocabulary into pyto.

### Materialization and Ticks

The investigation follows the neon/crop-first, identity-precedes-geometry discipline the synthesis credits to the later Python `quick_anno` line (`6309ff1`, `82f8fc9`) — but does so first, in TypeScript, roughly a day earlier: it ships one comparison image per course ("Each pair is original / cyan detected plus magenta unaccounted," `52417a9:investigations/s1-badge-pixels/README.md:17`) and refuses to assume the cause of a gap: "Antialiasing is a hypothesis, not yet a classification." (`52417a9:investigations/s1-badge-pixels/README.md:20`). This suggests the discipline originates here, not in the Python transfer — worth folding into synthesis §5 as a correction of order, not of substance.

`stage.ts` introduces `pxc.fork()` for per-variant isolation: "A PxC fork snapshots slot and function maps. It shares immutable values, including raster buffers. Each run's writes stay in its own fork." (`52417a9:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:11`; mechanism at `52417a9:packages/alg/src/exec/stage.ts:27-43`). This is a concrete, shipped partial answer to pyto's open `{?} TransactionalTick`: not rollback-within-a-Tick, but fork-per-variant so a failed feature's partial writes never contaminate `Default` or any sibling variant.

The same file's `invokePql` throws loud rather than silently on args/inputs collision — `throw new Error(\`Argument '${name}' shadows a named input.\`)` (`52417a9:packages/alg/src/exec/pql.ts:97`) — a second, independent PQL implementation that treats the shadow case as fatal, adding a data point to (not contradicting) pyto's `{?} SilentRules`, which concerns the production `contract.ts` engine specifically.

REVIEW.md's own open label, `{PartPublication}: canonical child addresses and sourceTickId stamping remain unset by the generic runner` (`52417a9:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:22`), is independently unresolved territory matching pyto's `{?} ObservationSeam`.

### Receipts and telemetry

No `contract.ts`-shaped `Receipt` appears anywhere in this tip's investigation code; the experimental `PqlRun` carries only `call`/`actualCall`/`args`/`inputs`/`output` per Calculation (`52417a9:packages/alg/src/exec/pql.ts:18-23`) — no `opId`, no `artifacts`, no `probes`, no `writes[]` testimony, a strictly thinner record than the production Receipt the synthesis quotes.

This tip's tree also carries a real, twice-stated telemetry-vs-decision rule, unrelated to the investigation itself but directly reusable: a diagnostic gray-pixel count in the ported Tee family logic "was **printed in the sweep log and nothing else**... It never selected or rejected anything... 'LAB gray payload (145 <= max(R,G,B) <= 175) was DIAGNOSTIC ONLY. It never selected/rejected this family. Do not add a gray kill rule.'" (`52417a9:docs/unported/g3-intact-tee-family.md:108`, restated at `:244` and `docs/unported/README.md:88`). This names exactly the failure mode pyto's Receipt/testimony boundary (`{?} ObservationSeam`) should guard against: a number computed for observation must never covertly become a gate.

### Reusable now

- `pxc.fork()` per-variant isolation (`stage.ts:27-43`) is directly portable to pyto's tournament execution (`consumers/discstudio-card/art_registry.py`, `{?} KeepLosers`): isolate every variant's writes at the store layer instead of the registry layer.
- The telemetry-must-never-gate rule (`docs/unported/g3-intact-tee-family.md:108,244`) is a named anti-pattern pyto's receipt design should cite explicitly.
- `px.pql.<Name>` self-published run records (`pql.ts:108`, `stage.ts:43`) give round-five's `px.run.<name>` proposal a second working ancestor beyond `px.view.*`.
- `dev-set-probe.mjs`'s pattern — run one experimental PCR across N corpus courses, aggregate plus per-course table, call out the one qualitative outlier by name (Heritage's 90.78% candidate, `52417a9:investigations/s1-badge-pixels/DEV-SET-INVESTIGATION.md:56-69`) — is a ready template for `{?} CrossProjectReuse` regression checks.

### Quotes

> "Dash's Track yields 18 badge candidates, containing 37,295 unique pixels... 94.34845% coverage."
> — `52417a9:investigations/s1-badge-pixels/README.md:8-10`

> "The enclosed `UnaccountedPx` are overwhelmingly threshold-transition pixels at boundaries between already-associated semantic Parts, not unexplained interior material."
> — `52417a9:investigations/s1-badge-pixels/INVESTIGATION.md:10`

> "A PxC fork snapshots slot and function maps. It shares immutable values, including raster buffers. Each run's writes stay in its own fork."
> — `52417a9:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:11`

> `if (Object.hasOwn(args,name)) throw new Error(\`Argument '${name}' shadows a named input.\`);`
> — `52417a9:packages/alg/src/exec/pql.ts:97`

> "'LAB gray payload (145 <= max(R,G,B) <= 175) was DIAGNOSTIC ONLY. It never selected/rejected this family. Do not add a gray kill rule.'"
> — `52417a9:docs/unported/g3-intact-tee-family.md:108`

> "One Node host replaces three experiment hosts... a standalone inspector; staging integration remains pending."
> — `52417a9:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:10`

> "{PartPublication}: canonical child addresses and sourceTickId stamping remain unset by the generic runner."
> — `52417a9:packages/alg/src/stages/S1/exp/badge-assembly/REVIEW.md:22`

### Questions for the owner

{?} PqlRunRootStatus: Should `px.pql.<Name>` become a formally reserved second segment (like `px.view.*`) in pyto's address tree, given it now has two independent ChainSpot precedents (`pql.ts:108`, `stage.ts:43`)? Bites: round-five address tree, `{?} ObservationSeam`.

{?} ForkAsTickTransaction: Is per-variant `pxc.fork()` (`stage.ts:27-43`) an acceptable substitute for `{?} TransactionalTick`'s rollback semantics, or does pyto still need true intra-Tick rollback separately from tournament isolation?

{?} TelemetryGateRule: Should pyto adopt the ChainSpot rule verbatim — a value computed only for logging/inspection must never influence its own Calculation's output — as a receipt-design constraint, not just a convention note?

{?} ReceiptWordCollision: Given `custody.receipt.txt` and `contract.ts`'s `Receipt` are unrelated concepts sharing one English word in ChainSpot, should pyto rename one of its own uses to avoid the same ambiguity when transferring vocabulary?

## b9d05cd (lab/dashs-ternary-edge-pattern)

Commit message: "Preserve Dash matrix source galleries, shared readings, and resumed H18 proof / Archive includes all 72 Dash variant outcomes, 20 explicit missing-seed rows, independent connection/spacing checks, numerical profiles, and a filterable source gallery. Add directly viewable H18/H16 comparisons and immutable resumed H18 measurements." (`git log -1 --format=%B b9d05cd`). It is a grafted root (`git show -s --format=%P b9d05cd` empty), so `git diff --stat main b9d05cd` is a whole-tree comparison, not semantic (1244 files, +154056/-139825) — consistent with the existing synthesis's note that this applies to all eight mined tips (`chainspot-branch-mining.md:30`). This tip previously failed the mining agent on output formatting (`questions.md:353-355`); this pass reads it directly.

### What it is

Not one experiment but a checkpoint archive of five sibling investigations under `experiments/dashs-track-edge-sensing/`, all diagnostic sensing prototypes over the 18 DashsTrack holes, explicitly not a fix to pathfinding: "It is an additive experiment checkpoint. It does not modify clean stages or claim to have fixed pathfinding." (`b9d05cd:experiments/dashs-track-edge-sensing/README.md:5-6`). The five: `ternary-edge` (fixed-ray RGB material classifier, EDGE/RIBBON/TERRAIN/UNKNOWN), `bend-follower` (beam-search paired-boundary tracker, capped at 90 poses), `dash-transition-render` (whole-raster Gaussian-derivative transition field, no seeds at all), `straight-edge-pattern` (opposite-wave anomaly search on straight holes), and `matrix-review` (a Sweep-matrix harness running 72 variant outcomes across all 18 holes plus 20 missing-seed rows). Confirms the earlier synthesis's structural finding directly: `packages/alg/src/exec/contract.ts` in this tip is the same blob `62b5d75` as all eight previously mined tips, and `PcrInspectionHost.svelte`/`TickInspection.svelte` are blob-identical too (`30ffdf2`, `0bf6b00`) — this ninth tip is authored on the identical stable substrate, not a fork of it.

### Addressing

This tip adds a concrete, previously-uncited data point to the `SlotRef`-openness finding already in the synthesis (§2c, `contract.ts:15-23`): production LAB code writes a Part address with **no** `px.`/`fn.` prefix at all. `scripts/chainspot-lab/sweep/matrix/materials.ts:347` computes `const materialAddress = \`matrix.material.${key}\`;` and then does `input.board.has(materialAddress)` / `input.board.set(materialAddress, material)` (`b9d05cd:scripts/chainspot-lab/sweep/matrix/materials.ts:350,354`) against `board: PxC` (imported as `import { pxFn, type PxC } from '@chainspot/alg/exec/board'`, `:18`). This is a real PxC write in shipped tooling, not a hypothetical: `PxC` is documented as "PxC's browser-safe address space" and `ExecBoard` is kept only "as a compatibility name because this is the existing production board evolving in place" (`b9d05cd:packages/alg/src/exec/board.ts:38-39`). Same pattern in the gateway adapter: `board.set('ternary.sourceSpec',{outDir})` and `board.set('ternary.materialTrace',trace)` (`b9d05cd:experiments/dashs-track-edge-sensing/ternary-edge/run_gateway.cjs:29,22`) — `ternary.sourceSpec`/`ternary.materialTrace` are declared consumes/produces on a real `ABFeatureSet` feature (`:25-26`) and appear as `declaredConsumes`/`writes` in the resulting receipt with no `px.` prefix (see Receipts below). This does not contradict the existing synthesis — it already found unprefixed `SlotRef` examples in `contract.ts` itself — but it upgrades the finding from "the type allows it" to "a live, currently-used LAB tool does it, at the top level, for the actual matrix cache." Where the synthesis proposed adopting a `scratch.*`-under-`px.` or reserved-segment discipline (§2e), this tip is a fresh instance of exactly the unenforced-root problem the synthesis already flagged at §2d ("ChainSpot has two answers to the same question… neither validates it") — now a third instance (`matrix.*`) alongside `scratch.*` (Python) and bare `badgeStage.*` (contract.ts examples). No mount, `px.view.*`, or content-digest-root construct appears anywhere in this tip — **missing**, consistent with §2d/§2e's finding that the mounts design is specific to `43e6ea3`.

### Viewer and PCR render

**Missing.** Nothing in this tip renders through `TickInspection.svelte`, `PcrInspectionHost.svelte`, `/lab/pcr`, or any PCR/Tick construct. `packages/alg/src/exec/pcr.ts` and `packages/alg/src/exec/gateway.ts` are present in the tree (shared substrate) but nothing under `experiments/dashs-track-edge-sensing/` imports or exercises them; `grep -ril "PrincipleComponentRender"` over the whole tip returns zero hits. All rendering here is bespoke: `matrix-review/render.py` (source comparison plots, "Green marks a sensor acceptance", `b9d05cd:experiments/dashs-track-edge-sensing/matrix-review/README.md:34`), `matrix-review/gallery.py` (filterable failure-group gallery, `:31,34`), `bend-follower/render.py` (evidence renderer that "does not run sensing, sample pixels, read annotation/target files, select a winner, or draw alternate paths", `b9d05cd:experiments/dashs-track-edge-sensing/bend-follower/README.md:3`), and `dash-transition-render`'s Matplotlib fields. These are single-purpose Python/JS scripts writing static JPEG/PNG, with no Storybook, SvelteKit, or per-Tick six-section layout — `{?} StorybookAsVehicle`'s lean (copy layout, discard toolchain, `questions.md:332-335`) is unaffected; this tip simply never used the toolchain in either direction.

### Storage

No DuckDB, no relational backend — `grep -ril duckdb` over the tip is empty. Storage here is: (a) the `PxC`/`ExecBoard` in-memory cache described above (`matrix.material.<key>`), with explicit hit/miss/write counters (`MatrixMaterialCounters`, `b9d05cd:scripts/chainspot-lab/sweep/matrix/materials.ts:31-38`) — a concrete, code-level instance of `{?} HitDefinition`'s "any Part or Calculation being used is a hit" (`questions.md:28-31`), now with real counter fields (`requests`, `hits`, `misses`, `writes`, `profileHits`, `profileMisses`, `profileWrites`); and (b) flat content-addressed files: `output/transition-fields.npz` ("regenerate instead of committing its ~140MB contents", `b9d05cd:experiments/dashs-track-edge-sensing/dash-transition-render/README.md:44`), `output/bands.json`, and `SOURCE-FREEZE.json` with an aggregate SHA-256 (`b9d05cd:experiments/dashs-track-edge-sensing/BEND-FOLLOWER-REVIEW.md:7-8`). No `ArtifactKind` union or declared-kind dispatch appears in this tip's own code — it relies on the shared `contract.ts` substrate only where it goes through the ABFeature gateway (ternary-edge), and plain files everywhere else. This is consistent with the synthesis's §4 point 5 finding that non-gateway experiment storage on this codebase is "filename-as-address, with no kind and no digest" — matrix-review and dash-transition-render are further examples of that same pattern, not a counterexample.

### Materialization and Ticks

No `Tick`, `PrincipleComponentRender`, or PCR composition anywhere in this tip's own code (grep confirms `\bTick\b` hits are all in the shared `packages/alg/src/exec/*.ts` substrate, never invoked here). The closest local analogue is the `ABFeatureSet` operation/feature model used by `ternary-edge` and `bend-follower`'s gateway adapters — one `OperationSpec` per feature (`ternary-edge.sample-and-classify`), OFF/ON ablation runs, single operation per run. This matches the synthesis's own framing of ABFeatureSet/PCR as a stable substrate the branches sit on top of, but here the tip stays one level below PCR (operations, not Ticks). Materializer conventions match the synthesis's §5 list closely and add confirming citations: **neon-first is absent here** — this tip predates or bypasses the quick_anno neon convention; instead its acceptance discipline is "source-visible result" tables with named pixel positions (`b9d05cd:experiments/dashs-track-edge-sensing/ternary-review/RESULTS.md:11-17`), functionally the same "identity precedes geometry" spirit (§5 point 2) applied via cross-section review rather than crops. The matrix-review README explicitly states the LAB-cache identity fields — "source bytes, frame, seed, masks, sensor parameters and calculation revision" (`b9d05cd:experiments/dashs-track-edge-sensing/matrix-review/README.md:23`) — which is a textual answer to `{?} CacheInvalidation` (what a revision means for a CV stage, `questions.md:244-247`): revision here is a named field alongside source/frame/seed/masks/params, not a single content hash, closer to ChessLab's own `implementation_sha256`-excludes-helpers compromise the synthesis already flagged as a limitation (§ "The production Receipt is the target shape").

### Receipts and telemetry

Two receipt shapes worth the owner's attention, both real (not proposed):

1. **A one-level-up wrapper around the per-Tick `Receipt` shape**, from a real run: `gateway-receipt.json` carries `featureId`, `traceHash`, and OFF/ON pairs each with `runId`, `invocation`, `setId`, `planFingerprint`, `ownedFeatureIds`, `enabledFeatureIds`, `manifestHash`, wrapping an `operations[]` array whose single entry is a byte-for-byte match to the synthesized `Receipt` fields (`opId`, `frozenCalculations` with `identityScope`/`limitation`, `declaredConsumes`/`declaredProduces`/`actualConsumes`/`actualProduces`, `writes` with `kind: "new-address"`, `probes: []`, `artifacts: []`) — `b9d05cd:experiments/dashs-track-edge-sensing/ternary-edge/output/gateway/gateway-receipt.json`. This confirms the synthesis's target `Receipt` shape end-to-end from a live gateway run, and shows the `writes[].kind` two-value convention (`"new-address"` vs `"replacement"`, per §4 point 3) is live in TypeScript too, not just the Python `core.py:62-66` citation already in the synthesis.
2. **A wholly different receipt schema for identity/lineage**, not mentioned anywhere in the existing synthesis: `artifacts/custody-receipts/DashsTrack.custody.receipt.txt`, `schema=chainspot-chain-of-custody@1`, per-Tee rows of `summary`, `evidenceRefs`, a `GAP: none (lineage complete)` line, and an `assignment: producer=… score=… rank=… ownership=selected` line (`b9d05cd:artifacts/custody-receipts/DashsTrack.custody.receipt.txt:1-10`). This is the receipt analogue for object-identity/assignment provenance (which Tee got which Badge/Basket and why) rather than for Calculation execution — a third receipt family (execution receipt, custody receipt, matrix-material cache counters) that the owner's engram-table thesis would need to reconcile or explicitly keep separate. **Missing:** no telemetry aggregation across runs (no dashboards, no time-series); each artifact is a single-run snapshot.

### Reusable now

- The `ABFeatureSet` OFF/ON ablation-receipt pattern (`run_gateway.cjs:25-36`) is a small, portable template for wrapping any experimental Python producer behind a declared-slot gateway with an assertable contract (`gateway ABFeature contract failed` check, `:36`) — directly reusable for pyto's own gateway-shaped experiments.
- `MatrixMaterialCounters` (`materials.ts:31-38`) is a ready-made concrete shape for `{?} HitDefinition`'s hit/miss bookkeeping, one level more detailed (separate profile vs. material counters) than anything cited so far.
- The chain-of-custody receipt schema is a reusable pattern for any pipeline needing per-object provenance separate from per-Tick execution receipts.

### Quotes

- "It is an additive experiment checkpoint. It does not modify clean stages or claim to have fixed pathfinding." — `b9d05cd:experiments/dashs-track-edge-sensing/README.md:5-6`
- "const materialAddress = \`matrix.material.${key}\`;" — `b9d05cd:scripts/chainspot-lab/sweep/matrix/materials.ts:347`
- "PxC's browser-safe address space. ExecBoard remains as a compatibility name because this is the existing production board evolving in place, not a second synchronized store." — `b9d05cd:packages/alg/src/exec/board.ts:38-40`
- "This is fixed-heading sensing; it has not changed steering or demonstrated Badge-to-C2 tracking." — `b9d05cd:experiments/dashs-track-edge-sensing/ternary-review/RESULTS.md:3`
- "A count that matches expectation is not evidence, and a bounding box is not an identity." (cited already for `6309ff1`; not present in `b9d05cd` — noting no equivalent identity-precedes-geometry line exists in this tip's own text, closest is the RESULTS.md source-visible tables above) — **missing** in this tip.
- "This is an approximate bounded search, not globally optimal fast marching." — `b9d05cd:experiments/dashs-track-edge-sensing/BEND-FOLLOWER-REVIEW.md:53`
- "Do not turn same-pixel model agreement into independent confidence." — `b9d05cd:experiments/dashs-track-edge-sensing/README.md:62`
- "GAP: none (lineage complete)" — `b9d05cd:artifacts/custody-receipts/DashsTrack.custody.receipt.txt:6`

### Questions for the owner

{?} MatrixAddressRoot: `matrix.material.<key>` is a live, unprefixed PxC address in shipped LAB tooling (`materials.ts:347`) — a third scratch/cache convention alongside ChainSpot's `px.<stage>.exp.*` and Python's `scratch.*`. Should pyto's `scratch`-root decision (round five) also cover cache-shaped addresses like this, or is a cache key exempt from the `px.`/`fn.` discipline entirely?

{?} CustodyReceiptFamily: the chain-of-custody schema (`chainspot-chain-of-custody@1`) records per-object assignment/lineage and is structurally unlike the per-Tick execution `Receipt`. Does pyto's receipt design need a second, explicit receipt family for object identity/provenance, or should custody facts become ordinary Parts read by a Calculation the way everything else is?

{?} OperationLevelReceiptWrapper: the gateway receipt here wraps per-Tick-shaped operation records inside an OFF/ON `ABFeatureSet`-level envelope (`setId`, `enabledFeatureIds`, `manifestHash`). Is this outer envelope something pyto's `PcrRun`/materializer should also carry (e.g., which features/knobs were enabled for a given render), or is it ChainSpot-specific ablation machinery that should stay out of pyto's kernel?

## 881c7e5 (lab/stage-aware-dev4)

### What it is

A dated investigation checkpoint (2026-09-05, one day before the eight previously-mined tips begin) that builds a **truth-assisted referee** for LAB's Sweep pipeline: given a retained Stage run and an annotation file, it restores the actual PxC (no re-execution), does maximum-cardinality bipartite matching between annotated holes and detected objects with a fixed pixel tolerance, and renders a verdict per Stage that distinguishes genuine misses from Tees the annotator never marked visible. Commit message: "Add stage-aware LAB referee with one-to-one scoring, visibility obligations and native diagnostics" (`881c7e5` commit message). `git diff --stat main 881c7e5` is a whole-tree comparison (no merge-base, matching the pattern already noted for the other eight tips) — 1140 files, +110488/-139825 — because `main` (`b1f4c83`) predates the entire LAB CLI (`Scope`/`Search`/`Traverse`/`Sweep`) this tip is built on.

`packages/alg/src/exec/contract.ts` is byte-identical here to the stable blob already established across all eight mined tips (`62b5d75`), as are `src/lib/evidence-workbench/PcrInspectionHost.svelte` (`30ffdf2`) and `TickInspection.svelte` (`0bf6b00`) — confirmed via `git ls-tree 881c7e5`. So this tip sits on the same production substrate; it does not touch it. What it adds instead is grading/diagnostic tooling one layer up, in `scripts/chainspot-lab/`.

### Addressing

**Nothing new, and this is itself informative.** Grepping the extracted tip for `PrincipleComponentRender`, `PQL`, `.mount(`, and `RootMount` returns zero hits; `px\.` appears in 50 files but only in the pre-existing S0-S3 production shape (`px.badges`, `px.baskets`, `px.tees`, `px.source.fullImage`, `px.tees.exp.pcr`, `px.tees.exp.selectionFn` — sampled via `git -C /home/user/samuelpmahan/chainspot show 881c7e5:...`). The `px.<domain>.exp.<name>` scratch shape the synthesis flags as one half of `{?} ScratchRootConflict` (§2d of the mining doc) is already present here a day before `5607611`/`b5a6ae0` — it isn't new to this tip, just further evidence it predates the root-mounts decision entirely. `docs/lab/stage-aware-dev4/DECISIONS.md` and `AUDIT.md` (`881c7e5:docs/lab/stage-aware-dev4/DECISIONS.md:1-39`, `881c7e5:docs/lab/stage-aware-dev4/AUDIT.md:1-15`) never mention a root, mount, or namespace decision — the only "namespace" word in the tip is a UI concept, Search Pages: "Pages are visibility/mutation namespaces, not raster copies" (`881c7e5:scripts/chainspot-lab/README.md:185`), unrelated to PxC addressing. **Missing**, confirmed rather than inferred: this branch does no addressing work at all; it consumes existing addresses read-only.

### Viewer and PCR render

`packages/alg/src/exec/pcr.ts` (93 lines) restates the design principle already known from the synthesis — a PCR composes already-produced Tick testimony and never executes: "PCR has deliberately no run() method: the production gateway is the only execution authority and hands this function the receipts it already produced" (`881c7e5:packages/alg/src/exec/pcr.ts:17-19`). This file's content matches the shape the synthesis describes for the shared substrate; it is not itself an experiment in this tip. Storybook appears in 20 files but only as the pre-existing per-Tick viewer infrastructure already documented in the synthesis §3 — this tip adds no new viewer surface. What this tip *does* add is a separate, non-Storybook diagnostic render: `makeLabeledContactSheet` composes per-hole crop images into one labeled PNG contact sheet (`881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:8,135`), one crop per Tee with an ownership overlay in magenta over accepted pixels (`881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:93-101,133`) — a CLI/file-based inspection artifact, not a browser page, closer in spirit to the "neon-first" materializer convention from the quick_anno tips than to the Svelte viewer.

### Storage

A concrete mechanism not present in the eight already-mined tips: the whole PxC board is serialized with Node's V8 `serialize`/`deserialize` into a flat `pxc.bin` file, one `[address, value]` pair per declared address, and restored later without re-running anything:

> "Explicit address custody: no reflection into a board's private storage." — `881c7e5:scripts/chainspot-lab/sweep/pxcSnapshot.ts:5`

Restoration is checksum-gated at read time: `readStageState` recomputes `digest(bytes)` against `receipt.artifacts.pxc.sha256` and throws "Retained PxC checksum mismatch" on drift, and separately re-hashes the original source image against `receipt.identity.inputSha256`, throwing "Source changed since the retained Sweep" (`881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:106-108`). This is a third storage answer alongside the DuckDB-Wasm archive and the quick_anno flat-file convention already synthesized: a full-board binary snapshot, addressed by content digest, restored cold with no dependency warm-up cost — directly relevant to `{?} WarmupBudget` and `{?} StorageKinds` as a workshop-grade backend that costs nothing to start.

### Materialization and Ticks

No change to the Tick/testimony contract — same byte-identical `contract.ts`. What this tip contributes is a *consumer* discipline for materialized state: the referee never re-executes a detector, only reads what a prior Sweep already retained, stated as a hard rule in the file's own header comment ("Reads the actual Stage PxC. Never executes a detector or writes truth into PxC." — `881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:1-3`) and reinforced in the checkpoint doc: "No Stage promoted or frozen. Frozen clean/ untouched." (`881c7e5:docs/lab/stage-aware-dev4/DECISIONS.md:39`). It also names a batch-level receipt aggregation that spans Ticks rather than reporting one: Sweep's batch mode writes `summary.txt`/`summary.json` per batch root with fields — badges, baskets, raw rings, pre-family tees, visible tees, visible deficit, operation count, runtime, conformance drift, status — each traced to a specific drawable/receipt field (`881c7e5:scripts/chainspot-lab/README.md:232`), including "conformance drift counts receipts whose actual consumes/produces omit a declared slot" — the same declared-vs-actual divergence check the synthesis's §3 flags as viewer-worthy, here computed as a cross-run aggregate statistic instead of a per-Tick warning.

### Receipts and telemetry

Two receipt-adjacent conventions worth carrying into pyto that the synthesis's `Receipt` walkthrough doesn't cover:

1. **A truth-taint field baked into the receipt schema, not a side note.** The audit receipt is explicitly tagged `mode:'TRUTH-ASSISTED-EVALUATION-ONLY'` (`881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:136`), and the LAB CLI records a parallel `TRUTH-TAINT` command-log entry whenever ground truth is used, then refuses a test run that reuses a tainted log: "A later test run reusing a command log that already contains truth taint also fails; use a fresh `LAB_COMMAND_LOG` for an independent test." (`881c7e5:scripts/chainspot-lab/README.md:66`). This is a stronger, enforced version of pyto's "declared vs actual" idea — provenance of *how a value was obtained* (truth-assisted vs blind) travels with the receipt and can fail a run outright, not just warn a viewer.
2. **Telemetry that must never become a filter, stated as a rule with teeth.** `docs/unported/g3-intact-tee-family.md` documents a diagnostic-only signal that was deliberately kept out of any gate: "LAB gray payload (145 <= max(R,G,B) <= 175) was DIAGNOSTIC ONLY. It never selected/rejected this family. Do not add a gray kill rule." (`881c7e5:docs/unported/g3-intact-tee-family.md:108`), repeated as rule 8 of a numbered port checklist: "Never add a gray-payload gate... Twice-stated in the source docs, restated here." (`881c7e5:docs/unported/g3-intact-tee-family.md:244`), and again in the unported README's table (`881c7e5:docs/unported/README.md:88`). The `{?} ObservationSeam` question in `pyto/questions.md:271-273` (should digests/durations live in `receipts` vs. testimony fields) has a sharper ChainSpot precedent here than in the synthesis: telemetry values are legitimate to record but must be structurally incapable of being read by any Calculation as a decision input — "If you want its telemetry back, emit it on a drawable," never a gate.

### Reusable now

- **`matchObjects`** (`881c7e5:scripts/chainspot-lab/sweep/verdict.ts` — actually `stageAudit.ts:25-50`): a dependency-free Hungarian-algorithm maximum-cardinality, minimum-distance matcher with dummy columns so an implausible match is never forced, and unique-identity/finite-coordinate validation that throws rather than silently coercing. Directly reusable for pyto's own truth-comparison tooling (`{?} VerificationOracleStamp` territory).
- **Visibility as independent evaluator metadata, never inferred from detection.** `judgeVisibleTees` treats `PARTIAL`/`INVISIBLE`/`UNKNOWN` truth labels as inputs a grader must be handed, not derived: "An unreviewed missing target makes S3 UNKNOWN, not PASS." (`881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:52-54`). This is a clean, testable answer to how a receipt-based grader should treat "the annotator didn't say" versus "the detector missed it" — pyto's `explain_changes`/oracle work has no equivalent axis yet.
- **`classifyBadges`** (`881c7e5:scripts/chainspot-lab/scoreboard/verdict.ts:63-96`): a pure, corpus-free five-way verdict classifier (OK/GARBAGE-LABEL/LOW-CONFIDENCE/COLLISION/UNREAD) with a documented, evidence-derived threshold (`881c7e5:scripts/chainspot-lab/scoreboard/verdict.ts:30-40`) — a template for pyto Calculations that need a defensible knob instead of a magic number.
- **The `./lab` cold-start discoverability contract** (`881c7e5:scripts/chainspot-lab/README.md:19-42`): `--help`/`tutorial`/`scope --help` work before `npm install`; a TypeScript-backed command fails loudly with the exact fix ("Run: ./lab setup") rather than a stack trace. Matches pyto's `{?} WhoWritesJS` requirement that "every brief must be executable cold by an agent."

### Quotes

- `881c7e5:packages/alg/src/exec/pcr.ts:17-19` — "PCR has deliberately no run() method: the production gateway is the only execution authority and hands this function the receipts it already produced."
- `881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:1-3` — "Reads the actual Stage PxC. Never executes a detector or writes truth into PxC."
- `881c7e5:scripts/chainspot-lab/sweep/stageAudit.ts:52-54` — "Visibility is independent evaluator metadata, never guessed from whether ALG found the object. An unreviewed missing target makes S3 UNKNOWN, not PASS."
- `881c7e5:scripts/chainspot-lab/sweep/pxcSnapshot.ts:5` — "Explicit address custody: no reflection into a board's private storage."
- `881c7e5:docs/lab/stage-aware-dev4/AUDIT.md:9` — "Auditor declares that uncertainty and uses the owner's 7 px total forgiveness; it does not optimize per-course shifts against coordinates or silently weaken production truth matching."
- `881c7e5:docs/unported/g3-intact-tee-family.md:108` — "LAB gray payload (145 <= max(R,G,B) <= 175) was DIAGNOSTIC ONLY. It never selected/rejected this family. Do not add a gray kill rule."
- `881c7e5:scripts/chainspot-lab/README.md:66` — "A later test run reusing a command log that already contains truth taint also fails; use a fresh `LAB_COMMAND_LOG` for an independent test."
- `881c7e5:scripts/chainspot-lab/README.md:230` — "It never loads Annotation truth implicitly. A normal single-image Sweep remains unchanged."

### Questions for the owner

{?} SnapshotVsMaterialization: `pxc.bin` (whole-board V8 serialize, digest-gated) is a third storage answer beyond the DuckDB archive and quick_anno flat files. Should pyto's materials store treat a full-board content-addressed snapshot as a first-class backend kind, or is per-address kind (already leaning-adopted) sufficient and this stays workshop-only?

{?} TruthTaintAsReceiptField: should pyto's `Receipt`/testimony carry an explicit provenance mode (blind vs. truth-assisted vs. proposal) the way `mode:'TRUTH-ASSISTED-EVALUATION-ONLY'` does here, so a downstream consumer can refuse to treat a tainted result as production evidence — this looks like a concrete mechanism for `{?} ProposalsNotFacts` and `{?} ConflictingEvidence`.

{?} VisibilityAxisInOracle: pyto's replay/oracle work (`{?} VerificationOracleStamp`, `{?} InputPartsChangedScope`) has no equivalent to "the truth-holder marked this UNKNOWN, so a miss is neither pass nor fail." Should the oracle contract add a third outcome bucket beyond match/mismatch?

{?} TelemetryGateBoundary: is there an enforcement mechanism intended for pyto analogous to ChainSpot's repeated documentation-only rule against gray-payload gating, or does pyto rely on the same "state it twice in prose" discipline?
