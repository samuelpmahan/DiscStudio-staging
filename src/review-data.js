/** Declared review requirements; never claims automatic human acceptance. */
export const reviewItems = [
  { id: 'domain', label: 'Shared domain & Shelf', parts: [
    { id: 'identity', reviewId: 'identity', label: 'Manufacturer + mold + physical disc identity', action: { href: '#/shelf', label: 'Inspect Shelf' }, verification: 'Edit once, then inspect the same disc on the Course.' },
    { id: 'bags', reviewId: 'bags', label: 'Named bags use shared physical-disc references', action: { href: '#/shelf', label: 'Inspect membership' }, verification: 'Add one disc to two bags; removing membership must not delete it. Inspect fn.disc.format.bagExport to confirm authored Bag order and physical IDs are retained.' },
    { id: 'persistence', reviewId: 'persistence', label: 'Drafts, photos and changes survive reload', action: { href: '#/shelf', label: 'Inspect saving' }, verification: 'Download/reload a draft; samples are labelled and optional flight values remain optional.' }
  ] },
  { id: 'presentations', label: 'Composition & OnTheCourse', parts: [
    { id: 'bindings', reviewId: 'bindings', label: 'Every field is discoverable; identity text is editable', action: { href: '#/components?node=maker', label: 'Edit manufacturer' }, verification: 'Move or restyle Manufacturer and Mold; add a custom domain field.' },
    { id: 'reuse', reviewId: 'reuse', label: 'One presentation works for Single and DiscBattle', action: { href: '#/components', label: 'Edit the shared design' }, verification: 'Inspect the shared Card and Course output after a preset edit, then fn.disc.format.shareImage. Ported painter art is reused; generic card node geometry stays on the existing presentation Calculation.' },
    { id: 'footage', reviewId: 'footage', label: 'Compose on footage, export a transparent overlay', action: { href: '#/course', label: 'Inspect Course' }, verification: 'Background footage and editor selection must never appear in the exported PNG.' },
    { id: 'states', reviewId: 'states', label: 'Independent states, scores, highlights and winner', action: { href: '#/course', label: 'Inspect comparison states' }, verification: 'Duplicate a state, edit scores, return to the earlier state. Scores are not Disc properties.' }
  ] },
  { id: 'infrastructure', label: 'Constraints, PxC & feedback', parts: [
    { id: 'constraints', reviewId: 'constraints', label: 'PutterWarz composes reusable rules', action: { href: '#/competition', label: 'Inspect rule results' }, verification: 'Bag ≤5; exactly 1 mold; exactly 3 throws/team/completed round. Open rounds show pending.' },
    { id: 'trace', reviewId: 'trace', label: 'Real PQL path and memoized Parts are inspectable', action: { href: '#/components?trace=1', label: 'Inspect px.render.*.art/card/svg and the fn.disc.format.shelfSheet/shareImage/bagExport PQL calculations; repeat unchanged inputs to confirm reuse and deterministic output bytes.' },
    { id: 'feedback', reviewId: 'feedback', label: 'Item comments persist and export with checkpoint identity', action: { href: '#/components', label: 'Return to editor' }, verification: 'This checklist is neat’s review-handoff component with local item comments. Nothing auto-accepts work.' }
  ] }
];
