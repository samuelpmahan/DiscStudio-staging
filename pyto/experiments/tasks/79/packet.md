# Task 79

Intent: the preset is the projection layer: the card cascade folds into the existing PxC composer (Component Editor) instead of a second page; global sits under each preset's own background, text, accent, radius, typeface and sponsor, a preset field set to inherit falls through to global, instances sit on top; The whole card section marks each field inherited or overridden with Reset to inherited, All cards is one more component tab with the four live previews and the global tokens, the #/cards route and the findings strip go away, and the seed presets keep their own looks
Starting point: 2d7934fe4661f5c934ee04296f5d9c693ac993c3 (land(task-78): card cascade editor as a PxC smoke test: four card projections (shelf, bag, single, competition) get cascading defaults global -> projection -> instance; each layer is a Part under px.discstudio.cards.*, fn.cards.effective and fn.cards.apply compose the effective card per projection inside the existing card chain, PQL prefix queries find overrides and inheritance, a recompose receipt says which edit recomposed which cards, and a three-pane editor (all cards, per-projection tabs, selected-card inspector) is retrofitted onto the existing surface; every friction is a proposal Part with its for, nothing is promoted)
Verify: npm test
Allow: src tests scripts/browser_test.py pyto/viewer/fixtures pyto/viewer/test pyto/experiments/cards pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
