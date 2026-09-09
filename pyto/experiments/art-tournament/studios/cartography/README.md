# Studio · cartography

Three seeded disc-art families and a pair of card renderers built on one idea:
a disc is a plate torn out of a course map book. One family draws the ground,
one draws the hole, one draws the bearing. The cards are the sheet those plates
are mounted on — neat-line, graticule, scale bar, title block, legend strip.

```
families.py      contour_basin / fairway_plat / wind_rose  +  FAMILY_PARAMS, CALCULATIONS
cards.py         render_single / render_battle             +  CALCULATIONS
selfcheck.py     determinism, RNG discipline, shape, lint and card-contract proof
build_preview.py regenerates every SVG, PNG and contact sheet under preview/
manifest.json    machine-readable summary
preview/         the sheets the judges look at (svg/ and png/ hold the sources)
```

## contour-basin — Contour Basin

The terrain the basket sits in, plated as filled contour bands rather than
stroked lines, so the shape survives being 42 pixels wide. A seeded summit sits
off-centre, drifts as it climbs, and every band is warped by two harmonics, so
one basin is a long ridge and the next a tight knoll. The tonal ramp runs from a
white-lifted `base` on the low ground to a near-`accent` summit; `accent` also
draws the index contours (the heavier every-third line), the hairline
interstitials between them, the rim and the label cartouche. `seed` sets the
summit offset and drift, the two harmonic frequencies, amplitudes and phases,
the squash of the bowl, the plate rotation, the drainage bearing and the spot
elevation figure; `label` prints once at 220 in the legend cartouche and is the
aria-label and `<title>` at every size. At 42px it is three bands and a light
spot-elevation dot: an off-centre layered island, unmistakably terrain and
unmistakably not any of the four existing families. 96px adds two more bands,
four hairlines and a benchmark triangle; 220px runs eight bands, nine
hairlines, the drainage line, the elevation figure and the name box.

## fairway-plat — Fairway Plat

One hole seen from directly above. A mown corridor doglegs from a tee pad to a
basket, tapering as it goes, with a green under the basket, trees crowding both
shoulders, woodland scattered across the rough on a jittered lattice that keeps
clear of the corridor, and — on about half of all seeds — a creek cutting across
the fairway. The colour rule is structural rather than tuned: the corridor is
`base` lifted toward white and the rough is `base` pushed toward `accent` and
then darkened, so the corridor reads lighter than its surroundings in every
palette, including a dark base with a bright accent. `accent` is the tee pad,
the dashed flight line, the basket and the rim. `seed` rotates the hole, picks
the dogleg side and bend, the corridor widths, the green, the tee-pad length,
the tree phase, whether there is water, and the hole number and par. `label`
prints at 220 in the cartouche below the hole number. At 42px it is rough,
corridor, tee nub and a solid basket dot: one confident light ribbon sweeping
across a darker disc with a target at its end.

## wind-rose — Wind Rose

The bearing compass from the corner of the sheet, turned into the disc's whole
subject. Sixteen kites alternate `accent` and a near-white tint; their reach
leans into a seeded prevailing bearing with a seeded falloff, so one rose is an
even star and the next is a lopsided gust. A folded two-tone needle runs out to
the bearing ring as the north point, with `N` beside its tip. Kite width is set
in viewBox units rather than radians, which is what keeps the rose from
collapsing into hairlines at 42px. `base` is the chart field and the pale kites,
`accent` the dark kites, the needle, the rings and the degree ticks. `seed` sets
the prevailing bearing, the rose tilt, the focus of the falloff, the hub and
kite dimensions, all sixteen reaches, the ring gap and the printed bearing.
`label` prints at 220 in the cartouche. At 42px it is eight fat kites and the
long needle — a compass star with an obvious pointing direction, which reads as
neither the petal rosette nor the orbit arc of the existing set.

## Cards

`render_single(card, art, width)` and `render_battle(card, art, width)` take the
JSON `card_composition.compose()` puts at `cards['single']` / `cards['battle']`
and a `presentationId -> art SVG` map. Both honour `card['layout']` (single:
`standard` 420x190 wide plate, `gallery` 340x470 portrait; battle: `standard`
700x224 abeam, `stacked` 440x346 in rows) and `card['details']` — details on
adds the note, the SPEED/GLIDE/TURN/FADE captions and the scale bar; details off
keeps the name, the maker/mold line and all four flight figures in a compact
ruled row on a shorter plate. Battle plates always carry a score slot, read from
`card['scores']` as an id map, an index map or a list, with a star and an accent
frame on `card['winner']`.

Art is inlined as a `<g>` copy of the source document's own elements, scaled from
its viewBox and clipped to the inset, with every id namespaced per participant.
A nested `<svg>` would have been shorter, but any host stylesheet that targets
`svg` — the tournament rasterizer's does — resizes it to the full card, and two
discs on one battle plate would otherwise collide on `clipPath` and gradient ids.

## Proof

`python3 selfcheck.py` runs 1361 assertions: every family at 3 palettes x 3 seeds
x 3 targets rendered twice and compared by sha256, the recorded RNG draw sequence
compared across 42/96/220 (identical, so no target consumes extra randomness),
document shape (intrinsic size, viewBox, r=220 clip, rim, aria-label, `<title>`,
text only at 220), harness lint on every artifact, and every card fixture x
family x width x details combination checked for name, maker/mold, four flight
figures, score slot, layout response and lint — including a worst-case battle
plate carrying two 220px basins (48406B of the 64KB cap) and a duplicate-id scan.
