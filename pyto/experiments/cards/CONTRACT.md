# Card cascade, the preset is the projection layer (task 79)

Task 78 built a second page (`#/cards`) beside the PxC composer that already
existed (the Component Editor at `#/components`), with its own token set painted
over the preset. Its `fn.cards.apply` overwrote every preset's background,
foreground, accent, radius and font unconditionally, so the Component Editor's
"The whole card" controls stopped rendering and every preset lost its own look.

The owner's way, which this task implements: **the preset IS the projection
layer.** Nothing is added beside the composer; the cascade is folded into it.

## The model

`world.cards = { global: { background, foreground, accent, font, radius, sponsor }, instances: { <projection>: { <discId>: { <token>: value, ... } } } }`

- `world.cards.projections` is gone. The projection layer of a projection is
  the preset that projection composes with: `shelf` and `bag` compose with
  `discImage`; `single` and `competition` compose with `world.layout.presetId`.
- A preset's own `background`, `foreground`, `accent`, `font`, `radius` and
  `sponsor` ARE its overrides. A preset field set to `null` (or, for `sponsor`,
  absent or `null`) **inherits** from global. `validatePreset` accepts `null`
  for these six fields; `'transparent'` stays a legal background.
- `global` always carries all six tokens; the root never inherits.
- Instances are unchanged: `instances.<projection>.<discId>` carries only the
  tokens it overrides.
- A draft without `cards`, or with the task-78 shape (a `projections` key),
  is normalised at `validateWorld`: `projections` is dropped (its values were
  never the presets'), defaults are filled, nothing is mutated in place.
- **Seed presets keep their looks, and something inherits.** In `createSeed`
  the presets that today carry the global values inherit them instead:
  `broadcast` and `showcase` get `background: null, foreground: null,
  accent: null, font: null, radius: null`; `minimal` keeps its own paper
  background, foreground and accent (overrides) but inherits `font` and
  `radius` (`null`); `discImage` keeps its own background and foreground,
  inherits `accent`, `font`, `radius`. `sponsor` is inherited everywhere
  (`null`) except `broadcast.sponsor = 'CHAINSPOT'` (so the OnTheCourse
  overlay shows the lockup as before). The seed instance override stays:
  `instances.shelf['buzzz-mint'].accent = '#d47d54'`.
  Consequence to embrace, not hide: a global `radius` or `font` edit
  recomposes all four projections; a global `background` edit recomposes the
  two that inherit it (single, competition) and not the two on `discImage`.

## The command

`{ type: 'cards.set', layer: 'global' | 'preset' | 'instance', presetId?, projection?, discId?, token, value }`

- `global`: `null` refused ("the root of the cascade never inherits").
- `preset`: needs `presetId`; sets `w.presets[presetId][token] = value`,
  `null` meaning inherit. This is the same mutation `preset.set` with a patch
  performs, so the Component Editor's existing `preset-color` / `preset-number`
  controls keep dispatching `preset.set` and are, from now on, the projection
  layer editor. Validation as before (colors `#rrggbb` or `'transparent'` for
  background, font names, radius 0..100, sponsor ≤ 40 chars).
- `instance`: unchanged from task 78.

## The Parts

Published by `publishWorld`: `px.discstudio.cards.tokens`,
`px.discstudio.cards.global`, `px.discstudio.cards.instance.<p>.<discId>`
(tombstoned when cleared). **No** `px.discstudio.cards.projection.*` Parts: the
projection layer is `px.presentation.<presetId>`, which is already published.

Produced: `px.discstudio.cards.effective.<p>.<discId>` (`fn.cards.effective`),
`px.discstudio.cards.preset.<p>.<discId>` (`fn.cards.apply`),
`px.discstudio.cards.query.<name>` (`fn.cards.query`).

`proposal.cards.*` is no longer published; `src/cards-findings.js` and the
findings test are deleted (the owner: notes are useless; the record of this
task against task 78 is a computed delta, task 80).

## The Calculations (src/cards.js, pure)

```
fn.cards.effective({ global, preset, instances, projectionName, discId })
   -> { projection, discId, presetId: preset.id, tokens, provenance: { token: 'global'|'preset'|'instance' }, layers: { global, preset: {only the six fields the preset overrides}, instance } }
fn.cards.apply({ preset, effective })      unchanged in shape: the preset with the effective tokens set, the sponsor node appended when non-empty
fn.cards.query({ global, presentations, layout, instances, effective, name, token, projection, discId })
   'overrides'  -> [{ layer: 'preset', presetId, token, value }, ..., { layer: 'instance', projection, discId, token, value }, ...]
   'inherits'   -> { projections: { <p>: boolean }, presets: { <presetId>: boolean }, instances: [{ projection, discId }] }
                   a projection inherits <token> when the preset it composes with (discImage, or layout.presetId) has the field null
   'provenance' -> the provenance map of the composed pair, or null
```

The Cascade Tick (in `cardSteps`, before `Card:`), still a chain of two:

```
fn.cards.effective  with { global: px.discstudio.cards.global, preset: px.presentation.<presetId>, instances: px.discstudio.cards.instance.<p>.* }  args { projectionName, discId }  into px.discstudio.cards.effective.<p>.<discId>
fn.cards.apply      with { preset: px.presentation.<presetId>, effective: px.discstudio.cards.effective.<p>.<discId> }  into px.discstudio.cards.preset.<p>.<discId>
```

`fn.cards.query` binds `presentations: px.presentation.*` and
`layout: px.comparison.layout` instead of the projection Parts.

`runtime.cards` keeps `projections`, `tokens`, `presetFor`, `effective`,
`recompose`, `query` with the same signatures. `recompose(discId, context)`
returns the same `{ receipt, cards: { <p>: { svg, width, height, part, changed } } }`.

## The editor: fold into `#/components`

- Delete the `#/cards` route, its nav link, `go-cards`, `cardsSidebar`,
  `cardsCenter`, `cardsInspector`, `cardsFindingsStrip`, `cardsProjectionEditor`,
  and the CSS that only that page used. Keep and reuse `tokenControl`,
  `cascadeResetButton`, `cardPreviewTile`, `cardsCascadeReceipt` (renamed as you
  like), the token-row / provenance-chip / preview-grid styles.
- `componentTabs` gains a fifth tab `['AllCards', 'All cards']` (ui.component
  === 'AllCards'). On it the center shows the four live previews grid from
  `runtime.cards.recompose(ui.discId, context())` (each tile: projection,
  the preset it composes with, `data-projection-preview`, `data-changed`,
  provenance chips) with the Specimen disc select above, and the inspector
  shows the six global tokens (`data-control="cascade-token" data-layer="global"`)
  each with "inherited by N of 4 projections" from `query('inherits')`, the
  last-recomposition line, and the undo row. The sidebar stays
  `componentSidebar`.
- In `nodeInspector`'s "The whole card" section, the existing background,
  text, accent and radius controls stay as they are (they dispatch `preset.set`)
  and each gets: the shown value = the effective value (the global one when the
  preset field is null), a mark "inherited from global" / "overridden here",
  and for an override a "Reset to inherited" button
  (`data-action="cascade-reset" data-layer="preset" data-preset="<id>" data-token`)
  that dispatches `preset.set` with `{ [token]: null }`. Add the two missing
  fields the same way: typeface (select sans/serif/mono) and sponsor lockup
  (text, maxlength 40). The "Transparent card background" check keeps working.
- Below it, a subsection "This disc, this projection": a projection select
  limited to the projections that compose with this preset (`DisplayCard`
  presets: single, competition; `discImage`: shelf, bag), and the six tokens
  at the instance layer for `ui.discId` (`data-layer="instance"
  data-projection data-disc`), each marked `global` / `preset` / `here`, with
  Reset for an override. The recomposition line under it.
- Every cascade edit (global, instance, and the preset controls) sets
  `ui.lastCascade = { edit, result: null }` and render() takes the one
  `recompose` for the All cards tab and the inspector's line exactly as task
  78's `cascadeSet` comment explains (recompose once per render, never in the
  handler, or `changed` is erased).
