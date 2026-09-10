# Card cascade: the contract (task 78)

The owner's mission, in his words: "card cascade editor as a PxC smoke test (~3h
timebox)". Four card projections get cascading defaults global -> projection ->
instance, retrofitted onto the existing card surface. Parts are the model,
Calculations do the composing, PQL finds things, receipts tell the story.
Everything stays lowercase: nothing here is promoted, no PxC fix is made.

## The four projections and where they already are

The studio already composes every card through one chain (src/runtime.js
`cardSteps`: Fields -> Art -> Card -> CardSvg). The projections are the four
places that chain is called from:

| projection    | existing call site                                   | preset today       |
|---------------|------------------------------------------------------|--------------------|
| `shelf`       | shelf route, bag grid `article.bag-card` (safeThumb) | `discImage`        |
| `bag`         | sidebar `.disc-row` thumbs, lineup entries, inspector art (safeThumb) | `discImage` |
| `single`      | Component Editor `runtime.card(discId, presetId)`   | the chosen preset  |
| `competition` | OnTheCourse overlay `runtime.scene` (`course.<entry>`)| `layout.presetId`  |

## The token set (small, on purpose)

`background`, `foreground`, `accent` (colors, `#rrggbb`), `font` (`sans` |
`serif` | `mono`), `radius` (integer 0..100), `sponsor` (the sponsor lockup:
a string of at most 40 characters; empty means no lockup).

## The model: `world.cards`

```json
{
  "global": { "background": "#203d36", "foreground": "#fcfbf5", "accent": "#b9d789", "font": "sans", "radius": 16, "sponsor": "" },
  "projections": { "shelf": {}, "bag": {}, "single": {}, "competition": {} },
  "instances": { "shelf": { "buzzz-mint": { "accent": "#d47d54" } } }
}
```

- `global` always carries all six tokens: the root of the cascade never inherits.
- `projections.<p>` and `instances.<p>.<discId>` carry only the tokens they override.
- A saved draft without `cards` gets these defaults when it is validated
  (domain.js `validateWorld`), so old drafts open unchanged.
- `createSeed()` ships one projection override and one instance override so the
  editor opens with something inherited AND something overridden to look at
  (e.g. `projections.competition.sponsor = "CHAINSPOT"`,
  `instances.shelf["buzzz-mint"].accent = "#d47d54"`).

## The command

`{ type: 'cards.set', layer: 'global' | 'projection' | 'instance', projection?, discId?, token, value }`

- `value: null` on `projection` / `instance` clears the override (the token
  inherits again). On `global` it is refused: "the root of the cascade never
  inherits".
- Values are validated per token (colors, font names, radius range, sponsor
  length). Unknown token or projection: refused with the names.
- Dispatched through the ordinary `runtime.dispatch`, so `px.undo.studio`
  already records the world before it: undo is the sentence it always was.

## The Parts (the studio's board uses dots; the brief's `px.discstudio.cards/...`)

Published by `publishWorld` (src/runtime.js), sourced like presets:

- `px.discstudio.cards.tokens` -- the token set: `{ name: { kind, label, ... } }`.
- `px.discstudio.cards.global`
- `px.discstudio.cards.projection.<p>` for each of the four projections (always present, possibly `{}`).
- `px.discstudio.cards.instance.<p>.<discId>` -- only for instances that exist.
  When an instance override is cleared to `{}` the Part is removed
  (tombstoned to `null` the way `publishWorld` already tombstones objects).

Produced by Calculations:

- `px.discstudio.cards.effective.<p>.<discId>` <- `fn.cards.effective`
  `{ projection, discId, tokens: {six}, provenance: { token: 'global'|'projection'|'instance' }, layers: { global, projection, instance } }`
- `px.discstudio.cards.preset.<p>.<discId>` <- `fn.cards.apply`
  the preset with the tokens applied: `background`, `foreground`, `accent`,
  `font`, `radius` set from the effective tokens; when `sponsor` is non-empty
  one text node `{ id: 'sponsor', kind: 'text', binding: '', text: sponsor, ... }`
  is appended bottom-right (inside the card; `validatePreset` must accept it).
- `px.discstudio.cards.query.<name>` <- `fn.cards.query` (see PQL).
- `proposal.cards.<k>` -- the findings, published from `src/cards-findings.js`
  at runtime creation so PQL (`proposal.cards.*`) and the editor read them.

## The Calculations (src/cards.js, pure; registered in src/runtime.js)

```
fn.cards.effective({ global, projection, instances, projectionName, discId })
fn.cards.apply({ preset, effective })
fn.cards.query({ global, projections, instances, effective, name, token? })
```

