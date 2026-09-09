# Hiding primitives: SUBDUE over the paint studio

Mined from 91 function graphs (1669 nodes, 1543 edges) covering the 16 families `art_registry.py` addresses, by `subdue.mine(beam=4, iterations=20, max_size=5, min_instances=2)`.  Rebuild with `python3 mine.py`; `--check` fails if this file drifts.

## Mined substructures

| rank | substructure | inst | families | lines | bits | ratio |
| ---: | --- | ---: | --- | --- | ---: | ---: |
| 1 | `v0=append/1, v1=for, v2=range/1 ; v1-in->v0, v2-arg->v1` | 33 | 15/16: block-print, chevron-run, contour-basin +12 | _families_botanical.py:500, _families_botanical.py:508, _families_botanical.py:528 +63 | 1903.3 | 0.9595 |
| 2 | `v0=append/1, v1=if ; v1-in->v0` | 38 | 13/16: block-print, contour-basin, fairway-plat +10 | _families_botanical.py:182, _families_botanical.py:183, _families_botanical.py:516 +73 | 1097.4 | 0.9757 |
| 3 | `v0=_f/1, v1=_f/1, v2=format/3+ ; v0-arg->v2, v1-arg->v2` | 18 | 3/16: chevron-run, score-bug, sweep-clock | _families_signal.py:130, _families_signal.py:131, _families_signal.py:172 +33 | 1007.0 | 0.9771 |
| 4 | `v0=uniform/2, v1=uniform/2 ; v0-next->v1` | 31 | 16/16: block-print, chevron-run, contour-basin +13 | _families_botanical.py:474, _families_botanical.py:475, _families_botanical.py:477 +59 | 888.6 | 0.9793 |
| 5 | `v0=append/1, v1=append/1 ; v0-next->v1` | 30 | 15/16: chevron-run, contour-basin, fairway-plat +12 | _families_cartography.py:249, _families_cartography.py:251, _families_cartography.py:356 +57 | 859.0 | 0.9795 |
| 6 | `v0=for, v1=range/1 ; v1-arg->v0` | 20 | 5/16: block-print, fairway-plat, nodding-seedhead +2 | _families_botanical.py:176, _families_botanical.py:482, _families_botanical.py:499 +18 | 559.7 | 0.9864 |
| 7 | `v0=<circle>, v1=n/1, v2=n/1 ; v1-arg->v0, v2-arg->v0` | 10 | 3/16: block-print, contour-basin, fairway-plat | _families_botanical.py:186, _families_cartography.py:245, _families_cartography.py:246 +7 | 528.8 | 0.9869 |
| 8 | `v0=<path>, v1=n/1, v2=stroke_for/2 ; v1-arg->v0, v2-arg->v1` | 10 | 2/16: contour-basin, fairway-plat | _families_cartography.py:220, _families_cartography.py:221, _families_cartography.py:225 +17 | 529.0 | 0.9867 |
| 9 | `v0=SUB2, v1=append/1 ; v0-in->v1` | 15 | 12/16: block-print, contour-basin, fairway-plat +9 | _families_botanical.py:182, _families_botanical.py:183, _families_botanical.py:186 +42 | 410.2 | 0.9895 |
| 10 | `v0=SUB3, v1=_f/1, v2=_f/1 ; v1-arg->v0, v2-arg->v0` | 9 | 3/16: chevron-run, score-bug, sweep-clock | _families_signal.py:187, _families_signal.py:189, _families_signal.py:194 +18 | 469.4 | 0.9879 |
| 11 | `v0=<g>, v1=SUB5 ; v0-arg->v1` | 12 | 11/16: chevron-run, fairway-plat, halftone-screen +8 | _families_cartography.py:387, _families_cartography.py:391, _families_foundry.py:198 +21 | 320.5 | 0.9916 |
| 12 | `v0=ValueError/1, v1=if ; v1-in->v0` | 10 | 16/16: block-print, chevron-run, contour-basin +13 | _families_botanical.py:51, _families_botanical.py:52, _families_botanical.py:53 +17 | 260.6 | 0.9931 |
| 13 | `v0=_cn/1, v1=stroke_for/2 ; v1-arg->v0` | 10 | 1/16: wind-rose | paint_families.py:465, paint_families.py:466, paint_families.py:506 +7 | 260.6 | 0.9930 |
| 14 | `v0=append/1, v1=for ; v1-in->v0` | 10 | 7/16: chevron-run, fairway-plat, halftone-screen +4 | _families_cartography.py:361, _families_cartography.py:363, _families_foundry.py:201 +17 | 260.7 | 0.9930 |
| 15 | `v0=int/1, v1=round/1 ; v1-arg->v0` | 10 | 7/16: block-print, contour-basin, fairway-plat +4 | _families_botanical.py:67, _families_botanical.py:68, _families_botanical.py:69 +7 | 260.7 | 0.9929 |
| 16 | `v0=SUB4, v1=random.Random/1 ; v1-next->v0` | 9 | 12/16: block-print, chevron-run, contour-basin +9 | _families_botanical.py:473, _families_botanical.py:474, _families_botanical.py:475 +24 | 230.7 | 0.9937 |
| 17 | `v0=_bn/1, v1=math.cos/1 ; v1-arg->v0` | 9 | 2/16: nodding-seedhead, pressed-fern | paint_families.py:283, paint_families.py:291, paint_families.py:366 +6 | 230.8 | 0.9937 |
| 18 | `v0=_bn/1, v1=math.sin/1 ; v1-arg->v0` | 9 | 2/16: nodding-seedhead, pressed-fern | paint_families.py:284, paint_families.py:292, paint_families.py:367 +6 | 230.9 | 0.9936 |
| 19 | `v0=mix/3+, v1=mix/3+ ; v0-next->v1` | 9 | 6/16: block-print, contour-basin, fairway-plat +3 | _families_botanical.py:100, _families_botanical.py:102, _families_botanical.py:103 +15 | 230.9 | 0.9936 |
| 20 | `v0=<circle>, v1=<clipPath>, v2=<defs> ; v1-next->v0, v2-next->v1` | 7 | 16/16: block-print, chevron-run, contour-basin +13 | _families_botanical.py:213, _families_cartography.py:107, _families_foundry.py:122 +4 | 350.3 | 0.9901 |

