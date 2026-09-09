# Art tournament — results, promotions and retained losers

Four studios (`foundry`, `signal`, `cartography`, `botanical`) each shipped
three seeded disc-art families plus a Single and a Battle card renderer against
one shared design contract. Three judges scored every item over eight criteria
at 0–3, so each item's ceiling is **72** (8 × 3 × 3 judges).

Everything below is a record. **No studio directory or render was deleted.**
Losing variants are preserved exactly as they were judged, under
`studios/<studio>/` (source, README, manifest, self-check) and
`renders/<studio>/` (SVG + PNG + contact sheets + lint output + PCR testimony).
They are the receipts for the scores in this table and for the code that was
promoted out of them.

---

## 1. Full tally

Scores arrived from the three judges under three different key spellings for
the same item (`studio/studio/item`, `studio/item`, `studio/studio:item`);
they are normalised to `kind:studio/item` here and summed.

| # | kind | studio | item | judge scores | total /72 | outcome |
|---:|---|---|---|---|---:|---|
| 1 | single | botanical | `render_single` | 23 + 23 + 23 | **69** | **PROMOTED** |
| 2 | family | botanical | `nodding-seedhead` | 23 + 23 + 22 | **68** | **PROMOTED** |
| 3 | family | botanical | `pressed-fern` | 23 + 23 + 22 | **68** | **PROMOTED** |
| 4 | single | foundry | `render_single` | 23 + 23 + 22 | **68** | retained |
| 5 | single | cartography | `render_single` | 23 + 22 + 22 | **67** | retained |
| 6 | battle | foundry | `render_battle` | 22 + 22 + 22 | **66** | retained |
| 7 | battle | signal | `render_battle` | 23 + 22 + 21 | **66** | **PROMOTED** |
| 8 | family | cartography | `wind-rose` | 23 + 22 + 20 | **65** | **PROMOTED** |
| 9 | single | signal | `render_single` | 23 + 21 + 21 | **65** | retained |
| 10 | battle | botanical | `render_battle` | 22 + 22 + 20 | **64** | retained |
| 11 | family | cartography | `fairway-plat` | 23 + 22 + 19 | **64** | retained |
| 12 | family | foundry | `halftone-screen` | 22 + 22 + 20 | **64** | retained |
| 13 | family | foundry | `register-mark` | 23 + 21 + 20 | **64** | retained |
| 14 | family | cartography | `contour-basin` | 22 + 21 + 20 | **63** | retained |
| 15 | battle | cartography | `render_battle` | 22 + 21 + 20 | **63** | retained |
| 16 | family | signal | `chevron-run` | 22 + 22 + 19 | **63** | retained |
| 17 | family | signal | `sweep-clock` | 23 + 22 + 17 | **62** | retained |
| 18 | family | foundry | `hot-foil` | 22 + 19 + 18 | **59** | retained |
| 19 | family | signal | `score-bug` | 22 + 19 + 17 | **58** | retained |
| 20 | family | botanical | `block-print` | 20 + 17 + 15 | **52** | retained |

Per studio: **botanical** took the top single and two of the three promoted
families; **cartography** took the third family; **signal** took the battle;
**foundry** placed four items in the top thirteen and promoted none — it was
never far behind and never first.

---

## 2. Judges

Three judges scored. **This stage received judge 1's card in full and only the
summed scores from judges 2 and 3** — their per-item annotations and `keep`
flags were not carried into the promotion input, and nothing has been invented
to fill the gap. Selection was therefore made on the tally, with judge 1's
written reasoning used to break the one tie (see §3).

### Judge 1 — bag-card disc golfer; favours instant recognition and phone legibility

> Reviewed baseline/sheet.png, all four sheet-42px-lineup.png, all twelve
> per-family sheets, all four sheet-cards.png plus native 400px card PNGs, and
> the module surfaces (FAMILY_PARAMS / CALCULATIONS / layout+details handling).
> Independent stroke-floor audit run over all 42px SVGs (see botanical craft
> notes).

