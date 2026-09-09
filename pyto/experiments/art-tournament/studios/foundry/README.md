# Foundry

Three disc-art families and a pair of card renderers drawn from one angle: **a
pro print shop's bed**. Nothing here is an abstract pattern for its own sake —
every mark is something a shop actually puts on plastic or on the proof sheet
that goes with it. Screened ink, registration targets, hot-stamp foil dies, tint
step wedges, crop marks.

    families.py      halftone-screen, register-mark, hot-foil
    cards.py         render_single / render_battle
    build_preview.py rebuild every SVG, PNG and contact sheet under preview/
    self_check.py    contract, RNG discipline, determinism, lint

    python3 build_preview.py     # 94 SVGs + 5 contact sheets
    python3 self_check.py        # must print ALL CHECKS PASSED

## Halftone Screen — `halftone-screen`

One ink, screened. Dots sit on a grid rotated to a real screen angle and their
radius ramps along a wedge direction, so the face runs from an open tint at one
edge into dots that overlap into solid coverage at the other — the way a
duotone screen print actually lays down. Four register ticks cut straight
through the rim to mark where the screen was hung. **Seed** picks the screen
angle (15°/45°/75°/105°), the direction the wedge ramps in, how open the light
end stays, and the phase of the rim ticks — so two seeds in the same palette
read as two different pulls off the same press. **Base** is the plastic under
the screen; **accent** is the single ink and owns every dot, the rim ring and
the ticks; **label** is hot-stamped into a knockout plate at the bottom of the
face at 220 only, uppercased and clipped to ten characters. At 42px the grid
drops to five cells across, so it reads as a handful of chunky blobs growing
from small to merged-solid across the face — unmistakably a dot field, and
unmistakably not concentric rings, petals, an arc or diagonal bars.

## Register Mark — `register-mark`

A press registration target blown up until it fills the whole disc. The four
quadrants are inked at descending tint steps from one solid quadrant, a
crosshair is *knocked out* of the ink to the rim (with an ink hairline down its
middle at 96 and above, the way a real register cross is trapped), corner crop
marks sit inside the quadrants, and a bullseye is knocked out of the plastic at
dead centre. **Seed** rotates the whole assembly, chooses which quadrant carries
the solid hit — the other three step down from it, so the tint pinwheel spins
with the seed — sets the crosshair's centre gap and nudges the crop mark inset.
**Base** is the plastic and does the knocking out (crosshair, crop marks,
bullseye core, label plate); **accent** is the ink and owns the quadrant tints,
the hairline, the bullseye ring and the rim. **Label** goes in the knockout
plate at 220. At 42px the crop marks and hairline drop away and it reads as a
bold pale cross over four steps of tone with a solid bullseye at the centre —
the strongest silhouette of the three, and legible even as a favicon.

## Hot Foil — `hot-foil`

A hot-stamp foil die pressed into the plastic. A faceted badge — hexagon or
octagon — fills most of the face; the die's bevel splits it into a lit half and
a shaded half with a narrow specular band riding the split, which is what makes
flat vector fill read as metal. Around it runs the knurl: the ring of teeth the
stamping die leaves where it bites. **Seed** chooses the die shape (hex or
octagon, hexagons twice as likely), rotates it, sets the rake angle of the
sheen, and phases the knurl ring. **Base** is the plastic and also draws the
die's inner keyline step (96 and above) and the label plate; **accent** is the
foil itself — badge fill, knurl teeth, rim ring. **Label** is stamped into the
knockout plate at 220. At 42px the keyline drops and the knurl coarsens to
twelve long teeth: a solid faceted medallion with a bright diagonal band across
it, ringed by ticks. Mass and metal, where halftone-screen is texture and
register-mark is line.

## Cards

The card is a proof pulled off the shop floor. Warm press paper, crop marks at
the four corners, a job line in letter-spaced caps, a spot-ink rule under it,
the disc name set large in serif, the mould line in caps, flight numbers in
inked cells with a spot bar across the top of each, a tint step wedge along the
bottom edge and a registration target where the pressman would sign off. The
participant's own `color` is the spot ink, so the card takes its accent from the
disc rather than imposing one.

Each layout is drawn in fixed natural units and `width` only scales the
viewBox — a 400px and a 700px render are the same drawing, never a reflow:

| card | layout | natural units | shape |
| --- | --- | --- | --- |
| single | `standard` | 400 × 176 | lower third: art well left, copy block right |
| single | `gallery` | 320 × 404 | portrait: art on the sheet, copy stacked under |
| battle | `standard` | 700 × 300 | two proofs side by side, VS target in the gutter |
| battle | `stacked` | 420 × 452 | two proofs stacked, VS target on the die line |

`details: false` drops the mould line and the flight cells, keeps the name and
art, and widens the battle score slot to fill the room. Battle cards always
carry a score slot; it reads `scores` as either a `{presentationId: value}` map
or a positional list and falls back to a dash, and `winner` / `manualWinner` /
`highlight` promote a panel to a spot-ink border with a `WINNER` mark. A
`presentationId` with no art in the `art` mapping gets a dashed *NO PLATE* well
instead of an exception. Art is inlined as a `<g transform>` copy of the source
document's elements with every id namespaced per participant — not a nested
`<svg>`, because a host stylesheet that sizes `svg` elements (the tournament
rasteriser ships one) would otherwise blow the artwork up to the whole page.

## Contract notes

Every family draws all of its seeded identity parameters *before* it branches on
target, so rendering the same seed at 42, 96 and 220 consumes identical RNG —
`self_check.py` proves this by counting draws through a patched `random.Random`
rather than by inspection. Stroke widths go through `_sw()`, which floors a
width to a whole output pixel at the target size, so nothing thins to nothing at
42px. Everything is pure stdlib, no lambdas are exposed as calculations, and
`CALCULATIONS` in each module registers the five entry points:
`fn.discArt.halftone-screen`, `fn.discArt.register-mark`, `fn.discArt.hot-foil`,
`fn.card.single.render`, `fn.card.battle.render`.

## Preview sheets

`preview/sheet-halftone-screen.png`, `preview/sheet-register-mark.png` and
`preview/sheet-hot-foil.png` each show one family across 3 palettes × 3 seeds ×
3 targets. `preview/sheet-42px.png` is the legibility test — all three families,
all palettes and seeds, at 42px only, upscaled so the actual pixels are
visible. `preview/sheet-cards.png` shows all four layouts at 400px and 700px
wide, plus a `details: false` variant of each and one battle card carrying real
scores and a winner.
