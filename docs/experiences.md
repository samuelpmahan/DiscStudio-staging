# DiscStudio Experiences

Status: Experience definition Parts load into the existing Studio board from
`src/experiences.js`. The #/experiences frame is live: six definitions discovered
from `px.studio.experiences` — UDS usable with its photo/paint specializations,
the other five defined with their existing views linked and their Experience
integration honestly pending. Frame context publishes under
`px.studio.uds.context.*` on use. [CLOUD-START.md](../CLOUD-START.md) carries the
remaining cloud pass.

## Definition

An **Experience** is a reusable description of something a person can do with
Parts: its purpose, the material it works with, the available actions, and the
lenses through which the person directs and inspects the result.

An Experience can remain useful indefinitely. Someone can explore, change their
mind, add material, repeat an action, compare outcomes, leave, and return. It does
not require every action to run or a particular next Experience to start.

This keeps the useful shape of a ChainSpot Stage: a name, purpose, named material,
executable Calculations, and visible results. ChainSpot's S0 intake names its
downstream consumer and an `exit_when`; `createPqlStage()` owns one composition
and can compare implementations on forked boards. Here, **each action can invoke
a composition; the Experience offers the actions**. A Stage can supply an action
without turning the whole Experience into a pipeline. Its experiment/comparator
machinery is available when comparing implementations is useful, not required
for opening a shelf.

**P&C** is Sam's name for the whole Parts and Calculations system, including the
store and query/composition machinery previously discussed as PxC/PQL. Existing
code identifiers remain valid; this is not a core API migration.

Experiences are Studio Parts loaded into its existing P&C store. Their actions use
existing commands, Calculations and PQL execution. A lens reads their bound material and results.
The definition does not introduce a second store, executor, or renderer.

## Small contract

The full interaction contract below guides the build. The initial definition
Parts carry the available shared requirements, specializations and source bindings;
loading a definition does not implement its interactions.

| Field | Meaning |
| --- | --- |
| `id`, `for` | Stable identity and the person's purpose. |
| `bindings` | Roles such as disc, bag, design and authored state, resolved to existing Part addresses. A role may be unfilled. |
| `actions` | Named things the person or agent can do. Each declares its needed bindings, existing command/composition, changed or produced material, and any external effect. |
| `lenses` | Ways to see and manipulate that material, retaining its source addresses. A gallery, inspector and canvas can belong to one Experience. |
| `outcomes` | Useful, inspectable results the person can keep. These are checkpoints, not mandatory exit conditions. |
| `continuations` | Other Experiences offered with explicit bindings carried forward. |

Each Experience lives directly under **`px.studio.<experience>.*`**. The loaded
`px.studio.experiences` index names the six general definition Parts.

| Address | Meaning |
| --- | --- |
| `px.studio.uds.definition` | Shared UploadDiscToShelf requirements and actions. |
| `px.studio.uds.photo.definition` | `UDS[photo]`: refers to the shared definition; adds only photo-specific needs. |
| `px.studio.uds.paint.definition` | `UDS[paint]`: refers to the same definition; adds only painting-specific needs. |
| `px.studio.uds.paint.families` | The actual 16-family painter vocabulary, imported from the existing implementation. |
| `px.studio.discviztype.*` | Shared photo/paint depiction choices, usable by UDS and graphics creation/export. |
| `px.studio.creategraphics.onthecourse.discspotlight.definition` | A purpose-specific definition referring to general CreateGraphics and the OnTheCourse purpose. |
| `px.studio.uds.context.<id>.*` | Proposed engagement material; not created by loading definitions. |

`UDS[DiscVizType]` is specialization by a named Part. Brackets describe the
composition to a reader; the current PQL parser has no new bracket syntax.
`specializes` is an ordinary address reference, not an automatic inheritance
engine. General requirements stay on UDS. Each variant records its differences.
The focused build must explicitly compose those Parts through existing Calculations.

A context binds the definition, specimen, depiction and view choices; it does not
own another copy of discs, bags or presets. An unfinished context is valid.
Missing material prevents only the action that needs it: no photo prevents a
photo action, never general UDS or painting.

Context navigation changes the view. Editing a fact changes a domain Part.
Editing a design changes a presentation Part. Making a graphic changes authored
composition material. Those scopes must be visible at the point of action.
Existing undo remains available for supported workspace changes; selecting a
disc must not silently author a highlight or winner.

