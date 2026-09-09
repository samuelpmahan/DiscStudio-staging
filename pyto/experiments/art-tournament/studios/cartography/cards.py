#!/usr/bin/env python3
"""Studio *cartography* card renderers: a disc card drawn as a map plate.

    render_single(card, art, width) -> str
    render_battle(card, art, width) -> str

`card` is the JSON that card_composition.compose() puts at cards['single'] or
cards['battle']; `art` maps presentationId -> a full disc-art SVG document
(any family, any target). Art is embedded as a nested <svg> whose ids are
namespaced per participant, so two discs on one battle plate never collide.

The plate borrows the vocabulary of a course map sheet: a double neat-line, a
graticule with corner ticks, a segmented scale bar under the disc inset, a
title block, and the flight numbers set as a map legend strip.

Layouts honored: single standard|gallery, battle standard|stacked. `details`
False drops the legend strip, the maker/mold eyebrow and the note, and the
plate shortens to suit.
"""
from __future__ import annotations

import html
import re

try:
    from families import mix
except ImportError:  # pragma: no cover - direct package-style import
    from .families import mix  # type: ignore

PAPER = "#f5f0e4"
FIELD = "#efe7d5"
INK = "#22302b"
MUTED = "#6f7c71"
GRID = "#cfc4a8"
NEAT = "#2b3a33"
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

FLIGHT_KEYS = (("flight1", "SPEED"), ("flight2", "GLIDE"), ("flight3", "TURN"), ("flight4", "FADE"))

_ROOT = re.compile(r"\A\s*(?:<\?xml[^>]*\?>\s*)?<svg\b([^>]*)>", re.S)
_VIEWBOX = re.compile(r'viewBox="([^"]*)"')
_ID = re.compile(r'id="([^"]+)"')


# ----------------------------------------------------------------- utilities

