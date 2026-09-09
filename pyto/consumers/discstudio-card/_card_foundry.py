#!/usr/bin/env python3
# RETAINED verbatim from pyto/experiments/art-tournament/studios/foundry/cards.py
# (studio *foundry*: render_single 68/72 -- lost the single by one point to
# botanical's 69; render_battle 66/72 -- tied signal on points and lost the
# tie-break on the judges' stated reason, that the score must be the largest
# object on a battle plate. experiments/art-tournament/RESULTS.md S1, S3.)
# Retained, not deleted: art_registry.py registers both under
# fn.card.<kind>.render.foundry as provisional, reversible vocabulary. This
# module imports nothing from its studio's families.py, so it is a byte-for-byte
# copy with only this header added.
"""Foundry studio - card renderers built like a press sheet.

The card is a proof pulled off the shop floor: warm paper stock, crop marks in
the corners, a spot-ink rule under the job line, a tint step wedge along the
bottom edge and a registration target where the pressman would sign it off. The
disc art drops into a keylined well the way artwork drops into an imposition.

    render_single(card: dict, art: dict[str, str], width: int) -> str
    render_battle(card: dict, art: dict[str, str], width: int) -> str

`card` is exactly what card_composition.compose() puts in cards['single'] /
cards['battle']; `art` maps presentationId -> a full art SVG document. Art is
inlined into a <g transform> copy of the source document's own elements, with
every id namespaced, so two arts can share one card without their clip paths or
gradients colliding - and so no host stylesheet that sizes `svg` elements can
resize the artwork. No data: URIs, no external fonts, no <image>. Same inputs
always produce byte-identical output.
"""
from __future__ import annotations

import html
import re
from typing import Any

# ---- press stock ---------------------------------------------------------- #
PAPER = "#f4f1e6"
PAPER_EDGE = "#e2dcc8"
INK = "#191821"
RULE = "#c6bfa8"
SANS = "sans-serif"
SERIF = "serif"

FLIGHT_KEYS = (("flight1", "SPEED"), ("flight2", "GLIDE"), ("flight3", "TURN"), ("flight4", "FADE"))

# Natural design units per (kind, layout). `width` just scales these.
GEOMETRY = {
    ("single", "standard"): (400, 176),
    ("single", "gallery"): (320, 404),
    ("battle", "standard"): (700, 300),
    ("battle", "stacked"): (420, 452),
}

_HEX = re.compile(r"^#[0-9a-fA-F]{3,8}$")
_ID = re.compile(r'\bid="([^"]+)"')
_URLREF = re.compile(r"url\(#([^)]+)\)")
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_VIEWBOX = re.compile(r'viewBox="([^"]+)"')
_TITLE = re.compile(r"<title>.*?</title>", re.IGNORECASE | re.DOTALL)


# --------------------------------------------------------------------------- #
# small primitives
# --------------------------------------------------------------------------- #

def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _spot(value: Any, fallback: str = "#7a3b1e") -> str:
    text = value if isinstance(value, str) else ""
    return text if _HEX.fullmatch(text) else fallback


def _number(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return "-"
    if isinstance(value, (int, float)):
        return str(int(value)) if float(value).is_integer() else f"{float(value):g}"
    text = str(value).strip()
    return text or "-"


def _fit(size: float, text: str, max_width: float, per_char: float = 0.58) -> float:
    length = max(len(text), 1)
    return round(min(size, max_width / (length * per_char)), 2)


def _text(x: float, y: float, content: str, size: float, *, fill: str = INK,
          font: str = SANS, weight: int = 400, anchor: str = "start",
          spacing: float = 0.0, opacity: float | None = None) -> str:
    bits = [f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size:g}"',
            f' fill="{fill}"']
    if weight != 400:
        bits.append(f' font-weight="{weight}"')
    if anchor != "start":
        bits.append(f' text-anchor="{anchor}"')
    if spacing:
        bits.append(f' letter-spacing="{spacing:g}"')
    if opacity is not None:
        bits.append(f' opacity="{opacity:g}"')
    bits.append(f">{content}</text>")
    return "".join(bits)


def _caps(x: float, y: float, content: str, size: float, *, fill: str = INK,
          anchor: str = "start", opacity: float = 0.62, spacing: float = 1.4) -> str:
    """Small letter-spaced caps - the shop's own labelling voice."""
    return _text(x, y, content, size, fill=fill, anchor=anchor, spacing=spacing,
                 opacity=opacity, weight=700)