## Beside the port

`port/painter/core.mjs` is what a human pulled out of these same sources by hand.  A mined substructure corresponds to a helper when its callees are that helper's studio spellings and nothing else.

| core.mjs helper | line | studio callees | mined |
| --- | ---: | --- | --- |
| `PyRandom` | 25 | choice, random, random.Random, randrange, uniform | ranks 4, 16 |
| `fmt` | 250 | format | not mined |
| `fmt1` | 264 | -- | n/a (an operator or a format spec, never a call) |
| `fmt2` | 267 | -- | n/a (an operator or a format spec, never a call) |
| `fmt3` | 270 | -- | n/a (an operator or a format spec, never a call) |
| `pyRound` | 273 | round | not mined |
| `pyRoundInt` | 283 | int, round | rank 15 |
| `pyMod` | 295 | -- | n/a (an operator or a format spec, never a call) |
| `pyFloorDiv` | 302 | -- | n/a (an operator or a format spec, never a call) |
| `pyStr` | 317 | str | not mined |
| `pyNum` | 349 | -- | n/a (an operator or a format spec, never a call) |
| `hypot` | 394 | math.hypot | not mined |
| `atan2` | 474 | math.atan2 | not mined |
| `sin` | 551 | math.sin | not mined |
| `cos` | 560 | math.cos | not mined |
| `escape` | 570 | html.escape | not mined |
| `degrees` | 593 | math.degrees | not mined |
| `radians` | 594 | math.radians | not mined |
| `xy` | 600 | _xy, xy | not mined |
| `strokeFloor` | 605 | _floor_width | not mined |
| `strokeText` | 613 | _stroke, _sw, stroke, stroke_for | not mined |
| `checkHex` | 619 | _check, _guard, fullmatch | not mined |

Mined substructures with no port helper -- compositions the hand port did not give a name:

- rank 1 (33 instances, 1903 bits): `v0=append/1, v1=for, v2=range/1 ; v1-in->v0, v2-arg->v1` -- callees: append, range
- rank 2 (38 instances, 1097 bits): `v0=append/1, v1=if ; v1-in->v0` -- callees: append
- rank 3 (18 instances, 1007 bits): `v0=_f/1, v1=_f/1, v2=format/3+ ; v0-arg->v2, v1-arg->v2` -- callees: _f, format
- rank 5 (30 instances, 859 bits): `v0=append/1, v1=append/1 ; v0-next->v1` -- callees: append
- rank 6 (20 instances, 560 bits): `v0=for, v1=range/1 ; v1-arg->v0` -- callees: range
- rank 7 (10 instances, 529 bits): `v0=<circle>, v1=n/1, v2=n/1 ; v1-arg->v0, v2-arg->v0` -- callees: n
- rank 8 (10 instances, 529 bits): `v0=<path>, v1=n/1, v2=stroke_for/2 ; v1-arg->v0, v2-arg->v1` -- callees: n, stroke_for
- rank 9 (15 instances, 410 bits): `v0=SUB2, v1=append/1 ; v0-in->v1` -- callees: append
- rank 10 (9 instances, 469 bits): `v0=SUB3, v1=_f/1, v2=_f/1 ; v1-arg->v0, v2-arg->v0` -- callees: _f, format
- rank 11 (12 instances, 320 bits): `v0=<g>, v1=SUB5 ; v0-arg->v1` -- callees: append
- rank 12 (10 instances, 261 bits): `v0=ValueError/1, v1=if ; v1-in->v0` -- callees: ValueError
- rank 13 (10 instances, 261 bits): `v0=_cn/1, v1=stroke_for/2 ; v1-arg->v0` -- callees: _cn, stroke_for
- rank 14 (10 instances, 261 bits): `v0=append/1, v1=for ; v1-in->v0` -- callees: append
- rank 17 (9 instances, 231 bits): `v0=_bn/1, v1=math.cos/1 ; v1-arg->v0` -- callees: _bn, math.cos
- rank 18 (9 instances, 231 bits): `v0=_bn/1, v1=math.sin/1 ; v1-arg->v0` -- callees: _bn, math.sin
- rank 19 (9 instances, 231 bits): `v0=mix/3+, v1=mix/3+ ; v0-next->v1` -- callees: mix
- rank 20 (7 instances, 350 bits): `v0=<circle>, v1=<clipPath>, v2=<defs> ; v1-next->v0, v2-next->v1` -- callees: none, pure control and emission

## What this proves

The units that pay for themselves in bits are compositions -- a formatter feeding a tag, a stroke floor formatted into a path, an emission inside a counted loop -- not the single-call shims `core.mjs` exports: 2 of its 22 helpers come back as a mined substructure, and 17 of the 20 mined substructures answer to no helper the hand port named.  Those 17 are the candidates, each with its evidence attached: how many instances, which of the 16 families, and the lines they were read off.  It proves nothing about behaviour -- a substructure is a shape in the call graph, not a promise that replacing it keeps a single byte of SVG the same.
