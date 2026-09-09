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
