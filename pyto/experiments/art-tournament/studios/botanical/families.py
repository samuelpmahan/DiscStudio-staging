#!/usr/bin/env python3
"""Studio *botanical* — three seeded disc-art families printed on warm paper.

Every family is a module-level function with the paint_components contract:

    fam(seed: int, base: str, accent: str, target: int, label: str) -> str

returning a FULL SVG document: 512-unit viewBox, ``width == height == target``,
art clipped to the r=220 disc, a rim, deterministic from ``seed`` alone, no RNG
consumed per target (identity is drawn once at the top of the function; the tier
only decides how many components are *emitted*), label text only at 220, plus an
aria-label and a <title>.

The angle is the botanical plate: pressed specimens and block-printed paper.
  * pressed-fern      — a frond pressed on a herbarium sheet, ghost and all
  * nodding-seedhead  — a seed head on its stalk, achenes packed in phyllotaxis
  * block-print       — a block-printed endpaper repeat, ink slightly off-register

Shared studio signature: a warm paper ground with a speckle of fibre grain, a
muted second tint for the ghost impression, and (at 220 only) a small mount
label plaque carrying the disc label and a seeded specimen figure.
"""
from __future__ import annotations

import html
import math
import random
import re

SIZE = 512
C = 256.0
R = 220
TAU = math.tau
GOLDEN = 2.399963229728653
TARGETS = (42, 96, 220)
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

FAMILIES = ("pressed-fern", "nodding-seedhead", "block-print")


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
    """Short, stable number formatting (1 decimal, no trailing zero)."""
    text = f"{value:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return "0" if text in ("-0", "") else text


def tones(base: str, accent: str) -> dict[str, str]:
    """The studio palette: warm paper, one ink, and the tints between them.

    Derived from base/accent only, so a dark base with a bright accent still
    reads: on dark ground the paper warms toward the accent instead of white.
    """
    if luma(base) < 0.42:
        paper = mix(base, accent, 0.13)
        deckle = mix(base, accent, 0.24)
    else:
        paper = mix(base, "#fdf6e6", 0.44)
        deckle = mix(base, accent, 0.16)
    return {
        "paper": paper,
        "deckle": deckle,
        "ink": accent,
        "ghost": mix(accent, paper, 0.64),
        "mid": mix(accent, paper, 0.36),
        "hair": mix(accent, paper, 0.52),
        "grain": mix(accent, paper, 0.44),
    }


# ------------------------------------------------------------------ geometry

def qpoint(p0, p1, p2, t: float) -> tuple[float, float]:
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def qangle(p0, p1, p2, t: float) -> float:
    u = 1.0 - t
    dx = 2 * u * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
    dy = 2 * u * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
    return math.degrees(math.atan2(dy, dx))


def control(p0, p2, bow: float) -> tuple[float, float]:
    """Control point that bows the p0->p2 chord sideways by `bow` of its length."""
    mx, my = (p0[0] + p2[0]) / 2.0, (p0[1] + p2[1]) / 2.0
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    return mx - dy * bow, my + dx * bow


def blade(x: float, y: float, angle: float, length: float, width: float, bend: float = 0.0) -> str:
    """A tapered leaf blade rooted at (x, y), pointing along `angle` degrees."""
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    tipx, tipy = x + dx * length, y + dy * length
    m = 0.44
    lift = bend * length * 0.20
    b1x = x + dx * length * m + px * (width + lift)
    b1y = y + dy * length * m + py * (width + lift)
    b2x = x + dx * length * m - px * (width - lift)
    b2y = y + dy * length * m - py * (width - lift)
    return (f"M{n(x)} {n(y)}Q{n(b1x)} {n(b1y)} {n(tipx)} {n(tipy)}"
            f"Q{n(b2x)} {n(b2y)} {n(x)} {n(y)}Z")


def taper(points: list[tuple[float, float]], widths: list[float]) -> str:
    """Closed polygon around a centreline, half-width per point (a tapered stem)."""
    left: list[str] = []
    right: list[str] = []
    count = len(points)
    for i, (x, y) in enumerate(points):
        j = min(i + 1, count - 1)
        k = max(i - 1, 0)
        dx, dy = points[j][0] - points[k][0], points[j][1] - points[k][1]
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length
        w = widths[i]
        left.append(f"{n(x + px * w)} {n(y + py * w)}")
        right.append(f"{n(x - px * w)} {n(y - py * w)}")
    return "M" + "L".join(left) + "L" + "L".join(reversed(right)) + "Z"


