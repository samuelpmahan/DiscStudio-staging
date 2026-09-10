# Card cascade as a PxC smoke test: findings (task 78)

The owner's brief: "Findings are first-class. Strengths noted; each friction
written as a proposal Part with its `for`, then the simplest workaround."
The Parts themselves are in `src/cards-findings.js` (published as
`proposal.cards.*` on the studio board, so `runtime.select('proposal.cards.')`
and the editor's findings strip read the same list). This page is the prose.

Everything here stays lowercase: a proposal is a part until the owner promotes it.

## What was built

- The model is four cascade layers as Parts: `px.discstudio.cards.global`,
  `px.discstudio.cards.projection.<shelf|bag|single|competition>`,
  `px.discstudio.cards.instance.<p>.<discId>` (only where an override exists).
- Composition is one Tick, `Cascade:<discId>`, a chain of two Calculations:
  `fn.cards.effective` (three layers in, tokens plus provenance out) then
  `fn.cards.apply` (the preset with the tokens applied). The existing
  `Card:<discId>` Tick binds the applied preset instead of `px.presentation.<id>`.
- The four projections are the four places the existing chain was already
  called from: the shelf bag grid, the sidebar and lineup thumbs, the Component
  Editor card, the OnTheCourse overlay.
- PQL reads: `fn.cards.query` over `px.discstudio.cards.projection.*`,
  `px.discstudio.cards.instance.*` and `px.discstudio.cards.effective.*`.
- Receipts: `cards-recompose` is one composition with the four chains as Ticks;
  a projection "changed" when its `fn.card.compose` step was computed, not reused.

## Strengths

(filled at integration)

## Frictions, each with its `for` and the simplest workaround

(filled at integration)