An AI can choose and compose the same declared actions. Determinism belongs to
the action with its captured inputs; a suggestion is not proof of what ran.
Keep the resulting receipt and actual produced addresses inspectable. Browser
file selection, download requests, IDs and timestamps remain explicit boundaries.

## The Experience catalog

The names are Sam's. The interaction choices below are proposed demo defaults.

### UploadDiscToShelf

**For:** add a physical specimen with a useful visual identity, with or without
a photo. Deterministic painting is an intended depiction path, not a temporary
placeholder or failed upload. A generated depiction does not invent physical facts.

**General UDS:** identify the specimen; supply/correct facts; inspect its depiction;
add to Shelf and optionally a selected bag; keep one creation command/undo. Cancel
leaves no half-created specimen. Continue with the same disc into exploration,
bag membership, or a spotlight. Those requirements apply to both variants.

| Specialization | Only the additional requirements |
| --- | --- |
| **UDS[photo]** | Choose/replace an image, inspect its preparation, preserve the source when choosing another depiction type. Local file reading and image preparation are effect boundaries. |
| **UDS[paint]** | Generate and inspect candidates using existing painters; vary family, seed and colors; retain the selected recipe; reproduce it. No image file, network or image-generation model is needed. |

The same DiscVizType selection must be usable by graphics creation/export. A
specimen's identity and facts do not change when its depiction changes. Retain
the chosen paint recipe and any supplied photo so switching can be reversible.

**Useful result:** one physical Disc identity and its referenced identity records,
with the same disc available to all later Experiences. Another copy of the same
mold is another specimen; adding an existing specimen to a bag is not duplication.

**Today:** `discComposer()` and `disc.create` provide one command/undo for creation
and optional membership. Photo-free creation already produces painted art through
`fn.disc.art`. `fn.art.assign` / `px.art.assignment` spread the painter families
across the Shelf and then group related material. `artInputs()` resolves the
actual family, seed, base, accent, target and label; authored overrides already
exist. `painter.mjs` contains 16 seeded families and is dependency-free.

`photoData()` prepares a local image, at most 1024 px, as WebP. There is no image
recognition or crop editor here today. The current renderer always prefers a
valid `disc.photo`, and the current creation command does not accept a complete
authored paint recipe. The build must expose deliberate depiction selection and
retain the recipe atomically with creation. Do not implement choosing paint by
deleting an existing photo. Existing `sample` labels need to distinguish illustrative
seed records from intentional painted depictions.

### ExploreShelf

**For:** find, recognize, inspect and choose from my physical discs, without
already having a bag or graphic in mind.

**Interaction:** browse the whole shelf; search, sort, group and filter; inspect a
disc and its bag memberships; correct a fact; select material for another action.
Clear filters from an empty result. Offer add to bag, create a bag from a selection,
DiscSpotlight, or a Competition lineup according to what is selected.

**Useful result:** a meaningful selection and, when authored, corrected shared
facts. Exploration is useful even when nothing changes and nothing is exported.

**Today:** `runtime.shelf()` produces `px.shelf.view` through `fn.shelf.query`;
search, sort, group, filters and single-disc inspection exist. The Shelf route's
center is currently a bag editor. An explicit whole-shelf working view and a
selection shared by the continuation actions are needed; multi-selection is a
proposed addition, not an existing promise.

### CreateBag

**For:** establish a collection for a round, purpose, or idea, starting empty,
from chosen discs, or from a bag I already like.

**Interaction:** name it in place, choose a starting point, see its contents while
adding or removing references, and reorder. A valid empty bag can be kept. Move
naturally into ManageBags or use its discs in a graphic.

**Useful result:** a named Bag whose ordered members reference the existing
physical discs. Creation does not require a competition, a fixed size or complete
disc facts.

**Today:** `entity.add` creates a Bag; `bag.duplicate`, `bag.membership` and
`bag.reorder` already supply the operations. The current New bag control uses a
browser prompt. Inline creation and “from this selection” connect these pieces.

### ManageBags

**For:** keep several useful collections and adapt them as my needs change.

**Interaction:** switch, rename, duplicate and inspect bags; add/remove members;
reorder; compare membership. Offer explicit **add to another bag** and **move
between bags** where useful: moving removes one membership as well as adding
another. Show that editing a disc's facts affects every bag that references it.

**Useful result:** independently editable collections sharing the right specimens.
Removing a membership leaves the specimen on the Shelf. Duplicating a bag copies
its references and order, not the physical discs. A referenced bag's deletion
refusal identifies what still uses it.

