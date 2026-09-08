# S3 across Dev6 — what the family vote is actually doing

The S3 checkpoint reported three Apple Maps chrome glyphs accepted as Tee
objects on Dash's Track. That was a one-course claim. Running the same
investigation across all six Dev6 courses turns it into a different and
sharper one.

`packages/alg/src/stages/` holds S0-S3 and no S4, so breadth is the only
direction the transfer pattern can still go.

## Reproduce

```sh
python -m pip install -e packages/quick_anno_py
npm run build --workspace @chainspot/alg
for c in DashsTrack Lenard TowneLake NorthPark HeritagePark AlexClark; do
  python experiments/quick-anno-python/s3.py \
    "$(ls ../chainspot-corpus/dev/*/${c}-full.* | head -1)"
done
```

Course identity comes from the filename stem, not the directory: the corpus
has `dev/Heritage/HeritagePark-full.png`, and extensions vary in kind and case
(`.jpg`, `.png`, `.PNG`).

## The ledger balances on every course

```text
COURSE          encl  diam elong bMute  cand  meas  unfr voted  tees  teePx
DashsTrack        32     5    27     3    24    20     4     2    18   4884
Lenard            37     5    32     3    29    23     6     6    17   2516
TowneLake         36     7    29     3    26    22     4     5    17   2498
NorthPark         31     5    26     3    23    20     3     4    16   2562
HeritagePark      37     5    32     3    29    18    11     4    14   1799
AlexClark         29     6    23     3    20    17     3     3    14   3111
```

`balanced: true` on all six — every enclosed ring leaves through exactly one
named door. `bMute` is **3 on all six courses**, which looked like six
coincidences and is not one; see "The constant `excludedByBadge: 3`" below.

## What the identity crops show

Judged from `s3-tee-crops.png` and `s3-voted-out-crops.png` per course, at
full resolution. Chrome is legible as letterforms — `SAT`, `MAP`, `Maps`,
`aps` — not inferred from position.

| Course | Tee objects | chrome ACCEPTED (false +) | voted out | of which real pads (false −) |
|---|---|---|---|---|
| DashsTrack | 18 | **3** — `SAT`, `aps`, `Map` | 2 | **1** — basket-occluded pad |
| Lenard | 17 | 0 | 6 | 0 — 2 swimming pools, 4 chrome |
| TowneLake | 17 | 0 | 5 | 0 — 2 built terrain, 3 chrome |
| NorthPark | 16 | 0 | 4 | 0 — 1 terrain, 3 chrome |
| HeritagePark | 14 | 0 | 4 | 0 — 2 rooftop/driveway, 2 chrome |
| AlexClark | 14 | **1** — `Map` | 3 | **1** — basket-adjacent pad |

## The actual finding

**Apple Maps chrome produces ring-plus-frame candidates that survive to
`measured` on all six courses.** Every course has `SAT` / `MAP` / `Maps`
glyphs sitting in either its accepted set or its voted-out set. The candidates
are universal; only their fate differs.

**The family size vote is the only thing filtering them, and it is a size
filter standing in for an identity filter.** It has no notion of chrome, of
occluders, or of what a tee is. It asks one question — is this frame's
major/minor/area within log-ratio 1.25/1.25/1.5 of a common family — and
chrome answers it correctly often enough to be excluded on four courses and
incorrectly on two.

Because it is the wrong kind of filter, it errs in **both** directions on the
same two courses:

- **False positives:** 4 chrome glyphs accepted as Tee objects (DashsTrack 3,
  AlexClark 1). On DashsTrack that produces 18 Tee objects on an 18-hole
  course, a number that looks like success and is not.
- **False negatives:** 2 real tee pads rejected (DashsTrack, AlexClark), both
  by the same mechanism — a basket sprite overlaps the pad, the visible area
  shrinks, and the area ratio drops it. DashsTrack's: frame `[409,1748,22,33]`,
  area 171 vs anchor 276 = 1.61 > `AREA_RATIO` 1.5, while its major axis
  (32.2) is *larger* than the anchor's (30.9).

It also does useful work nobody designed it to do: on Lenard it rejected two
**swimming pools**, on HeritagePark two rooftop/driveway rectangles, on
TowneLake and NorthPark built terrain. Bright quadrilaterals are common in
aerial imagery. The size vote is currently the corpus's whole defense against
them.