def _crop_marks(w: float, h: float, inset: float = 9.0, arm: float = 13.0) -> str:
    out = ['<g id="crop" stroke="' + INK + '" stroke-width="1" opacity=".5" fill="none">']
    for cx, sx in ((inset, 1), (w - inset, -1)):
        for cy, sy in ((inset, 1), (h - inset, -1)):
            out.append(f'<path d="M{cx + sx * arm:.1f} {cy:.1f} L{cx:.1f} {cy:.1f}'
                       f' L{cx:.1f} {cy + sy * arm:.1f}"/>')
    out.append("</g>")
    return "".join(out)


def _register(cx: float, cy: float, r: float, spot: str) -> str:
    return (f'<g id="reg-{int(cx)}-{int(cy)}">'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{PAPER}"'
            f' stroke="{INK}" stroke-width="1.3" opacity=".85"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.42:.1f}" fill="{spot}"/>'
            f'<path d="M{cx - r * 1.5:.1f} {cy:.1f} H{cx + r * 1.5:.1f}'
            f' M{cx:.1f} {cy - r * 1.5:.1f} V{cy + r * 1.5:.1f}"'
            f' stroke="{INK}" stroke-width="1.1" opacity=".7"/></g>')


def _wedge(x: float, y: float, cell_w: float, cell_h: float, spot: str, steps: int = 6,
           ident: str = "wedge") -> str:
    out = [f'<g id="{ident}">']
    for i in range(steps):
        opacity = 1.0 - i * (0.92 / max(steps - 1, 1))
        out.append(f'<rect x="{x + i * cell_w:.1f}" y="{y:.1f}" width="{cell_w - 1:.1f}"'
                   f' height="{cell_h:.1f}" fill="{spot}" opacity="{opacity:.2f}"/>')
    out.append("</g>")
    return "".join(out)


# --------------------------------------------------------------------------- #
# art embedding
# --------------------------------------------------------------------------- #

def _namespace(markup: str, prefix: str) -> str:
    def rename_id(match: re.Match[str]) -> str:
        return f'id="{prefix}-{match.group(1)}"'

    def rename_ref(match: re.Match[str]) -> str:
        return f"url(#{prefix}-{match.group(1)})"

    return _URLREF.sub(rename_ref, _ID.sub(rename_id, markup))


def _art_element(art_svg: str, prefix: str, x: float, y: float, size: float) -> str:
    """Inline a full art SVG's contents into a <g>, fitted to (x, y, size, size).

    A transform, not a nested <svg>: a host stylesheet that sizes `svg` elements
    (the tournament rasteriser ships one) would otherwise blow the nested art up
    to the whole page. A <g> has no such attack surface, and the art's own disc
    clipPath still does the clipping.
    """
    open_tag = _SVG_OPEN.search(art_svg)
    if not open_tag:
        return ""
    inner = art_svg[open_tag.end():]
    end = inner.rfind("</svg>")
    if end != -1:
        inner = inner[:end]
    inner = _TITLE.sub("", inner).strip()
    box = _VIEWBOX.search(open_tag.group(0))
    try:
        vx, vy, vw, vh = (float(part) for part in (box.group(1) if box else "0 0 512 512").split())
    except (AttributeError, ValueError):
        vx, vy, vw, vh = 0.0, 0.0, 512.0, 512.0
    if vw <= 0 or vh <= 0:
        vw, vh = 512.0, 512.0
    scale = min(size / vw, size / vh)
    ox = x + (size - vw * scale) / 2.0 - vx * scale
    oy = y + (size - vh * scale) / 2.0 - vy * scale
    return (f'<g transform="translate({ox:.3f} {oy:.3f}) scale({scale:.5f})">'
            f'{_namespace(inner, prefix)}</g>')


def _art_well(participant: dict, art: dict[str, str], prefix: str,
              x: float, y: float, size: float, spot: str) -> str:
    """Keylined well with the art dropped in, or an empty plate if there is none."""
    out = [f'<g id="well-{prefix}">',
           f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="{size + 8:.1f}"'
           f' height="{size + 8:.1f}" fill="#ffffff" opacity=".55"/>',
           f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="{size + 8:.1f}"'
           f' height="{size + 8:.1f}" fill="none" stroke="{RULE}" stroke-width="1"/>']
    markup = art.get(participant.get("presentationId", "")) if isinstance(art, dict) else None
    if isinstance(markup, str) and markup.strip():
        out.append(_art_element(markup, prefix, x, y, size))
    else:
        out.append(f'<circle cx="{x + size / 2:.1f}" cy="{y + size / 2:.1f}"'
                   f' r="{size * 0.42:.1f}" fill="none" stroke="{spot}"'
                   f' stroke-width="2" stroke-dasharray="6 5" opacity=".8"/>')
        out.append(_caps(x + size / 2, y + size / 2 + 4, "NO PLATE", max(7.0, size * 0.075),
                         anchor="middle", opacity=0.55))
    out.append("</g>")
    return "".join(out)


