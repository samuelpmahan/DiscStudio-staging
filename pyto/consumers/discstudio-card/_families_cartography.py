#!/usr/bin/env python3
# RETAINED verbatim from pyto/experiments/art-tournament/studios/cartography/families.py
# (studio *cartography*: wind-rose 65/72 PROMOTED, fairway-plat 64/72 retained,
# contour-basin 63/72 retained; experiments/art-tournament/RESULTS.md S1).
# The whole studio module is kept, helpers and all, so the renders under
# experiments/art-tournament/renders/cartography/ stay valid receipts. The
# promoted slug is NOT served from here: art_registry.py points `wind-rose` at
# paint_families, the promoted copy, so its bytes stay identical.
"""Studio *cartography* — three seeded disc-art families drawn as course charts.

Every family is a module-level function with the paint_components contract:

    fam(seed: int, base: str, accent: str, target: int, label: str) -> str

returning a FULL SVG document: 512-unit viewBox, ``width == height == target``,
art clipped to the r=220 disc, a rim, deterministic from ``seed`` alone, no RNG
consumed per target (identity is drawn once, tiers only decide how many
components are *emitted*), label text only at 220, plus aria-label and <title>.

The angle is course cartography: a disc is a plate from a course map book.
  * contour-basin  — the terrain under the basket, as filled contour bands
  * fairway-plat   — one hole, plated from above: rough, corridor, tee, basket
  * wind-rose      — the bearing compass in the corner of the map sheet
"""
from __future__ import annotations

import html
import math
import random
import re

SIZE = 512
C = 256.0
R = 220
TARGETS = (42, 96, 220)
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

FAMILIES = ("contour-basin", "fairway-plat", "wind-rose")


# ---------------------------------------------------------------- primitives

def _check(base: str, accent: str, target: int) -> None:
    if target not in TARGETS:
        raise ValueError("target must be one of 42, 96, 220")
    if not HEX.fullmatch(base) or not HEX.fullmatch(accent):
        raise ValueError("base and accent must be six-digit hex colors")


def _rgb(value: str) -> tuple[int, int, int]:
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def mix(a: str, b: str, t: float) -> str:
    """Blend two hex colors; t=0 is all a, t=1 is all b. Deterministic."""
    ar, ag, ab = _rgb(a)
    br, bg, bb = _rgb(b)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return "#%02x%02x%02x" % (
        int(round(ar + (br - ar) * t)),
        int(round(ag + (bg - ag) * t)),
        int(round(ab + (bb - ab) * t)),
    )


def luma(value: str) -> float:
    r, g, b = _rgb(value)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def stroke_for(target: int, source: float, min_output: float = 1.0) -> float:
    """Keep a 512-unit stroke at least `min_output` device px wide at `target`."""
    scale = target / SIZE
    return max(source, round(min_output / scale, 1))


def n(value: float) -> str:
    text = f"{value:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return "-0" if text == "-0" else text


def xy(radius: float, angle: float, cx: float = C, cy: float = C) -> tuple[float, float]:
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def poly(points: list[tuple[float, float]], close: bool = True) -> str:
    parts = ["M", n(points[0][0]), " ", n(points[0][1])]
    for x, y in points[1:]:
        parts += ["L", n(x), " ", n(y)]
    if close:
        parts.append("Z")
    return "".join(parts)


def _shell(slug: str, kind: str, target: int, label: str, base: str, accent: str,
           art: list[str], stamp: list[str], text: list[str]) -> str:
    """Shared document frame: base disc, art, rim, stamp, 220-only text."""
    safe = html.escape(label, quote=True)
    aria = html.escape(f"{label} — {kind} course chart disc", quote=True)
    ink = accent
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{target}" height="{target}" '
        f'viewBox="0 0 {SIZE} {SIZE}" role="img" aria-label="{aria}">',
        f'<defs><clipPath id="{slug}-disc"><circle cx="256" cy="256" r="{R}"/></clipPath>',
        f'<linearGradient id="{slug}-depth" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".18"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".28"/></linearGradient></defs>',
        f'<g id="base" clip-path="url(#{slug}-disc)">',
        f'<circle cx="256" cy="256" r="{R}" fill="{base}"/>', '</g>',
        f'<g id="art" clip-path="url(#{slug}-disc)">',
    ]
    out += art
    out += [
        f'<circle cx="256" cy="256" r="{R}" fill="url(#{slug}-depth)"/>',
        '</g>',
        '<g id="rim" fill="none">',
        f'<circle cx="256" cy="256" r="216" stroke="{ink}" stroke-width="{n(stroke_for(target, 7))}" opacity=".9"/>',
        f'<circle cx="256" cy="256" r="201" stroke="#fff" stroke-width="{n(stroke_for(target, 3))}" opacity=".28"/>',
        '</g>',
        '<g id="stamp">',
    ]
    out += stamp
    out.append('</g>')
    if target == 220 and text:
        out.append('<g id="text">')
        out += text
        out.append('</g>')
    out += [f'<title>{safe}</title>', '</svg>']
    return "\n".join(out) + "\n"


