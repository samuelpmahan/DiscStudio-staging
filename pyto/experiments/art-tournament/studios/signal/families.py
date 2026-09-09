#!/usr/bin/env python3
"""Studio *signal* disc-art families: broadcast graphics on a disc face.

Three families, each a piece of live-sports television furniture:

    chevron-run   a transition wipe -- a run of fat chevrons with a lit nose
    score-bug     the lower-third score plate -- band, chip, lit segments
    sweep-clock   the shot clock -- tick ring, filled wedge, bright hand

Every family is ``fam(seed, base, accent, target, label) -> str`` and returns a
full SVG document sharing paint_components' contract: 512-unit viewBox,
width = height = target, a ``#disc`` clip at r=220, the same rim pair, a
``<title>`` plus ``aria-label``, deterministic output from ``seed`` alone, and
label text only at target 220. Identity parameters are drawn from
``random.Random(seed)`` once, in a fixed order, before any target branching, so
rendering a second target consumes no extra RNG and yields the same identity.

Colour discipline (why these read at 42px): the caller supplies two colours, so
each family derives two more by contrast rather than by hue. ``edge`` is the
colour that separates from the *base* (white on a dark or mid disc, near-black
on a pale one) and carries the one bright "live" mark; ``knock`` is the colour
that separates from the *accent* and is used only for marks sitting on top of
an accent mass. Both are pure functions of the input hexes.
"""
from __future__ import annotations

import html
import math
import random

SIZE = 512
C = 256
R = 220
TARGETS = (42, 96, 220)

WHITE = "#ffffff"
NEAR_BLACK = "#111318"


# ---------------------------------------------------------------- colour ---