Judge 1's best picks (their 23s): `foundry/register-mark`,
`foundry/render_single`, `signal/sweep-clock`, `signal/render_single`,
`signal/render_battle`. Every item judge 1 wrote up carried `keep: true` — this
judge cut nothing.

Judges 2 and 3: best picks not recoverable from the promotion input.

---

## 3. What was promoted, and from where

### Families → `consumers/discstudio-card/paint_families.py`

| slug | from | tally | notes |
|---|---|---:|---|
| `pressed-fern` | `studios/botanical/families.py` | 68 | |
| `nodding-seedhead` | `studios/botanical/families.py` | 68 | |
| `wind-rose` | `studios/cartography/families.py` | 65 | |

The three highest-scoring families, taken in tally order. Two come from the same
studio; no per-studio quota was applied, because none was specified and the
scores were not close enough to justify inventing one (`wind-rose` at 65 leads
the next family, `fairway-plat`, by only one point, but `nodding-seedhead` and
`pressed-fern` at 68 lead everything by three).

The code is **verbatim** from the studio modules. The two studios shipped
byte-identical `_check`, `_rgb`, `mix`, `luma` and `stroke_for` helpers, so
those are shared; their number formatters differ (botanical collapses `-0` to
`0`, cartography keeps `-0`), so both are kept as `_bn` and `_cn` and every call
site was rewritten to the right one. Equivalence was then proved rather than
assumed: **360 renders** (3 families × 8 seeds × 5 palettes × 3 targets)
compared byte-for-byte against the original studio modules, **0 mismatches**.

`paint_components.py` keeps its `render()` signature. It now imports
`paint_families`, exposes `CLASSIC_FAMILIES + PROMOTED_FAMILIES` as `FAMILIES`,
and dispatches promoted slugs **before touching the RNG**, so the four
originals render exactly as before.

### Card renderers → `consumers/discstudio-card/card_render.py`

| function | from | tally | notes |
|---|---|---:|---|
| `render_single` | `studios/botanical/cards.py` | 69 | the tournament's highest-scoring item of any kind |
| `render_battle` | `studios/signal/cards.py` | 66 | tie broken on the judges' stated reason |

`render_battle` was a 66–66 tie between `signal` and `foundry`. It went to
`signal` on judge 1's reasoning, which is about the thing a battle card exists
to do:

> The score is the largest object on the card, which is exactly right for a
> battle and exactly what foundry, cartography and botanical all got backwards.

against foundry's:

> battle_standard-400.png: score chip glyph is smaller than the flight
> numerals — the wrong thing wins the eye on a battle card.

The promoted code lives verbatim beside the seam in `_card_botanical.py` and
`_card_signal.py`; `card_render.py` is the thin, registrable surface
(`render_single`, `render_battle`, `CALCULATIONS`). The **only** edit to either
studio source was inlining the two colour helpers (`mix`, `contrast_ink`) that
`signal/cards.py` imported from its own `families.py`, copied verbatim, so the
module stands alone. Equivalence proved the same way: all four sample cards ×
three widths compared against the studio modules, **0 mismatches**.

### The cross-studio graft

Judge 1 named exactly one small, specific defect that a graft could fix:

> The one thing that costs it: with manufacturer and mold empty, `_maker_line`
> silently substitutes the note, so the card prints 'FIRST RUN' in the mold slot
> with no signal that the mold is unrecorded — cartography and botanical both
> say 'UNRECORDED MOLD' instead.

That defect belongs to `foundry/render_single`, which was **not** promoted, so
no graft was needed: the promoted `botanical` single already prints
`UNRECORDED MOLD`, and the promoted `signal` battle falls back to the
`physicalDiscId` (`DISC-1`) rather than promoting the note. Both behaviours are
now pinned by
`test_card_render.test_an_unrecorded_mold_is_marked_not_papered_over_with_the_note`.
No other graft was named by a judge, and none was invented.

### Known follow-up (not a promotion decision)

