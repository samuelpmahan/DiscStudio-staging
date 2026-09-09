#!/usr/bin/env python3
"""Studio *botanical* card renderers: the disc set as a botanical plate.

    render_single(card, art, width) -> str
    render_battle(card, art, width) -> str

`card` is the JSON that card_composition.compose() puts at cards['single'] or
cards['battle']; `art` maps presentationId -> a full disc-art SVG document (any
family, any target). The art is inlined as a <g> copy of the source document's
own elements — never a nested <svg>, which any host stylesheet targeting `svg`
would resize (the tournament rasterizer does exactly that) — with every id
namespaced per participant so two discs on one battle plate cannot collide.

The plate is warm stock: a deckle-edged ground, a hairline double rule with a
pressed-leaf ornament at each corner, an engraved name in serif, a letterspaced
maker/mold eyebrow, the note in italic, and the flight numbers set as a
herbarium measurement strip (serif figures over a hairline, small-caps captions
underneath). Battle plates carry a wax-seal score cartouche.

Layouts honored: single standard|gallery, battle standard|stacked. details=False
drops the note, the strip captions and the corner ornaments and shortens the
plate; the name, the maker/mold line, all four figures and the score stay.
"""
from __future__ import annotations

import html
import re

FLIGHT_KEYS = (("flight1", "SPEED"), ("flight2", "GLIDE"), ("flight3", "TURN"), ("flight4", "FADE"))

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_ROOT = re.compile(r"\A\s*(?:<\?xml[^>]*\?>\s*)?<svg\b([^>]*)>", re.S)
_VIEWBOX = re.compile(r'viewBox="([^"]*)"')
_ID = re.compile(r'id="([^"]+)"')

# The studio's paper. Fixed stock, so a plate reads the same whatever ink the
# disc carries; the participant's own color only tints rules and figures.
STOCK = "#f6efdd"
EDGE = "#efe5cd"
INK = "#2c2a20"
MUTED = "#7d735c"
HAIR = "#cdbf9c"
RULE = "#8d7f5e"
SERIF = "serif"
SANS = "sans-serif"


# ----------------------------------------------------------------- utilities

