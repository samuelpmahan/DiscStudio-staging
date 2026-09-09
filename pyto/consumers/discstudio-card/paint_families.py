#!/usr/bin/env python3
"""Promoted disc-art families from the art tournament (see
``pyto/experiments/art-tournament/RESULTS.md``).

Three families won promotion out of the four studios:

  * ``pressed-fern``      studio *botanical*   (tally 68/72)
  * ``nodding-seedhead``  studio *botanical*   (tally 68/72)
  * ``wind-rose``         studio *cartography* (tally 65/72)

Each family is a module-level function with the ``paint_components`` contract::

    fam(seed: int, base: str, accent: str, target: int, label: str) -> str

returning a FULL SVG document: a 512-unit viewBox with ``width == height ==
target``, art clipped to the r=220 disc, a rim, deterministic from ``seed``
alone, no RNG consumed per target (identity is drawn once at the top of the
function; the tier only decides how many components are *emitted*), label text
only at 220, plus an aria-label and a ``<title>``.

The two studios shipped their own numeric formatters, so both are kept verbatim
as ``_bn`` (botanical: collapses "-0" to "0") and ``_cn`` (cartography: keeps
"-0"). Everything else the two studios wrote identically is shared. The
promoted code is otherwise byte-for-byte the tournament source, so the renders
under ``experiments/art-tournament/renders/`` remain valid receipts.
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

FAMILIES = ("pressed-fern", "nodding-seedhead", "wind-rose")


# ------------------------------------------------- primitives (both studios)

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


def _bn(value: float) -> str:
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
    return (f"M{_bn(x)} {_bn(y)}Q{_bn(b1x)} {_bn(b1y)} {_bn(tipx)} {_bn(tipy)}"
            f"Q{_bn(b2x)} {_bn(b2y)} {_bn(x)} {_bn(y)}Z")


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
        left.append(f"{_bn(x + px * w)} {_bn(y + py * w)}")
        right.append(f"{_bn(x - px * w)} {_bn(y - py * w)}")
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
            out.append(f'<rect x="{_bn(x)}" y="{_bn(y)}" width="{_bn(size * 3.4)}" height="{_bn(size * .7)}"'
                       f' transform="rotate({_bn(a * 27 % 180)} {_bn(x)} {_bn(y)})" opacity="{opacity:.2f}"/>')
        else:
            out.append(f'<circle cx="{_bn(x)}" cy="{_bn(y)}" r="{_bn(size)}" opacity="{opacity:.2f}"/>')
    return [f'<g id="grain" fill="{color}">'] + out + ['</g>'] if out else []


def plaque(t: dict[str, str], label: str, figure: str, tilt: float) -> list[str]:
    """The mount label: a small paper plaque with the disc label and a figure."""
    safe = html.escape(label.strip()[:13], quote=True)
    out = [f'<g id="plaque" transform="rotate({_bn(tilt)} 256 418)">',
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
            f' stroke-width="{_bn(stroke_for(target, 7))}" opacity=".9"/>',
            f'<circle cx="256" cy="256" r="205" stroke="{t["deckle"]}"'
            f' stroke-width="{_bn(stroke_for(target, 3))}" opacity=".55"/>', '</g>']
    if text:
        out += ['<g id="text">'] + text + ['</g>']
    out += [f'<title>{safe}</title>', '</svg>']
    return "\n".join(out) + "\n"

# ------------------------------------- studio botanical: pressed paper plates

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
                    vein.append(f'M{_bn(x)} {_bn(y)}L{_bn(x + math.cos(ar) * length * .88)}'
                                f' {_bn(y + math.sin(ar) * length * .88)}')
        if detail:
            # the crozier: the frond tip still curled from the press
            tipx, tipy = qpoint(p0, p1, p2, 1.0)
            ang = math.radians(qangle(p0, p1, p2, 1.0))
            cx = tipx + math.cos(ang) * 16 - math.sin(ang) * 15
            cy = tipy + math.sin(ang) * 16 + math.cos(ang) * 15
            out.append(f'<path d="M{_bn(tipx)} {_bn(tipy)}Q{_bn(tipx + math.cos(ang) * 30)}'
                       f' {_bn(tipy + math.sin(ang) * 30)} {_bn(cx)} {_bn(cy)}" fill="none"'
                       f' stroke="{color}" stroke-width="7" stroke-linecap="round"/>')
        out.append('</g>')
        if vein:
            out.append(f'<path d="{"".join(vein)}" stroke="{t["paper"]}" stroke-width="1.7"'
                       f' opacity=".38" fill="none"/>')
        return out

    art: list[str] = []
    pairs = 5 if target == 42 else (10 if target == 96 else 14)
    if target != 42:
        art.append(f'<g id="ghost" transform="rotate({_bn(rot + ghost_rot)} 256 256)'
                   f' translate({_bn(ghost_slip)} {_bn(ghost_slip * .5)})" opacity=".42">')
        art += frond(t["ghost"], max(5, pairs - 4), 1.0, False, False)
        art.append('</g>')
    art.append(f'<g id="frond" transform="rotate({_bn(rot)} 256 256)">')
    art += frond(t["ink"], pairs, 1.0, target != 42, target == 220,
                 t["paper"] if target != 42 else "")
    art.append('</g>')
    if target == 220:
        # mounting tape, the way a pressed specimen is held to the sheet
        for k, (tx, ty, ta) in enumerate(((150.0, 168.0, 62.0), (330.0, 330.0, 62.0))):
            art.append(f'<g transform="rotate({_bn(ta + rot)} {_bn(tx)} {_bn(ty)})">'
                       f'<rect x="{_bn(tx - 52)}" y="{_bn(ty - 13)}" width="104" height="26" rx="2"'
                       f' fill="{t["paper"]}" opacity=".3"/>'
                       f'<rect x="{_bn(tx - 52)}" y="{_bn(ty - 13)}" width="104" height="26" rx="2" fill="none"'
                       f' stroke="{t["paper"]}" stroke-width="1.4" opacity=".5"/></g>')
    text = plaque(t, label, f"No. {number}", tilt) if target == 220 else []
    return document(target, label, base, t, art, text, grain_phase)


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
            art.append(f'<path d="M{_bn(lx)} {_bn(ly)}L{_bn(lx + math.cos(ar) * leaf_len * .8)}'
                       f' {_bn(ly + math.sin(ar) * leaf_len * .8)}" stroke="{t["paper"]}"'
                       f' stroke-width="2" opacity=".4" fill="none"/>')
    # bracts around the head
    shown = 8 if target == 42 else bracts
    for i in range(shown):
        a = i * TAU / shown + seed_phase * 0.3
        j = jit[i % 40]
        reach = head_r + bract_len * (1.0 + j * 0.28)
        art.append(f'<path d="M{_bn(hx + math.cos(a - 0.16) * head_r * .92)} {_bn(hy + math.sin(a - 0.16) * head_r * .92)}'
                   f'L{_bn(hx + math.cos(a) * reach)} {_bn(hy + math.sin(a) * reach)}'
                   f'L{_bn(hx + math.cos(a + 0.16) * head_r * .92)} {_bn(hy + math.sin(a + 0.16) * head_r * .92)}Z"'
                   f' fill="{t["mid"] if target == 220 and i % 2 else t["ink"]}"/>')
    # the head itself
    art.append(f'<circle cx="{_bn(hx)}" cy="{_bn(hy)}" r="{_bn(head_r)}" fill="{t["ink"]}"/>')
    if target == 220:
        arcs = []
        for k in range(11):
            leg = []
            for step in range(7):
                u = step / 6.0
                rad = head_r * 0.96 * u
                a = k * TAU / 11 + seed_phase + u * 1.35
                leg.append(f"{_bn(hx + rad * math.cos(a))} {_bn(hy + rad * math.sin(a))}")
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
        art.append(f'<circle cx="{_bn(hx + rad * math.cos(a))}" cy="{_bn(hy + rad * math.sin(a))}"'
                   f' r="{_bn(size)}"/>')
    art.append('</g>')
    # loosed seeds drifting off the head
    floats = 0 if target == 42 else (2 if target == 96 else 4)
    for i in range(floats):
        a, dist, size, spin = drift[i]
        fx, fy = hx + math.cos(a) * dist * 0.62, hy + math.sin(a) * dist * 0.52
        rays = []
        for k in range(7):
            ra = -math.pi / 2 + (k - 3) * 0.34
            rays.append(f'M{_bn(fx)} {_bn(fy - size)}L{_bn(fx + math.cos(ra) * size * 2.1)}'
                        f' {_bn(fy - size + math.sin(ra) * size * 2.1)}')
        art.append(f'<g transform="rotate({_bn(spin)} {_bn(fx)} {_bn(fy)})">'
                   f'<ellipse cx="{_bn(fx)}" cy="{_bn(fy)}" rx="{_bn(size * .42)}" ry="{_bn(size)}" fill="{t["ink"]}"/>'
                   f'<path d="{"".join(rays)}" stroke="{t["ink"]}" stroke-width="1.8" opacity=".72"'
                   f' fill="none"/></g>')
    text = plaque(t, label, f"ACHENES {count}", tilt) if target == 220 else []
    return document(target, label, base, t, art, text, grain_phase)

# ------------------------------------- studio cartography: survey sheet plate

def _cn(value: float) -> str:
    text = f"{value:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return "-0" if text == "-0" else text


def xy(radius: float, angle: float, cx: float = C, cy: float = C) -> tuple[float, float]:
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def poly(points: list[tuple[float, float]], close: bool = True) -> str:
    parts = ["M", _cn(points[0][0]), " ", _cn(points[0][1])]
    for x, y in points[1:]:
        parts += ["L", _cn(x), " ", _cn(y)]
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
        f'<circle cx="256" cy="256" r="216" stroke="{ink}" stroke-width="{_cn(stroke_for(target, 7))}" opacity=".9"/>',
        f'<circle cx="256" cy="256" r="201" stroke="#fff" stroke-width="{_cn(stroke_for(target, 3))}" opacity=".28"/>',
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
    bits = [f'<text x="{_cn(x)}" y="{_cn(y)}" font-family="{family}" font-size="{_cn(size)}"']
    if weight != 400:
        bits.append(f' font-weight="{weight}"')
    if anchor != "start":
        bits.append(f' text-anchor="{anchor}"')
    if spacing:
        bits.append(f' letter-spacing="{_cn(spacing)}"')
    bits.append(f' fill="{fill}" stroke="{halo}" stroke-width="{_cn(stroke_for(target, size * 0.16, 1.4))}"'
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
        f'<rect x="{_cn(256 - width / 2)}" y="398" width="{_cn(width)}" height="34" rx="5" fill="{paper}" '
        f'stroke="{accent}" stroke-width="{_cn(stroke_for(target, 2.6))}" opacity=".96"/>',
        f'<text x="256" y="421" text-anchor="middle" font-family="sans-serif" font-size="20" '
        f'letter-spacing="2.4" fill="{mix(accent, "#000000", 0.45)}">{display}</text>',
    ]


# ------------------------------------------------------------ contour-basin


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
            art.append(f'<path d="M{_cn(x0)} {_cn(y0)} L{_cn(x1)} {_cn(y1)}" stroke="{ink}" '
                       f'stroke-width="{_cn(stroke_for(target, 1.6))}" opacity=".22"/>')
    if target != 42:
        for radius in (ring_r, 112.0):
            art.append(f'<circle cx="256" cy="256" r="{_cn(radius)}" fill="none" stroke="{ink}" '
                       f'stroke-width="{_cn(stroke_for(target, 2.6))}" opacity=".45"/>')
    if target == 220:
        for i in range(72):
            a = i * math.tau / 72 + tilt
            major = i % 6 == 0
            x0, y0 = xy(ring_r, a)
            x1, y1 = xy(ring_r + (18.0 if major else 9.0), a)
            art.append(f'<path d="M{_cn(x0)} {_cn(y0)} L{_cn(x1)} {_cn(y1)}" stroke="{ink}" '
                       f'stroke-width="{_cn(stroke_for(target, 5.5 if major else 2.4))}" '
                       f'opacity="{".8" if major else ".45"}"/>')
    elif target == 96:
        for i in range(16):
            a = i * math.tau / 16 + tilt
            x0, y0 = xy(ring_r, a)
            x1, y1 = xy(ring_r + 15.0, a)
            art.append(f'<path d="M{_cn(x0)} {_cn(y0)} L{_cn(x1)} {_cn(y1)}" stroke="{ink}" '
                       f'stroke-width="{_cn(stroke_for(target, 5))}" opacity=".6"/>')

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
                       f'stroke="{ink}" stroke-width="{_cn(stroke_for(target, 2.4))}"/>')
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
               f'stroke="{ink}" stroke-width="{_cn(stroke_for(target, 3))}"/>')
    art.append(f'<path d="{poly([tip, lft, tail])}" fill="{ink}"/>')

    stamp: list[str] = []
    hub_r = 24.0 if target == 42 else (19.0 if target == 96 else 21.0)
    stamp.append(f'<circle cx="256" cy="256" r="{_cn(hub_r)}" fill="{pale}" stroke="{ink}" '
                 f'stroke-width="{_cn(stroke_for(target, 7))}"/>')
    if target != 42:
        stamp.append(f'<circle cx="256" cy="256" r="{_cn(hub_r * 0.36)}" fill="{ink}"/>')

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

RENDERERS = {
    "pressed-fern": pressed_fern,
    "nodding-seedhead": nodding_seedhead,
    "wind-rose": wind_rose,
}

CALCULATIONS = {
    "fn.discArt.pressed-fern": pressed_fern,
    "fn.discArt.nodding-seedhead": nodding_seedhead,
    "fn.discArt.wind-rose": wind_rose,
}


def render(family: str, seed: int, base: str, accent: str, target: int, label: str) -> str:
    """paint_components-shaped entry point, keyed by family slug."""
    if family not in RENDERERS:
        raise ValueError("family is unsupported")
    return RENDERERS[family](seed, base, accent, target, label)
