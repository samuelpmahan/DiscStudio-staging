# Card cascade as a PxC smoke test: findings (task 78)

The owner's brief: "Findings are a first-class deliverable. Wherever PxC carries
the design effortlessly, note it as a strength. Wherever you feel friction — a
needed workaround, an inexpressible query, a composition that fights back —
write it down as a proposal Part carrying its for (why it would matter), then
keep moving with the simplest workaround that holds."

The Parts themselves are `src/cards-findings.js`, published on the studio board
as `proposal.cards.*` when the runtime is created, so one prefix query, the
Cards page's findings strip, `runtime.select('proposal.cards.')` and
`tests/cards.test.js` all read one list. This page is the prose. Everything
stays lowercase: a proposal is a part until the owner promotes it.

## What was built (the contract is `CONTRACT.md` beside this page)

- **Parts are the model.** `px.discstudio.cards.global`,
  `px.discstudio.cards.projection.<shelf|bag|single|competition>`,
  `px.discstudio.cards.instance.<projection>.<discId>` (only where an override
  exists; cleared ones are tombstoned), `px.discstudio.cards.tokens`.
  The world carries them as `world.cards`; `cards.set` is the one command.
- **Calculations do the composing.** One Tick, `Cascade:<card>`, a chain of
  `fn.cards.effective` (three layers in, six tokens plus provenance out) then
  `fn.cards.apply` (the preset with the tokens painted on, plus the sponsor
  lockup node). The existing `Card:<card>` Tick binds the applied preset.
  The four projections are the four call sites the chain already had: the
  shelf bag grid, the sidebar and lineup thumbs, the Component Editor card,
  the OnTheCourse overlay.
- **PQL finds things.** `fn.cards.query` binds `px.discstudio.cards.projection.*`,
  `px.discstudio.cards.instance.*` and `px.discstudio.cards.effective.*` and
  answers `overrides`, `inherits` and `provenance`, each on the record at
  `px.discstudio.cards.query.<name>`.
- **Receipts tell the story.** `cards-recompose` is one composition with the
  four chains as Ticks (`Cascade:shelf` … `Card:competition`); a projection
  "recomposed" when its `fn.card.compose` step was computed, not reused. The
  acceptance test: a global edit recomposes all four; a projection edit or an
  instance edit recomposes exactly one (`tests/cards.test.js`).
- **The editor.** `#/cards`: All cards (globals) on the left, the four live
  previews with projection tabs and the projection layer in the centre, the
  selected card's instance layer, the last recomposition and the findings on
  the right. Inherited values are shown and marked `global` / `projection` /
  `here`; every override has "Reset to inherited"; undo is the existing undo.

## Strengths (where PxC carried it)

- **chainInATick.** Effective then apply is one Tick and `classifyTick` calls it
  a chain. The Tick boundary is exactly where the cascade becomes inspectable.
- **prefixQueryForOptionalLayer.** A layer that may not exist is a prefix query
  that answers `{}`; the refusal of missing reads pushed the design to a query
  rather than a nullable binding.
- **memoIsTheChangeDetector.** "Which cards did this edit recompose" is the
  receipt's own computed/reused column. No dirty-tracking was written.
- **undoUnchanged.** `cards.set` is a command like any other; undo is still one
  sentence.
- **retrofitIsOneBinding.** Four surfaces, one changed `preset:` binding plus a
  projection name at each call site.
- **oldDraftsOpen.** Defaults are filled at validation without mutating a frozen
  world.

## Frictions (each a proposal Part with its `for`, the workaround shipped, the proposal)

| part | for | workaround shipped | proposal |
|---|---|---|---|
| `changedIsComputed` | receipts saying exactly which edit recomposed which cards | `changed = not reused`, the page says "recomposed" never "differs" | the studio receipt row carries a label hash of each produced value, as the Python receipt's `produce_sha256` does |
| `reachWithoutComposing` | "inherited by N cards" before those cards were ever composed | projections are counted (always known), instances are labelled "among composed cards" | `fn.cards.query` binds `px.domain.Disc.*` too and a reach query answers from the layers and the domain without composing |
| `threeNamesForOneCall` | readable Tick names when one disc is composed four ways in one run | a `label` parameter on `cardSteps` | a Tick name derived from what the Tick produces |
| `memoRingEviction` | `changed` staying trustworthy past 24 projection-by-disc pairs | the smoke test stays under the ring | memo keyed per produce address, one slot per address |
| `nodeIdCollision` | the sponsor lockup as an appended node | the id `sponsor` is reserved | namespaced appended node ids, or the lockup as a layer over the card |
| `presetPerDisc` | the address space of applied presets (48 addresses for mostly 4 values) | memo makes the repeats reuse | the applied preset addressed by the label of its tokens |
| `classifyBeforeRunning` | knowing a Tick would be refused before running it | a test asserts `classifyTick` says chain | `runtime.classify(name, ticks)` on the record before anything is invoked |

The reads the editor needed that could NOT be one query as the board stands:
"which cards would change if I edit this token" for cards never composed
(`reachWithoutComposing`), and "did the card actually differ" (`changedIsComputed`).
Both are noted as findings, per the brief, and both have a proposal that would
make them one query.

## Out of scope, kept out

No theming beyond the six tokens, no competition animation beyond the static
live state, nothing promoted, no PxC fix: the memo ring, the receipt row and
`classifyTick` are described in proposals, not changed.