def _num(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _accent(value, fallback: str = "#4c7f6a") -> str:
    return value.lower() if isinstance(value, str) and HEX.fullmatch(value) else fallback


def _flight(value) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "—"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value == int(value) else f"{value:g}"
    return esc(value)


def _fit(text: str, size: float, box: float, ratio: float = 0.56) -> float:
    span = max(len(text) * ratio, 1.0)
    return max(6.0, min(size, box / span))


def _text(x: float, y: float, body: str, size: float, fill: str = INK, anchor: str = "start",
          weight: int = 400, family: str = "sans-serif", spacing: float = 0.0,
          opacity: float = 1.0) -> str:
    bits = [f'<text x="{_num(x)}" y="{_num(y)}" font-family="{family}" font-size="{_num(size)}"']
    if weight != 400:
        bits.append(f' font-weight="{weight}"')
    if anchor != "start":
        bits.append(f' text-anchor="{anchor}"')
    if spacing:
        bits.append(f' letter-spacing="{_num(spacing)}"')
    if opacity != 1.0:
        bits.append(f' opacity="{_num(opacity)}"')
    bits.append(f' fill="{fill}">{body}</text>')
    return "".join(bits)


# ------------------------------------------------------------- art embedding

def _art_parts(svg_text: str) -> tuple[str, str]:
    match = _ROOT.match(svg_text or "")
    if not match:
        raise ValueError("art must be a full <svg> document")
    inner = svg_text[match.end():]
    close = inner.rfind("</svg>")
    if close == -1:
        raise ValueError("art SVG is not closed")
    box = _VIEWBOX.search(match.group(1))
    return inner[:close], (box.group(1) if box else "0 0 512 512")


def _namespace(markup: str, prefix: str) -> str:
    for name in sorted(set(_ID.findall(markup)), key=len, reverse=True):
        markup = markup.replace(f'id="{name}"', f'id="{prefix}{name}"')
        markup = markup.replace(f"url(#{name})", f"url(#{prefix}{name})")
        markup = markup.replace(f'href="#{name}"', f'href="#{prefix}{name}"')
    return markup


def _embed(svg_text: str, prefix: str, x: float, y: float, size: float) -> str:
    """Inline the art's own elements under a transform.

    A nested <svg> would be resized by any host stylesheet that targets `svg`
    (the tournament rasterizer does exactly that), so the art is copied in as a
    <g>: ids namespaced, scaled from its own viewBox, clipped to its box.
    """
    inner, box = _art_parts(svg_text)
    inner = _namespace(inner, prefix)
    try:
        min_x, min_y, box_w, box_h = (float(v) for v in box.replace(",", " ").split())
    except ValueError:
        min_x, min_y, box_w, box_h = 0.0, 0.0, 512.0, 512.0
    span = max(box_w, box_h) or 512.0
    scale = size / span
    return (f'<defs><clipPath id="{prefix}box"><rect x="{_num(x)}" y="{_num(y)}" '
            f'width="{_num(size)}" height="{_num(size)}"/></clipPath></defs>'
            f'<g clip-path="url(#{prefix}box)"><g transform="translate({_num(x)} {_num(y)}) '
            f'scale({_num(scale)}) translate({_num(-min_x)} {_num(-min_y)})">{inner}</g></g>')


def _missing(x: float, y: float, size: float, accent: str) -> str:
    r = size / 2.0
    return (f'<g><circle cx="{_num(x + r)}" cy="{_num(y + r)}" r="{_num(size * 0.43)}" fill="{FIELD}" '
            f'stroke="{accent}" stroke-width="2" stroke-dasharray="6 5"/>'
            + _text(x + r, y + r + 4, "NO PLATE", 9, MUTED, anchor="middle", spacing=1.2) + '</g>')


# ------------------------------------------------------------- plate pieces

def _plate(w: float, h: float, accent: str, highlight: bool) -> str:
    """Neat-line, graticule and corner ticks: the sheet everything sits on."""
    out = [f'<rect x="0" y="0" width="{_num(w)}" height="{_num(h)}" rx="10" fill="{PAPER}"/>',
           f'<rect x="7" y="7" width="{_num(w - 14)}" height="{_num(h - 14)}" fill="{FIELD}"/>',
           '<g stroke="' + GRID + '" stroke-width="0.7" opacity=".85">']
    step = 28.0
    x = 7.0 + step
    while x < w - 7:
        out.append(f'<path d="M{_num(x)} 7 V{_num(h - 7)}"/>')
        x += step
    y = 7.0 + step
    while y < h - 7:
        out.append(f'<path d="M7 {_num(y)} H{_num(w - 7)}"/>')
        y += step
    out.append('</g>')
    out.append(f'<rect x="7" y="7" width="{_num(w - 14)}" height="{_num(h - 14)}" fill="none" '
               f'stroke="{NEAT}" stroke-width="1.6"/>')
    out.append(f'<rect x="12" y="12" width="{_num(w - 24)}" height="{_num(h - 24)}" fill="none" '
               f'stroke="{NEAT}" stroke-width="0.7" opacity=".55"/>')
    for cx, cy in ((12, 12), (w - 12, 12), (12, h - 12), (w - 12, h - 12)):
        out.append(f'<path d="M{_num(cx - 7)} {_num(cy)} h14 M{_num(cx)} {_num(cy - 7)} v14" '
                   f'stroke="{accent}" stroke-width="1.4" opacity=".85"/>')
    out.append(f'<rect x="0" y="0" width="{_num(w)}" height="{_num(h)}" rx="10" fill="none" '
               f'stroke="{accent if highlight else NEAT}" stroke-width="{3.5 if highlight else 1.2}"/>')
    return "".join(out)


def _inset(art: str | None, prefix: str, x: float, y: float, size: float, accent: str,
           scale_bar: bool = True) -> str:
    """The disc plate: art in a ruled circular inset with a scale bar beneath."""
    r = size / 2.0
    # The art's own disc is r=220 in a 512 box; ring and ticks hug that, not the box.
    disc = size * (220.0 / 512.0)
    out = [f'<circle cx="{_num(x + r)}" cy="{_num(y + r)}" r="{_num(disc + 4)}" fill="{PAPER}" '
           f'stroke="{accent}" stroke-width="1.2" opacity=".9"/>']
    out.append(_embed(art, prefix, x, y, size) if art else _missing(x, y, size, accent))
    for i in range(4):
        ang = i * 90
        out.append(f'<g transform="rotate({ang} {_num(x + r)} {_num(y + r)})">'
                   f'<path d="M{_num(x + r)} {_num(y + r - disc - 10)} v6" stroke="{NEAT}" '
                   'stroke-width="1.3"/></g>')
    if scale_bar:
        bar_w = size * 0.56
        bx = x + (size - bar_w) / 2.0
        by = y + r + disc + 19
        cell = bar_w / 4.0
        for i in range(4):
            out.append(f'<rect x="{_num(bx + i * cell)}" y="{_num(by)}" width="{_num(cell)}" height="4" '
                       f'fill="{NEAT if i % 2 == 0 else PAPER}" stroke="{NEAT}" stroke-width="0.6"/>')
    return "".join(out)


def _eyebrow(participant: dict, x: float, y: float, box: float, accent: str) -> str:
    maker = str(participant.get("manufacturer") or "").strip()
    mold = str(participant.get("mold") or "").strip()
    variant = str(participant.get("variant") or "").strip()
    parts = [p for p in (maker, mold, variant) if p]
    body = esc(" · ".join(parts).upper()) if parts else "UNRECORDED MOLD"
    size = _fit(body, 10.5, box, ratio=0.78)
    out = [_text(x, y, body, size, MUTED if parts else mix(MUTED, PAPER, 0.35), spacing=1.4)]
    out.append(f'<path d="M{_num(x)} {_num(y + 5)} h{_num(box * 0.34)}" stroke="{accent}" stroke-width="2"/>')
    return "".join(out)


def _name(participant: dict, x: float, y: float, box: float, size: float) -> str:
    body = esc(str(participant.get("name") or "Untitled plate"))
    return _text(x, y, body, _fit(body, size, box, ratio=0.60), INK, weight=700, family="serif")


def _note(participant: dict, x: float, y: float, box: float) -> str:
    body = str(participant.get("note") or "").strip()
    if not body:
        return ""
    return _text(x, y, esc(body), _fit(body, 11, box, ratio=0.55), MUTED)


def _legend(participant: dict, x: float, y: float, box: float, accent: str,
            value_size: float = 21.0) -> str:
    """Flight numbers set as a map legend strip, one ruled cell per figure."""
    cell = box / 4.0
    out = [f'<path d="M{_num(x)} {_num(y)} h{_num(box)}" stroke="{NEAT}" stroke-width="1" opacity=".6"/>']
    for i, (key, label) in enumerate(FLIGHT_KEYS):
        cx = x + cell * i + cell / 2.0
        value = _flight((participant.get("flightValues") or {}).get(key))
        if i:
            out.append(f'<path d="M{_num(x + cell * i)} {_num(y + 3)} v{_num(value_size + 16)}" '
                       f'stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<path d="M{_num(cx)} {_num(y)} v5" stroke="{accent}" stroke-width="2"/>')
        out.append(_text(cx, y + value_size + 2, esc(value), value_size, INK, anchor="middle",
                         weight=700, family="serif"))
        out.append(_text(cx, y + value_size + 15, label, 7.6, MUTED, anchor="middle", spacing=1.1))
    return "".join(out)


def _legend_compact(participant: dict, x: float, y: float, box: float, accent: str,
                    size: float = 17.0) -> str:
    """details=False keeps the four figures, drops their captions and rules."""
    cell = box / 4.0
    out = [f'<path d="M{_num(x)} {_num(y - size - 4)} h{_num(box)}" stroke="{NEAT}" '
           'stroke-width="1" opacity=".45"/>']
    for i, (key, _label) in enumerate(FLIGHT_KEYS):
        cx = x + cell * i + cell / 2.0
        value = _flight((participant.get("flightValues") or {}).get(key))
        if i:
            out.append(f'<path d="M{_num(x + cell * i)} {_num(y - size + 2)} v{_num(size)}" '
                       f'stroke="{GRID}" stroke-width="1"/>')
        out.append(_text(cx, y, esc(value), size, INK, anchor="middle", weight=700, family="serif"))
    return "".join(out)


def _score(value, x: float, y: float, w: float, h: float, accent: str, winner: bool) -> str:
    body = "–" if value is None or value == "" else esc(value)
    out = [f'<rect x="{_num(x)}" y="{_num(y)}" width="{_num(w)}" height="{_num(h)}" rx="6" '
           f'fill="{mix(accent, PAPER, 0.84)}" stroke="{accent}" stroke-width="1.6"/>',
           _text(x + w / 2.0, y + h * 0.64, body, _fit(body, h * 0.56, w * 0.8, ratio=0.62), INK,
                 anchor="middle", weight=700, family="serif"),
           _text(x + w / 2.0, y + h - 5, "SCORE", 7, MUTED, anchor="middle", spacing=1.1)]
    if winner:
        out.append(f'<circle cx="{_num(x + w)}" cy="{_num(y)}" r="8" fill="{accent}"/>')
        out.append(_text(x + w, y + 3.6, "★", 10, PAPER, anchor="middle"))
    return "".join(out)


def _sheet_note(card: dict, x: float, y: float, accent: str) -> str:
    title = str(card.get("title") or "").strip()
    body = esc(title.upper()) if title else f"{card.get('type', 'single').upper()} PLATE · {esc(str(card.get('layout', 'standard')).upper())}"
    return _text(x, y, body, 8.4, mix(MUTED, PAPER, 0.2), spacing=1.6)


def _document(w: float, h: float, width: int, body: str, aria: str) -> str:
    scale = width / w
    height = int(round(h * scale))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {_num(w)} {_num(h)}" role="img" aria-label="{aria}">'
            f'<title>{aria}</title>{body}</svg>\n')