# ------------------------------------------------------------- shared chrome

def grain(target: int, phase: float, color: str) -> list[str]:
    """Paper fibre speckle. Deterministic from one seeded phase; none at 42."""
    count = 0 if target == 42 else (26 if target == 96 else 54)
    out: list[str] = []
    for i in range(count):
        a = i * GOLDEN + phase
        rad = 212.0 * math.sqrt(((i * 0.6180339887 + phase * 0.159) % 1.0))
        x, y = C + rad * math.cos(a), C + rad * math.sin(a)
        size = 1.4 + 1.9 * ((i * 7 + 3) % 5) / 4.0
        opacity = 0.10 + 0.05 * ((i * 3) % 4) / 3.0
        if i % 3 == 0 and target == 220:
            out.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(size * 3.4)}" height="{n(size * .7)}"'
                       f' transform="rotate({n(a * 27 % 180)} {n(x)} {n(y)})" opacity="{opacity:.2f}"/>')
        else:
            out.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(size)}" opacity="{opacity:.2f}"/>')
    return [f'<g id="grain" fill="{color}">'] + out + ['</g>'] if out else []


def plaque(t: dict[str, str], label: str, figure: str, tilt: float) -> list[str]:
    """The mount label: a small paper plaque with the disc label and a figure."""
    safe = html.escape(label.strip()[:13], quote=True)
    out = [f'<g id="plaque" transform="rotate({n(tilt)} 256 418)">',
           f'<rect x="150" y="386" width="212" height="64" rx="3" fill="{t["paper"]}"'
           f' stroke="{t["hair"]}" stroke-width="1.6" opacity=".95"/>',
           f'<rect x="155" y="391" width="202" height="54" rx="2" fill="none"'
           f' stroke="{t["hair"]}" stroke-width=".8" opacity=".6"/>',
           f'<text x="256" y="420" text-anchor="middle" font-family="serif" font-size="23"'
           f' letter-spacing="1.5" fill="{t["ink"]}">{safe}</text>',
           f'<text x="256" y="439" text-anchor="middle" font-family="sans-serif" font-size="11"'
           f' letter-spacing="3" fill="{t["mid"]}">{html.escape(figure, quote=True)}</text>',
           '</g>']
    return out


def document(target: int, label: str, base: str, t: dict[str, str], art: list[str],
             text: list[str], grain_phase: float, defs: str = "") -> str:
    safe = html.escape(label, quote=True)
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{target}" height="{target}"'
        f' viewBox="0 0 {SIZE} {SIZE}" role="img" aria-label="{safe}">',
        '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
        '<radialGradient id="depth" cx=".38" cy=".32" r=".78">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".16"/>'
        '<stop offset=".72" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".20"/></radialGradient>'
        + defs + '</defs>',
        '<g id="base" clip-path="url(#disc)">',
        f'<circle cx="256" cy="256" r="220" fill="{base}"/>',
        f'<circle cx="256" cy="256" r="220" fill="{t["paper"]}" opacity=".93"/>',
    ]
    out += grain(target, grain_phase, t["grain"])
    out += ['<circle cx="256" cy="256" r="220" fill="url(#depth)"/>', '</g>',
            '<g id="art" clip-path="url(#disc)">']
    out += art
    out += ['</g>', '<g id="rim" fill="none">',
            f'<circle cx="256" cy="256" r="216" stroke="{t["ink"]}"'
            f' stroke-width="{n(stroke_for(target, 7))}" opacity=".9"/>',
            f'<circle cx="256" cy="256" r="205" stroke="{t["deckle"]}"'
            f' stroke-width="{n(stroke_for(target, 3))}" opacity=".55"/>', '</g>']
    if text:
        out += ['<g id="text">'] + text + ['</g>']
    out += [f'<title>{safe}</title>', '</svg>']
    return "\n".join(out) + "\n"


# ----------------------------------------------------------- 1. pressed-fern