A Single plate and a Battle plate now speak two different visual languages —
warm botanical stock versus a dark broadcast lower third. The tally scored the
two card kinds separately and they did not agree on a studio. Unifying them is
a design call, so it was left to a later pass rather than decided here by
whoever happened to be assembling the module.

---

## 4. What was not promoted, and why

**Families ranked 4th and below.** `fairway-plat` (64), `halftone-screen` (64),
`register-mark` (64), `contour-basin` (63), `chevron-run` (63), `sweep-clock`
(62), `hot-foil` (59), `score-bug` (58), `block-print` (52). Only three family
slots were open; these lost on points. Three are worth naming because the
margin was one point and judge 1 rated two of them at the very top of the
field — `register-mark` ("the most legible mark in the entire field at 42"),
`sweep-clock` ("reads instantly at 42 … and it is concentric, so it still looks
like a disc") and `chevron-run` ("the only mark that actually says 'speed'").
Judges 2 and 3 did not agree, and the tally is the tally.

Two failures were diagnosed rather than merely outscored, and are recorded so
the next pass does not repeat them:

* `foundry/halftone-screen` — "That gap between tiers is the family's core
  problem for a bag card — the badge I see at 42 is not the art I bought at
  220."
* `signal/score-bug` — "the art's fake score bar sits next to the card's real
  SCORE panel and the two compete — the one place a family should stay quiet,
  it shouts." Scored 1/3 on card legibility, the lowest single criterion score
  anywhere in the tournament.

**Card renderers.** `foundry/render_single` (68) and `cartography/render_single`
(67) lost the single by one and two points. `foundry/render_battle` (66) lost
the battle on the tie-break above; `botanical/render_battle` (64) and
`cartography/render_battle` (63) lost on points. All four remain intact and
runnable in their studio directories.

---

## 5. Judge 1's per-item annotations, verbatim

Reproduced exactly as submitted. Judge 1's card was truncated by the promotion
input partway through the last entry; the cut is marked.

### foundry / halftone-screen — family — 20/24, keep

identity-at-42px 2 · composition-at-220 3 · palette-behavior 3 · seed-variation 2 · craft 3 · reuse-surface 3 · originality 2 · card-legibility 2

> sheet-42px-lineup (1,1)-(3,1) cool, (4,1)-(6,1) dark, (7,1)-(8,1)+(1,2) warm: at 42 the screen collapses to ~6 fat dots and reads 'bubbles' — distinct from the baseline four at (4,4)-(7,4) but generic. sheet-halftone-screen (1,1) at 220 is a different animal: a fine duotone ramp with register ticks and a knocked-out MAKO plate, genuinely handsome. That gap between tiers is the family's core problem for a bag card — the badge I see at 42 is not the art I bought at 220. Cool seeds (1,1)(4,1)(7,1) are near-interchangeable.

- identity-at-42px — sheet-42px-lineup (1,1): six blobs; distinct from baseline but reads as generic dots, and does not predict the 220.
- composition-at-220 — sheet-halftone-screen (1,1)/(4,1)/(7,1): screen ramp + register ticks + label plate, well balanced across the face.
- palette-behavior — rows 1/2/3 of sheet-halftone-screen: cool, dark (yellow field, dark dots) and warm all coherent; accent is the single ink and nothing else.
- seed-variation — sheet-halftone-screen (1,1) vs (4,1) vs (7,1): angle and ramp direction change but the read barely does.
- craft — min stroke 12.2 units = 1.00 device px at 42; clip holds, label only at 220, lint and determinism clean.
- reuse-surface — FAMILY_PARAMS names the seed-driven fields and carries an explicit 42/96/220 tier table; CALCULATIONS key fn.discArt.halftone-screen correct.
- originality — halftone is a worn motif; the register-tick framing is the fresh part.
- card-legibility — in sheet-cards battle_standard-400 the screen reads as texture in the art well — no identity at card scale.

### foundry / register-mark — family — 23/24, keep

identity-at-42px 3 · composition-at-220 3 · palette-behavior 3 · seed-variation 2 · craft 3 · reuse-surface 3 · originality 3 · card-legibility 3

> sheet-42px-lineup (3,3)-(8,3) and (1,4)-(3,4): crosshair to the rim + four tint-stepped quadrants + centre bullseye. This is the most legible mark in the entire field at 42 and it is concentric, so it still reads as a disc rather than a sticker. Native register-mark-cool-3-220.png confirms the 220: offset registration lines, corner crop marks, a clean two-ring bullseye and a legible MAKO plate at (bottom-centre). Only real failure is seed: (3,3), (4,3) and (5,3) are the same disc to my eye, so three of these on a bag would not be tellable apart.

- identity-at-42px — sheet-42px-lineup (3,3): unmistakable at thumbnail, nothing in the baseline row (4,4)-(7,4) is close to it.
- composition-at-220 — register-mark-cool-3-220.png: crosshair, quadrants, crop marks and bullseye balance the face; label plate sits clear of the art.
- palette-behavior — sheet-register-mark rows 1/2/3: dark (yellow/charcoal) is loud but internally consistent; accent carries quadrant tints, crosshair, rings and crop marks.
- seed-variation — sheet-register-mark (2,1) vs (5,1) vs (8,1): rotation plus which quadrant is solid — too subtle to distinguish two discs on a bag.
- craft — 1.00 device px floor at 42, clip clean, label 220-only, lint 0 failures, byte-identical across a separate interpreter run.
- reuse-surface — FAMILY_PARAMS is honest about what seed rotates vs which quadrant inks; signature and CALCULATIONS mapping are directly registrable.
- originality — a press registration target as disc art is a genuinely new idea here and it doubles as a sighting mark.
- card-legibility — foundry/cards/battle_standard-400.png, DISC-2 well: still reads as a crosshair at ~90px.

### foundry / hot-foil — family — 19/24, keep

identity-at-42px 2 · composition-at-220 3 · palette-behavior 2 · seed-variation 2 · craft 3 · reuse-surface 3 · originality 2 · card-legibility 2

> sheet-hot-foil (1,1) cool-220: faceted die, raked sheen band, 32-tooth knurl ring, keyline — a convincing hot-stamp. Row 2 (dark) is the best of the three palettes; row 1 (cool) is the weakest thing foundry shipped, a navy polygon on mid-blue where the knurl teeth are the only thing carrying the identity. sheet-42px-lineup (2,2)-(4,2): at 42 the badge is a dark mass with a light slash and, cool-palette, sits close to being any dark blob.

- identity-at-42px — sheet-42px-lineup (2,2): hex mass + streak reads, but cool contrast is thin and the knurl is the only family tell.
- composition-at-220 — sheet-hot-foil (1,2) dark-3-220: die, sheen and knurl ring all land; label plate clear.
- palette-behavior — sheet-hot-foil row 1 (cool) is muddy navy-on-blue; row 2 (dark) and row 3 (warm) are strong. Accent = the foil, used with intent.
- seed-variation — sheet-hot-foil (2,1) hex vs (5,1) vs (8,1): side count and rake angle change; visible but modest.
- craft — 1.00 device px floor at 42; clip, label tier, lint and determinism all clean.
- reuse-surface — FAMILY_PARAMS enumerates die shape, rotation, rake and knurl phase plus the tier table.
- originality — foil-stamp badge is a familiar print conceit; the knurl ring is the distinguishing move.
- card-legibility — foundry/cards/single_gallery-400.png: at 240px in the gallery well it is handsome, but at the battle card's ~90px well it flattens to a dark hexagon.

### foundry / render_single — single — 23/24, keep

identity-at-42px 3 · composition-at-220 3 · palette-behavior 3 · seed-variation 3 · craft 3 · reuse-surface 3 · originality 3 · card-legibility 2

> Native single_standard-400.png: crop-mark corners, JOB ACTIVE eyebrow left / SPOT #4C9BC6 right, accent rule, 34px serif 'Warm Mako', FIRST RUN, four grey flight cells with accent top-rules, 5/4/-1/1 over SPEED/GLIDE/TURN/FADE, art in a bordered proof tile, tint ramp along the bottom. Native single_gallery-400.png is a full 400x~600 proof sheet with the disc at ~350px and 40px flight numerals — a different document, not a stretched one, so the layout flag earns its keep. The one thing that costs it: with manufacturer and mold empty, _maker_line silently substitutes the note, so the card prints 'FIRST RUN' in the mold slot with no signal that the mold is unrecorded — cartography and botanical both say 'UNRECORDED MOLD' instead.

- identity-at-42px — as a card thumbnail the cream stock + crop marks + serif name are identifiable instantly.
- composition-at-220 — single_standard-400.png: art tile left, type block right, no collisions; gallery re-flows to a vertical proof.
- palette-behavior — the best accent discipline in the field — participant color becomes a literal spot ink (rules, cell heads, tint ramp) and is printed as 'SPOT #4C9BC6'.
- seed-variation — sheet-cards single_standard-400 (1,1) vs single_gallery-400 (2,1): standard and gallery differ in aspect, hierarchy and art scale; details=False drops eyebrow and rules.
- craft — _fit() guards every string, crop marks sit inside the frame, art embedded as an inline namespaced group, lint clean, byte-identical re-render.
- reuse-surface — render_single(card, art, width) exact; CALCULATIONS carries fn.card.single.render; card['layout'] and card['details'] both read from the dict, width is the only presentation arg.
- originality — a letterpress job ticket is a real point of view and nothing in presentation.js looks like it.
- card-legibility — name/flight/labels all clear at 400, but the mold slot prints the note as if it were the mold, and 'SPOT #4C9BC6' competes with the eyebrow for the top-right.

### foundry / render_battle — battle — 22/24, keep

identity-at-42px 3 · composition-at-220 2 · palette-behavior 3 · seed-variation 3 · craft 3 · reuse-surface 3 · originality 3 · card-legibility 2

> Native battle_standard-400.png: two bordered panels split by a dashed rule with a circular VS badge at (centre), JOB ACTIVE / JOB RIVAL eyebrows, large serif names, art proof tiles, a dark score chip captioned SCORE, four flight cells each, BATTLE PROOF footer and a register bug bottom-right. Clean and legible at native — my first read off sheet-cards (3,1) that it was cramped was a downscale artifact. sheet-cards battle_stacked-400 (4,1) is the better of the two layouts: full-width rows, bigger art, real breathing room. The score is the weak element: a '-' placeholder set smaller than the flight numerals, so on a phone I read speed/glide before I read who is winning.

- identity-at-42px — the print-shop chrome is recognizable at thumbnail in sheet-cards (3,1)/(4,1).
- composition-at-220 — battle_standard-400.png: at 400 each panel gets ~370 units, so the art tile drops to ~90px and the disc art becomes decoration; stacked (sheet-cards (4,1)) does not have this problem.
- palette-behavior — each participant's color drives its own panel rules and score chip head — the two sides are told apart by ink, not just position.
- seed-variation — standard (side-by-side, dashed spine) vs stacked (two full rows, VS between) are meaningfully different documents.
- craft — no overflow, VS badge centred on the spine, lint clean, determinism verified cross-process.
- reuse-surface — render_battle(card, art, width) exact, fn.card.battle.render registered, layout and details both honored (score vs score_lean bands).
- originality — 'BATTLE PROOF' as a press proof is a consistent and specific idea.
- card-legibility — battle_standard-400.png: score chip glyph is smaller than the flight numerals — the wrong thing wins the eye on a battle card.

### signal / chevron-run — family — 22/24, keep

identity-at-42px 3 · composition-at-220 3 · palette-behavior 2 · seed-variation 2 · craft 3 · reuse-surface 3 · originality 3 · card-legibility 3

> sheet-42px-lineup (1,1)/(2,1)/(3,1): a stack of fat chevrons with a lit nose — along with register-mark, the fastest read in the tournament at 42, and it is the only mark that actually says 'speed'. sheet-chevron-run (3,1)/(3,4)/(3,7) at 220 adds a fifth chevron, the wash band, speed rules and the name plate, all still legible. Palette holds three ways but (1,7) chevron-run-dark-3-42 carries a muddy dark shadow band across the lower-left that reads like a rendering smudge rather than a design element. Seeds 7 and 42 (rows 2/3 vs 5/6) are close enough that I would not tell those two discs apart in a bag pocket.

- identity-at-42px — sheet-42px-lineup (1,1)-(3,1): reads at thumbnail in all three palettes, nothing in baseline (4,4)-(7,4) resembles it.
- composition-at-220 — sheet-chevron-run (3,1): chevron run, band, rules and MAKO plate all placed; slightly busy on warm but never crowded.
- palette-behavior — sheet-chevron-run (1,7) dark-3-42: a heavy dark wash band in the lower-left muddies the face; cool (rows 4-6) and warm (rows 1-3) are clean.
- seed-variation — sheet-chevron-run (1,4) seed 7 vs (1,7) seed 42: chevron count and tilt move, but the family is one motif and two of three seeds read alike.
- craft — min stroke 1.00 device px at 42, clip holds, plate only at 220, lint clean, 89/89 determinism.
- reuse-surface — the best FAMILY_PARAMS in the field: every seed-derived quantity has a named numeric range (tilt -17..17, pitch 54..76, arm 96..140) plus a per-target tier table.
- originality — a broadcast wipe frozen on a disc face — new, and it carries meaning rather than decoration.
- card-legibility — signal/cards/single_standard-400.png: still reads as chevrons in the 88px art well.

### signal / score-bug — family — 19/24, keep

identity-at-42px 3 · composition-at-220 2 · palette-behavior 3 · seed-variation 2 · craft 3 · reuse-surface 3 · originality 2 · card-legibility 1

> sheet-42px-lineup (1,2)/(2,2)/(3,2): a lit score bar laid as a chord across the disc — unmissable at 42, and the dark-palette version (3,2) is the highest-contrast tile anywhere in this tournament. But it is a chord, so sheet-score-bug (3,1) at 220 leaves the top third and bottom third of the face dead, and the mark is literally the card's own UI moved onto the disc. In signal/cards/battle_standard-400.png the Rival disc carries score-bug directly beside the card's real score panel, and the two read as the same widget twice — that collision is the reason this scores below its siblings.

- identity-at-42px — sheet-42px-lineup (1,2)-(3,2): instantly recognizable and unlike anything in the baseline.
- composition-at-220 — sheet-score-bug (3,1)/(3,4): band + chip + tally + colon read well, but the face above and below the chord is empty.
- palette-behavior — sheet-score-bug rows 7-9 (dark): gold band on charcoal is the strongest palette response in the field; unlit segments are a darkened mix of the accent, not a grey.
- seed-variation — sheet-score-bug (1,4) seed 7 vs (1,7) seed 42: tilt is only ±5 deg, so variation reduces to segment count and chip side.
- craft — 1.00 device px floor at 42, chord clipped inside the disc, plate 220-only, lint and determinism clean.
- reuse-surface — FAMILY_PARAMS gives ranges per seed field and states which target drops the cue ticks.
- originality — clever nod, but it borrows the app's own lower-third rather than inventing a disc mark.
- card-legibility — signal/cards/battle_standard-400.png, DISC-2 well: the art's fake score bar sits next to the card's real SCORE panel and the two compete — the one place a family should stay quiet, it shouts.

### signal / sweep-clock — family — 23/24, keep

identity-at-42px 3 · composition-at-220 3 · palette-behavior 3 · seed-variation 3 · craft 3 · reuse-surface 3 · originality 2 · card-legibility 3

> sheet-42px-lineup (1,3)/(2,3)/(3,3): tick ring, filled sweep wedge, bright hand, hub. Reads instantly at 42 and — unlike score-bug's chord or chevron-run's diagonal — it is concentric, so it still looks like a disc, which is what I want on a bag. sheet-sweep-clock cols 1/2/3 show a clean 6/12/24 tick ladder across 42/96/220 with identity unchanged, the discipline the whole contract is asking for. Seed range is the real win: (3,1) warm-3-220 is a ~180 deg wedge, (3,7) dark-3-220 is ~200 deg with a different hand, (3,9) dark-42-220 is a narrow slice — three obviously different discs that are obviously the same family. Minor nit at (1,1) warm-3-42, where the leftmost chunky tick abuts the rim and reads as detached.

- identity-at-42px — sheet-42px-lineup (1,3)-(3,3): wedge + hand + ticks land at thumbnail in all three palettes; distinct from all four baseline marks.
- composition-at-220 — sheet-sweep-clock (3,4) cool-3-220: 24-tick ring, wedge, hub ring, hand and name plate — balanced and quiet.
- palette-behavior — rows 1-3 warm, 4-6 cool, 7-9 dark all coherent; hand/quarter-tick/pip ink is chosen from base luminance so it never disappears.
- seed-variation — sheet-sweep-clock (3,1) vs (3,7) vs (3,9): wedge start and sweep vary enough to tell three discs apart at a glance without leaving the family.
- craft — 1.00 device px stroke floor at 42, tick ring inside the clip, plate 220-only, lint 89/89, determinism verified.
- reuse-surface — FAMILY_PARAMS gives start -118..-62 deg, sweep 105..300 deg, hub 46..62 units and the 6/12/24 tick ladder — you can predict a render before running it.
- originality — shot-clock/radar is a stock motif; the tier ladder and the base-luminance ink pick are what make it feel authored.
- card-legibility — reads cleanly in an art well at 88px and does not compete with any card chrome.

### signal / render_single — single — 23/24, keep

identity-at-42px 3 · composition-at-220 3 · palette-behavior 3 · seed-variation 3 · craft 3 · reuse-surface 3 · originality 2 · card-legibility 3

> Native single_standard-400.png: near-black bed with an accent hairline top and bottom, DISC-1 eyebrow left / SINGLE tag right, 'Warm Mako' in ~34px white bold, FIRST RUN beneath, four flight cells with ~26px numerals over 12px SPEED/GLIDE/TURN/FADE, accent chevrons closing the right edge, art disc at 88px on the left. This is the phone card — highest contrast in the field by a distance and the only one I could read at arm's length in sun. sheet-cards single_gallery-400 (1,2) is a genuinely different document: 320x~410 showcase, art at ~200px with flanking chevrons, name at ~44px, full-width flight boxes. Eyebrow handling is honest — with manufacturer/mold empty it falls back to physicalDiscId ('DISC-1') rather than pretending the note is a mold.

- identity-at-42px — sheet-cards (1,1): the dark bed + chevron tail is identifiable as this studio's card at thumbnail size.
- composition-at-220 — single_standard-400.png: art / name / flight row read left-to-right with no collision; gallery re-stacks rather than stretching.
- palette-behavior — participant color drives the bed hairlines, cell top-rules, chevrons and art rim; the chrome stays neutral so the accent means something.
- seed-variation — sheet-cards (1,1) standard vs (1,2) gallery: 320x132 lower-third vs 320x410 showcase — the layout flag changes the document, not the scale.
- craft — _fit() with a 6.0 floor on every string, art embedded as a namespaced inline group, generic sans-serif, lint clean, 89/89 byte-identical.
- reuse-surface — signature exact, fn.card.single.render registered, layout and details both read off the card dict; width is the sole presentation argument.
- originality — closest of the four to the broadcast lower-third already in presentation.js — excellent execution, but it is extending an existing vocabulary rather than proposing one.
- card-legibility — single_standard-400.png: best name, flight-number and label legibility in the tournament at 400px.

### signal / render_battle — battle — 23/24, keep

> Native battle_standard-400.png: 'DISC BATTLE' header with a LIVE dot top-right, DISC-1 and DISC-2 art discs at the outer edges, both names at ~24px white, a large central score panel split by a divider carrying two em-dash placeholders with a VS badge notched into its lower edge and SCORE captioned below, then eight flight cells (4 per side) with ~22px numerals. The score is the largest object on the card, which is exactly right for a battle and exactly what foundry, cartography and botanical all got backwards. sh.

*(Judge 1's card ends here — truncated in the promotion input mid-word. The
per-criterion breakdown for this item and every annotation for the cartography
and botanical items were not carried through. The summed scores in §1 are
complete; these annotations are not.)*

---

## 6. What the promotion is guarded by

`consumers/discstudio-card/test_paint_families.py` (8 tests)

- every original family × every target matches a **sha256 recorded before**
  `paint_families` was wired in — the freeze on the four originals;
- `FAMILIES == CLASSIC_FAMILIES + PROMOTED_FAMILIES`, promotion appended only;
- promoted families deterministic within **and across** processes (135 renders
  hashed in-process, re-hashed in a fresh interpreter);
- every family × target × palette lint-clean (checks mirror
  `harness/lint_svg.py`; the two were verified to agree over 189 documents);
- document contract at every target: `viewBox="0 0 512 512"`, `width == height
  == target`, an `aria-label`, a `<title>`, and label `<text>` **only** at 220;
- unknown family rejected by both entry points;
- `FAMILY_PARAMS` complete, `CALCULATIONS` keyed `fn.discArt.<slug>`, no lambdas;
- **no two of the seven families rasterize alike at 42px** — headless Chromium
  screenshot, sha256 per family, all seven distinct (skips cleanly if Playwright
  or the browser is absent).

`consumers/discstudio-card/test_card_render.py` (11 tests)

- both single layouts (`standard`, `gallery`) and both battle layouts
  (`standard`, `stacked`) render from real `compose()` output plus an art
  mapping, lint-clean, carrying name, manufacturer/mold, all four
  SPEED/GLIDE/TURN/FADE labels and values, and a score slot for battle;
- layout changes the document rather than scaling it; `details` is honoured by
  both renderers; a battle with no scores still renders its slot;
- an unrecorded mold is marked, never papered over with the note;
- deterministic within and across processes over 24 layout × details × width
  combinations; renders never mutate the card or the art;
- art inlined with no `data:` URI, external href, `<image>`, `<foreignObject>`
  or non-generic font; ids unique across both discs on one battle plate;
- `CALCULATIONS` registrable, signatures `(card, art, width)`, no lambdas;
- **PCR fan-out**: one `fn.discArt.render` result (`id="render-art"`) consumed
  by both card calculations, asserted through execution testimony —
  `inputs["art"] == "fn:render-art"` for `single-card` and `battle-card`, in
  that order — with the parts read back out of the `PxC` and compared to direct
  calls.

Suite total: **37** (18 pre-tournament + 8 + 11).
`scripts/check_all.sh` pins the consumer count, so its `EXPECT_CONSUMER`
default was moved 18 → 37 in the same change.

---

## 7. Where the losers live

| path | what it holds |
|---|---|
| `studios/<studio>/families.py` | all three families per studio, including the nine not promoted |
| `studios/<studio>/cards.py` | both card renderers per studio, including the six not promoted |
| `studios/<studio>/README.md`, `manifest.json` | each studio's own statement of intent and inventory |
| `studios/<studio>/selfcheck.py` (`self_check.py` in foundry) | each studio's own determinism/lint gate |
| `studios/<studio>/build_preview.py`, `preview/` | the studio's own preview build |
| `renders/<studio>/families/<slug>/` | every judged SVG + PNG, all seeds × palettes × targets |
| `renders/<studio>/cards/` | every judged card SVG + PNG at 400 and 700 |
| `renders/<studio>/*.png` | the contact sheets the judges actually looked at |
| `renders/<studio>/pcr-testimony.json`, `verify-result.json`, `lint-output.txt` | per-studio receipts |
| `baseline/` | the four pre-tournament families rendered the same way, for comparison |
| `harness/` | `render_svg.py`, `contact_sheet.py`, `lint_svg.py`, `fixtures.py` |

Nothing here is generated from the promoted modules, and nothing here is needed
by them — the consumer's suite is standalone. These are the receipts.