**Today:** switching, renaming, duplication, deletion checks, membership and order
exist. A simultaneous membership comparison/transfer lens is the nearby addition.
Any new multi-bag move should be one atomic command and one undo; two unrelated
dispatches would expose a half-move. Competition limits apply in that context,
not as a universal restriction on bag creation.

### CreateGraphics[OnTheCourse]

**For:** give selected material a visual purpose and make a usable composition.
OnTheCourse supplies one of the two contexts below.

**Interaction:** enter with selected material or choose it here; choose purpose,
design and frame; directly edit the bound composition; inspect where a displayed
fact comes from; choose whether a style edit affects this instance, a shared
design, or shared defaults. Keep a design or authored state, compare another,
return to the source disc to correct it, or continue to export.

**Useful result:** a composition over the selected Parts and a visible graphic
produced by the shared render chain. A reusable design retains bindings rather
than copies of the selected disc's text.

**Today:** `#/course` and `#/components` provide live compositions, saved designs,
field bindings, the card cascade, frame/layout controls and authored states.
The work is to make entry purpose and edit scope legible and carry context between
them. Selecting a different purpose should not reset a design or modify facts as
a side effect. The same card primitive serves multiple purposes.

### ExportGraphics[OnTheCourse]

**For:** take the graphic I have inspected into the place I intend to use it.

**Interaction:** enter with the same composition and authored state; see exactly
which graphic(s), dimensions, format and background treatment will be generated;
export the current graphic or an explicit set. Keep each job's result or failure
visible, and let the person return to creation with the same context.

**Useful result:** actual PNG/SVG bytes and a receipt identifying the rendered
material and hashes. A browser download request is not proof that the file was
saved, published, or seen by an audience.

**Today:** `planExports()` supports current, all states, vertical states and one
card per lineup disc. `runExportJob()` uses the same `runtime.scene()` and actual
SVG as preview, then `pngFromSvg()` when requested. Jobs currently bind identities
when queued but resolve source values when they run. Their source snapshot is
captured at render time, before asynchronous PNG work. The demo must show that
choice; proposed default for “export what I inspected” is an explicit capture
when enqueueing. A later “use latest values” mode can be explicit. This is local
to export, not a requirement to freeze live Parts across Experiences.

Queue state is page-lifetime; the workspace retains the latest 100 export records.
There is no automatic durable queue or unlimited export history. Footage is local
preview context, and transparent PNG/SVG export does not encode a video.

## OnTheCourse supplies purpose

| Purpose | Bound material and what the person does | Existing implementation |
| --- | --- | --- |
| **DiscSpotlight** | One physical disc, a design and frame; optional bag/round context. Make this disc understandable and visually useful in the chosen setting. | `mode: 'card'`, `layout.singlePresetId`, single projection. `singleCardPanel()` and the shared DisplayCard render chain. The card is a component; spotlight is why it is being used. |
| **Competition** | A lineup of disc references, rules/context when present, and authored states. Communicate a comparison or contest: arrange participants, enter scores, inspect derived standings, choose highlights, keep moments. | `mode: 'battle'`, `world.battle`, competition projection and `fn.battle.*`. The separate domain `Competition`, `Team`, `Round` and `Throw` records provide rule/round context where bound. |

`CreateGraphics[OnTheCourse.DiscSpotlight]` and
`CreateGraphics[OnTheCourse.Competition]` specialize the same Experience;
ExportGraphics uses those same contexts. These are not four independent renderers
or a mandatory sequence of screens. A comparison can start without an organized
tournament. A rule-derived standing and a manually authored winner/highlight must
remain distinguishable; the Experience name does not imply new scoring inference.

**Naming assumption:** Competition is the user-facing successor to DiscBattle.
Existing `battle` identifiers and the distinct domain Competition are mapped here,
not renamed or silently merged. A bound context makes their relationship explicit.

## What to connect first

Sam's build order: **build the common Experience frame, then fill Experiences
one by one**. The first cloud pass is the frame plus UDS, starting with chevron-run,
pressed-fern and contour-basin from `px.studio.uds.paint.starterfamilies`. The
broader painter vocabulary remains available. Later passes fill ExploreShelf,
CreateBag, ManageBags, CreateGraphics and ExportGraphics. This is an implementation
order, not a required sequence for people using the product.

