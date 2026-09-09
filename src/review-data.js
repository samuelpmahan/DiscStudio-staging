/** Declared review requirements; never claims automatic human acceptance. */
export const reviewItems = [
  { id: 'domain', label: 'Shared domain & Shelf', parts: [
    { id: 'identity', reviewId: 'identity', label: 'Manufacturer + mold + physical disc identity', action: { href: '#/shelf', label: 'Inspect Shelf' }, verification: 'Edit once, then inspect the same disc on the Course.' },
    { id: 'bags', reviewId: 'bags', label: 'Named bags use shared physical-disc references', action: { href: '#/shelf', label: 'Inspect membership' }, verification: 'Add one disc to two bags; removing membership must not delete it.' },
    { id: 'persistence', reviewId: 'persistence', label: 'Drafts, photos and changes survive reload', action: { href: '#/shelf', label: 'Inspect saving' }, verification: 'Download/reload a draft; samples are labelled and optional flight values remain optional.' }
  ] },
  { id: 'presentations', label: 'Composition & OnTheCourse', parts: [
    { id: 'bindings', reviewId: 'bindings', label: 'Every field is discoverable; identity text is editable', action: { href: '#/components?node=maker', label: 'Edit manufacturer' }, verification: 'Move or restyle Manufacturer and Mold; add a custom domain field.' },
    { id: 'reuse', reviewId: 'reuse', label: 'One presentation works for Single and DiscBattle', action: { href: '#/components', label: 'Edit the shared design' }, verification: 'Preset edits must immediately change the actual Course SVG and PNG.' },
    { id: 'footage', reviewId: 'footage', label: 'Compose on footage, export a transparent overlay', action: { href: '#/course', label: 'Inspect Course' }, verification: 'Background footage and editor selection must never appear in the exported PNG.' },
    { id: 'states', reviewId: 'states', label: 'Independent states, scores, highlights and winner', action: { href: '#/course', label: 'Inspect comparison states' }, verification: 'Duplicate a state, edit scores, return to the earlier state. Scores are not Disc properties.' }
  ] },
  { id: 'infrastructure', label: 'Constraints, PxC & feedback', parts: [
    { id: 'constraints', reviewId: 'constraints', label: 'PutterWarz composes reusable rules', action: { href: '#/competition', label: 'Inspect rule results' }, verification: 'Bag ≤5; exactly 1 mold; exactly 3 throws/team/completed round. Open rounds show pending.' },
    { id: 'trace', reviewId: 'trace', label: 'Real PQL path and memoized Parts are inspectable', action: { href: '#/components?trace=1', label: 'Inspect PxC' }, verification: 'Change layout or score and inspect upstream reused material in the actual runtime trace.' },
    { id: 'feedback', reviewId: 'feedback', label: 'Item comments persist and export with checkpoint identity', action: { href: '#/components', label: 'Return to editor' }, verification: 'This checklist is neat’s review-handoff component with local item comments. Nothing auto-accepts work.' },
    { id: 'record', reviewId: 'record', label: 'The composition exports its own pyto-run-record@1 and opens a Tick render', action: { href: '#/course?trace=1', label: 'Inspect the run record' }, verification: 'Route: OnTheCourse with the sample workspace (DiscBattle, three discs) → Inspect PxC ↗. “Export run record ↓” downloads a pyto-run-record@1 the shared validator accepted and keeps it as the Part px.run.on-the-course (14 Ticks, 14 invocations); “Open Tick render ↗” saves a standalone page with one section per Tick. Verified: npm test, node --test pyto/viewer/test/*.test.mjs, and scripts/browser_test.py --embedded, whose new block runs the studio on a real local origin and opens the saved page over file:// with zero network requests. Not verified: a deployed build — scripts/build.mjs (outside this task’s allowed set) copies src/, public/, concept-b/, index.html and docs/, so pyto/viewer/ is absent from dist/; because src/app.js and src/runtime.js import it directly, dist/ does not load at all until that copy list includes pyto/viewer/.' }
  ] }
];