# --------------------------------------------------------------------------- #
# participant copy
# --------------------------------------------------------------------------- #

def _job_line(participant: dict) -> str:
    pid = str(participant.get("presentationId", "") or "unset").upper()
    return f"JOB {pid}"


def _maker_line(participant: dict) -> str:
    parts = [str(participant.get("manufacturer", "") or "").strip(),
             str(participant.get("mold", "") or "").strip()]
    parts = [p for p in parts if p]
    variant = str(participant.get("variant", "") or "").strip()
    if variant:
        parts.append(variant)
    if parts:
        return " / ".join(parts).upper()
    note = str(participant.get("note", "") or "").strip()
    return (note.upper() if note else "UNSPECIFIED MOLD")


def _flight_cells(participant: dict, x: float, y: float, cell_w: float, cell_h: float,
                  spot: str, *, columns: int = 4, gap: float = 4.0,
                  ident: str = "flight") -> str:
    values = participant.get("flightValues") or {}
    if not isinstance(values, dict):
        values = {}
    out = [f'<g id="{ident}">']
    for index, (key, label) in enumerate(FLIGHT_KEYS):
        col, row = index % columns, index // columns
        cx = x + col * (cell_w + gap)
        cy = y + row * (cell_h + gap)
        value = _number(values.get(key))
        out.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w:.1f}"'
                   f' height="{cell_h:.1f}" fill="{INK}" opacity=".055"/>')
        out.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w:.1f}"'
                   f' height="{max(2.0, cell_h * 0.055):.1f}" fill="{spot}"/>')
        size = _fit(min(cell_h * 0.5, cell_w * 0.62), value, cell_w * 0.82, 0.62)
        label_size = round(max(5.5, min(cell_h * 0.16, cell_w * 0.2)), 2)
        out.append(_text(cx + cell_w / 2, cy + cell_h * 0.62, _esc(value), size,
                         font=SANS, weight=700, anchor="middle"))
        out.append(_caps(cx + cell_w / 2, cy + cell_h * 0.86,
                         label, label_size, anchor="middle",
                         opacity=0.6, spacing=round(label_size * 0.13, 2)))
    out.append("</g>")
    return "".join(out)


def _score_value(card: dict, index: int, pid: str) -> str:
    scores = card.get("scores")
    if isinstance(scores, dict):
        for key in (pid, str(index)):
            if key in scores:
                return _number(scores[key])
    elif isinstance(scores, list) and index < len(scores):
        entry = scores[index]
        if isinstance(entry, dict):
            return _number(entry.get("score", entry.get("value")))
        return _number(entry)
    return "-"


def _is_winner(card: dict, index: int, pid: str) -> bool:
    for field in ("winner", "manualWinner", "highlight"):
        value = card.get(field)
        if isinstance(value, str) and value and value == pid:
            return True
        if isinstance(value, bool):
            continue
        if isinstance(value, int) and value == index:
            return True
    return False


def _score_block(card: dict, index: int, pid: str, x: float, y: float,
                 w: float, h: float, spot: str) -> str:
    value = _score_value(card, index, pid)
    won = _is_winner(card, index, pid)
    out = ['<g id="score-' + _esc(pid) + '">',
           f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
           f' fill="{INK}"/>',
           f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}"'
           f' height="{max(3.0, h * 0.07):.1f}" fill="{spot}"/>']
    size = _fit(h * 0.52, value, w * 0.74, 0.62)
    out.append(_text(x + w / 2, y + h * 0.68, _esc(value), size, fill=PAPER,
                     font=SANS, weight=700, anchor="middle"))
    out.append(_caps(x + w / 2, y + h * 0.9, "SCORE", max(6.0, h * 0.115),
                     fill=PAPER, anchor="middle", opacity=0.7))
    if won:
        out.append(f'<rect x="{x - 3:.1f}" y="{y - 3:.1f}" width="{w + 6:.1f}"'
                   f' height="{h + 6:.1f}" fill="none" stroke="{spot}" stroke-width="3"/>')
    out.append("</g>")
    return "".join(out)


# --------------------------------------------------------------------------- #
# document shell
# --------------------------------------------------------------------------- #