The two courses where it fails in both directions, DashsTrack and AlexClark,
are the two `.jpg` captures; the four where it holds are `.png`. That
correlation is **noted, not explained** — file format is a proxy for how the
screenshot was captured and cropped, and this survey did not establish the
mechanism. AlexClark is already on record as the course `screenChrome.ts` was
tuned against.

## The constant `excludedByBadge: 3` — solved, and it is correct behaviour

Three rings excluded by Badge mute on six different courses, at six different
zoom levels, looked like six coincidences. It is not a coincidence: the crops
show the same three badges every time — **4, 14 and 10** — and the rings are
the *enclosed counters of the digits*.

On a course numbered 1-18 the counters that survive the `tee-rect` elongation
filter are the `4` in hole 4, the `4` in hole 14 and the `0` in hole 10.
Round counters (`6`, `8`, `9`, `16`, `18`, and the second `8` in 8) classify
as `diamond` and die one filter earlier, in `diamondDropped`. Three is
therefore *structural* for any 1-18 course, not an artifact.

This is the Badge mute doing exactly its job, on exactly the failure mode the
CV engrams say has cost this project repeatedly: digit glyphs masquerading as
tee evidence. Receipts: `s3-badge-muted-crops.png` on every course
(DashsTrack reads 4/14/10, HeritagePark reads 10/4/14).

## The unframed bucket, and the one ring in it that matters

Screening every unframed ring against its own course's accepted tee-ring
profile (inner-hole width, height and area — and for DashsTrack and AlexClark
recomputed from real pads only, since their accepted sets contain chrome and
would otherwise widen their own reference):

```text
DashsTrack     0 of  4 unframed rings match the tee profile
Lenard         0 of  6
TowneLake      0 of  4
NorthPark      0 of  3
HeritagePark   1 of 11   <- [1219,1511,9,9] holeArea 46, ringFrac 0.75
AlexClark      0 of  3
```

Everything else in the bucket is correctly dropped: parking lots, rooftops and
driveways with dark cars as enclosed holes, and the counters of the letters in
`Maps` along the bottom edge.

The single exception is on HeritagePark, the course that finds 14 Tee objects
for 18 holes. Ring `[1219,1511,9,9]`, holeArea 46, sits inside Heritage's
accepted profile on all three measures (w 6-10, h 5-10, area 45-80), 591px
above the bottom edge — nowhere near the chrome strip — and its `ringFrac` of
0.75 says a quarter of its enclosing band is not bright, which is why no
enclosing component was found. The crop marks it on a small pad-shaped bright
object adjacent to badge 15.

**What is claimed:** a tee-profile ring, in tee territory, dies in the
unframed bucket on HeritagePark, and the completeness invariant says every
such drop must be classified.

**What is not claimed:** that this object is hole 15's tee. Identity precedes
geometry, and badge-ray adjudication is not run in this lane. Badge chrome
stays the competing hypothesis until something better than a crop rules on it.

## A tool fix this survey forced

`neon.crops` originally outlined the tile, not the subject. On Heritage's
unframed ring 5 that was the difference between "a badge" and "a pad beside a
badge" — two different findings. Crops now draw the bbox at its scaled
position inside the tile, so every rejection crop says which object it is
about rather than "something near here".

## What this does not say

- It does not say how many holes each course *should* find at S3. Recovery is
  `NOT RUN` at this stage; a count below 18 is expected, not a defect.
- It does not classify which hole loses its tee in the two false-negative
  cases. That needs badge-ray adjudication this lane does not run.
- It does not propose a fix. No threshold was moved, no selector edited,
  nothing registered into `S3_PLAN`. This lane proves the investigation
  pattern; the algorithm is the owner's call.
- It does not establish the identity of HeritagePark's unframed tee-profile
  ring beyond "pad-shaped bright object adjacent to badge 15".

## Why the crops were necessary

Every one of these calls came from the per-object identity crop panels, and
none of them is visible in the course-zoom panels that preceded them. The
full-course views agreed with the receipt on all six courses. A count that
matches expectation is not evidence, and a bounding box is not an identity.