def _num(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _rgb(value: str) -> tuple[int, int, int]:
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def mix(a: str, b: str, t: float) -> str:
    ar, ag, ab = _rgb(a)
    br, bg, bb = _rgb(b)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return "#%02x%02x%02x" % (int(round(ar + (br - ar) * t)),
                              int(round(ag + (bg - ag) * t)),
                              int(round(ab + (bb - ab) * t)))


def _luma(value: str) -> float:
    r, g, b = _rgb(value)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def ink_of(participant: dict) -> str:
    """The participant's color, darkened until it can be read on the stock."""
    value = participant.get("color")
    value = value.lower() if isinstance(value, str) and HEX.fullmatch(value) else "#6d7a4a"
    while _luma(value) > 0.52:
        value = mix(value, "#241f16", 0.28)
    return value


def flight(value) -> str:
    if value is None or value == "" or isinstance(value, bool):
        return "—"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value == int(value) else f"{value:g}"
    return esc(value)


def fit(text: str, size: float, box: float, ratio: float = 0.54) -> float:
    """Shrink a type size until the string fits the box (never below 7)."""
    span = max(len(text) * ratio, 1.0)
    return max(7.0, min(size, box / span))


def text(x: float, y: float, body: str, size: float, fill: str = INK, anchor: str = "start",
         family: str = SANS, spacing: float = 0.0, weight: int = 400, style: str = "",
         opacity: float = 1.0) -> str:
    bits = [f'<text x="{_num(x)}" y="{_num(y)}" font-family="{family}" font-size="{_num(size)}"']
    if weight != 400:
        bits.append(f' font-weight="{weight}"')
    if anchor != "start":
        bits.append(f' text-anchor="{anchor}"')
    if spacing:
        bits.append(f' letter-spacing="{_num(spacing)}"')
    if style:
        bits.append(f' font-style="{style}"')
    if opacity != 1.0:
        bits.append(f' opacity="{_num(opacity)}"')
    bits.append(f' fill="{fill}">{body}</text>')
    return "".join(bits)


def rule(x1: float, y1: float, x2: float, y2: float, color: str = HAIR, w: float = 1.0,
         opacity: float = 1.0) -> str:
    return (f'<path d="M{_num(x1)} {_num(y1)}L{_num(x2)} {_num(y2)}" stroke="{color}"'
            f' stroke-width="{_num(w)}"' + (f' opacity="{_num(opacity)}"' if opacity != 1 else "") +
            ' fill="none"/>')


def leaf(x: float, y: float, size: float, spin: float, color: str, opacity: float = 1.0) -> str:
    """A small pressed-leaf ornament, used on the plate corners and the seal."""
    return (f'<path d="M0 {_num(-size)}Q{_num(size * .52)} 0 0 {_num(size)}'
            f'Q{_num(-size * .52)} 0 0 {_num(-size)}Z" fill="{color}"'
            + (f' opacity="{_num(opacity)}"' if opacity != 1 else "") +
            f' transform="translate({_num(x)} {_num(y)}) rotate({_num(spin)})"/>')


# ------------------------------------------------------------- art embedding

def _art_parts(svg_text: str) -> tuple[str, tuple[float, float, float, float]]:
    match = _ROOT.match(svg_text or "")
    if not match:
        raise ValueError("art must be a full <svg> document")
    inner = svg_text[match.end():]
    close = inner.rfind("</svg>")
    if close == -1:
        raise ValueError("art SVG is not closed")
    found = _VIEWBOX.search(match.group(1))
    box = (0.0, 0.0, 512.0, 512.0)
    if found:
        parts = found.group(1).replace(",", " ").split()
        if len(parts) == 4:
            box = tuple(float(p) for p in parts)  # type: ignore[assignment]
    return inner[:close], box


def _namespace(markup: str, prefix: str) -> str:
    for name in sorted(set(_ID.findall(markup)), key=len, reverse=True):
        markup = markup.replace(f'id="{name}"', f'id="{prefix}{name}"')
        markup = markup.replace(f"url(#{name})", f"url(#{prefix}{name})")
        markup = markup.replace(f'href="#{name}"', f'href="#{prefix}{name}"')
    return markup


def embed(svg_text: str, prefix: str, cx: float, cy: float, diameter: float) -> str:
    """Inline the art's own elements, scaled so its viewBox fills `diameter`."""
    inner, (bx, by, bw, bh) = _art_parts(svg_text)
    inner = _namespace(inner, prefix)
    scale = diameter / max(bw, bh)
    x = cx - diameter / 2.0
    y = cy - diameter / 2.0
    return (f'<g transform="translate({_num(x)} {_num(y)}) scale({_num(scale)})'
            f' translate({_num(-bx)} {_num(-by)})">{inner}</g>')


def specimen(art_svg: str | None, prefix: str, cx: float, cy: float, diameter: float,
             tint: str, captioned: bool) -> str:
    """The disc mounted on the plate: a hairline ring, the art, and a shadow."""
    r = diameter / 2.0
    out = [f'<g><circle cx="{_num(cx)}" cy="{_num(cy + r * .045)}" r="{_num(r)}" fill="{RULE}" opacity=".16"/>']
    if art_svg:
        out.append(f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r * 1.045)}" fill="{EDGE}"/>')
        out.append(embed(art_svg, prefix, cx, cy, diameter))
    else:
        out.append(f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r)}" fill="{EDGE}"'
                   f' stroke="{HAIR}" stroke-width="1.2" stroke-dasharray="4 4"/>')
        out.append(leaf(cx, cy, r * 0.42, 24, HAIR, 0.7))
        out.append(text(cx, cy + r * 0.72, "NO PLATE", fit("NO PLATE", r * 0.26, diameter * .8),
                        MUTED, "middle", SANS, 1.4))
    out.append(f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r * 1.045)}" fill="none"'
               f' stroke="{tint}" stroke-width="1.6" opacity=".55"/>')
    if captioned:
        out.append(f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r * 1.13)}" fill="none"'
                   f' stroke="{HAIR}" stroke-width=".9" opacity=".85"/>')
    out.append("</g>")
    return "".join(out)


# ------------------------------------------------------------- plate furniture

