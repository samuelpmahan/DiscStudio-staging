# Focused build: Experience frame first, then UDS[DiscVizType]

Read this first, then `docs/experiences.md` and `AGENTS.md`. This bundle is the
local Studio working snapshot, including uncommitted source. `bundle-source.json`
identifies its branch/base and file coverage; `bundle-manifest.json` hashes the
actual uploaded bytes. It is not a claim to contain the latest upstream P&C or
the entire ecosystem. Do not replace these files with a clone of their base commit.

## Sam's direction

P&C is the name for the whole Parts and Calculations system (including what code
calls PxC/PQL). Experiences are Studio Parts under `px.studio.<experience>.*`.
They are open-ended purposes with actions and lenses, not forced pipeline stages.

UploadDiscToShelf (UDS) has common requirements regardless of depiction. Define
those once. `UDS[photo]` and `UDS[paint]` add their differences. Deterministic
painting is intentional capability: a picture is not required. DiscVizType also
applies to CreateGraphics/ExportGraphics. Preserve shared physical-disc identity.

The human steers; P&C makes the changes reusable, deterministic where possible,
and inspectable. Surface choices in the product where they matter. Ordinary
editing should be easy and reversible. Do not introduce approval on every click.

## Build the frame, then fill it one Experience at a time

First deliver a runnable frame in the existing application: discover the loaded
Experience Parts, choose an Experience, show its purpose and bound material,
render the selected lens/actions, and retain the context when leaving and
returning. General definitions and specialization differences must compose
through the existing P&C machinery. Show which Experiences are defined, currently
being filled, or usable; a named slot is not an implemented Experience. Existing
working Studio views remain available while their Experience integration is pending.

Keep that frame milestone inspectable, then fill **UDS only** in this first pass:

1. UDS shows common identity/facts/membership controls and a deliberate Photo/Paint
   choice. Paint works immediately without a file. Start with just **chevron-run,
   pressed-fern and contour-basin** and a small understandable set of controls.
   The full existing painter source remains bundled; do not spend this pass
   exposing or refining all 16 families. These three are ordinary selected Parts,
   not a second renderer or a hard limit on the reusable capability.
2. A retained paint recipe includes resolved family, seed, base, accent, target
   and label. Recipe selection and any necessary source identity determine the
   same SVG on replay; changing an unrelated selection must not reroll it.
3. One Add creates the specimen, chosen depiction/recipe and optional bag membership
   atomically through the existing command path. One undo removes that creation.
   Cancel creates no specimen. Empty optional facts remain empty.
4. The selected depiction follows the same disc onto the existing Shelf. Allow
   photo/paint switching while retaining both sources and the specimen's identity.
   Use the existing card/export path as a compatibility smoke test; do not build
   the CreateGraphics/ExportGraphics Experiences during this first pass.
5. A saved/imported draft restores the same chosen depiction. Existing drafts
   remain usable under an explicit compatibility default that preserves their
   current appearance. Explain that default in the return report.

Return the frame checkpoint and the UDS checkpoint separately when both UDS paths
are demonstrable, records validate, and the return package below is complete.
Do not implement all six Experiences together, redesign competition
scoring, add a new renderer/executor, or pursue speculative core optimizations.

Working default for new UDS: paint is immediately usable; a person can choose a
photo. This is a stated implementation default, not an assertion Sam chose every
detail. General UDS must never require a photo. Keep general requirements separate
from differences so another DiscVizType can reuse the path later.

Following passes fill ExploreShelf, CreateBag, ManageBags,
CreateGraphics[OnTheCourse], then ExportGraphics[OnTheCourse], one at a time.
Their definitions are already present. Each pass reuses the frame and earlier
capabilities and leaves a runnable, inspectable checkpoint. This order is the
build plan; people using the finished Experiences are not forced through it.

## Where the code is

- `src/experiences.js`: loaded definition Parts. `px.studio.experiences` indexes
  the six Experiences. UDS common and photo/paint definitions already refer to
  one another; their UI and effective specialization composition are your work.
- `src/runtime.js`: `createStudioRuntime`, registration, `publishWorld`,
  `dispatch`, `cardSteps`, `sceneComposition`. Load Parts with the existing board;
  execute through existing PQL. `src/core/exec.js` is this app's real executor.
- `src/domain.js`: `schema`, `applyCommand`, `validateWorld`, `disc.create`,
  reference-preserving bag operations. Declare any new domain fields once here.