def _halo(x: float, y: float, body: str, size: float, fill: str, halo: str, target: int,
          anchor: str = "start", weight: int = 400, family: str = "sans-serif",
          spacing: float = 0.0) -> str:
    """Map lettering: a fill with a matched halo, so figures read over any band."""
    bits = [f'<text x="{n(x)}" y="{n(y)}" font-family="{family}" font-size="{n(size)}"']
    if weight != 400:
        bits.append(f' font-weight="{weight}"')
    if anchor != "start":
        bits.append(f' text-anchor="{anchor}"')
    if spacing:
        bits.append(f' letter-spacing="{n(spacing)}"')
    bits.append(f' fill="{fill}" stroke="{halo}" stroke-width="{n(stroke_for(target, size * 0.16, 1.4))}"'
                f' stroke-linejoin="round" paint-order="stroke">{body}</text>')
    return "".join(bits)


def _cartouche(label: str, base: str, accent: str, target: int) -> list[str]:
    """The sheet's name box: a legend cartouche so the label survives any palette."""
    display = html.escape(label.strip()[:12], quote=True)
    if not display:
        return []
    span = max(len(label.strip()[:12]), 1)
    width = min(268.0, span * 16.4 + 30.0)
    paper = mix(base, "#ffffff", 0.88)
    return [
        f'<rect x="{n(256 - width / 2)}" y="398" width="{n(width)}" height="34" rx="5" fill="{paper}" '
        f'stroke="{accent}" stroke-width="{n(stroke_for(target, 2.6))}" opacity=".96"/>',
        f'<text x="256" y="421" text-anchor="middle" font-family="sans-serif" font-size="20" '
        f'letter-spacing="2.4" fill="{mix(accent, "#000000", 0.45)}">{display}</text>',
    ]


# ------------------------------------------------------------ contour-basin