def pressed_fern(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """A frond pressed flat on a herbarium sheet, its ghost impression behind."""
    _check(base, accent, target)
    rng = random.Random(seed)
    rot = rng.uniform(-30, 30)
    bow = rng.uniform(0.14, 0.34) * (1.0 if rng.random() < 0.5 else -1.0)
    back = rng.uniform(30, 48)
    width_k = rng.uniform(0.15, 0.20)
    reach = rng.uniform(0.92, 1.10)
    ghost_rot = rng.uniform(9, 21) * (-1.0 if bow > 0 else 1.0)
    ghost_slip = rng.uniform(26, 46)
    pitch_k = rng.uniform(0.88, 1.14)
    jit = [rng.uniform(-1.0, 1.0) for _ in range(48)]
    number = rng.randrange(104, 989)
    tilt = rng.uniform(-2.2, 2.2)
    grain_phase = rng.uniform(0, TAU)
    t = tones(base, accent)

    p0 = (104.0, 416.0)
    p2 = (416.0, 108.0)
    p1 = control(p0, p2, bow)

    def frond(color: str, pairs: int, opacity: float, detail: bool, veins: bool,
              outline: str = "") -> list[str]:
        bulk = 1.35 if target == 42 else 1.0
        cut = (f' stroke="{outline}" stroke-width="2.6" stroke-opacity=".6" stroke-linejoin="round"'
               if outline else "")
        out: list[str] = [f'<g fill="{color}"{cut}>']
        vein: list[str] = []
        pts = [qpoint(p0, p1, p2, i / 20.0) for i in range(21)]
        widths = [11.5 * bulk * (1.0 - 0.70 * (i / 20.0)) + 1.8 for i in range(21)]
        out.append(f'<path d="{taper(pts, widths)}"/>')
        for i in range(pairs):
            u = 0.07 + (i + 0.5) / pairs * 0.90
            x, y = qpoint(p0, p1, p2, u)
            ang = qangle(p0, p1, p2, u)
            # a frond swells just above the stipe and tapers to the crozier
            prof = (1.16 - 0.86 * u) * min(1.0, 0.34 + 2.6 * u)
            length = 150.0 * reach * pitch_k * max(prof, 0.16)
            # at 42 the frond carries fewer, fatter pinnae so the mark keeps its mass
            w = length * width_k * (1.55 if target == 42 else 1.0)
            for side in (1.0, -1.0):
                j = jit[(i * 2 + (0 if side > 0 else 1)) % 48]
                a = ang + side * (back + j * 7.0)
                out.append(f'<path d="{blade(x, y, a, length * (1.0 + j * 0.07), w, side * 0.34)}"/>')
                if veins:
                    ar = math.radians(a)
                    vein.append(f'M{n(x)} {n(y)}L{n(x + math.cos(ar) * length * .88)}'
                                f' {n(y + math.sin(ar) * length * .88)}')
        if detail:
            # the crozier: the frond tip still curled from the press
            tipx, tipy = qpoint(p0, p1, p2, 1.0)
            ang = math.radians(qangle(p0, p1, p2, 1.0))
            cx = tipx + math.cos(ang) * 16 - math.sin(ang) * 15
            cy = tipy + math.sin(ang) * 16 + math.cos(ang) * 15
            out.append(f'<path d="M{n(tipx)} {n(tipy)}Q{n(tipx + math.cos(ang) * 30)}'
                       f' {n(tipy + math.sin(ang) * 30)} {n(cx)} {n(cy)}" fill="none"'
                       f' stroke="{color}" stroke-width="7" stroke-linecap="round"/>')
        out.append('</g>')
        if vein:
            out.append(f'<path d="{"".join(vein)}" stroke="{t["paper"]}" stroke-width="1.7"'
                       f' opacity=".38" fill="none"/>')
        return out

    art: list[str] = []
    pairs = 5 if target == 42 else (10 if target == 96 else 14)
    if target != 42:
        art.append(f'<g id="ghost" transform="rotate({n(rot + ghost_rot)} 256 256)'
                   f' translate({n(ghost_slip)} {n(ghost_slip * .5)})" opacity=".42">')
        art += frond(t["ghost"], max(5, pairs - 4), 1.0, False, False)
        art.append('</g>')
    art.append(f'<g id="frond" transform="rotate({n(rot)} 256 256)">')
    art += frond(t["ink"], pairs, 1.0, target != 42, target == 220,
                 t["paper"] if target != 42 else "")
    art.append('</g>')
    if target == 220:
        # mounting tape, the way a pressed specimen is held to the sheet
        for k, (tx, ty, ta) in enumerate(((150.0, 168.0, 62.0), (330.0, 330.0, 62.0))):
            art.append(f'<g transform="rotate({n(ta + rot)} {n(tx)} {n(ty)})">'
                       f'<rect x="{n(tx - 52)}" y="{n(ty - 13)}" width="104" height="26" rx="2"'
                       f' fill="{t["paper"]}" opacity=".3"/>'
                       f'<rect x="{n(tx - 52)}" y="{n(ty - 13)}" width="104" height="26" rx="2" fill="none"'
                       f' stroke="{t["paper"]}" stroke-width="1.4" opacity=".5"/></g>')
    text = plaque(t, label, f"No. {number}", tilt) if target == 220 else []
    return document(target, label, base, t, art, text, grain_phase)


# ------------------------------------------------------- 2. nodding-seedhead

def nodding_seedhead(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """A seed head nodding on its stalk, achenes packed in a phyllotactic spiral."""
    _check(base, accent, target)
    rng = random.Random(seed)
    head_a = rng.uniform(-2.55, -0.62)
    head_d = rng.uniform(62, 98)
    head_r = rng.uniform(82, 100)
    bracts = rng.randrange(11, 18)
    bract_len = rng.uniform(26, 44)
    seed_phase = rng.uniform(0, TAU)
    stalk_bow = rng.uniform(-0.30, 0.30)
    leaf_side = 1.0 if rng.random() < 0.5 else -1.0
    leaf_len = rng.uniform(92, 124)
    leaf_at = rng.uniform(0.34, 0.52)
    drift = [(rng.uniform(0, TAU), rng.uniform(140, 205), rng.uniform(12, 18),
              rng.uniform(0, 180)) for _ in range(4)]
    jit = [rng.uniform(-1.0, 1.0) for _ in range(40)]
    count = rng.randrange(23, 97)
    tilt = rng.uniform(-2.2, 2.2)
    grain_phase = rng.uniform(0, TAU)
    t = tones(base, accent)

    hx, hy = C + head_d * math.cos(head_a), C + head_d * math.sin(head_a)
    foot = (C + stalk_bow * 150.0, 486.0)
    stem_c = control((hx, hy), foot, stalk_bow * 0.42 + 0.14)
    steps = 16
    pts = [qpoint((hx, hy), stem_c, foot, i / steps) for i in range(steps + 1)]
    widths = [7.0 + 6.5 * (i / steps) for i in range(steps + 1)]

    art: list[str] = []
    # stalk
    art.append(f'<path d="{taper(pts, widths)}" fill="{t["ink"]}"/>')
    # stalk leaves
    leaves = 1 if target == 42 else 2
    for i in range(leaves):
        u = leaf_at + i * 0.22
        lx, ly = qpoint((hx, hy), stem_c, foot, min(u, 0.92))
        ang = qangle((hx, hy), stem_c, foot, min(u, 0.92))
        side = leaf_side if i % 2 == 0 else -leaf_side
        art.append(f'<path d="{blade(lx, ly, ang + side * 78, leaf_len * (1 - i * 0.16), leaf_len * 0.26, side * 0.95)}"'
                   f' fill="{t["ink"]}" stroke="{t["paper"]}" stroke-width="2.4" stroke-opacity=".5"/>')
        if target == 220:
            ar = math.radians(ang + side * 78)
            art.append(f'<path d="M{n(lx)} {n(ly)}L{n(lx + math.cos(ar) * leaf_len * .8)}'
                       f' {n(ly + math.sin(ar) * leaf_len * .8)}" stroke="{t["paper"]}"'
                       f' stroke-width="2" opacity=".4" fill="none"/>')
    # bracts around the head
    shown = 8 if target == 42 else bracts
    for i in range(shown):
        a = i * TAU / shown + seed_phase * 0.3
        j = jit[i % 40]
        reach = head_r + bract_len * (1.0 + j * 0.28)
        art.append(f'<path d="M{n(hx + math.cos(a - 0.16) * head_r * .92)} {n(hy + math.sin(a - 0.16) * head_r * .92)}'
                   f'L{n(hx + math.cos(a) * reach)} {n(hy + math.sin(a) * reach)}'
                   f'L{n(hx + math.cos(a + 0.16) * head_r * .92)} {n(hy + math.sin(a + 0.16) * head_r * .92)}Z"'
                   f' fill="{t["mid"] if target == 220 and i % 2 else t["ink"]}"/>')
    # the head itself
    art.append(f'<circle cx="{n(hx)}" cy="{n(hy)}" r="{n(head_r)}" fill="{t["ink"]}"/>')
    if target == 220:
        arcs = []
        for k in range(11):
            leg = []
            for step in range(7):
                u = step / 6.0
                rad = head_r * 0.96 * u
                a = k * TAU / 11 + seed_phase + u * 1.35
                leg.append(f"{n(hx + rad * math.cos(a))} {n(hy + rad * math.sin(a))}")
            arcs.append("M" + "L".join(leg))
        art.append(f'<path d="{"".join(arcs)}" fill="none" stroke="{t["paper"]}"'
                   f' stroke-width="1.6" opacity=".22"/>')
    seeds = 9 if target == 42 else (48 if target == 96 else 118)
    art.append(f'<g id="achenes" fill="{t["paper"]}" opacity=".82">')
    for i in range(seeds):
        u = (i + 0.6) / seeds
        rad = head_r * 0.88 * math.sqrt(u)
        a = i * GOLDEN + seed_phase
        size = (5.6 if target == 42 else (3.5 if target == 96 else 2.9)) * (0.62 + 0.62 * math.sqrt(u))
        art.append(f'<circle cx="{n(hx + rad * math.cos(a))}" cy="{n(hy + rad * math.sin(a))}"'
                   f' r="{n(size)}"/>')
    art.append('</g>')
    # loosed seeds drifting off the head
    floats = 0 if target == 42 else (2 if target == 96 else 4)
    for i in range(floats):
        a, dist, size, spin = drift[i]
        fx, fy = hx + math.cos(a) * dist * 0.62, hy + math.sin(a) * dist * 0.52
        rays = []
        for k in range(7):
            ra = -math.pi / 2 + (k - 3) * 0.34
            rays.append(f'M{n(fx)} {n(fy - size)}L{n(fx + math.cos(ra) * size * 2.1)}'
                        f' {n(fy - size + math.sin(ra) * size * 2.1)}')
        art.append(f'<g transform="rotate({n(spin)} {n(fx)} {n(fy)})">'
                   f'<ellipse cx="{n(fx)}" cy="{n(fy)}" rx="{n(size * .42)}" ry="{n(size)}" fill="{t["ink"]}"/>'
                   f'<path d="{"".join(rays)}" stroke="{t["ink"]}" stroke-width="1.8" opacity=".72"'
                   f' fill="none"/></g>')
    text = plaque(t, label, f"ACHENES {count}", tilt) if target == 220 else []
    return document(target, label, base, t, art, text, grain_phase)


# ------------------------------------------------------------ 3. block-print

def _sprig(scale: float, t: dict[str, str], color: str, detail: bool) -> list[str]:
    """A three-blade sprig, drawn around the origin at `scale` units."""
    out = [f'<path d="M0 {n(scale * .62)}Q{n(scale * .1)} 0 0 {n(-scale * .66)}" fill="none"'
           f' stroke-width="{n(scale * .085)}" stroke-linecap="round"/>']
    for i, (y, side, ln) in enumerate(((0.30, 1.0, 0.62), (0.02, -1.0, 0.72), (-0.30, 1.0, 0.54))):
        out.append(f'<path d="{blade(0, scale * y, -90 + side * 52, scale * ln, scale * ln * 0.30, side * 0.4)}"'
                   f' stroke="none"/>')
    if detail:
        out.append(f'<circle cx="0" cy="{n(-scale * .66)}" r="{n(scale * .09)}" stroke="none"/>')
    return out


def _pod(scale: float, t: dict[str, str], color: str, detail: bool) -> list[str]:
    """A split seed pod: a pointed hull with seeds inside."""
    w = scale * 0.34
    out = [f'<path d="M0 {n(-scale * .7)}Q{n(w)} 0 0 {n(scale * .7)}Q{n(-w)} 0 0 {n(-scale * .7)}Z"'
           f' stroke="none"/>']
    if detail:
        for k in (-1, 0, 1):
            out.append(f'<circle cx="0" cy="{n(k * scale * .28)}" r="{n(scale * .12)}"'
                       f' fill="{t["paper"]}" opacity=".8"/>')
    return out


def _berry(scale: float, t: dict[str, str], color: str, detail: bool) -> list[str]:
    """A berry cluster: three fruits on short pedicels."""
    out = []
    for k, (dx, dy) in enumerate(((0.0, -0.34), (-0.30, 0.20), (0.30, 0.22))):
        out.append(f'<path d="M0 0L{n(dx * scale)} {n(dy * scale)}"'
                   f' stroke-width="{n(scale * .07)}" fill="none"/>')
        out.append(f'<circle cx="{n(dx * scale)}" cy="{n(dy * scale)}" r="{n(scale * .25)}" stroke="none"/>')
        if detail:
            out.append(f'<circle cx="{n(dx * scale - scale * .08)}" cy="{n(dy * scale - scale * .09)}"'
                       f' r="{n(scale * .06)}" fill="{t["paper"]}" opacity=".55"/>')
    return out


_MOTIFS = (_sprig, _pod, _berry)
_PAIRS = ((0, 1), (0, 2), (1, 2))


def block_print(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """A block-printed endpaper: a botanical repeat, the second pull off-register."""
    _check(base, accent, target)
    rng = random.Random(seed)
    rot = rng.uniform(-16, 16)
    pitch_k = rng.uniform(0.88, 1.12)
    half_drop = 0.5 if rng.random() < 0.62 else 0.0
    mis_a = rng.uniform(0, TAU)
    mis_d = rng.uniform(3.5, 8.5)
    pair = _PAIRS[rng.randrange(3)]
    swap = rng.random() < 0.5
    jitter = rng.uniform(4, 15)
    jit = [rng.uniform(-1.0, 1.0) for _ in range(64)]
    block_no = rng.randrange(2, 19)
    ticks = rng.randrange(28, 46)
    tilt = rng.uniform(-2.2, 2.2)
    grain_phase = rng.uniform(0, TAU)
    t = tones(base, accent)

    pitch = (150.0 if target == 42 else (124.0 if target == 96 else 108.0)) * pitch_k
    row = pitch * 0.88
    scale = pitch * 0.56
    detail = target == 220
    cols = int(560 / pitch) + 3
    rows = int(560 / row) + 3
    mx, my = math.cos(mis_a) * mis_d, math.sin(mis_a) * mis_d

    def field(color: str, dx: float, dy: float, want_detail: bool) -> list[str]:
        out: list[str] = [f'<g fill="{color}" stroke="{color}">']
        for j in range(rows):
            for i in range(cols):
                x = -pitch + i * pitch + (half_drop * pitch if j % 2 else 0.0) + dx
                y = -row + j * row + dy
                if math.hypot(x - C, y - C) > 244:
                    continue
                k = (i * 7 + j * 13) % 64
                which = pair[(i + j) % 2] if not swap else pair[(i + j + 1) % 2]
                spin = jit[k] * jitter + (0.0 if (i + j) % 2 else 180.0)
                out.append(f'<g transform="translate({n(x)} {n(y)}) rotate({n(spin)})">')
                out += _MOTIFS[which](scale, t, color, want_detail)
                out.append('</g>')
        out.append('</g>')
        return out

    art: list[str] = []
    art.append(f'<g id="repeat" transform="rotate({n(rot)} 256 256)">')
    if target != 42:
        art.append(f'<g id="offregister" opacity=".45">')
        art += field(t["ghost"], mx, my, False)
        art.append('</g>')
    art += field(t["ink"], 0.0, 0.0, detail)
    art.append('</g>')
    if target == 220:
        art.append(f'<circle cx="256" cy="256" r="196" fill="none" stroke="{t["mid"]}"'
                   f' stroke-width="2.4" opacity=".7"/>')
        art.append(f'<circle cx="256" cy="256" r="188" fill="none" stroke="{t["mid"]}"'
                   f' stroke-width="1.1" opacity=".5"/>')
        marks = []
        for i in range(ticks):
            a = i * TAU / ticks + rot * math.pi / 180
            marks.append(f'M{n(C + 196 * math.cos(a))} {n(C + 196 * math.sin(a))}'
                         f'L{n(C + 206 * math.cos(a))} {n(C + 206 * math.sin(a))}')
        art.append(f'<path d="{"".join(marks)}" stroke="{t["mid"]}" stroke-width="2" opacity=".55" fill="none"/>')
    text = plaque(t, label, f"BLOCK {block_no} / PULL II", tilt) if target == 220 else []
    return document(target, label, base, t, art, text, grain_phase)


# ------------------------------------------------------------------ registry

FAMILY_PARAMS = {
    "pressed-fern": {
        "name": "Pressed Fern",
        "seed": ("Rotates the frond on the sheet, bows the rachis and picks which way, sets the pinna "
                 "backsweep, the blade width ratio and reach, the pitch of the pairs, the ghost "
                 "impression's rotation and slip, a per-pinna length jitter, the plaque tilt, the paper "
                 "grain phase and the specimen number."),
        "base": "The sheet: the disc fill, warmed toward cream (or toward the accent on a dark base).",
        "accent": "The pressed plant itself — rachis, pinnae, crozier — plus the rim and the plaque type.",
        "label": "Set on the mount plaque at 220 beside the frond count and specimen number; aria-label and <title> at every target.",
        "target": ("42 = rachis + 7 pairs of solid pinnae; 96 = 11 pairs, the ghost impression, the curled "
                   "crozier tip, paper grain; 220 = 15 pairs with midribs, two mounting-tape strips, full "
                   "grain and the mount plaque."),
    },
    "nodding-seedhead": {
        "name": "Nodding Seed Head",
        "seed": ("Places the head off-centre (bearing and distance) and sizes it, sets the bract count and "
                 "reach, the phyllotactic phase, the stalk bow, which side the leaves take and how long "
                 "they are, the four drifting seeds' bearings, the plaque tilt, the grain phase and the "
                 "printed achene count."),
        "base": "The paper ground under the specimen.",
        "accent": "The head, bracts, stalk and leaves; achenes are knocked out of it in paper.",
        "label": "Set on the mount plaque at 220 above the achene count; aria-label and <title> at every target.",
        "target": ("42 = head with 9 chunky achenes, 8 bracts, stalk and one leaf; 96 = 48 achenes, all "
                   "bracts, two leaves, two drifting seeds; 220 = 134 achenes, 13 parastichy arcs, "
                   "alternating bract tints, leaf midribs, four drifting seeds and the plaque."),
    },
    "block-print": {
        "name": "Block Print",
        "seed": ("Rotates the block on the paper, sets the repeat pitch and whether it is a half-drop, "
                 "chooses which two of the three motifs (sprig, pod, berry) alternate and in which parity, "
                 "the per-cell rotation jitter, the off-register direction and distance, the border tick "
                 "count, the plaque tilt, the grain phase and the block number."),
        "base": "The endpaper stock; every motif is printed on it.",
        "accent": "The printing ink; the off-register second pull is the same ink let down toward the paper.",
        "label": "Set on the mount plaque at 220 above the block number; aria-label and <title> at every target.",
        "target": ("42 = a coarse repeat, one ink, solid motifs; 96 = a tighter repeat plus the off-register "
                   "pull and paper grain; 220 = the full repeat with motif detail (pod seeds, berry "
                   "highlights, sprig bud), a ticked border rule and the plaque."),
    },
}

CALCULATIONS = {
    "fn.discArt.pressed-fern": pressed_fern,
    "fn.discArt.nodding-seedhead": nodding_seedhead,
    "fn.discArt.block-print": block_print,
}

RENDERERS = {
    "pressed-fern": pressed_fern,
    "nodding-seedhead": nodding_seedhead,
    "block-print": block_print,
}


def render(family: str, seed: int, base: str, accent: str, target: int, label: str) -> str:
    """paint_components-shaped entry point, keyed by family slug."""
    if family not in RENDERERS:
        raise ValueError("family is unsupported")
    return RENDERERS[family](seed, base, accent, target, label)
