#!/usr/bin/env python3
# RETAINED verbatim from pyto/experiments/art-tournament/studios/foundry/families.py
# (studio *foundry*: halftone-screen 64/72, register-mark 64/72, hot-foil 59/72 --
# all three retained, none promoted; experiments/art-tournament/RESULTS.md S1).
# Nothing was deleted and nothing was renamed: the studio's helpers travel with
# its families so the renders under experiments/art-tournament/renders/foundry/
# stay valid receipts for this code. art_registry.py is the seam that publishes
# these as provisional, reversible vocabulary.
"""Foundry studio - disc art that looks like it came off a print shop's bed.

Three families, each built from a real pre-press artefact:

  halftone-screen : a duotone halftone wedge, dots on a rotated screen grid
                    ramping from an open tint to solid ink coverage.
  register-mark   : a press registration target - full-bleed crosshair, tint
                    steps in the four quadrants, crop marks, centre bullseye.
  hot-foil        : a hot-stamp foil die - faceted badge, sheen band across the
                    facets, knurled tick ring where the die bites the plastic.

Every family is a module-level function with the paint_components contract:

    fam(seed: int, base: str, accent: str, target: int, label: str) -> str

returning a FULL SVG document (512 viewBox, width = height = target, disc clip
at r=220, rim, deterministic, label only at 220). Identity parameters are drawn
from random.Random(seed) once, before any target branching, so rendering the
same seed at another target consumes exactly the same RNG.
"""
from __future__ import annotations

import html
import math
import random

SIZE, C, R = 512, 256, 220
TARGETS = (42, 96, 220)
TAU = math.tau

FAMILIES = ("halftone-screen", "register-mark", "hot-foil")

# What each input actually moves, per family. Consumed by manifest.json / README.
FAMILY_PARAMS: dict[str, dict[str, object]] = {
    "halftone-screen": {
        "name": "Halftone Screen",
        "concept": "Duotone halftone wedge: one ink, screened on a rotated grid, "
                   "ramping from an open tint into solid coverage.",
        "seed": "picks the screen angle (15/45/75/105 deg), the direction the tint "
                "wedge ramps in, the minimum dot size (how open the light end stays) "
                "and the phase of the four rim register ticks.",
        "base": "the plastic - fills the disc under the screen and knocks out the "
                "label plate at 220.",
        "accent": "the single ink - every dot, the rim ring and the register ticks.",
        "label": "hot-stamped into a knockout plate at the bottom of the face; "
                 "drawn only at 220, uppercased, clipped to 10 characters.",
        "targets": {42: "5 cells across, blobs only", 96: "9 cells + register ticks",
                    220: "15 cells + register ticks + label plate"},
    },
    "register-mark": {
        "name": "Register Mark",
        "concept": "A press registration target laid over the whole face: crosshair "
                   "to the rim, four quadrants inked at descending tint steps, crop "
                   "marks, bullseye at centre.",
        "seed": "rotates the whole assembly, chooses which quadrant carries solid ink "
                "(the other three step down from it), sets the crosshair centre gap "
                "and nudges the crop mark inset.",
        "base": "the plastic; also knocks out the bullseye core and the label plate.",
        "accent": "the ink - quadrant tints, crosshair, bullseye rings, crop marks.",
        "label": "knockout plate at the bottom of the face, 220 only, uppercased, "
                 "clipped to 10 characters.",
        "targets": {42: "quadrant tints + crosshair + bullseye", 96: "adds crop marks",
                    220: "adds finer bullseye ring + label plate"},
    },
    "hot-foil": {
        "name": "Hot Foil",
        "concept": "A hot-stamp foil die: faceted badge, a sheen band raked across "
                   "the facets, and the knurled tick ring the die leaves in the rim.",
        "seed": "chooses the die shape (hex or octagon), rotates the die, sets the "
                "rake angle of the foil sheen band and the phase of the knurl ring.",
        "base": "the plastic; also the knockout keyline inside the badge and the "
                "label plate.",
        "accent": "the foil - badge fill, knurl ticks and rim ring.",
        "label": "knockout plate at the bottom of the face, 220 only, uppercased, "
                 "clipped to 10 characters.",
        "targets": {42: "12 long knurl teeth, solid badge, bevel split + specular band",
                    96: "20 teeth + die keyline", 220: "32 teeth + die keyline + label plate"},
    },
}


