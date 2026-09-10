/**
 * The findings of the card cascade smoke test (task 78), as Parts. Each is
 * published on the studio board at its `address` when the runtime is created,
 * so `proposal.cards.*` is one PQL prefix query and the Cards page's findings
 * strip, `runtime.select('proposal.cards.')` and a test all read one list.
 *
 * Strengths say where PxC carried the design without a workaround. Frictions
 * are proposals: each carries its `for` (why it would matter), the workaround
 * the editor ships with, and the proposal itself. Everything here is lowercase;
 * a proposal is a part until the owner promotes it (pyto/experiments/cards/FINDINGS.md).
 */
export const findings = [
  {
    address: 'proposal.cards.chainInATick', kind: 'strength',
    text: 'Effective tokens then applied preset is one Tick, Cascade:<card>, a chain of two Calculations; the sequence is inspectable at the Tick boundary and classifyTick names it a chain. Nothing new was needed (task 57).'
  },
  {
    address: 'proposal.cards.prefixQueryForOptionalLayer', kind: 'strength',
    text: 'An instance layer that may not exist is read as the prefix query px.discstudio.cards.instance.<projection>.*, which answers {} instead of refusing a missing address. The refusal of missing reads pushed the design to a query rather than a nullable binding.'
  },
  {
    address: 'proposal.cards.memoIsTheChangeDetector', kind: 'strength',
    text: 'Which cards an edit recomposed fell out of the existing memo: the receipt already says computed or reused per invocation, so recompose() reads its own receipt and no dirty-tracking was written.'
  },
  {
    address: 'proposal.cards.undoUnchanged', kind: 'strength',
    text: 'cards.set is an ordinary command through fn.studio.applyCommand, so px.undo.studio records the world before it and undo is still one sentence.'
  },
  {
    address: 'proposal.cards.retrofitIsOneBinding', kind: 'strength',
    text: 'The retrofit onto four surfaces is one changed binding, preset: in the Card Tick now reads the applied preset Part, plus a projection name at each call site.'
  },
  {
    address: 'proposal.cards.oldDraftsOpen', kind: 'strength',
    text: 'A draft saved before the cascade existed opens unchanged: validateWorld fills the default layers and returns a new world instead of mutating a frozen one.'
  },
  {
    address: 'proposal.cards.changedIsComputed', kind: 'friction',
    for: 'Receipts telling exactly which edit recomposed which cards.',
    text: 'A computed step is not a changed value: setting a token at one layer to the value it already inherits recomputes the card with an identical result and the receipt still says computed. The studio receipt row carries no digest of what was produced (the Python receipt carries produce_sha256).',
    workaround: 'recompose() reports changed = not reused and the page says "recomposed", never "differs".',
    proposal: 'The studio receipt row carries a label hash of each produced value, as the Python receipt does; changed is then a produce label that differs from the previous run of the same address.'
  },
  {
    address: 'proposal.cards.changeIsOneShot', kind: 'friction',
    for: 'The page showing "recomposed" on the cards an edit reached, for as long as the reader looks.',
    text: 'The memo answers "what changed" only in the first run after an edit: the next run of the same composition reuses everything, so a page that recomposes on every render erases its own story one render later.',
    workaround: 'The page recomposes once per render and keeps the run measured right after the edit as the story; a repeated change event with the same value is not an edit.',
    proposal: 'The same as changedIsComputed: a produce label on the receipt row makes "changed" a comparison of two records, not a property of the run that happened to come first.'
  },
  {
    address: 'proposal.cards.reachWithoutComposing', kind: 'friction',
    for: 'The All-cards pane saying which cards inherit a token before those cards have ever been composed.',
    text: 'query(inherits) answers the projections from the projection Parts alone, but its instances come from px.discstudio.cards.effective.*, which only holds cards composed so far; a disc never rendered in a projection is invisible to the query. The reach IS expressible without composing: every disc under px.domain.Disc.* times four projections, minus the instance Parts that override the token.',
    workaround: 'The page counts projections (always known) and labels the instance count "among composed cards".',
    proposal: 'fn.cards.query binds px.domain.Disc.* as well, and a reach query answers from the layers and the domain without composing a single card.'
  },
  {
    address: 'proposal.cards.threeNamesForOneCall', kind: 'friction',
    for: 'Readable Tick names in the recompose receipt (Cascade:shelf, Card:bag) when one disc is composed four ways in one run.',
    text: 'cardSteps now takes the disc id, an address suffix and a Tick label: three names for one call, because Tick names default to the disc id and four chains for one disc would collide.',
    workaround: 'A label parameter; recompose() passes the projection name.',
    proposal: 'The runtime derives a Tick name from what the Tick produces, since the produce address already says what the Tick is.'
  },
  {
    address: 'proposal.cards.memoRingEviction', kind: 'friction',
    for: 'changed staying trustworthy when a session composes many projection-by-disc pairs.',
    text: 'The memo is a 24-slot ring per Calculation address; a session that composes more than 24 projection-by-disc pairs evicts live signatures and the receipt reports a spurious computed that no reader can tell from a real change.',
    workaround: 'The smoke test stays under the ring (twelve discs, the page composes one disc four ways).',
    proposal: 'Memo keyed per produce address, one slot per address replaced on change, the way source() already keeps inputs.'
  },
  {
    address: 'proposal.cards.nodeIdCollision', kind: 'friction',
    for: 'The sponsor lockup as a node appended to the applied preset.',
    text: 'A user preset that already has a node with id sponsor collides with the appended lockup and validatePreset refuses the composed card.',
    workaround: 'The id is reserved and documented; the seed presets have no such node.',
    proposal: 'Node ids that a Calculation appends are namespaced (cascade.sponsor), or the lockup is a layer over the card rather than a node in the preset.'
  },
  {
    address: 'proposal.cards.presetPerDisc', kind: 'friction',
    for: 'The address space of the applied presets.',
    text: 'px.discstudio.cards.preset.<projection>.<disc> is one Part per projection-by-disc pair although only an instance override makes a preset differ per disc: twelve discs give 48 addresses for what is mostly four values.',
    workaround: 'The memo makes the repeats reuse, not compute.',
    proposal: 'The applied preset is addressed by the label of its effective tokens, so identical presets share one Part and a card binds the Part its tokens name.'
  },
  {
    address: 'proposal.cards.classifyBeforeRunning', kind: 'friction',
    for: 'Knowing whether the Cascade Tick would be refused (a backwards read, a duplicate producer) before running it.',
    text: 'classifyTick is exported by the core but the runtime has no way to ask a composition "would you run" without running it; the sibling-read rule is easy to misread as forbidding the chain until task 57\'s carve-out is found.',
    workaround: 'A test reads the recorded PQL document back and asserts classifyTick says chain.',
    proposal: 'runtime.classify(name, ticks): the composition\'s Ticks with their mode and any refusal, computed and on the record, before anything is invoked.'
  }
];