`cardSteps(discId, presetId, context, entry, suffix, projection = 'single')`
gains one Tick BEFORE `Card:<discId>`, a chain of two Calculations (task 57:
inside a Tick the Calculations are a sequence in declared order, and the Tick
boundary is where the sequence becomes inspectable):

```
Tick `Cascade:<discId>`
  fn.cards.effective  with { global: px.discstudio.cards.global,
                             projection: px.discstudio.cards.projection.<p>,
                             instances: px.discstudio.cards.instance.<p>.* }   (prefix query: {} when none)
                      args { projectionName: <p>, discId }
                      into px.discstudio.cards.effective.<p>.<discId>
  fn.cards.apply      with { preset: px.presentation.<presetId>,
                             effective: px.discstudio.cards.effective.<p>.<discId> }
                      into px.discstudio.cards.preset.<p>.<discId>
Tick `Card:<discId>`  fn.card.compose with preset: px.discstudio.cards.preset.<p>.<discId>   (was px.presentation.<presetId>)
```

`runtime.card(discId, presetId, context, entry, projection = 'single')`;
`runtime.scene(...)` uses `competition`; `safeThumb(discId, preset, projection)`
in app.js passes `shelf` from the bag grid and `bag` everywhere else.

## The runtime API the editor uses (`runtime.cards`)

```
runtime.cards.projections            -> ['shelf', 'bag', 'single', 'competition']
runtime.cards.tokens                 -> the token set (same value as the Part)
runtime.cards.presetFor(projection)  -> the preset id that projection composes with today
runtime.cards.effective(projection, discId, context)
    -> runs composition 'cards-effective' (the Cascade Tick alone) and returns
       the effective Part; the run is on the record like any other
runtime.cards.recompose(discId, context)
    -> one composition 'cards-recompose' with the four projections' chains as
       Ticks named Cascade:<p>, Card:<p>, ... ; returns
       { receipt, cards: { <p>: { svg, width, height, changed: boolean, part } } }
       where changed === the Card:<p> step of this run was computed, not reused.
       This is the acceptance test: after a global edit all four are changed;
       after a projection edit exactly one; after an instance edit exactly one.
runtime.cards.query(name, args)      -> runs 'cards-query' and returns the Part:
    'overrides'          -> every projection and instance override: [{ layer, projection, discId?, token, value }]
    'inherits', { token } -> for each projection, whether it inherits <token> from global,
                            and which composed instances (effective Parts on the board)
                            inherit it: { projections: { <p>: boolean }, instances: [...] }
    'provenance', { projection, discId } -> the provenance map of that effective Part, or null if not composed yet
```

Every query is a Calculation bound to prefix queries (`px.discstudio.cards.projection.*`,
`px.discstudio.cards.instance.*`, `px.discstudio.cards.effective.*`), so the read
is on the record. A read that cannot be written that way is a finding, not a
workaround hidden in the UI.

## The editor (route `#/cards`, nav "Cards")

Three panes, Figma / devtools mental model:

1. Left, "All cards": the six global tokens, editable. Under each, from
   `query('inherits')`: "inherited by N of 4 projections".
2. Center: four live previews in a grid, one per projection, each the actual
   composed SVG of the selected disc for that projection (from
   `cards.recompose`), labelled with the projection name and the preset it uses.
   The selected projection is marked; clicking one selects it. Above the grid,
   projection tabs. Below the grid, the projection layer for the selected tab:
   the six tokens, each marked `inherited from global` or `overridden here`,
   editable, with "Reset to inherited" for an override.
3. Right, the selected card inspector: disc picker; for the selected
   projection x disc, the six tokens with their provenance mark
   (`global` / `projection` / `here`), editable at the instance layer,
   "Reset to inherited" per override. Below: the last recomposition receipt:
   "<layer>.<token> -> <value> recomposed: shelf, bag, single, competition"
   (the `changed` projections of the last `recompose`). Below that, the
   findings strip: every `proposal.cards.*` Part, strengths and frictions,
   each friction with its `for`.

Every edit dispatches `cards.set`, then calls `cards.recompose` for the
selected disc and re-renders. Undo is the existing `undo` action.

## Tests (tests/cards.test.js, node:test)

- effective tokens and provenance over three layers; clearing an override inherits again; `null` on global refused.
- one global edit: `recompose` says all four changed; a projection edit: exactly that one; an instance edit: exactly that one.
- the existing surfaces carry the cascade: `runtime.card(..., 'single').svg` contains the global background; with a `competition.sponsor` override, the scene SVG contains the lockup text and the single card does not.
- PQL: `query('overrides')` lists the seed's overrides; `query('inherits', { token })` matches the world.
- old drafts: `validateWorld` on a world without `cards` fills the defaults.
- every existing test stays green unchanged (fixtures untouched).