# --------------------------------------------------------------------------- #
# shared shop floor helpers
# --------------------------------------------------------------------------- #

def _floor_width(target: int, min_output: float) -> float:
    """Stroke width, in viewBox units, that lands on `min_output` output px."""
    return round(min_output / (target / SIZE), 1)


def _sw(source: float, target: int, min_output: float = 1.0) -> str:
    return f"{max(source, _floor_width(target, min_output)):.1f}"


def _check(target: int) -> None:
    if target not in TARGETS:
        raise ValueError(f"target must be one of {TARGETS}")


def _poly(cx: float, cy: float, radius: float, sides: int, rotation: float) -> str:
    pts = []
    for i in range(sides):
        a = math.radians(rotation) + i * TAU / sides
        pts.append(f"{cx + radius * math.cos(a):.1f},{cy + radius * math.sin(a):.1f}")
    return " ".join(pts)


def _open(target: int, label: str, extra_defs: tuple[str, ...] = ()) -> tuple[list[str], str]:
    safe = html.escape(label, quote=True)
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{target}" height="{target}"'
        f' viewBox="0 0 {SIZE} {SIZE}" role="img" aria-label="{safe}">',
        '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
        '<linearGradient id="depth" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity=".16"/>'
        '<stop offset="1" stop-color="#000000" stop-opacity=".30"/></linearGradient>',
    ]
    out.extend(extra_defs)
    out.append('</defs>')
    return out, safe


def _plate(base: str) -> list[str]:
    return [
        '<g id="base" clip-path="url(#disc)">',
        f'<circle cx="256" cy="256" r="220" fill="{base}"/>',
        '<circle cx="256" cy="256" r="220" fill="url(#depth)"/>',
        '</g>',
    ]


def _rim(accent: str, target: int) -> list[str]:
    return [
        '<g id="rim" fill="none">',
        f'<circle cx="256" cy="256" r="216" stroke="{accent}"'
        f' stroke-width="{_sw(7, target)}" opacity=".92"/>',
        f'<circle cx="256" cy="256" r="203" stroke="#ffffff"'
        f' stroke-width="{_sw(3, target)}" opacity=".30"/>',
        '</g>',
    ]


def _label_plate(label: str, base: str, accent: str, target: int) -> list[str]:
    """A knockout plate with the label hot-stamped into it. 220 only."""
    if target != 220:
        return []
    text = label.strip()[:10].upper()
    if not text:
        return []
    width = 16.0 * len(text) + 40.0
    x = 256.0 - width / 2.0
    return [
        '<g id="text">',
        f'<rect x="{x:.1f}" y="396" width="{width:.1f}" height="36" rx="4"'
        f' fill="{base}" stroke="{accent}" stroke-width="3" opacity=".96"/>',
        f'<text x="257.5" y="421" text-anchor="middle" font-family="sans-serif"'
        f' font-size="20" font-weight="700" letter-spacing="3"'
        f' fill="{accent}">{html.escape(text, quote=True)}</text>',
        '</g>',
    ]


def _close(safe: str) -> list[str]:
    return [f'<title>{safe}</title>', '</svg>']


# --------------------------------------------------------------------------- #
# family 1 - halftone screen
# --------------------------------------------------------------------------- #

