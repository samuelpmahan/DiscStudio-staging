# Studio *botanical*

Warm paper and botanical print. Three seeded disc-art families and a pair of card
renderers that treat a disc the way a nineteenth-century plate book treats a plant:
pressed on cream stock, printed in one ink with the ghost of a second pull, and
captioned in serif on a small mount label. The studio signature is shared by all
three families — a paper ground warmed out of `base`, a speckle of fibre grain, a
muted second tint for the ghost impression, and (at 220 only) a mount plaque
carrying the disc label and one seeded specimen figure.

Files: `families.py` (the three families, `FAMILY_PARAMS`, `CALCULATIONS`),
`cards.py` (`render_single`, `render_battle`, `CALCULATIONS`), `selfcheck.py`
(the contract proof), `build_preview.py` (regenerates `preview/`).

## pressed-fern — Pressed Fern

A frond pressed flat on a herbarium sheet. A tapered rachis bows across the paper
from the lower left; pinnae are set in pairs along it, swept forward toward a
curled crozier tip, their length swelling just above the stipe and tapering out at
the top the way a real frond does. Each blade is cut apart from its neighbours by a
paper-coloured woodcut outline, and a second, fainter impression of the same frond
is slipped and rotated behind it — the ghost the specimen leaves when the sheet is
pressed twice. **seed** rotates the frond, bows the rachis and picks the bend
direction, sets the pinna backsweep, blade width and reach, the pair pitch, the
ghost's rotation and slip, a per-pinna jitter, the plaque tilt, the grain phase and
the specimen number. **base** is the sheet. **accent** is the plant, the rim and the
plaque type. **label** is set in serif on the plaque at 220 above `No. 788`. At 42px
it is a bold feathered diagonal — five pairs of fattened pinnae on a thickened
rachis, no ghost and no grain — reading as a sprig laid corner to corner, nothing
like the arc of Orbit Foundry or the rosette of Petal Press.

## nodding-seedhead — Nodding Seed Head

A seed head nodding on its stalk. The head sits off-centre on a seeded bearing, its
achenes packed in a golden-angle phyllotactic spiral and knocked *out* of the ink in
paper, so the head reads as texture rather than a blob; a ring of pointed bracts
spikes out around it, and a tapered stalk runs down to the lower rim carrying
drooping leaves. At the larger tiers, seeds loosed from the head drift off on their
pappus rays. **seed** places and sizes the head, sets the bract count and reach, the
phyllotactic phase, the stalk bow, the leaf side and length, the four drifting seeds'
bearings and spins, the plaque tilt, the grain phase and the printed achene count.
**base** is the ground; **accent** is head, bracts, stalk, leaves and seeds; **label**
is set on the plaque at 220 above `ACHENES 44`. At 42px it is a spiky head on a
stalk with nine chunky knocked-out achenes and one leaf — an unmistakable silhouette
at a glance, asymmetric where Petal Press is a centred rosette.

## block-print — Block Print

A block-printed endpaper. Two of three carved motifs — a three-blade sprig, a split
seed pod, a berry cluster — alternate on a half-drop lattice, each cell rotated a
little off true as a hand-pulled block would be, and the whole block is pulled a
second time slipped off-register in a let-down ink. At 220 the sheet gets its double
border rule with ticks and the motifs get their detail: the seeds inside the pod, the
highlight on each berry, the bud on the sprig. **seed** rotates the block, sets the
pitch and half-drop, chooses which two motifs alternate and in which parity, the
per-cell jitter, the off-register direction and distance, the tick count, the plaque
tilt, the grain phase and the block number. **base** is the stock; **accent** is the
ink; **label** is set on the plaque at 220 above `BLOCK 12 / PULL II`. At 42px it is
a coarse all-over field of seven or eight solid botanical marks in one ink — a
texture, not an object, which is what separates it at a glance from both of its
siblings and from the three big bars of Tessellated Flight.

## Cards

`render_single(card, art, width)` and `render_battle(card, art, width)` take the JSON
`card_composition.compose()` puts at `cards['single']` / `cards['battle']` and a
`presentationId -> art SVG` mapping. The plate is warm stock with a double rule, a
tint band pulled from the participant's own colour, and a pressed-leaf ornament in
each corner; the disc is mounted in a hairline specimen ring, the name is engraved in
serif under a letterspaced maker/mold eyebrow, the note is set in italic, and the
flight numbers run as a herbarium measurement strip — serif figures over a hairline
with SPEED/GLIDE/TURN/FADE in small caps beneath. `single` honours **standard**
(landscape, disc left) and **gallery** (portrait, disc above the type); `battle`
honours **standard** (two halves either side of a `vs` rule, each score a wax seal set
on its own specimen, each strip running the full width of its half) and **stacked**
(two rows, each with its own seal at the right). `details=False` drops the note, the
captions and the ornaments and shortens the plate; the name, maker/mold line, all
four figures and the score survive. Missing art degrades to a dashed `NO PLATE` ring
rather than raising. Art is inlined as a `<g>` copy with per-participant id
namespacing — never a nested `<svg>`, which a host stylesheet targeting `svg` would
resize — so two discs never collide on ids.

## Proof

`python3 selfcheck.py` renders 81 art documents and 48 card plates twice each and
compares sha256; records every seeded draw at 42/96/220 and asserts the logs are
identical; checks intrinsic size, viewBox, disc clip, rim, aria-label, title and
text-only-at-220; lints every artifact with the harness linter; and checks the card
contract (name, maker/mold, four figures, score slot, layout, details flag, unique
ids on a two-disc plate, missing-art fallback, and the three score shapes).
