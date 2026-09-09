# Port the painter to JavaScript, verified by digest

A bounded task for any coding agent (DeepSeek, OpenCode, Codex, Claude). It is checkable by one
command and needs no judgment call: the port passes when every case is byte-identical.

## Why

DiscStudio ships as a static site with no backend. The disc-art families and card renderers were
designed, judged and promoted in Python (`pyto/consumers/discstudio-card/`). For users, they must
run in the browser. JS is first class here; the Python side is the workshop that produced the
reference bytes. The record of "same inputs, same bytes in both runtimes" is the proof the port is
the same format, and it is how every future format crosses from the workshop to the site.

## The task

Write `painter.mjs`, a dependency-free ES module (no npm, no DOM, runs under Node 22 and in a
browser) exporting:

```js
export function render(family, seed, base, accent, target, label) // -> string, the full SVG document
```

that reproduces, byte for byte, the Python output for all 16 families over the fixture matrix:
3 palettes x 3 seeds x 3 targets = 27 cases per family, 432 in all. Optionally also `cards.mjs`
exporting `renderSingle(card, art, width)` and `renderBattle(card, art, width)` for the two
promoted card renderers (8 cases).

Sources to port, verbatim in behavior:

- `pyto/consumers/discstudio-card/paint_components.py` (the 4 classic families and the shared
  frame: 512-unit viewBox, disc clip, rim, stroke floors, label at 220 only)
- `pyto/consumers/discstudio-card/paint_families.py` and `_families_{foundry,cartography,signal,botanical}.py`
  (the 12 tournament families; `art_registry.py` maps slug to function)
- `pyto/consumers/discstudio-card/card_render.py`, `_card_botanical.py`, `_card_signal.py` (cards)

The traps, all of which the fixtures will catch:

- Python's `random.Random(seed)` is a Mersenne Twister with Python's exact `uniform`, `randrange`
  and `choice` semantics. Port the generator and those methods exactly (MT19937 with Python's
  seeding by `init_by_array` over the integer's 32-bit chunks, `random()` from two 32-bit draws,
  `randrange` via `_randbelow` with `getrandbits`). Do not use `Math.random`.
- Python float formatting: `f"{x:.1f}"` rounds half to even on the binary value and `round(x, 1)`
  likewise; JS `toFixed` differs on ties. Match Python's behavior, including `-0.0` where it
  appears.
- `html.escape(label, quote=True)` for labels and `<title>`.
- Line endings: the Python output joins with `\n` and ends with `\n`.
- Identity parameters are drawn once per render before any target-dependent branch; rendering a
  different target must consume no additional random draws.

## Verify

```sh
cd pyto/consumers/discstudio-card/port/painter
node verify_port.mjs ./painter.mjs            # families
node verify_port.mjs ./painter.mjs ./cards.mjs # families and cards
```

The verifier prints per-family counts and the first divergence position with 40 characters of
context on each side for every failing case, and exits 0 only when all cases match. Fixtures:
`fixtures/expected.json` (432 cases with the full expected SVG text) and
`fixtures/expected-cards.json` (8 cases).

## Hand back

`painter.mjs` (and `cards.mjs` if attempted), the verifier's output, and a note on which trap cost
the most time. Partial ports are useful: a family that passes all 27 cases is done regardless of
the others, and the per-family table says which are.

## Scoring

Byte-identical cases out of 432, then out of 8. Nothing else counts. A port that passes with an
extra dependency does not pass.