def plate(w: float, h: float, tint: str, ornaments: bool) -> str:
    """Deckled stock, a double rule, and a pressed leaf in each corner."""
    out = [f'<rect width="{_num(w)}" height="{_num(h)}" fill="{STOCK}"/>',
           f'<rect x="3" y="3" width="{_num(w - 6)}" height="{_num(h - 6)}" fill="none"'
           f' stroke="{RULE}" stroke-width="1.6" opacity=".85"/>',
           f'<rect x="8" y="8" width="{_num(w - 16)}" height="{_num(h - 16)}" fill="none"'
           f' stroke="{HAIR}" stroke-width=".9"/>',
           f'<rect x="3" y="3" width="{_num(w - 6)}" height="7" fill="{tint}" opacity=".55"/>']
    if ornaments:
        for x, y, spin in ((16, 16, 135), (w - 16, 16, -135), (16, h - 16, 45), (w - 16, h - 16, -45)):
            out.append(leaf(x, y, 7.5, spin, RULE, 0.5))
    return "".join(out)


def eyebrow(participant: dict) -> str:
    maker = str(participant.get("manufacturer") or "").strip()
    mold = str(participant.get("mold") or "").strip()
    line = " · ".join(p for p in (maker, mold) if p) or "UNRECORDED MOLD"
    return esc(line.upper())


def strip(x: float, y: float, w: float, participant: dict, tint: str, captions: bool,
          figure: float = 25.0) -> str:
    """The flight measurements: four serif figures over a hairline."""
    out = [rule(x, y, x + w, y, RULE, 1.1, 0.7)]
    cell = w / 4.0
    values = participant.get("flightValues") or {}
    for i, (key, caption) in enumerate(FLIGHT_KEYS):
        cx = x + cell * (i + 0.5)
        if i:
            out.append(rule(x + cell * i, y + 3, x + cell * i, y + figure * 1.05, HAIR, 0.8))
        body = flight(values.get(key))
        out.append(text(cx, y + figure * 0.92, body, figure, INK, "middle", SERIF))
        if captions:
            out.append(text(cx, y + figure * 1.46, caption, min(9.5, cell * 0.19), MUTED,
                            "middle", SANS, 1.5))
    out.append(rule(x, y + figure * (1.62 if captions else 1.12), x + w,
                    y + figure * (1.62 if captions else 1.12), tint, 1.4, 0.55))
    return "".join(out)


def nameplate(x: float, y: float, w: float, participant: dict, tint: str, details: bool,
              size: float = 30.0, note_size: float = 12.0) -> str:
    """Eyebrow, engraved name, and (with details) the note in italic."""
    name = esc(str(participant.get("name") or "Untitled").strip() or "Untitled")
    out = [text(x, y, eyebrow(participant), min(10.5, fit(eyebrow(participant), 10.5, w, 0.62)),
                MUTED, "start", SANS, 1.8),
           text(x, y + size * 0.92, name, fit(name, size, w, 0.56), INK, "start", SERIF, 0.2)]
    if details:
        note = str(participant.get("note") or "").strip()
        if note:
            out.append(text(x, y + size * 1.42, esc(note), note_size, MUTED, "start", SERIF, 0, 400, "italic"))
        out.append(rule(x, y + size * 1.72, x + w * 0.34, y + size * 1.72, tint, 1.6, 0.7))
    return "".join(out)


def _score_map(card: dict) -> dict[str, str]:
    scores = card.get("scores")
    out: dict[str, str] = {}
    ids = [p.get("presentationId", "") for p in card.get("participants", [])]
    if isinstance(scores, dict):
        for key, value in scores.items():
            if key in ids:
                out[key] = flight(value)
            elif isinstance(key, str) and key.isdigit() and int(key) < len(ids):
                out[ids[int(key)]] = flight(value)
    elif isinstance(scores, list):
        for index, value in enumerate(scores[:len(ids)]):
            out[ids[index]] = flight(value)
    return out


def _winner(card: dict) -> str:
    for key in ("manualWinner", "winner", "highlight"):
        value = card.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            ids = [p.get("presentationId", "") for p in card.get("participants", [])]
            if 0 <= value < len(ids):
                return ids[value]
    return ""


