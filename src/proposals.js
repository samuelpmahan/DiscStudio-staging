/**
 * What running the ChainSpot LAB's Stages inside the studio asked of the studio's
 * own PxC that it could not quite say.
 *
 * The port files its frictions against the LAB as `proposal.lab.*` Parts
 * (src/lab/map.js `finding`). These are the other direction: the studio is the
 * thing under test, the Stages are the load, and each entry below is one place
 * where the studio's execution model, not the Stage, was the awkward one. They
 * are published as `proposal.studio.*` Parts by `createStudioRuntime`, so they
 * are on the board beside the receipts a reader is already reading, and a reader
 * can find them in Inspect → Browse all Parts.
 *
 * Each carries `for` (why it matters, in the words of the thing that hurt),
 * `kind` (`friction` or `strength`), `text` (what happened), `workaround` (what
 * this sprint did instead) and `proposal` (what would remove it). Nothing here
 * is a claim about ChainSpot's own kernel: it is about this browser core,
 * src/core/exec.js, and the adapter over it in src/runtime.js.
 */
export const STUDIO_PROPOSALS = {
  'memo.rasterinputs': {
    kind: 'friction',
    for: 'a Calculation whose input is a raster cannot afford the memo that makes the studio fast for cards',
    text: "The studio memoizes every registered Calculation on `stable({ revision, inputs })` -- a canonical stringify of the input VALUES (src/runtime.js `register`). A card's inputs are a few hundred bytes and the memo is why the comparison re-renders for free. S0's input is 2,097,152 numbers; stringifying it costs more than the crop, and on one capture it can never hit twice, because each Stage reads its own predecessor's produce exactly once.",
    workaround: 'the `fn.lab.*` Calculations are registered with no memo and no freeze of the result, the way the LAB harness registers them (src/runtime.js `registerLabCalculation`), so a Stage pays for nothing it cannot use.',
    proposal: 'key the memo on Part identity rather than Part value: an address plus the material id the producing invocation already recorded. Two calls with the same inputs are then the same call without reading a single sample.'
  },
  'freeze.bigparts': {
    kind: 'friction',
    for: 'freezing is how the studio keeps a published Part honest, and it is O(every sample)',
    text: '`pxc.set` deep-freezes what it publishes (src/runtime.js, `freeze` in src/domain.js), which walks every element of every array. For the world that is nothing; for `px.exp.lab.course.canonicalpixels` it is a two-million-element walk per publish, repeated for each mask and component set a Stage publishes.',
    workaround: 'accepted and measured: the whole pipeline is about a second in the browser, and the guarantee is worth it. Nothing in this sprint weakened it.',
    proposal: 'a Part kind for bulk numeric data (a typed array, frozen by its container and never handed out unfrozen), so immutability costs one object instead of two million.'
  },
  'run.mutabletally': {
    kind: 'friction',
    for: 'the state a run is IN, while it runs, is exactly what a Part may not be',
    text: 'The Course route needs a running tally -- which Stage produced, which refused and why -- and the honest place for it is a Part. But a Part is frozen the instant it is published, so the tally cannot be updated in place: the pipeline keeps a mutable tally in the closure and publishes a CLONE of it after every Stage (src/runtime.js `publishLabRun`).',
    workaround: 'publish a snapshot per Stage. The Part is always a true statement about a moment, and the moments are the Stage boundaries.',
    proposal: 'name the idiom (a snapshot Part per Tick boundary) or give the board an append-only Part whose history is the value.'
  },
  'provenance.noreverseindex': {
    kind: 'friction',
    for: 'a reader who clicks an object on the raster wants to know which Calculation put it there',
    text: 'The receipts say what each invocation produced; nothing says, for one address, which invocation produced it. The Course route answers "which Stage, which Tick, which Calculation" by scanning every `px.receipt.lab-*` trace for a row whose produces include the address (src/runtime.js `labProvenance`).',
    workaround: 'the scan is small and the answer is read off the record, not off a second index the studio maintains.',
    proposal: 'a reserved `px.produced.<address>` Part, or a prefix query over receipts by produce, written by the same code that already records the invocation.'
  },
  'geometry.noframe': {
    kind: 'friction',
    for: 'two Parts of pixel coordinates are only comparable if they name the raster they were measured in',
    text: "Every Stage publishes coordinates in the canonical raster's frame, but only the course graph carries the frame itself. The `course` arrangement, which stands DisplayCards at the holes, therefore has to take whichever Part it was given and derive a frame -- from the Part if it has one, otherwise from the extent of the anchors themselves (src/presentation.js `courseAnchors`).",
    workaround: 'derive and say so: the arrangement reports the frame it used, and the placements carry the anchor they were placed on.',
    proposal: 'a convention that a geometry Part names its frame (`frame: { widthPx, heightPx }` or the address of the raster), so a consumer never guesses the coordinate space.'
  },
  'refusal.wholecomposition': {
    kind: 'friction',
    for: 'one Calculation that cannot run takes down the whole render, not its own Tick',
    text: "Selecting the course arrangement before a course exists refuses `fn.comparison.layout`, and `invokePql` fails the composition -- so the OnTheCourse route renders the studio's visible-model-boundary panel instead of the comparison. That is honest, and it is also all-or-nothing: there is no way to say \"this Calculation could not run; the rest of the composition still did\".",
    workaround: 'the refusal names what to do about it in one sentence ("open Course, give it a capture and run the pipeline"), and the arrangement control offers the route.',
    proposal: 'a Calculation-level refusal the receipt carries as a row (produced: none, reason: …), so a composition can be partly satisfied and still be a record.'
  },
  'exec.carriedthestages': {
    kind: 'strength',
    for: 'what the studio core already had that seven Stages needed and did not have to be given',
    text: "Nothing in src/core/exec.js changed this sprint. The Stages' documents are the LAB's own (S1's YAML, the documents the other Stages' OperationSpecs imply), read by the studio's `readPql` and run by `invokePql`; each Stage became one composition with a receipt and a pyto-run-record the Tick viewer already draws; the prefix query `px.receipt.*` listed the Stage receipts beside the card ones with no change to the Inspect page; and a Stage reading its predecessor's produce by address is the same binding a DisplayCard uses to read a Disc.",
    proposal: 'none: this is the part that worked.'
  },
  'serve.mjsmimetype': {
    kind: 'friction',
    for: 'a demo is not demo-ready if `npm run dev` cannot open it',
    text: "The development server (scripts/serve.mjs) mapped `.js` but not `.mjs`, so `pyto/viewer/embed.mjs` -- which src/app.js imports -- was served as application/octet-stream and Chromium refused the whole module graph under strict MIME checking. The studio simply did not load over `npm run dev`; the browser test never caught it because it serves the page another way.",
    workaround: 'one line: `.mjs` is a JavaScript module too.',
    proposal: 'the browser test should drive the studio over `npm run dev` at least once, so the way a person opens it is the way it is checked.'
  }
};

/** Each proposal as a `proposal.studio.<key>` Part, in one pass. */
export function studioProposalParts() {
  return Object.entries(STUDIO_PROPOSALS).map(([key, value]) => [`proposal.studio.${key}`, { key, ...value }]);
}