def halftone_screen(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """One ink, screened. A tint wedge that ramps into solid coverage."""
    _check(target)
    rng = random.Random(seed)
    screen = rng.choice((15.0, 45.0, 75.0, 105.0))
    ramp = rng.uniform(0.0, TAU)
    openness = rng.uniform(0.16, 0.34)
    tick_phase = rng.uniform(-10.0, 10.0)

    out, safe = _open(target, label)
    out += _plate(base)

    cells = 5 if target == 42 else (9 if target == 96 else 15)
    cell = 2.0 * R / cells
    ca, sa = math.cos(math.radians(screen)), math.sin(math.radians(screen))
    rx, ry = math.cos(ramp), math.sin(ramp)
    reach = int(cells // 2) + 2

    out.append('<g id="art" clip-path="url(#disc)">')
    out.append(f'<g id="screen" fill="{accent}">')
    for row in range(-reach, reach + 1):
        for col in range(-reach, reach + 1):
            u = (col + 0.5 * (row % 2)) * cell
            v = row * cell
            x = C + u * ca - v * sa
            y = C + u * sa + v * ca
            dx, dy = x - C, y - C
            t = 0.5 + (dx * rx + dy * ry) / (2.0 * R)
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            radius = cell * 0.5 * (openness + (1.62 - openness) * (t ** 1.35))
            if radius < 1.2 or dx * dx + dy * dy > (R + radius) ** 2:
                continue
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}"/>')
    out.append('</g>')
    out.append('</g>')

    out += _rim(accent, target)

    # Register ticks, cut clean through the rim the way a press sheet marks
    # where the screen was hung. Drawn over the rim, clipped to the plastic.
    out.append('<g id="stamp" clip-path="url(#disc)">')
    if target != 42:
        out.append(f'<g stroke="{base}" stroke-width="{_sw(16, target, 1.7)}"'
                   f' stroke-linecap="butt">')
        for i in range(4):
            a = math.radians(tick_phase + i * 90.0)
            out.append(f'<line x1="{C + 150 * math.cos(a):.1f}" y1="{C + 150 * math.sin(a):.1f}"'
                       f' x2="{C + 222 * math.cos(a):.1f}" y2="{C + 222 * math.sin(a):.1f}"/>')
        out.append('</g>')
        out.append(f'<g stroke="{accent}" stroke-width="{_sw(3.5, target, 0.8)}"'
                   f' stroke-linecap="butt" opacity=".95">')
        for i in range(4):
            a = math.radians(tick_phase + i * 90.0)
            out.append(f'<line x1="{C + 156 * math.cos(a):.1f}" y1="{C + 156 * math.sin(a):.1f}"'
                       f' x2="{C + 222 * math.cos(a):.1f}" y2="{C + 222 * math.sin(a):.1f}"/>')
        out.append('</g>')
    out.append('</g>')
    out += _label_plate(label, base, accent, target)
    out += _close(safe)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# family 2 - register mark
# --------------------------------------------------------------------------- #

_TINTS = (1.0, 0.66, 0.40, 0.18)


def register_mark(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """A press registration target blown up to fill the whole face."""
    _check(target)
    rng = random.Random(seed)
    rotation = rng.uniform(-16.0, 16.0)
    solid = rng.randrange(4)
    gap = rng.uniform(58.0, 82.0)
    crop_inset = rng.uniform(-10.0, 10.0)

    out, safe = _open(target, label)
    out += _plate(base)
    out.append('<g id="art" clip-path="url(#disc)">')
    out.append(f'<g transform="rotate({rotation:.1f} 256 256)">')

    # Four quadrants, inked at descending tint steps from the solid one.
    for q in range(4):
        tint = _TINTS[(q - solid) % 4]
        if tint <= 0.0:
            continue
        a0 = q * TAU / 4.0
        a1 = a0 + TAU / 4.0
        x0, y0 = C + 300 * math.cos(a0), C + 300 * math.sin(a0)
        x1, y1 = C + 300 * math.cos(a1), C + 300 * math.sin(a1)
        out.append(f'<path d="M256 256 L{x0:.1f} {y0:.1f} A300 300 0 0 1 {x1:.1f} {y1:.1f} Z"'
                   f' fill="{accent}" opacity="{tint:.2f}"/>')

    # Crop marks: L brackets in the corners of the imposition.
    if target != 42:
        arm = 46.0
        inset = 148.0 + crop_inset
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            px, py = C + sx * inset, C + sy * inset
            out.append(f'<path d="M{px - sx * arm:.1f} {py:.1f} L{px:.1f} {py:.1f}'
                       f' L{px:.1f} {py - sy * arm:.1f}" fill="none" stroke="{base}"'
                       f' stroke-width="{_sw(9, target)}" opacity=".8"/>')

    # The crosshair: knocked out of the ink, then hairlined in ink down its
    # middle, so it stays crisp over the solid quadrant and the open one alike.
    arms = tuple((C + dx * gap, C + dy * gap, C + dx * 232, C + dy * 232)
                 for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)))
    out.append(f'<g stroke="{base}" stroke-width="{_sw(22, target, 2.2)}"'
               f' stroke-linecap="butt">')
    for x1, y1, x2, y2 in arms:
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    out.append('</g>')
    if target != 42:
        out.append(f'<g stroke="{accent}" stroke-width="{_sw(4, target, 0.9)}"'
                   f' stroke-linecap="butt" opacity=".9">')
        for x1, y1, x2, y2 in arms:
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
        out.append('</g>')

    out.append('</g>')
    out.append('</g>')

    # Bullseye at dead centre - knocked out of the plastic, ringed in ink.
    out.append('<g id="stamp">')
    out.append(f'<circle cx="256" cy="256" r="{gap - 8:.1f}" fill="{base}"'
               f' stroke="{accent}" stroke-width="{_sw(12, target)}"/>')
    if target == 220:
        out.append(f'<circle cx="256" cy="256" r="{gap - 26:.1f}" fill="none"'
                   f' stroke="{accent}" stroke-width="4" opacity=".7"/>')
    out.append(f'<circle cx="256" cy="256" r="{max(11.0, gap * 0.24):.1f}" fill="{accent}"/>')
    out.append('</g>')

    out += _rim(accent, target)
    out += _label_plate(label, base, accent, target)
    out += _close(safe)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# family 3 - hot foil