def contour_basin(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """Filled contour bands: the terrain bowl the basket sits in, plated."""
    _check(base, accent, target)
    rng = random.Random(seed)
    # --- identity, drawn once. Order is fixed so every target sees the same values.
    off_x = rng.uniform(-40.0, 40.0)
    off_y = rng.uniform(-34.0, 34.0)
    tilt = rng.uniform(0.0, math.tau)
    drift = rng.uniform(10.0, 26.0)
    k1 = rng.randrange(2, 5)
    k2 = rng.randrange(5, 9)
    a1 = rng.uniform(0.08, 0.17)
    a2 = rng.uniform(0.03, 0.09)
    p1 = rng.uniform(0.0, math.tau)
    p2 = rng.uniform(0.0, math.tau)
    squash = rng.uniform(0.74, 0.99)
    rot = rng.uniform(-32.0, 32.0)
    creek_a = rng.uniform(0.0, math.tau)
    elevation = rng.randrange(180, 940)

    bands = 3 if target == 42 else (5 if target == 96 else 8)
    samples = 32 if target == 42 else (52 if target == 96 else 76)
    low = mix(base, "#ffffff", 0.26)
    high = mix(base, accent, 0.95)

    def ring(radius: float, frac: float, wobble: float = 1.0) -> list[tuple[float, float]]:
        cx = C + off_x + drift * frac * math.cos(tilt)
        cy = C + off_y + drift * frac * math.sin(tilt)
        pts = []
        for i in range(samples):
            a = i * math.tau / samples
            warp = 1.0 + wobble * (a1 * math.sin(k1 * a + p1 + frac * 1.35)
                                   + a2 * math.sin(k2 * a + p2 - frac * 0.9))
            r = radius * warp
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a) * squash))
        return pts

    def band_radius(frac: float) -> float:
        return 268.0 - (268.0 - 46.0) * (frac ** 1.1)

    art: list[str] = [f'<g transform="rotate({n(rot)} 256 256)">']
    for i in range(bands):
        frac = i / (bands - 1)
        fill = mix(low, high, frac ** 0.85)
        art.append(f'<path d="{poly(ring(band_radius(frac), frac))}" fill="{fill}"/>')
    # Index contours: the heavier every-third line a topo sheet labels.
    if target != 42:
        for i in range(bands):
            if i % 3 != 1:
                continue
            frac = i / (bands - 1)
            art.append(f'<path d="{poly(ring(band_radius(frac), frac))}" fill="none" stroke="{accent}" '
                       f'stroke-width="{n(stroke_for(target, 4.4))}" opacity=".5"/>')
        hair = 4 if target == 96 else 9
        for i in range(hair):
            frac = (i + 0.5) / hair
            art.append(f'<path d="{poly(ring(band_radius(frac) + 8.0, frac, 1.06))}" fill="none" '
                       f'stroke="{accent}" stroke-width="{n(stroke_for(target, 2.0))}" opacity=".3"/>')
    art.append('</g>')
    # The drainage the basin sheds through, drawn in disc space so it always shows.
    if target == 220:
        pts = []
        for i in range(9):
            t = i / 8.0
            r = 24.0 + t * 196.0
            a = creek_a + 0.22 * math.sin(t * 2.6 + p1)
            pts.append(xy(r, a, C + off_x * 0.6, C + off_y * 0.6))
        art.append(f'<path d="{poly(pts, close=False)}" fill="none" stroke="{mix(base, "#ffffff", 0.66)}" '
                   f'stroke-width="{n(stroke_for(target, 5))}" opacity=".55" stroke-linecap="round"/>')

    hx = C + off_x + drift * math.cos(tilt)
    hy = C + off_y + drift * math.sin(tilt)
    hx, hy = xy(math.hypot(hx - C, hy - C), math.atan2(hy - C, hx - C) + math.radians(rot))
    ink = mix(base, "#ffffff", 0.92)
    stamp: list[str] = []
    if target == 42:
        stamp.append(f'<circle cx="{n(hx)}" cy="{n(hy)}" r="20" fill="{ink}"/>')
        stamp.append(f'<circle cx="{n(hx)}" cy="{n(hy)}" r="8" fill="{high}"/>')
    else:
        size = 16.0 if target == 96 else 19.0
        stamp.append(f'<path d="{poly([(hx, hy - size), (hx + size * 0.95, hy + size * 0.74), (hx - size * 0.95, hy + size * 0.74)])}" '
                     f'fill="{ink}" stroke="{high}" stroke-width="{n(stroke_for(target, 3))}"/>')
        stamp.append(f'<circle cx="{n(hx)}" cy="{n(hy + size * 0.3)}" r="{n(size * 0.2)}" fill="{high}"/>')

    text = [_halo(hx + 28, hy + 9, str(elevation), 21, ink, high, target, weight=700)]
    text += _cartouche(label, base, accent, target)
    return _shell("cb", "contour basin", target, label, base, accent, art, stamp, text)


# ------------------------------------------------------------- fairway-plat