- `window.discStudio.cards()` keeps returning `ui.lastCascade`.

## Tests

`tests/cards.test.js` rewritten for the new layers:
- seed: broadcast inherits background (null) and overrides sponsor; discImage overrides background; the instance override exists.
- `validateWorld` fills defaults for a draft without `cards` and drops a task-78 `projections` key, without mutating a frozen world.
- effective/provenance over global -> preset -> instance; a preset field set to null inherits again; null on global refused; a preset edit through `preset.set` changes provenance to `preset`.
- recompose: a global `radius` edit changes all four; a global `background` edit changes exactly single and competition; a `preset.set` on `discImage.accent` changes exactly shelf and bag; an instance edit changes exactly one.
- the Cascade Tick is a chain; the recompose receipt names the four Ticks; runRecord validates.
- the existing surfaces carry the cascade: the OnTheCourse overlay carries the broadcast sponsor lockup; the single card does not carry a sponsor when broadcast's sponsor is set to null; the `minimal` preset still renders its paper background (`#f9f7ef`) after the retrofit.
- the Component Editor's preset controls are live: after `preset.set` broadcast background, `runtime.card('buzzz-mint','broadcast', ctx)` carries the value.
- query('overrides') lists preset-layer and instance overrides; query('inherits') matches the world.
- sponsor node: as before.

`tests/core.test.js` stays as task 78 left it unless a count moves; the two
viewer fixtures (`pyto/viewer/fixtures/discstudio-display-card.json`,
`tests/fixtures/serial-run-record.json`) are regenerated from the real runtime
if and only if their bytes change (they will: the Cascade Tick now binds
`px.presentation.<id>` instead of a projection Part); note it.

`scripts/browser_test.py`: replace the task-78 cards section with the same
checks on the Component Editor: All cards tab, edit global radius -> four
previews `data-changed="true"`; edit global accent -> shelf stays (the instance
override), three change; on the DisplayCard tab edit the preset accent control
(`preset-color` data-key accent) -> the All cards tab shows single and
competition recomposed and shelf/bag not; Reset to inherited on that field ->
`discStudio.world.presets.broadcast.accent === null` and the control shows the
global value; instance edit on single -> exactly single; no horizontal overflow
at 1536 and 390 wide. Screenshot the All cards tab to `out/cards.png`.
