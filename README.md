# DiscStudio · PxC staging

An independently deployable staging checkpoint: Concept B's warm visual language, Concept A's footage-context/transparent-overlay workflow, and the actual ChainSpot PxC/PQL runtime. The existing DiscStudio Concept A, Concept B and candidate deployments are not modified.

## Open it

- `#/shelf` — physical discs, photos, identity and named bags.
- `#/course` — Single Disc / DiscBattle, footage context, scores, independent states, shared designs and transparent PNG/SVG export.
- `#/components` — Disc / DisplayCard / DiscComp presentation editor. Manufacturer and mold are real selectable, draggable bindings, like every other field.
- `#/competition` — PutterWarz and reusable, parameterized Constraints.

The root and `/concept-b/` alias load the same application. Hash routes work on static GitHub Pages without a server router. There is no account, backend or automatic telemetry upload. Data and review comments are stored locally under staging-specific keys. Keep downloaded drafts as backups.

## Run and verify

Requires Node 22 or later. The application has no npm runtime or build dependencies.

```sh
npm test
npm run build
node scripts/serve.mjs dist
# Open http://localhost:4173/
```

The normal browser verification uses Python 3 and Playwright:

```sh
python -m pip install playwright==1.57.0
python -m playwright install chromium
python scripts/browser_test.py --url http://127.0.0.1:4173/
```

CI runs unit tests, builds the exact commit, starts the static server, executes the real-origin browser checks, emits a neat-compatible review checkpoint, and only then deploys. Browser screenshots, the actual exported PNG, inspection fixture and verification reports are retained as an Actions artifact. The fixture reviewer is explicitly an automated test, never Sam's acceptance.

`python scripts/browser_test.py --embedded` is a local restricted-environment alternative: real JS/SVG/canvas, in-memory localStorage test double. It does **not** prove real origin persistence or HTTP navigation; normal CI mode does.

## Integration contract

The [Experiences contract and demo interaction inventory](docs/experiences.md)
maps UploadDiscToShelf, ExploreShelf, CreateBag, ManageBags and OnTheCourse
creation/export to the existing Parts and actions. It distinguishes current
capabilities from the connections still needed. Definition Parts load under
`px.studio.<experience>.*`; UDS shares general requirements across photo/paint
specializations. The [cloud build brief](CLOUD-START.md) builds the frame first,
then UDS with three existing painters, followed by the other Experiences one at
a time. Create a fresh upload with `python3 scripts/bundle-experience.py`.

`src/domain.js` owns runtime object/field definitions and the immutable command reducer. Adding a displayable field makes it discoverable; the inspector does not have a second field whitelist. Reference traversal is bounded/cycle-safe; unset fields remain available. Domain field metadata controls library grouping/order.

`src/runtime.js` adapts the existing ChainSpot core. Domain changes invoke `fn.studio.applyCommand` through PQL. Rendering invokes field resolution → disc art → card composition → SVG → comparison layout → overlay SVG. Those actual output Parts feed both the preview and PNG export. Memoized values are retained in PxC, matched by full inputs and calculation revision; the trace distinguishes reuse from computation. Memoization is session-local, not a durable cache promise.

`src/presentation.js` is the one graphic implementation. Saved presentations bind to fields rather than copying a particular disc's text. Single and Battle use the same primitive. Inspector selection is not a highlight; authored state is separate from physical-disc facts. CSS/preview pulse motion is not video export.

`src/constraints.js` supplies bag count, distinct mold count, and exact team throw count, composed with AND/OR. Fewer throws is pending for an open round and fails when the round is complete. Extra throws fail immediately. Removing all enabled constraints produces `unconstrained`, not an invented validation pass.

## Review

Use **Review & comments** in the lower right. Each review item has its own link, inspected flag and comment, with the selected object/preset/state context captured. Enter a name and export the inspection JSON to return it to an agent. Nothing is sent automatically. Comments are scoped to the exact source fingerprint and build commit; a newer build does not silently inherit old acceptance.

The checked-in `.neat/items/DS-STUDIO-02.json` declares the work. CI emits an exact-commit item and submission under `/review/` and in the artifact, using neat's review-handoff contract. Human inspection, automated verification, acceptance and promotion remain distinct. See `AGENTS.md`.

## Boundaries

Photos are prepared locally to at most 1024 px and stored as WebP; retain your originals elsewhere. Footage is local preview context and is neither persisted in the draft nor included in transparent export. PNG receipts retain hashes and the resolved facts/preset/state, not repeated copies of every photo. Save the SVG for a self-contained graphic. No automatic publication, reach, sales or performance claims are inferred from edits or exports.

The seeded manufacturer/mold facts and artwork are illustrative sample material, not a maintained product catalog. Product records can be unresolved/custom; flight numbers may be absent. This checkpoint includes no CV, audio/video encoding, cloud synchronization or competitive scoring inference.

Implementation provenance and the original/runtime boundaries are in `docs/PROVENANCE.md`.