def _document(body: str, natural_w: float, natural_h: float, width: int, label: str) -> str:
    render_w = max(1, int(width))
    render_h = max(1, round(render_w * natural_h / natural_w))
    safe = _esc(label)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{render_w}" height="{render_h}"'
        f' viewBox="0 0 {natural_w:g} {natural_h:g}" role="img" aria-label="{safe}">\n'
        f'<rect width="{natural_w:g}" height="{natural_h:g}" fill="{PAPER}"/>\n'
        f'<rect x="0.5" y="0.5" width="{natural_w - 1:g}" height="{natural_h - 1:g}"'
        f' fill="none" stroke="{PAPER_EDGE}" stroke-width="1"/>\n'
        f'{body}\n<title>{safe}</title>\n</svg>\n'
    )


def _participants(card: dict, wanted: int) -> list[dict]:
    people = card.get("participants")
    if not isinstance(people, list):
        people = []
    people = [p for p in people if isinstance(p, dict)][:wanted]
    while len(people) < wanted:
        people.append({"presentationId": f"slot{len(people) + 1}", "name": "Empty slot"})
    return people


def _layout(card: dict, kind: str) -> str:
    valid = {"single": ("standard", "gallery"), "battle": ("standard", "stacked")}[kind]
    layout = card.get("layout", "standard")
    return layout if layout in valid else "standard"


# --------------------------------------------------------------------------- #
# single card
# --------------------------------------------------------------------------- #