def seal(cx: float, cy: float, r: float, value: str, tint: str, captioned: bool) -> str:
    """A wax-seal score cartouche."""
    out = [f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r)}" fill="{EDGE}" stroke="{tint}"'
           f' stroke-width="1.8" opacity=".95"/>',
           f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r * .84)}" fill="none" stroke="{HAIR}"'
           f' stroke-width=".9"/>']
    body = value if value else "–"
    out.append(text(cx, cy + r * 0.30, body, fit(body, r * 1.05, r * 1.5, 0.62), INK, "middle", SERIF))
    if captioned:
        out.append(text(cx, cy + r * 1.44, "SCORE", min(9.0, r * 0.34), MUTED, "middle", SANS, 1.8))
    else:
        out.append(text(cx, cy + r * 1.44, "SCORE", min(8.0, r * 0.30), MUTED, "middle", SANS, 1.4))
    return "".join(out)


def edition(x: float, y: float, kind: str, layout: str, anchor: str = "start") -> str:
    body = esc(f"PLATE · {kind} · {layout}".upper())
    return text(x, y, body, 8.0, MUTED, anchor, SANS, 1.6, 400, "", 0.85)


def frame(w: float, h: float, width: int, label: str, body: str) -> str:
    height = max(1, round(width * h / w))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
            f' viewBox="0 0 {_num(w)} {_num(h)}" role="img" aria-label="{esc(label)}">'
            f'{body}<title>{esc(label)}</title></svg>\n')


def _participants(card: dict, count: int) -> list[dict]:
    values = [p for p in card.get("participants", []) if isinstance(p, dict)]
    while len(values) < count:
        values.append({"presentationId": f"missing{len(values)}", "name": "Unplated"})
    return values[:count]


# ------------------------------------------------------------- single plates