Breadth first: complete one small reusable interaction, then use it across the
Experiences it enables. These are proposed additions; the existing operations
above are the implementation starting points.

| Nearby addition | Visible review point | Reuse |
| --- | --- | --- |
| Bound selection and continuation | Choose a disc on the Shelf, open its spotlight, correct its photo, and return to the same composition. Show the same identity at each stop. | Every Experience; one context binding mechanism. |
| Purpose and edit scope | Change this card's accent, then change the shared design. The preview shows the affected instances and makes the scope understandable. | DiscSpotlight and Competition; existing card cascade. |
| Inline bag creation and membership actions | Make a bag from a selection, add a member to another bag, and undo a move in one action. Shared disc facts still agree. | ExploreShelf, CreateBag, ManageBags. |
| General UDS with photo/paint specializations | Add a disc with a chosen deterministic painting and no file; add one with a photo; keep the same general identity/membership interactions. Switch depiction without deleting either source. | UDS, graphics creation and export share DiscVizType. |
| Inspectable export capture | Queue a graphic, change the live design, then inspect which version the queued export actually used. Preserve success and failure evidence. | Both OnTheCourse purposes and every export format. |

A short demo can start anywhere: add a disc with paint or a photo; use the same specimen in two bags;
make its spotlight; add it to a Competition; keep a second authored state; export
the chosen graphic. Returning to correct its nickname should update every live
binding while a previously exported artifact remains identifiable as its own
result. That demonstrates the links working, not six disconnected feature tours.

## Implementation map and evidence limits

| Concern | Existing source to extend |
| --- | --- |
| Loaded Experience definitions | [`src/experiences.js`](../src/experiences.js): `studioExperienceParts`, loaded by `createStudioRuntime`. Prefix queries can consume these Parts like any others; no alternate executor is involved. |
| Identity, schemas and commands | [`src/domain.js`](../src/domain.js): `schema`, `partAddress`, `applyCommand`. `px.domain.Disc.<id>`, `px.domain.Bag.<id>`, related identity and competition records. |
| Publication and execution | [`src/runtime.js`](../src/runtime.js): `publishWorld`, `dispatch`, `shelf`, `cardSteps`, `sceneComposition`, `scene`. `px.studio.world`, `px.presentation.<id>`, `px.comparison.layout`, `px.comparison.states`, `px.render.*`. |
| Shared graphics and scope | [`src/presentation.js`](../src/presentation.js), [`src/cards.js`](../src/cards.js): `cardsEffective`, `cardsApply`, `cardsQuery`; shelf, bag, single and competition projections. |
| Interaction and effect boundaries | [`src/app.js`](../src/app.js): `openComposer`, `discComposer`, `shelfCenter`, `singleCardPanel`, `courseCenter`, `courseInspector`, `runExportJob`. [`src/media.js`](../src/media.js): `photoData`, `pngFromSvg`, `downloadBlob`. |
| Export intent and status | [`src/exports.js`](../src/exports.js): `planExports`, `queueProgress`; `export.record` in the domain reducer. |
| Constraints | [`src/constraints.js`](../src/constraints.js): domain and lineup rules retain pass/fail/pending/unconstrained meanings. |
| Prior Stage pattern | Local `ChainSpot-s0-selected/packages/alg/src/exec/stage.ts`: `createPqlStage`; `packages/alg/src/stages/S0/clean/S0.stage.yaml`. Studio [`src/lab/stages.js`](../src/lab/stages.js): `validateStage`, `drawingFor`, `stageView`; drawings chosen from produced addresses. |
| Existing behavioral evidence | [`tests/experiences.test.js`](../tests/experiences.test.js), [`tests/art.test.js`](../tests/art.test.js), [`tests/bags.test.js`](../tests/bags.test.js), [`tests/shelf.test.js`](../tests/shelf.test.js), [`tests/cards.test.js`](../tests/cards.test.js), [`tests/battle.test.js`](../tests/battle.test.js), [`tests/exports.test.js`](../tests/exports.test.js), [`tests/core.test.js`](../tests/core.test.js). |

Current receipts and run records use composition names, such as
`px.receipt.on-the-course` and `px.run.on-the-course`. Repeating a composition can
replace those Parts. A future Experience history must retain the records it
promises under invocation identities; today's receipt list is not already an
immutable history of every interaction. Similarly, current local view preferences
are not a persisted Experience context. These gaps are explicit work, not reasons
to duplicate the runtime.