def render_single(card: dict, art: dict[str, str], width: int) -> str:
    """Render cards['single'] as a one-up press proof."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    layout = _layout(card, "single")
    details = bool(card.get("details", True))
    person = _participants(card, 1)[0]
    spot = _spot(person.get("color"))
    name = str(person.get("name", "") or "Untitled disc")
    w, h = GEOMETRY[("single", layout)]
    body = [_crop_marks(w, h)]

    if layout == "gallery":
        # Portrait: art on the sheet, copy stacked underneath, wedge between.
        body.append(_caps(20, 30, _job_line(person), 9.5, opacity=0.6))
        body.append(_caps(300, 30, f"SPOT {spot.upper()}", 7.5, anchor="end", opacity=0.42))
        body.append(f'<rect x="20" y="36" width="280" height="3" fill="{spot}"/>')
        body.append(_art_well(person, art, "p0", 48, 50, 224, spot))
        body.append(_wedge(20, 288, 35, 8, spot, steps=7))
        body.append(_register(290, 292, 7, spot))
        size = _fit(34, name, 268, 0.55)
        body.append(_text(160, 328, _esc(name), size, font=SERIF, weight=700, anchor="middle"))
        if details:
            body.append(_caps(160, 346, _maker_line(person), 10, anchor="middle", opacity=0.66))
            body.append(_flight_cells(person, 18, 354, 68, 46, spot))
        else:
            body.append(_caps(160, 346, "NO DETAILS", 10, anchor="middle", opacity=0.42))
    else:
        # Landscape lower-third: art well left, copy block right.
        body.append(_art_well(person, art, "p0", 20, 26, 124, spot))
        body.append(_wedge(20, 160, 16.5, 8, spot, steps=8))
        body.append(_caps(164, 32, _job_line(person), 9, opacity=0.6))
        body.append(_caps(382, 32, f"SPOT {spot.upper()}", 7.5, anchor="end", opacity=0.42))
        body.append(f'<rect x="164" y="38" width="218" height="3" fill="{spot}"/>')
        size = _fit(31, name, 216, 0.55)
        body.append(_text(164, 70, _esc(name), size, font=SERIF, weight=700))
        if details:
            body.append(_caps(164, 88, _maker_line(person), 9.5, opacity=0.66))
            body.append(_flight_cells(person, 164, 98, 51, 52, spot))
        else:
            body.append(_caps(164, 88, "NO DETAILS", 9.5, opacity=0.42))
        body.append(_register(370, 163, 8, spot))

    return _document("\n".join(body), w, h, width, f"{name} card")


# --------------------------------------------------------------------------- #
# battle card
# --------------------------------------------------------------------------- #

# Per-battle-layout panel geometry, all offsets relative to the panel origin.
# Bands never overlap: header / art row (art | flights | score) / wedge.
PANEL_BANDS = {
    "standard": {"size": (300.0, 234.0), "name": (58.0, 27.0), "maker": 74.0,
                 "art": (14.0, 86.0, 118.0), "flights": (146.0, 156.0, 31.5, 44.0, 4),
                 "score": (152.0, 86.0, 132.0, 62.0),
                 "score_lean": (152.0, 86.0, 132.0, 62.0), "wedge": 218.0},
    "stacked": {"size": (384.0, 186.0), "name": (50.0, 24.0), "maker": 66.0,
                "art": (14.0, 74.0, 96.0), "flights": (124.0, 74.0, 39.0, 60.0, 4),
                "score": (306.0, 74.0, 64.0, 60.0),
                "score_lean": (124.0, 74.0, 246.0, 60.0), "wedge": 150.0},
}


def _battle_panel(card: dict, person: dict, index: int, art: dict[str, str],
                  x: float, y: float, layout: str, details: bool) -> str:
    band = PANEL_BANDS[layout]
    w, h = band["size"]
    spot = _spot(person.get("color"))
    pid = str(person.get("presentationId", f"slot{index}"))
    name = str(person.get("name", "") or "Untitled disc")
    won = _is_winner(card, index, pid)
    out = [f'<g id="panel{index}">',
           f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
           f' fill="#ffffff" opacity=".45"/>',
           f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
           f' fill="none" stroke="{spot if won else RULE}"'
           f' stroke-width="{3 if won else 1}"/>']
    out.append(_caps(x + 14, y + 18, _job_line(person), 9, opacity=0.6))
    out.append(f'<rect x="{x + 14:.1f}" y="{y + 24:.1f}" width="{w - 28:.1f}"'
               f' height="3" fill="{spot}"/>')
    name_y, name_size = band["name"]
    out.append(_text(x + 14, y + name_y, _esc(name), _fit(name_size, name, w - 96, 0.55),
                     font=SERIF, weight=700))
    if details:
        out.append(_caps(x + 14, y + band["maker"], _maker_line(person), 9.5, opacity=0.66))
    ax, ay, asize = band["art"]
    out.append(_art_well(person, art, f"p{index}", x + ax, y + ay, asize, spot))
    if details:
        fx, fy, fw, fh, cols = band["flights"]
        out.append(_flight_cells(person, x + fx, y + fy, fw, fh, spot, columns=cols,
                                 ident=f"flight{index}"))
    sx, sy, sw, sh = band["score"] if details else band["score_lean"]
    out.append(_score_block(card, index, pid, x + sx, y + sy, sw, sh, spot))
    if won:
        out.append(_caps(x + w - 14, y + 18, "WINNER", 9, fill=spot, anchor="end", opacity=1.0))
    wedge_x = x + band["flights"][0]
    wedge_span = (x + w - 14) - wedge_x
    out.append(_wedge(wedge_x, y + band["wedge"], wedge_span / 8, 7, spot, steps=8,
                      ident=f"wedge{index}"))
    out.append("</g>")
    return "".join(out)


def _versus(cx: float, cy: float, spot: str, vertical: bool, span: float) -> str:
    if vertical:
        line = f'M{cx:.1f} {cy - span:.1f} V{cy + span:.1f}'
    else:
        line = f'M{cx - span:.1f} {cy:.1f} H{cx + span:.1f}'
    return (f'<g id="versus"><path d="{line}" stroke="{INK}" stroke-width="1"'
            f' stroke-dasharray="5 6" opacity=".45" fill="none"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="19" fill="{PAPER}"'
            f' stroke="{INK}" stroke-width="1.4"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="13" fill="none" stroke="{spot}"'
            f' stroke-width="2.4"/>'
            + _text(cx, cy + 5, "VS", 14, font=SANS, weight=700, anchor="middle") + '</g>')


def render_battle(card: dict, art: dict[str, str], width: int) -> str:
    """Render cards['battle'] as a two-up press proof with score slots."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    layout = _layout(card, "battle")
    details = bool(card.get("details", True))
    people = _participants(card, 2)
    spot = _spot(people[0].get("color"))
    w, h = GEOMETRY[("battle", layout)]
    body = [_crop_marks(w, h)]
    title = str(card.get("title", "") or "").strip()

    if layout == "stacked":
        body.append(_battle_panel(card, people[0], 0, art, 18, 24, "stacked", details))
        body.append(_battle_panel(card, people[1], 1, art, 18, 242, "stacked", details))
        body.append(_versus(210, 226, spot, False, 168))
        body.append(_caps(18, 444, title.upper() if title else "BATTLE PROOF", 9, opacity=0.5))
        body.append(_register(392, 440, 8, spot))
    else:
        body.append(_battle_panel(card, people[0], 0, art, 18, 26, "standard", details))
        body.append(_battle_panel(card, people[1], 1, art, 382, 26, "standard", details))
        body.append(_versus(350, 143, spot, True, 112))
        body.append(_caps(18, 288, title.upper() if title else "BATTLE PROOF", 9, opacity=0.5))
        body.append(_register(672, 283, 8, spot))

    names = " vs ".join(str(p.get("name", "") or "Untitled disc") for p in people)
    return _document("\n".join(body), w, h, width, f"{names} battle card")


CALCULATIONS = {
    "fn.card.single.render": render_single,
    "fn.card.battle.render": render_battle,
}