- `src/app.js`: `openComposer`, `discComposer`, `compose-add` handler, Shelf,
  `singleCardPanel`, `runExportJob`, draft import/export. Use existing routes.
- `src/presentation.js`: `prepareDiscArt`, `artInputs`, `composeCard`, `cardSvg`.
  A valid photo currently wins unconditionally. Change this using a retained
  depiction choice, not by destroying the photo or silently copying values.
- `src/art.js`: `assignArt` and `shelfItems`. Existing distribution deliberately
  spreads initial families, then groups related discs. Retain this useful policy.
- `pyto/consumers/discstudio-card/port/painter/`: all 16 actual JavaScript painters,
  seeded PRNG, families and fixtures. `render(family, seed, base, accent, target,
  label)` returns SVG. This is code generation of artwork, not an AI service.
- `src/cards.js`: shared cascade and shelf/bag/single/competition projections.
- `src/exports.js`, `src/media.js`: queue planning, photo preparation, PNG encoding.
- `pyto/viewer/RECORD.md`, `adapters.js`, `embed.mjs`: actual shared record contract,
  validation and Tick pages. Python runtime installation is not required for this
  Studio build; the supplied JavaScript runtime is what the app executes.
- `tests/experiences.test.js`, `art.test.js`, `core.test.js`, `shelf.test.js`,
  `bags.test.js`, `cards.test.js`, `exports.test.js`: reusable behavioral evidence.

## Facts that should prevent wasted work

`artInputs()` currently derives a seed from `sampleHue` and includes the label in
the full renderer inputs. A family/seed pair alone is not the entire recipe.
The current `disc.create` accepts a photo but not a full paint recipe. Authored
art fields exist elsewhere; integrate them coherently into the creation command.

The existing adapter freezes Parts and memoizes Calculations over input values.
Reuse that behavior. Definition loading is not an execution receipt and does not
automatically implement `specializes`; compose the selected base/variant through
a small ordinary Calculation when the build needs an effective definition.

`dispatch` generates/overwrites event IDs and timestamps. Compare render outputs
with the same captured material; do not demand identical whole-run timing or
event metadata. Runtime receipts use composition names and can be replaced on
rerun. Retain the specific records you report under run identities/files.

An export job currently resolves source values when it runs. For this focused
build prove preview/export agreement on a held, unchanged composition. Record
the queue-version issue as a follow-up rather than expanding into a queue rewrite.

The legacy `sample` art flag currently includes no-photo artwork. A purposeful
painted depiction of a real specimen is not a claim that its physical stamp looks
like that picture. Use clear labels; don't imply all painted discs are fake samples.

## Run and verify

Requires Node 22+; the app has no npm runtime/build dependencies.

```sh
python3 scripts/bundle-experience.py --verify .
npm test
npm run build
node scripts/serve.mjs dist
```

The manifest verifies the starting snapshot. Run that before editing; afterward
its mismatches are a useful list of changed files, not a reason to overwrite work.
Default server: `http://127.0.0.1:4173/`. Existing browser suite:

```sh
python3 -m pip install playwright==1.57.0
python3 -m playwright install chromium
python3 scripts/browser_test.py --url http://127.0.0.1:4173/
```

Add focused real-browser tests for both UDS variants, canceled/committed creation,
undo, same identity across projections, retained sources while switching, draft
reload, and actual PNG/SVG output. Test pure recipe determinism independently of
browser screenshot/PNG encoder differences. Missing evidence is not equivalence.
Keep the existing suite. The two sealed `evidence/card-render` fixtures are bundled
because the existing shadow-render test requires them; they are not new work scope.

## Return something we can land

Before editing, make a local Git baseline of the verified bundle if your environment
has no repository. It is distinct from the recorded upstream base commit. Never
commit a local environment or credentials. Work locally; no push/publication is
requested by this brief.

Return a zip containing changed/new source files with repository-relative paths,
a patch from your exact bundle baseline, and a file list that states deletions
explicitly. Include the incoming manifest digest, updated contract, test logs,
browser screenshots, representative painted recipes, generated SVG/PNG files,
observed records and a Tick page. Name implementation assumptions and unresolved
decisions with their visible consequences. Separate measured results from human
acceptance. Keep `.neat/items/DS-STUDIO-02.json` and `src/review-data.js` aligned.

The local checkout may advance while you work. A return patch and the byte manifest
allow us to compare your changes with that starting material without overwriting
new local work. Do not send a whole replacement directory as the only handoff.