def _scores_for(card: dict, participants: list[dict]) -> list:
    raw = card.get("scores")
    out: list = []
    for index, participant in enumerate(participants):
        value = None
        if isinstance(raw, dict):
            value = raw.get(participant.get("presentationId"))
            if value is None:
                value = raw.get(str(index))
        elif isinstance(raw, list) and index < len(raw):
            value = raw[index]
        if isinstance(value, dict):
            value = value.get("score")
        out.append(value)
    return out


def _winners(card: dict, participants: list[dict]) -> list[bool]:
    marked = card.get("manualWinner") or card.get("winner") or card.get("highlight")
    ids = [p.get("presentationId") for p in participants]
    if isinstance(marked, str):
        return [pid == marked for pid in ids]
    if isinstance(marked, int) and not isinstance(marked, bool):
        return [i == marked for i in range(len(ids))]
    return [False] * len(ids)


def _participants(card: dict, count: int) -> list[dict]:
    people = [p for p in (card.get("participants") or []) if isinstance(p, dict)]
    while len(people) < count:
        people.append({"presentationId": f"slot-{len(people)}", "name": "", "flightValues": {}})
    return people[:count]


# ----------------------------------------------------------------- renderers

def render_single(card: dict, art: dict, width: int = 400) -> str:
    """One disc, plated. layout 'standard' is a wide sheet, 'gallery' a portrait."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    art = art if isinstance(art, dict) else {}
    width = max(120, int(width))
    participant = _participants(card, 1)[0]
    accent = _accent(participant.get("color"))
    details = card.get("details", True) is not False
    layout = card.get("layout", "standard")
    layout = layout if layout in ("standard", "gallery") else "standard"
    pid = participant.get("presentationId")
    disc = art.get(pid)

    if layout == "gallery":
        w = 340.0
        h = 470.0 if details else 408.0
        body = [_plate(w, h, accent, False),
                _inset(disc, "a0-", 46, 34, 248, accent, scale_bar=details),
                _sheet_note(card, 22, 28, accent),
                _eyebrow(participant, 26, 330, w - 52, accent),
                _name(participant, 26, 366, w - 52, 34)]
        if details:
            body.append(_note(participant, 26, 386, w - 52))
            body.append(_legend(participant, 26, 404, w - 52, accent, value_size=24))
        else:
            body.append(_legend_compact(participant, 26, 394, w - 52, accent, size=22))
    else:
        w = 420.0
        h = 190.0 if details else 146.0
        art_size = 140.0 if details else 104.0
        art_y = 22.0 if details else 20.0
        col = 190.0 if details else 152.0
        body = [_plate(w, h, accent, False),
                _inset(disc, "a0-", 20, art_y, art_size, accent, scale_bar=details),
                _text(w - 20, 28, "SINGLE PLATE", 8.4, mix(MUTED, PAPER, 0.2), anchor="end",
                      spacing=1.6),
                _eyebrow(participant, col, 48 if details else 52, w - col - 22, accent),
                _name(participant, col, 86 if details else 88, w - col - 22, 30)]
        if details:
            body.append(_note(participant, col, 106, w - col - 22))
            body.append(_legend(participant, col, 122, w - col - 22, accent))
        else:
            body.append(_legend_compact(participant, col, 122, w - col - 22, accent))
    aria = esc(f"{participant.get('name') or 'Disc'} — single card plate ({layout})")
    return _document(w, h, width, "".join(body), aria)


def render_battle(card: dict, art: dict, width: int = 660) -> str:
    """Two discs on one match plate. 'standard' sets them abeam, 'stacked' in rows."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    art = art if isinstance(art, dict) else {}
    width = max(200, int(width))
    people = _participants(card, 2)
    details = card.get("details", True) is not False
    layout = card.get("layout", "standard")
    layout = layout if layout in ("standard", "stacked") else "standard"
    scores = _scores_for(card, people)
    winners = _winners(card, people)
    accents = [_accent(p.get("color")) for p in people]
    lead = accents[0]

    if layout == "stacked":
        w = 440.0
        row_h = 140.0 if details else 110.0
        h = 52.0 + row_h * 2 + 14.0
        body = [_plate(w, h, lead, False),
                _text(24, 34, "MATCH PLATE · STACKED", 8.6, mix(MUTED, PAPER, 0.2), spacing=1.8),
                f'<path d="M24 40 H{_num(w - 24)}" stroke="{NEAT}" stroke-width="1" opacity=".55"/>']
        for index, participant in enumerate(people):
            top = 52.0 + row_h * index
            accent = accents[index]
            size = 100.0 if details else 68.0
            body.append(_inset(art.get(participant.get("presentationId")), f"a{index}-",
                               24, top + 12, size, accent, scale_bar=False))
            col = 24 + size + 26
            box = w - col - 92
            body.append(_eyebrow(participant, col, top + (26 if details else 30), box, accent))
            body.append(_name(participant, col, top + (56 if details else 58), box, 24))
            if details:
                body.append(_legend(participant, col, top + 72, box, accent, value_size=17))
            else:
                body.append(_legend_compact(participant, col, top + 82, box, accent))
            body.append(_score(scores[index], w - 82, top + 16, 56, 58, accent, winners[index]))
            if index == 0:
                body.append(f'<path d="M24 {_num(top + row_h - 4)} H{_num(w - 24)}" stroke="{GRID}" '
                            'stroke-width="1" stroke-dasharray="5 4"/>')
                body.append(f'<circle cx="{_num(w / 2)}" cy="{_num(top + row_h - 4)}" r="12" '
                            f'fill="{PAPER}" stroke="{NEAT}" stroke-width="1.2"/>')
                body.append(_text(w / 2, top + row_h, "VS", 9, INK, anchor="middle", weight=700, spacing=0.8))
    else:
        w = 700.0
        h = 224.0 if details else 172.0
        block_w = 300.0
        centre = w / 2.0
        body = [_plate(w, h, lead, False)]
        for index, participant in enumerate(people):
            bx = 14.0 if index == 0 else 386.0
            accent = accents[index]
            size = 116.0 if details else 84.0
            body.append(_inset(art.get(participant.get("presentationId")), f"a{index}-",
                               bx + 8, 44.0 if details else 34.0, size, accent, scale_bar=False))
            col = bx + size + 22
            box = bx + block_w - col - 12
            body.append(_eyebrow(participant, col, 66 if details else 60, box, accent))
            body.append(_name(participant, col, 98 if details else 92, box, 24))
            if details:
                body.append(_legend(participant, bx + 8, 168, block_w - 16, accent, value_size=18))
            else:
                body.append(_legend_compact(participant, bx + 8, 140, block_w - 16, accent))
            if winners[index]:
                body.append(f'<rect x="{_num(bx)}" y="30" width="{_num(block_w)}" '
                            f'height="{_num(h - 44)}" rx="7" fill="none" stroke="{accent}" '
                            'stroke-width="2" opacity=".8"/>')
        # Centre column: the match rosette over the score pair.
        body.append(f'<circle cx="{_num(centre)}" cy="56" r="15" fill="{PAPER}" stroke="{NEAT}" '
                    'stroke-width="1.4"/>')
        for i in range(8):
            body.append(f'<g transform="rotate({i * 45} {_num(centre)} 56)">'
                        f'<path d="M{_num(centre)} 41 v-5" stroke="{NEAT}" stroke-width="1.1" '
                        'opacity=".7"/></g>')
        body.append(_text(centre, 60, "VS", 10, INK, anchor="middle", weight=700, spacing=0.8))
        base_y = 132.0 if details else 118.0
        for index in range(2):
            value = "–" if scores[index] is None or scores[index] == "" else esc(scores[index])
            anchor = "end" if index == 0 else "start"
            x = centre - 15 if index == 0 else centre + 15
            body.append(_text(x, base_y, value, _fit(value, 34, 40, ratio=0.62), INK,
                              anchor=anchor, weight=700, family="serif"))
            if winners[index]:
                star_x = x + (-13 if index == 0 else 13)
                body.append(f'<circle cx="{_num(star_x)}" cy="{_num(base_y - 32)}" r="7" '
                            f'fill="{accents[index]}"/>')
                body.append(_text(star_x, base_y - 29, "★", 9, PAPER, anchor="middle"))
        if any(v is not None and v != "" for v in scores):
            body.append(_text(centre, base_y - 7, "–", 17, MUTED, anchor="middle"))
        body.append(_text(centre, base_y + 16, "SCORE", 7, MUTED, anchor="middle", spacing=1.2))
        body.append(f'<path d="M{_num(centre)} {_num(base_y + 30)} V{_num(h - 26)}" stroke="{GRID}" '
                    'stroke-width="1.2" stroke-dasharray="6 5"/>')
        body.append(_text(centre, 30, "MATCH PLATE", 8.6, mix(MUTED, PAPER, 0.2), anchor="middle",
                          spacing=2.2))
    names = " vs ".join(str(p.get("name") or "disc") for p in people)
    aria = esc(f"{names} — battle card plate ({layout})")
    return _document(w, h, width, "".join(body), aria)


CALCULATIONS = {
    "fn.card.single.render": render_single,
    "fn.card.battle.render": render_battle,
}