def fairway_plat(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """One hole plated from above: rough, mown corridor, tee pad, basket."""
    _check(base, accent, target)
    rng = random.Random(seed)
    # --- identity, drawn once.
    rot = rng.uniform(-56.0, 56.0)
    dogleg = 1.0 if rng.random() < 0.5 else -1.0
    bend = rng.uniform(60.0, 150.0)
    w_tee = rng.uniform(76.0, 104.0)
    w_green = rng.uniform(30.0, 46.0)
    green_r = rng.uniform(44.0, 62.0)
    hole_no = rng.randrange(1, 19)
    par = rng.choice((3, 3, 3, 4))
    creek = rng.random() < 0.55
    tree_phase = rng.uniform(0.0, math.tau)
    tee_len = rng.uniform(44.0, 62.0)
    creek_at = rng.uniform(0.38, 0.66)

    tee = (146.0, 366.0)
    basket = (366.0, 146.0)
    mid = ((tee[0] + basket[0]) / 2.0, (tee[1] + basket[1]) / 2.0)
    dx, dy = basket[0] - tee[0], basket[1] - tee[1]
    length = math.hypot(dx, dy)
    ctrl = (mid[0] + dogleg * bend * (-dy / length), mid[1] + dogleg * bend * (dx / length))

    def bez(t: float) -> tuple[float, float]:
        u = 1.0 - t
        return (u * u * tee[0] + 2 * u * t * ctrl[0] + t * t * basket[0],
                u * u * tee[1] + 2 * u * t * ctrl[1] + t * t * basket[1])

    def tangent(t: float) -> tuple[float, float]:
        u = 1.0 - t
        gx = 2 * u * (ctrl[0] - tee[0]) + 2 * t * (basket[0] - ctrl[0])
        gy = 2 * u * (ctrl[1] - tee[1]) + 2 * t * (basket[1] - ctrl[1])
        m = math.hypot(gx, gy) or 1.0
        return gx / m, gy / m

    def half_width(t: float) -> float:
        return (w_tee + (w_green - w_tee) * t) / 2.0 * (1.0 + 0.16 * math.sin(math.pi * t))

    def offset(t: float, k: float) -> tuple[float, float]:
        px, py = bez(t)
        gx, gy = tangent(t)
        return px - gy * k, py + gx * k

    steps = 18 if target == 42 else 34
    left = [offset(i / steps, half_width(i / steps)) for i in range(steps + 1)]
    right = [offset(i / steps, -half_width(i / steps)) for i in range(steps + 1)]
    corridor = poly(left + list(reversed(right)))

    # Tone, not hue, carries the map: the mown corridor is lifted off `base` and
    # the rough is pushed down from it, so the corridor reads lighter in every
    # palette (including a dark base with a bright accent).
    rough = mix(mix(base, accent, 0.30), "#000000", 0.30)
    mown = mix(base, "#ffffff", 0.34)
    green = mix(base, "#ffffff", 0.66)
    edge = mix(mown, "#ffffff", 0.45)
    canopy = mix(rough, "#000000", 0.44)
    water = mix(rough, accent, 0.55)

    art: list[str] = [f'<g transform="rotate({n(rot)} 256 256)">',
                      f'<rect x="-40" y="-40" width="592" height="592" fill="{rough}"/>']
    # Tree line, planted along both shoulders of the corridor.
    if target != 42:
        spine = [(bez(i / 16.0), half_width(i / 16.0)) for i in range(17)]

        def clearance(px: float, py: float) -> float:
            """How far a candidate tree sits outside the mown corridor."""
            worst = 1e9
            for (sx, sy), half in spine:
                worst = min(worst, math.hypot(px - sx, py - sy) - half)
            return worst

        # Shoulder line: trees crowding both edges of the corridor.
        count = 15 if target == 96 else 22
        for side in (-1.0, 1.0):
            for i in range(count):
                t = (i + 0.25) / count
                phase = i * 2.3 + tree_phase + (0.0 if side > 0 else 0.9)
                k = side * (half_width(t) + 24.0 + 16.0 * math.sin(phase))
                tx, ty = offset(t, k)
                if math.hypot(tx - C, ty - C) > 236.0:
                    continue
                art.append(f'<circle cx="{n(tx)}" cy="{n(ty)}" r="{n(8.0 + 6.0 * abs(math.sin(phase * 1.3)))}" '
                           f'fill="{canopy}" opacity=".8"/>')
        # Woodland beyond the shoulders, on a jittered lattice, corridor kept clear.
        if target == 220:
            for gy in range(9):
                for gx in range(9):
                    phase = gx * 1.7 + gy * 2.9 + tree_phase
                    tx = 40.0 + gx * 54.0 + 16.0 * math.sin(phase)
                    ty = 40.0 + gy * 54.0 + 16.0 * math.cos(phase * 1.4)
                    if math.hypot(tx - C, ty - C) > 232.0 or clearance(tx, ty) < 34.0:
                        continue
                    art.append(f'<circle cx="{n(tx)}" cy="{n(ty)}" r="{n(7.0 + 5.0 * abs(math.sin(phase)))}" '
                               f'fill="{canopy}" opacity=".55"/>')
    art.append(f'<ellipse cx="{n(basket[0])}" cy="{n(basket[1])}" rx="{n(green_r)}" '
               f'ry="{n(green_r * 0.88)}" fill="{green}" opacity=".95" stroke="{edge}" stroke-width="{n(stroke_for(target, 3))}"/>')
    art.append(f'<path d="{corridor}" fill="{mown}"/>')
    if target == 220:
        # Mowing stripes: the aerial giveaway that this corridor is maintained.
        for k in (-0.55, -0.18, 0.18, 0.55):
            band = [offset(i / 14.0, half_width(i / 14.0) * k) for i in range(15)]
            art.append(f'<path d="{poly(band, close=False)}" fill="none" stroke="#ffffff" '
                       f'stroke-width="{n(stroke_for(target, 9))}" opacity=".08"/>')
    if target != 42:
        art.append(f'<path d="{corridor}" fill="none" stroke="{edge}" '
                   f'stroke-width="{n(stroke_for(target, 3.4))}" opacity=".7"/>')
    if target == 220 and creek:
        px, py = bez(creek_at)
        gx, gy = tangent(creek_at)
        pts = []
        for i in range(15):
            s = -300.0 + i * (600.0 / 14.0)
            wob = 16.0 * math.sin(i * 0.85 + tree_phase)
            pts.append((px - gy * s + gx * wob, py + gx * s + gy * wob))
        art.append(f'<path d="{poly(pts, close=False)}" fill="none" stroke="{water}" '
                   f'stroke-width="{n(stroke_for(target, 22))}" opacity=".9"/>')
        art.append(f'<path d="{poly(pts, close=False)}" fill="none" stroke="{edge}" '
                   f'stroke-width="{n(stroke_for(target, 2.4))}" opacity=".55"/>')
    if target != 42:
        centre = [bez(i / 14.0) for i in range(15)]
        art.append(f'<path d="{poly(centre, close=False)}" fill="none" stroke="{accent}" '
                   f'stroke-width="{n(stroke_for(target, 4.6))}" opacity=".85" '
                   'stroke-dasharray="18 13" stroke-linecap="round"/>')
    gx, gy = tangent(0.0)
    ang = math.degrees(math.atan2(gy, gx))
    art.append(f'<g transform="translate({n(tee[0])} {n(tee[1])}) rotate({n(ang)})">'
               f'<rect x="{n(-tee_len * 0.5)}" y="-31" width="{n(tee_len)}" height="62" rx="7" fill="{accent}"/>'
               f'<rect x="{n(-tee_len * 0.5)}" y="-31" width="{n(tee_len)}" height="62" rx="7" fill="none" '
               f'stroke="{edge}" stroke-width="{n(stroke_for(target, 3))}" opacity=".8"/></g>')
    art.append('</g>')

    bx, by = xy(math.hypot(basket[0] - C, basket[1] - C),
                math.atan2(basket[1] - C, basket[0] - C) + math.radians(rot))
    stamp: list[str] = []
    if target == 42:
        stamp.append(f'<circle cx="{n(bx)}" cy="{n(by)}" r="32" fill="{accent}"/>')
        stamp.append(f'<circle cx="{n(bx)}" cy="{n(by)}" r="14" fill="{mix(base, "#ffffff", 0.72)}"/>')
    else:
        stamp.append(f'<circle cx="{n(bx)}" cy="{n(by)}" r="{27 if target == 96 else 31}" fill="none" '
                     f'stroke="{accent}" stroke-width="{n(stroke_for(target, 10))}"/>')
        stamp.append(f'<circle cx="{n(bx)}" cy="{n(by)}" r="{10 if target == 96 else 12}" fill="{accent}"/>')
        if target == 220:
            stamp.append(f'<path d="M{n(bx)} {n(by - 31)} v-24" stroke="{accent}" '
                         f'stroke-width="{n(stroke_for(target, 7))}" stroke-linecap="round"/>')

    ink = mix(base, "#ffffff", 0.94)
    text = [
        _halo(96, 154, str(hole_no), 62, ink, mix(base, accent, 0.8), target, weight=700, family="serif"),
        _halo(98, 180, f"PAR {par}", 18, ink, mix(base, accent, 0.8), target, spacing=2.2),
    ]
    text += _cartouche(label, base, accent, target)
    return _shell("fp", "fairway plat", target, label, base, accent, art, stamp, text)


# ----------------------------------------------------------------- wind-rose

def wind_rose(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """The bearing compass off the corner of the sheet: a rose of wind spikes."""
    _check(base, accent, target)
    rng = random.Random(seed)
    # --- identity, drawn once.
    prevail = rng.uniform(0.0, math.tau)
    tilt = rng.uniform(-0.20, 0.20)
    focus = rng.uniform(1.3, 3.0)
    hub = rng.uniform(24.0, 38.0)
    kite = rng.uniform(0.34, 0.56)
    petals = [rng.uniform(0.38, 1.0) for _ in range(16)]
    bearing = rng.randrange(0, 360)
    ring_gap = rng.uniform(4.0, 16.0)

    dark = luma(base) < 0.42
    field = mix(base, accent, 0.20 if not dark else 0.14)
    pale = mix(base, "#ffffff", 0.80 if not dark else 0.86)
    ink = accent
    ring_r = 182.0 - ring_gap
    arms = 8 if target == 42 else 16
    step = 16 // arms

    art: list[str] = [f'<circle cx="256" cy="256" r="{R}" fill="{field}"/>']
    if target == 220:
        for i in range(16):
            a = i * math.tau / 16 + tilt
            x0, y0 = xy(hub, a)
            x1, y1 = xy(ring_r, a)
            art.append(f'<path d="M{n(x0)} {n(y0)} L{n(x1)} {n(y1)}" stroke="{ink}" '
                       f'stroke-width="{n(stroke_for(target, 1.6))}" opacity=".22"/>')
    if target != 42:
        for radius in (ring_r, 112.0):
            art.append(f'<circle cx="256" cy="256" r="{n(radius)}" fill="none" stroke="{ink}" '
                       f'stroke-width="{n(stroke_for(target, 2.6))}" opacity=".45"/>')
    if target == 220:
        for i in range(72):
            a = i * math.tau / 72 + tilt
            major = i % 6 == 0
            x0, y0 = xy(ring_r, a)
            x1, y1 = xy(ring_r + (18.0 if major else 9.0), a)
            art.append(f'<path d="M{n(x0)} {n(y0)} L{n(x1)} {n(y1)}" stroke="{ink}" '
                       f'stroke-width="{n(stroke_for(target, 5.5 if major else 2.4))}" '
                       f'opacity="{".8" if major else ".45"}"/>')
    elif target == 96:
        for i in range(16):
            a = i * math.tau / 16 + tilt
            x0, y0 = xy(ring_r, a)
            x1, y1 = xy(ring_r + 15.0, a)
            art.append(f'<path d="M{n(x0)} {n(y0)} L{n(x1)} {n(y1)}" stroke="{ink}" '
                       f'stroke-width="{n(stroke_for(target, 5))}" opacity=".6"/>')

    reach = []
    for i in range(16):
        a = i * math.tau / 16 + tilt
        bias = (math.cos(a - prevail) + 1.0) / 2.0
        reach.append(62.0 + 112.0 * petals[i] * (0.42 + 0.58 * bias ** focus))
    # Kite half-width is set in viewBox units, not in radians, so a 42px rose
    # still carries mass instead of collapsing into hairlines.
    kw = (30.0 if target == 42 else 17.0) * (0.7 + kite)
    for j in range(arms):
        i = j * step
        a = i * math.tau / 16 + tilt
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        tip = (C + ux * reach[i], C + uy * reach[i])
        lft = (C + ux * hub + px * kw, C + uy * hub + py * kw)
        rgt = (C + ux * hub - px * kw, C + uy * hub - py * kw)
        if i % 2 == 0:
            art.append(f'<path d="{poly([tip, lft, (C, C), rgt])}" fill="{ink}" opacity=".95"/>')
        else:
            art.append(f'<path d="{poly([tip, lft, (C, C), rgt])}" fill="{pale}" opacity=".92" '
                       f'stroke="{ink}" stroke-width="{n(stroke_for(target, 2.4))}"/>')
    # The prevailing needle: one long folded blade out to the bearing ring, the
    # north point of the rose. Two tones so the fold reads at any size.
    ux, uy = math.cos(prevail), math.sin(prevail)
    px, py = -uy, ux
    nw = 30.0 if target == 42 else 21.0
    tip = (C + ux * (ring_r - 8.0), C + uy * (ring_r - 8.0))
    mid = hub * 1.15
    lft = (C + ux * mid + px * nw, C + uy * mid + py * nw)
    rgt = (C + ux * mid - px * nw, C + uy * mid - py * nw)
    tail = (C - ux * hub * 0.9, C - uy * hub * 0.9)
    art.append(f'<path d="{poly([tip, lft, tail, rgt])}" fill="{pale}" '
               f'stroke="{ink}" stroke-width="{n(stroke_for(target, 3))}"/>')
    art.append(f'<path d="{poly([tip, lft, tail])}" fill="{ink}"/>')

    stamp: list[str] = []
    hub_r = 24.0 if target == 42 else (19.0 if target == 96 else 21.0)
    stamp.append(f'<circle cx="256" cy="256" r="{n(hub_r)}" fill="{pale}" stroke="{ink}" '
                 f'stroke-width="{n(stroke_for(target, 7))}"/>')
    if target != 42:
        stamp.append(f'<circle cx="256" cy="256" r="{n(hub_r * 0.36)}" fill="{ink}"/>')

    nx = C + ux * (ring_r - 40.0) + px * 30.0
    ny = C + uy * (ring_r - 40.0) + py * 30.0
    text = [
        _halo(nx, ny + 10, "N", 30, mix(base, "#ffffff", 0.94), ink, target,
              anchor="middle", weight=700, family="serif"),
        _halo(256, 106, f"{bearing:03d}°", 19, mix(base, "#ffffff", 0.9), ink, target,
              anchor="middle", spacing=2.0),
    ]
    text += _cartouche(label, base, accent, target)
    return _shell("wr", "wind rose", target, label, base, accent, art, stamp, text)


# ------------------------------------------------------------------ registry

FAMILY_PARAMS: dict[str, dict[str, str]] = {
    "contour-basin": {
        "name": "Contour Basin",
        "seed": ("Places the summit off-centre, sets the drift of the slope, the two harmonic "
                 "frequencies and amplitudes that wobble every contour, the squash of the bowl, "
                 "the plate rotation, the saddle bearing, and the spot-elevation figure."),
        "base": "Fills the disc and is the low-ground band; every band is a base->accent blend.",
        "accent": "The high ground, the hairline contours, the rim, the spot-elevation triangle and the label.",
        "label": "Drawn once at 220 under the bands; the aria-label and <title> at every target.",
        "target": "42 = 3 filled bands + a summit dot; 96 = 5 bands + 4 hairlines + benchmark triangle; "
                  "220 = 8 bands, 9 hairlines, the dashed saddle line, elevation figure and label.",
    },
    "fairway-plat": {
        "name": "Fairway Plat",
        "seed": ("Rotates the hole on the plate, picks the dogleg side and how hard it bends, the tee and "
                 "green corridor widths, the green radius, the tee-pad length, whether a water hazard is "
                 "plotted, the tree-line phase, and the hole number and par."),
        "base": "The mown corridor and green; the rough is a base->accent blend so contrast survives any palette.",
        "accent": "Rough tint, tee pad, dashed flight line, basket, water hatch, rim and label.",
        "label": "Drawn once at 220 beneath the hole number; the aria-label and <title> at every target.",
        "target": "42 = rough, corridor, tee pad, solid basket; 96 = + corridor edging, dashed flight line, "
                  "16 trees; 220 = + 34 trees, water hazard with hatch, basket pole, hole number and par.",
    },
    "wind-rose": {
        "name": "Wind Rose",
        "seed": ("Sets the prevailing bearing, the rose tilt, how tightly the reach focuses on that bearing, "
                 "the hub radius, the kite width, all sixteen spike reaches, the bearing-ring gap and the "
                 "printed bearing in degrees."),
        "base": "The chart field under the rose (a light base->accent wash) and the pale alternating kites.",
        "accent": "The dark alternating kites, the prevailing needle and arrowhead, the bearing rings and ticks.",
        "label": "Drawn once at 220 below the rose; the aria-label and <title> at every target.",
        "target": "42 = 8 kites + needle + hub; 96 = 16 kites, two bearing rings, 16 ticks; "
                  "220 = + 72 degree ticks with majors, the N glyph, the bearing figure and label.",
    },
}

CALCULATIONS = {
    "fn.discArt.contour-basin": contour_basin,
    "fn.discArt.fairway-plat": fairway_plat,
    "fn.discArt.wind-rose": wind_rose,
}

RENDERERS = {
    "contour-basin": contour_basin,
    "fairway-plat": fairway_plat,
    "wind-rose": wind_rose,
}


def render(family: str, seed: int, base: str, accent: str, target: int, label: str) -> str:
    """paint_components-shaped entry point, keyed by family slug."""
    if family not in RENDERERS:
        raise ValueError("family is unsupported")
    return RENDERERS[family](seed, base, accent, target, label)