# --------------------------------------------------------------------------- #

def hot_foil(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """A hot-stamp foil die: faceted badge, raked sheen, knurled tick ring."""
    _check(target)
    rng = random.Random(seed)
    facets = rng.choice((6, 6, 8))
    die_rotation = rng.uniform(-22.0, 22.0)
    rake = rng.uniform(-38.0, 38.0)
    knurl_phase = rng.uniform(0.0, 22.0)

    badge_r = 144.0
    die_points = _poly(C, C, badge_r, facets, die_rotation)
    defs = (f'<clipPath id="die"><polygon points="{die_points}"/></clipPath>',)
    out, safe = _open(target, label, defs)
    out += _plate(base)

    out.append('<g id="art" clip-path="url(#disc)">')
    # Knurl: the ring of teeth the stamping die leaves around the impression.
    teeth = 12 if target == 42 else (20 if target == 96 else 32)
    tooth_in = 168.0 if target == 42 else 176.0
    out.append(f'<g id="knurl" stroke="{accent}" stroke-width="{_sw(14, target)}"'
               f' stroke-linecap="butt" opacity=".92">')
    for i in range(teeth):
        a = math.radians(knurl_phase + i * 360.0 / teeth)
        out.append(f'<line x1="{C + tooth_in * math.cos(a):.1f}"'
                   f' y1="{C + tooth_in * math.sin(a):.1f}"'
                   f' x2="{C + 210 * math.cos(a):.1f}" y2="{C + 210 * math.sin(a):.1f}"/>')
    out.append('</g>')
    out.append('</g>')

    out.append('<g id="stamp">')
    out.append(f'<polygon points="{die_points}" fill="{accent}"/>')
    # Foil sheen: the die's bevel splits the badge into a lit half and a shaded
    # half, with one narrow specular band riding the split line.
    out.append('<g clip-path="url(#die)">')
    out.append(f'<g transform="rotate({rake:.1f} 256 256)">')
    out.append('<rect x="-16" y="-16" width="544" height="256" fill="#ffffff" opacity=".22"/>')
    out.append('<rect x="-16" y="256" width="544" height="272" fill="#000000" opacity=".20"/>')
    out.append('<rect x="-16" y="232" width="544" height="26" fill="#ffffff" opacity=".55"/>')
    out.append('<rect x="-16" y="300" width="544" height="14" fill="#ffffff" opacity=".22"/>')
    out.append('</g>')
    out.append('</g>')
    # Keyline: the die's inner step, knocked back to the plastic colour.
    if target != 42:
        inner = _poly(C, C, badge_r - 34.0, facets, die_rotation)
        out.append(f'<polygon points="{inner}" fill="none" stroke="{base}"'
                   f' stroke-width="{_sw(9, target)}" opacity=".75"/>')
    out.append('</g>')

    out += _rim(accent, target)
    out += _label_plate(label, base, accent, target)
    out += _close(safe)
    return "\n".join(out) + "\n"


FAMILY_FUNCTIONS = {
    "halftone-screen": halftone_screen,
    "register-mark": register_mark,
    "hot-foil": hot_foil,
}

CALCULATIONS = {
    "fn.discArt.halftone-screen": halftone_screen,
    "fn.discArt.register-mark": register_mark,
    "fn.discArt.hot-foil": hot_foil,
}