def _channels(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def _hex(r: float, g: float, b: float) -> str:
    def clamp(x: float) -> int:
        return max(0, min(255, int(round(x))))

    return "#{:02x}{:02x}{:02x}".format(clamp(r), clamp(g), clamp(b))


def mix(a: str, b: str, t: float) -> str:
    """Blend hex colour `a` toward hex colour `b` by t in [0, 1]."""
    ar, ag, ab = _channels(a)
    br, bg, bb = _channels(b)
    return _hex(ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t)


def luminance(value: str) -> float:
    """Rough relative luminance in [0, 1]; good enough to pick a contrast ink."""
    r, g, b = _channels(value)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def contrast_ink(value: str, pivot: float = 0.62) -> str:
    """White over a dark/mid colour, near-black over a pale one."""
    return NEAR_BLACK if luminance(value) > pivot else WHITE


# --------------------------------------------------------------- helpers ---

def _f(value: float) -> str:
    text = "{:.1f}".format(value)
    return text[:-2] if text.endswith(".0") else text


def _stroke(source: float, target: int, min_output: float = 1.0) -> str:
    """Keep a 512-unit stroke at least `min_output` device px wide at `target`."""
    return _f(max(source, round(min_output * SIZE / target, 1)))


def _xy(radius: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return C + radius * math.cos(a), C + radius * math.sin(a)


def _open(target: int, safe: str, base: str, accent: str) -> list[str]:
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="{t}" height="{t}" '
        'viewBox="0 0 {s} {s}" role="img" aria-label="{a}">'.format(t=target, s=SIZE, a=safe),
        '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
        '<linearGradient id="depth" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".18"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".28"/></linearGradient></defs>',
        '<g id="base" clip-path="url(#disc)">',
        '<circle cx="256" cy="256" r="220" fill="{}"/>'.format(base),
        '<circle cx="256" cy="256" r="220" fill="url(#depth)"/>',
        '</g>',
        '<g id="rim" fill="none">',
        '<circle cx="256" cy="256" r="216" stroke="{}" stroke-width="{}" opacity=".9"/>'.format(
            accent, _stroke(7, target)),
        '<circle cx="256" cy="256" r="201" stroke="#fff" stroke-width="{}" opacity=".28"/>'.format(
            _stroke(3, target)),
        '</g>',
    ]


def _label_plate(label: str, accent: str, knock: str) -> list[str]:
    """A broadcast name plate, drawn only at target 220."""
    display = label.strip()[:10]
    if not display:
        return []
    size, spacing = 22.0, 2.0
    text_w = len(display) * (size * 0.63 + spacing)
    width = max(122.0, text_w + 46)
    x = C - width / 2
    return [
        '<g id="text">',
        '<rect x="{}" y="402" width="{}" height="38" rx="7" fill="{}"/>'.format(
            _f(x), _f(width), accent),
        '<rect x="{}" y="410" width="7" height="22" rx="3.5" fill="{}" opacity=".95"/>'.format(
            _f(x + 11), knock),
        '<text x="{}" y="428" text-anchor="middle" font-family="sans-serif" font-size="22" '
        'font-weight="700" letter-spacing="2" fill="{}">{}</text>'.format(
            _f(C + spacing / 2 + 5), knock, html.escape(display, quote=True)),
        '</g>',
    ]


def _close(safe: str) -> list[str]:
    return ['<title>{}</title>'.format(safe), '</svg>']


def _guard(target: int) -> None:
    if target not in TARGETS:
        raise ValueError("target must be one of {}".format(TARGETS))


# ------------------------------------------------------------ chevron-run ---

def chevron_run(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """A broadcast wipe: a run of fat chevrons marching with a lit nose."""
    _guard(target)
    rng = random.Random(seed)
    tilt = rng.uniform(-17, 17)
    pitch = rng.uniform(54, 76)
    phase = rng.uniform(-34, 34)
    arm = rng.uniform(96, 140)
    chip_deg = rng.uniform(-46, 46)

    safe = html.escape(label, quote=True)
    edge = contrast_ink(base)
    knock = contrast_ink(accent, pivot=0.5)
    count = 3 if target == 42 else (4 if target == 96 else 5)
    nose = 84.0
    width = 40 if target == 42 else (34 if target == 96 else 30)

    out = _open(target, safe, base, accent)
    out.append('<g id="art" clip-path="url(#disc)">')
    out.append('<g transform="rotate({} 256 256)">'.format(_f(tilt)))
    out.append('<rect x="-60" y="{}" width="632" height="{}" fill="{}" opacity=".16"/>'.format(
        _f(C - arm - 34), _f(2 * arm + 68), accent))
    if target != 42:
        reach = (count - 1) / 2.0 * pitch + nose
        for sign in (-1, 1):
            y = C + sign * (arm + 16)
            out.append('<path d="M{x0} {y} H{x1}" stroke="{a}" stroke-width="{w}" opacity=".3" '
                       'stroke-linecap="round"/>'.format(
                           x0=_f(C + phase * 0.5 - reach - 46), x1=_f(C + phase * 0.5 + reach),
                           y=_f(y), a=accent, w=_stroke(6, target, 1.0)))
    span = (count - 1) * pitch
    for i in range(count):
        x = C + phase * 0.5 + (i - (count - 1) / 2.0) * pitch - span * 0.0
        opacity = 0.42 + 0.58 * (i / float(count - 1))
        out.append(
            '<path d="M{x0} {y0} L{x1} 256 L{x0} {y1}" fill="none" stroke="{a}" stroke-width="{w}" '
            'stroke-linecap="butt" stroke-linejoin="miter" opacity="{o:.2f}"/>'.format(
                x0=_f(x - nose / 2), x1=_f(x + nose / 2), y0=_f(C - arm), y1=_f(C + arm),
                a=accent, w=_stroke(width, target, 2.0), o=opacity))
    lead_x = C + phase * 0.5 + ((count - 1) / 2.0) * pitch
    # the lit nose rides on top of the accent mass, so it takes the knock ink
    out.append(
        '<path d="M{x0} {y0} L{x1} 256 L{x0} {y1}" fill="none" stroke="{e}" stroke-width="{w}" '
        'stroke-linecap="butt" stroke-linejoin="miter" opacity=".95"/>'.format(
            x0=_f(lead_x - nose / 2), x1=_f(lead_x + nose / 2), y0=_f(C - arm), y1=_f(C + arm),
            e=knock, w=_stroke(width * 0.34, target, 1.4)))
    out.append('</g>')
    out.append('</g>')

    cx, cy = C + chip_deg * 1.8, C - arm - 24
    size = 30 if target == 42 else 26
    out += [
        '<g id="stamp">',
        '<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="4" fill="{e}" '
        'transform="rotate({r} {cx} {cy})"/>'.format(
            x=_f(cx - size / 2), y=_f(cy - size / 2), s=size, e=edge,
            r=_f(tilt), cx=_f(cx), cy=_f(cy)),
        '<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="4" fill="none" stroke="{a}" '
        'stroke-width="{w}" transform="rotate({r} {cx} {cy})"/>'.format(
            x=_f(cx - size / 2), y=_f(cy - size / 2), s=size, a=accent,
            w=_stroke(7, target, 1.0), r=_f(tilt), cx=_f(cx), cy=_f(cy)),
        '</g>',
    ]
    if target == 220:
        out += _label_plate(label, accent, knock)
    out += _close(safe)
    return "\n".join(out) + "\n"


# -------------------------------------------------------------- score-bug ---

def score_bug(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """The lower-third score plate: band, logo chip, lit tally segments."""
    _guard(target)
    rng = random.Random(seed)
    tilt = rng.uniform(-5, 5)
    y_off = rng.uniform(-26, 36)
    lit = rng.randrange(1, 5)
    chip_right = rng.randrange(2)
    tick_shift = rng.uniform(-18, 18)

    safe = html.escape(label, quote=True)
    edge = contrast_ink(base)
    knock = contrast_ink(accent, pivot=0.5)
    dim = mix(accent, "#000000", 0.5) if luminance(accent) > 0.32 else mix(accent, "#000000", 0.62)
    cy = C + y_off
    half = 54.0
    cells = 3 if target == 42 else 5
    pad, chip, gap, colon_w = 86.0, 66.0, 15.0, 18.0
    run_w = (SIZE - 2 * pad) - chip - colon_w - 2 * gap
    cell_gap = 12.0
    cell_w = (run_w - (cells - 1) * cell_gap) / cells
    if chip_right:
        run_x = pad
        colon_x = pad + run_w + gap
        chip_x = colon_x + colon_w + gap
    else:
        chip_x = pad
        colon_x = pad + chip + gap
        run_x = colon_x + colon_w + gap

    out = _open(target, safe, base, accent)
    out.append('<g id="art" clip-path="url(#disc)">')
    out.append('<g transform="rotate({} 256 256)">'.format(_f(tilt)))
    # rule above the plate, then the plate, then its drop shadow
    out.append('<rect x="-40" y="{}" width="592" height="{}" fill="{}" opacity=".9"/>'.format(
        _f(cy - half - 26), _stroke(9, target, 1.2), edge))
    if target != 42:
        for i in range(3):
            out.append('<rect x="{x}" y="{y}" width="{w}" height="18" fill="{a}" opacity=".5"/>'.format(
                x=_f(96 + tick_shift + i * 42), y=_f(cy - half - 48), w=_stroke(9, target, 1.0), a=accent))
    out.append('<rect x="-40" y="{}" width="592" height="{}" fill="{}"/>'.format(
        _f(cy - half), _f(2 * half), accent))
    out.append('<rect x="-40" y="{}" width="592" height="18" fill="#000" opacity=".26"/>'.format(
        _f(cy + half)))
    out.append('<rect x="-40" y="{}" width="592" height="{}" fill="{}" opacity=".55"/>'.format(
        _f(cy + half + 18), _stroke(7, target, 1.0), accent))
    # logo chip
    out.append('<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="8" fill="{k}"/>'.format(
        x=_f(chip_x), y=_f(cy - chip / 2), s=_f(chip), k=knock))
    out.append(
        '<path d="M{x0} {y0} L{x1} {cy} L{x0} {y1}" fill="none" stroke="{a}" stroke-width="{w}" '
        'stroke-linejoin="miter"/>'.format(
            x0=_f(chip_x + chip * 0.3), x1=_f(chip_x + chip * 0.68), cy=_f(cy),
            y0=_f(cy - chip * 0.24), y1=_f(cy + chip * 0.24), a=accent,
            w=_stroke(12, target, 1.6)))
    # tally segments
    for i in range(cells):
        x = run_x + i * (cell_w + cell_gap)
        on = i < lit
        out.append('<rect x="{x}" y="{y}" width="{w}" height="46" rx="4" fill="{f}"/>'.format(
            x=_f(x), y=_f(cy - 23), w=_f(cell_w), f=(knock if on else dim)))
    out.append('</g>')
    out.append('</g>')
    # the clock colon, sitting between the chip and the tally
    out += ['<g id="stamp">']
    for dy in (-27, 7):
        out.append('<rect x="{x}" y="{y}" width="{w}" height="{w}" rx="3" fill="{k}" '
                   'transform="rotate({r} 256 256)"/>'.format(
                       x=_f(colon_x), y=_f(cy + dy), w=_f(colon_w), k=knock, r=_f(tilt)))
    out.append('</g>')
    if target == 220:
        out += _label_plate(label, accent, knock)
    out += _close(safe)
    return "\n".join(out) + "\n"


# ------------------------------------------------------------ sweep-clock ---

def sweep_clock(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """A shot clock: tick ring, filled sweep wedge, one bright hand."""
    _guard(target)
    rng = random.Random(seed)
    start = rng.uniform(-118, -62)
    sweep = rng.uniform(105, 300)
    ring_shift = rng.uniform(0, 14)
    hub = rng.uniform(46, 62)
    pip_r = rng.uniform(96, 138)

    safe = html.escape(label, quote=True)
    edge = contrast_ink(base)
    knock = contrast_ink(accent, pivot=0.5)
    ticks = 6 if target == 42 else (12 if target == 96 else 24)
    wedge_r = 152.0
    end = start + sweep

    out = _open(target, safe, base, accent)
    out.append('<g id="art" clip-path="url(#disc)">')
    out.append('<circle cx="256" cy="256" r="184" fill="none" stroke="{}" stroke-width="{}" '
               'opacity=".3"/>'.format(accent, _stroke(11, target, 1.0)))
    for i in range(ticks):
        deg = ring_shift + i * (360.0 / ticks)
        major = (i % max(1, ticks // 4)) == 0
        inner = 158.0 if major else 168.0
        x0, y0 = _xy(inner, deg)
        x1, y1 = _xy(196.0, deg)
        out.append('<path d="M{x0} {y0} L{x1} {y1}" stroke="{c}" stroke-width="{w}" '
                   'stroke-linecap="butt" opacity="{o}"/>'.format(
                       x0=_f(x0), y0=_f(y0), x1=_f(x1), y1=_f(y1),
                       c=(edge if major else accent),
                       w=_stroke(16 if major else 11, target, 1.6 if major else 1.0),
                       o=".92" if major else ".8"))
    large = 1 if sweep > 180 else 0
    sx, sy = _xy(wedge_r, start)
    ex, ey = _xy(wedge_r, end)
    out.append(
        '<path d="M256 256 L{sx} {sy} A{r} {r} 0 {la} 1 {ex} {ey} Z" fill="{a}" opacity=".62"/>'.format(
            sx=_f(sx), sy=_f(sy), ex=_f(ex), ey=_f(ey), r=_f(wedge_r), la=large, a=accent))
    out.append(
        '<path d="M256 256 L{sx} {sy} A{r} {r} 0 {la} 1 {ex} {ey} Z" fill="none" stroke="{a}" '
        'stroke-width="{w}" stroke-linejoin="round"/>'.format(
            sx=_f(sx), sy=_f(sy), ex=_f(ex), ey=_f(ey), r=_f(wedge_r), la=large, a=accent,
            w=_stroke(10, target, 1.0)))
    hx, hy = _xy(178.0, end)
    out.append('<path d="M256 256 L{x} {y}" stroke="{e}" stroke-width="{w}" '
               'stroke-linecap="round"/>'.format(x=_f(hx), y=_f(hy), e=edge,
                                                 w=_stroke(18, target, 2.4)))
    px, py = _xy(pip_r, start + sweep / 2.0)
    out.append('<circle cx="{x}" cy="{y}" r="{r}" fill="{e}" opacity=".9"/>'.format(
        x=_f(px), y=_f(py), r=14 if target == 42 else 11, e=edge))
    out.append('</g>')
    out += [
        '<g id="stamp">',
        '<circle cx="256" cy="256" r="{r}" fill="{b}" stroke="{a}" stroke-width="{w}"/>'.format(
            r=_f(hub), b=base, a=accent, w=_stroke(14, target, 1.6)),
        '<circle cx="256" cy="256" r="{r}" fill="{e}"/>'.format(r=_f(hub * 0.38), e=edge),
        '</g>',
    ]
    if target == 220:
        out += _label_plate(label, accent, knock)
    out += _close(safe)
    return "\n".join(out) + "\n"


FAMILY_PARAMS: dict[str, dict[str, object]] = {
    "chevron-run": {
        "name": "Chevron Run",
        "concept": "A broadcast transition wipe frozen on the disc: a run of fat chevrons "
                   "over a wash band, the leading one carrying a bright inner nose.",
        "seed": {
            "tilt": "-17..17 deg rotation of the whole run",
            "pitch": "54..76 units between chevrons",
            "phase": "-34..34 units of travel along the run axis",
            "arm": "96..140 units of chevron half-height (how open the V is)",
            "chip_deg": "-46..46, scaled to slide the cue chip along the top edge of the band",
        },
        "base": "disc body fill; its luminance sets the cue chip ink, and the accent's sets "
                "the lit nose ink, so both stay legible on any palette",
        "accent": "chevron mass, wash band, speed rules, rim ring, cue-chip outline, label plate",
        "label": "aria-label and <title> at every target; the first 10 characters are set in the "
                 "name plate at 220 only",
        "targets": {"42": "3 chevrons, no speed rules, fattest strokes",
                    "96": "4 chevrons plus the two speed rules",
                    "220": "5 chevrons, finest strokes, name plate"},
    },
    "score-bug": {
        "name": "Score Bug",
        "concept": "The lower-third score bug laid across the disc: a hard accent band with a "
                   "logo chip, a run of tally segments (some lit) and a clock colon.",
        "seed": {
            "tilt": "-5..5 deg of the whole bug",
            "y_off": "-26..36 units of band height on the face",
            "lit": "1..4 of the segments read as lit",
            "chip_right": "which end of the band carries the logo chip",
            "tick_shift": "-18..18 units sliding the cue ticks above the band",
        },
        "base": "disc body fill; its luminance picks the colour of the hairline rule above the band",
        "accent": "the band itself, the chevron inside the chip, the cue ticks, the rim, the "
                  "unlit segments (as a darkened mix) and the label plate",
        "label": "aria-label and <title> at every target; first 10 characters in the plate at 220",
        "targets": {"42": "3 wide segments, no cue ticks",
                    "96": "5 segments plus the cue ticks",
                    "220": "5 segments, cue ticks, name plate"},
    },
    "sweep-clock": {
        "name": "Sweep Clock",
        "concept": "The shot clock: a tick ring with heavier quarter ticks, a filled sweep wedge "
                   "and one bright hand at the leading edge.",
        "seed": {
            "start": "-118..-62 deg where the wedge opens (near twelve o'clock)",
            "sweep": "105..300 deg of elapsed wedge",
            "ring_shift": "0..14 deg rotation of the tick ring",
            "hub": "46..62 units of hub radius",
            "pip_r": "96..138 units -- how far out the lit pip sits inside the wedge",
        },
        "base": "disc body fill and hub fill; its luminance picks the hand, quarter-tick and pip colour",
        "accent": "wedge fill and outline, minor ticks, ring, hub ring, rim, label plate",
        "label": "aria-label and <title> at every target; first 10 characters in the plate at 220",
        "targets": {"42": "6 ticks, thickest hand",
                    "96": "12 ticks",
                    "220": "24 ticks, name plate"},
    },
}

RENDERERS = {
    "chevron-run": chevron_run,
    "score-bug": score_bug,
    "sweep-clock": sweep_clock,
}

CALCULATIONS = {
    "fn.discArt.chevron-run": chevron_run,
    "fn.discArt.score-bug": score_bug,
    "fn.discArt.sweep-clock": sweep_clock,
}