def render_single(card: dict, art: dict[str, str], width: int) -> str:
    """A single-disc plate. layout: 'standard' (landscape) or 'gallery' (portrait)."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    art = art if isinstance(art, dict) else {}
    width = int(width)
    if width < 80:
        raise ValueError("width must be at least 80")
    layout = card.get("layout", "standard")
    layout = layout if layout in ("standard", "gallery") else "standard"
    details = bool(card.get("details", True))
    person = _participants(card, 1)[0]
    pid = str(person.get("presentationId", "p0"))
    tint = ink_of(person)
    plate_art = art.get(pid)
    name = str(person.get("name") or "Untitled")

    if layout == "gallery":
        w, h = 340.0, (466.0 if details else 402.0)
        body = [plate(w, h, tint, details),
                specimen(plate_art, "a-", w / 2.0, 172.0, 236.0, tint, details),
                rule(34, 306, w - 34, 306, HAIR, 1.0),
                nameplate(34, 336, w - 68, person, tint, details, 32.0, 12.5),
                strip(34, 396 if details else 350, w - 68, person, tint, details, 26.0),
                edition(w / 2.0, h - 14, "single", layout, "middle")]
    else:
        w, h = 424.0, (190.0 if details else 152.0)
        disc = 132.0 if details else 118.0
        body = [plate(w, h, tint, details),
                specimen(plate_art, "a-", 22.0 + disc / 2.0, h / 2.0 + 2.0, disc, tint, details),
                nameplate(disc + 46.0, 44.0, w - disc - 74.0, person, tint, details, 30.0, 12.0),
                strip(disc + 46.0, 108.0 if details else 92.0, w - disc - 74.0, person, tint, details, 25.0),
                edition(w - 16, h - 12, "single", layout, "end")]
    return frame(w, h, width, f"{name} — botanical single plate ({layout})", "".join(body))


# ------------------------------------------------------------- battle plates

def render_battle(card: dict, art: dict[str, str], width: int) -> str:
    """A two-disc match plate. layout: 'standard' (side by side) or 'stacked'."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    art = art if isinstance(art, dict) else {}
    width = int(width)
    if width < 80:
        raise ValueError("width must be at least 80")
    layout = card.get("layout", "standard")
    layout = layout if layout in ("standard", "stacked") else "standard"
    details = bool(card.get("details", True))
    people = _participants(card, 2)
    scores = _score_map(card)
    champion = _winner(card)
    tints = [ink_of(p) for p in people]
    names = [str(p.get("name") or "Untitled") for p in people]

    if layout == "stacked":
        w, h = 470.0, (378.0 if details else 306.0)
        row_h = (h - 74.0) / 2.0
        body = [plate(w, h, tints[0], details),
                text(w / 2.0, 32.0, "MATCH PLATE", 10.5, MUTED, "middle", SANS, 3.4)]
        for index, person in enumerate(people):
            pid = str(person.get("presentationId", f"p{index}"))
            top = 44.0 + index * row_h
            disc = min(row_h - 28.0, 118.0)
            won = champion and pid == champion
            if won:
                body.append(f'<rect x="14" y="{_num(top - 4)}" width="{_num(w - 28)}"'
                            f' height="{_num(row_h - 6)}" fill="{tints[index]}" opacity=".07"/>')
                body.append(rule(14, top - 4, 14, top + row_h - 10, tints[index], 3.0, 0.85))
                body.append(leaf(26, top + 10, 6.5, 90, tints[index], 0.9))
            body.append(specimen(art.get(pid), f"{'ab'[index]}-", 30.0 + disc / 2.0,
                                 top + row_h / 2.0 - 6.0, disc, tints[index], details))
            left = 40.0 + disc
            body.append(nameplate(left, top + 26.0, w - disc - 156.0, person, tints[index],
                                  details, 25.0, 11.0))
            body.append(strip(left, top + (74.0 if details else 62.0), w - disc - 156.0, person,
                              tints[index], details, 20.0))
            body.append(seal(w - 58.0, top + row_h / 2.0 - 8.0, 32.0, scores.get(pid, ""),
                             tints[index], details))
            if index == 0:
                body.append(rule(24, 44.0 + row_h - 6.0, w - 24, 44.0 + row_h - 6.0, HAIR, 1.0))
        body.append(edition(w / 2.0, h - 13, "battle", layout, "middle"))
    else:
        w, h = 720.0, (238.0 if details else 190.0)
        disc = 142.0 if details else 126.0
        half = (w - 116.0) / 2.0
        body = [plate(w, h, tints[0], details)]
        for index, person in enumerate(people):
            pid = str(person.get("presentationId", f"p{index}"))
            x0 = 16.0 + index * (half + 84.0)
            won = champion and pid == champion
            if won:
                body.append(f'<rect x="{_num(x0 - 4)}" y="26" width="{_num(half + 8)}"'
                            f' height="{_num(h - 56)}" fill="{tints[index]}" opacity=".07"/>')
                body.append(rule(x0 - 4, 26, x0 + half + 4, 26, tints[index], 2.6, 0.9))
                body.append(leaf(x0 + half - 8, 38, 6.5, 180, tints[index], 0.9))
            body.append(specimen(art.get(pid), f"{'ab'[index]}-", x0 + disc / 2.0,
                                 h / 2.0 + 4.0, disc, tints[index], details))
            left = x0 + disc + 16.0
            wide = half - disc - 20.0
            body.append(nameplate(left, 62.0, wide, person, tints[index], details, 27.0, 11.5))
            body.append(strip(left, 128.0 if details else 112.0, wide, person, tints[index],
                              details, 23.0))
        centre = w / 2.0
        body.append(rule(centre, 34, centre, h - 34, HAIR, 1.0))
        body.append(f'<circle cx="{_num(centre)}" cy="{_num(h / 2.0)}" r="27" fill="{STOCK}"/>')
        body.append(leaf(centre, h / 2.0 - 30, 7.0, 180, RULE, 0.55))
        body.append(leaf(centre, h / 2.0 + 30, 7.0, 0, RULE, 0.55))
        body.append(text(centre, h / 2.0 + 6.0, "vs", 21.0, RULE, "middle", SERIF, 0, 400, "italic"))
        for index, person in enumerate(people):
            pid = str(person.get("presentationId", f"p{index}"))
            body.append(seal(centre + (-1 if index == 0 else 1) * 62.0, 62.0, 30.0,
                             scores.get(pid, ""), tints[index], details))
        body.append(edition(w - 16, h - 12, "battle", layout, "end"))
    return frame(w, h, width, f"{names[0]} vs {names[1]} — botanical match plate ({layout})",
                 "".join(body))


CALCULATIONS = {
    "fn.card.single.render": render_single,
    "fn.card.battle.render": render_battle,
}
