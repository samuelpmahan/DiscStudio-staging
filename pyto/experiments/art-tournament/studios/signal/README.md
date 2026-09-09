# Studio signal — broadcast graphics on a disc

Three disc-art families and two card renderers built from the furniture of a live sports
broadcast: the transition wipe, the lower-third score bug, the shot clock. The studio is
optimised for the DiscBattle score moment — at any width the eye is meant to land on the
score first, the two discs second, everything else third.

The colour rule that makes all of it survive a 42px tile: the caller gives two colours, so
each family derives two more by *contrast* rather than by hue. `edge` separates from the
**base** (white over a dark or mid disc, near-black over a pale one) and carries the single
bright "live" mark; `knock` separates from the **accent** and is used only for marks that sit
on top of an accent mass. Nothing is ever brown-on-brown or navy-on-navy, on any palette.

## chevron-run

A broadcast transition wipe frozen on the disc: a run of fat chevrons marching across a soft
accent wash band, the leading one carrying a bright inner nose so the run reads as *moving*
rather than as decoration. **seed** sets the tilt of the whole run (−17..17°), the pitch
between chevrons (54..76 units), the phase along the run axis, how open the V is (arm
96..140), and where the small square cue chip rides on the band's top edge. **base** fills the
disc and its luminance picks the cue-chip ink; **accent** is the chevron mass, the wash band,
the two speed rules and the rim, and its luminance picks the lit nose ink. **label** is the
aria-label and `<title>` at every target and is set, first ten characters, in the name plate
at 220. At **42px** you get three fat arrows with one lit nose — a directional mark that
cannot be confused with Orbit Foundry's thin arc or Tessellated Flight's parallel slabs; 96
adds a fourth chevron and the speed rules, 220 a fifth and the name plate.

## score-bug

The lower-third score bug laid straight across the disc: a hard-edged accent band with a
hairline rule above it, a knockout logo chip with a chevron cut into it, a clock colon, and a
run of tally segments of which some are lit. It is the only family here with a flat horizontal
mass, which is exactly why it holds up when shrunk. **seed** sets the band's height on the
face (−26..36 units), its tilt (±5°), how many segments are lit (1..4), which end of the band
carries the chip, and how the cue ticks slide above it. **base** fills the disc and its
luminance picks the hairline rule's ink; **accent** is the band, the chip's chevron, the cue
ticks, the rim and — darkened — the unlit segments. **label** rides the name plate at 220.
At **42px** it is a bold horizontal bar with a bright block and a chip: a scoreboard strip,
legible as a distinct silhouette next to anything in the baseline set; 96 and 220 go from
three wide segments to five plus cue ticks.

## sweep-clock

The shot clock: a tick ring with heavier quarter ticks, a filled sweep wedge for elapsed time,
one bright hand on the leading edge, and a hub that doubles as the family's stamp. Radial mass
where chevron-run is directional and score-bug is horizontal, so the three never collapse into
each other. **seed** sets where the wedge opens (near twelve o'clock, −118..−62°), how much
has elapsed (105..300°), the tick ring's rotation, the hub radius (46..62) and how far out the
lit pip sits inside the wedge. **base** fills the disc and the hub, and its luminance picks the
hand, quarter-tick and pip ink; **accent** is the wedge, its outline, the minor ticks, the
ring, the hub ring and the rim. **label** rides the name plate at 220. At **42px** it reads as
a gauge — pie wedge plus one bright hand — which no baseline family resembles; 96 doubles the
ticks to twelve, 220 to twenty-four.

## Cards

`render_single(card, art, width)` and `render_battle(card, art, width)` take the JSON from
`card_composition.compose()` and a `presentationId -> art SVG` map. The plate is a dark
broadcast bed with an accent hairline, a letterspaced eyebrow (manufacturer · mold · variant,
falling back to the physical disc id), one heavy name, and a strip of flight cells reading
SPEED GLIDE TURN FADE from `flight1..flight4`. Single honours `standard` (400×174 lower third)
and `gallery` (320×402 showcase); battle honours `standard` (660×300, two discs flanking one
centre scoreboard block) and `stacked` (440×424, two lower thirds each with its own score
plate). In both battle layouts the leading side's half of the scoreboard **fills with that
disc's colour** and the trailing numeral dims — that fill is the score moment. Scores come from
`card['scores']` (dict by presentationId, dict by index, or list) or `participant['score']`;
absent scores render an en dash and the header shows LIVE instead of a winner tag. `winner` /
`manualWinner` overrides the leader and tags the header, `highlight` rings a participant, and
`details: false` drops the eyebrow, note and flight cells so the art, name and score carry the
card alone. Art is inlined under a placed `<g>` with per-participant id namespacing — no
nested `<svg>` viewport (a host stylesheet sizing `svg { width: … }`, which the tournament's
own rasterizer does, would otherwise blow the disc out of its slot), no data: URI, no webfont.

## Reproducing

    python3 build_preview.py      # 97 SVGs + PNGs + the contact sheets under preview/
    python3 selfcheck.py          # 300 checks: contract, determinism, RNG discipline, lint

`preview/` holds `squint-42.png` (all three families × 3 palettes × 3 seeds at 42px),
`grid-96.png`, one `<family>-palettes.png` per family (3 palettes × 3 targets plus a seed row
at 220), and `cards-400.png` / `cards-700.png` covering both layouts of both card kinds with
scored, unscored and `details: false` variants.
