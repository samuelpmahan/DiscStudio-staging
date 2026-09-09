#!/usr/bin/env python3
"""Studio *signal* card renderers: the disc card as broadcast furniture.

    render_single(card, art, width) -> str
    render_battle(card, art, width) -> str

`card` is the JSON card_composition.compose() puts at cards['single'] or
cards['battle']; `art` maps presentationId -> a full disc-art SVG document
(any family, any target). Art is inlined under a placed <g> whose ids are
namespaced per participant, so two discs on one plate never collide, and no
nested viewport, data: URI, external href or webfont is used anywhere.

The plate is a live-sports lower third: a dark bed, an accent hairline along
the top, an eyebrow in letterspaced caps, one heavy name, a strip of flight
cells (SPEED GLIDE TURN FADE) and -- for a battle -- a single scoreboard block
whose leading half fills with that disc's colour. That fill is the moment the
whole studio is built around: at any width the eye lands on the score first,
the two discs second, everything else third.

Layouts honoured: single standard|gallery, battle standard|stacked. With
`details` False the eyebrow, note and flight cells drop out, the art grows and
the name and score carry the card alone.
"""
from __future__ import annotations

import html
import re

try:
    from families import contrast_ink, mix
except ImportError:  # pragma: no cover - package-style import
    from .families import contrast_ink, mix  # type: ignore

BED = "#0a0e13"
PANEL = "#151d27"
RULE = "#2d3c4d"
TEXT = "#f4f7fa"
MUTED = "#93a5b8"
FALLBACK_ACCENT = "#b9d789"

HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
FLIGHTS = (("flight1", "SPEED"), ("flight2", "GLIDE"), ("flight3", "TURN"), ("flight4", "FADE"))

_ROOT = re.compile(r"\A\s*(?:<\?xml[^>]*\?>\s*)?<svg\b([^>]*)>", re.S)
_VIEWBOX = re.compile(r'viewBox="([^"]*)"')
_TITLE = re.compile(r"<title>.*?</title>", re.S)
_ID = re.compile(r'\bid="([^"]+)"')


# --------------------------------------------------------------- plumbing ---

def _f(value: float) -> str:
    text = "{:.2f}".format(float(value))
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _accent(participant: dict) -> str:
    value = participant.get("color")
    if isinstance(value, str) and HEX.fullmatch(value.strip()):
        return value.strip().lower()
    return FALLBACK_ACCENT


def _fit(text: str, max_w: float, size: float, ratio: float = 0.60, floor: float = 6.0) -> float:
    n = len(text)
    if n <= 0:
        return size
    return round(max(floor, min(size, max_w / (n * ratio))), 1)


def _number(value: object) -> str:
    if isinstance(value, bool) or value is None or value == "":
        return "–"
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value))
        return ("{:.1f}".format(float(value))).rstrip("0").rstrip(".")
    return _esc(value)[:4]


def _eyebrow(participant: dict) -> str:
    parts = [str(participant.get(key, "") or "").strip()
             for key in ("manufacturer", "mold", "variant")]
    parts = [p for p in parts if p]
    if not parts:
        physical = str(participant.get("physicalDiscId", "") or "").strip()
        parts = [physical] if physical else ["UNCATALOGUED"]
    return " · ".join(parts).upper()


def _art_svg(art_text: str, prefix: str, x: float, y: float, size: float) -> str:
    """Inline a disc-art document as a placed <g>, with its ids namespaced.

    The art's own elements are copied in and put under one translate/scale, so
    the card carries no nested <svg> viewport: a host stylesheet that sizes
    `svg { width: ... }` cannot resize the disc out of its slot, and there is
    no data: URI or external reference anywhere in the result.
    """
    match = _ROOT.search(art_text or "")
    if not match:
        return ""
    viewbox = _VIEWBOX.search(match.group(1))
    numbers = [float(v) for v in re.split(r"[\s,]+", (viewbox.group(1) if viewbox else "").strip())
               if v] if viewbox else []
    if len(numbers) != 4 or numbers[2] <= 0 or numbers[3] <= 0:
        numbers = [0.0, 0.0, 512.0, 512.0]
    min_x, min_y, box_w, box_h = numbers
    inner = art_text[match.end():art_text.rindex("</svg>")]
    inner = _TITLE.sub("", inner)
    for ident in sorted(set(_ID.findall(inner)), key=len, reverse=True):
        inner = inner.replace('id="{}"'.format(ident), 'id="{}{}"'.format(prefix, ident))
        inner = inner.replace("url(#{})".format(ident), "url(#{}{})".format(prefix, ident))
        inner = inner.replace('href="#{}"'.format(ident), 'href="#{}{}"'.format(prefix, ident))
    scale = size / max(box_w, box_h)
    tx = x + (size - box_w * scale) / 2.0 - min_x * scale
    ty = y + (size - box_h * scale) / 2.0 - min_y * scale
    return '<g transform="translate({tx} {ty}) scale({s})">{inner}</g>'.format(
        tx=_f(tx), ty=_f(ty), s=_f(round(scale, 6)), inner=inner.strip())


def _art_or_stub(art: dict, participant: dict, prefix: str, x: float, y: float,
                 size: float, accent: str) -> str:
    key = str(participant.get("presentationId", ""))
    text = (art or {}).get(key)
    if text:
        return _art_svg(text, prefix, x, y, size)
    initial = _esc((str(participant.get("name", "")) or "?").strip()[:1].upper() or "?")
    return (
        '<g><circle cx="{cx}" cy="{cy}" r="{r}" fill="{p}" stroke="{a}" stroke-width="{w}"/>'
        '<text x="{cx}" y="{ty}" text-anchor="middle" font-family="sans-serif" '
        'font-size="{fs}" font-weight="700" fill="{a}">{i}</text></g>'
    ).format(cx=_f(x + size / 2), cy=_f(y + size / 2), r=_f(size / 2 - 2), p=PANEL, a=accent,
             w=_f(max(1.5, size * 0.03)), ty=_f(y + size / 2 + size * 0.17),
             fs=_f(size * 0.46), i=initial)


def _caps(x: float, y: float, text: str, size: float, fill: str = MUTED,
          anchor: str = "start", spacing: float = 1.4, weight: int = 600) -> str:
    return ('<text x="{x}" y="{y}" text-anchor="{an}" font-family="sans-serif" font-size="{s}" '
            'font-weight="{w}" letter-spacing="{ls}" fill="{f}">{t}</text>').format(
                x=_f(x), y=_f(y), an=anchor, s=_f(size), w=weight, ls=_f(spacing), f=fill,
                t=_esc(text))


def _heavy(x: float, y: float, text: str, size: float, fill: str = TEXT,
           anchor: str = "start") -> str:
    return ('<text x="{x}" y="{y}" text-anchor="{an}" font-family="sans-serif" font-size="{s}" '
            'font-weight="800" fill="{f}">{t}</text>').format(
                x=_f(x), y=_f(y), an=anchor, s=_f(size), f=fill, t=_esc(text))


def _chevrons(x: float, y: float, height: float, accent: str, count: int = 3,
              pitch: float = 9.0, weight: float = 4.0, flip: bool = False) -> str:
    out = []
    for i in range(count):
        cx = x + i * pitch
        nose = height * 0.5
        x0, x1 = (cx + nose, cx) if flip else (cx, cx + nose)
        out.append(
            '<path d="M{x0} {y0} L{x1} {ym} L{x0} {y1}" fill="none" stroke="{a}" '
            'stroke-width="{w}" opacity="{o:.2f}"/>'.format(
                x0=_f(x0), x1=_f(x1), y0=_f(y - height / 2), ym=_f(y), y1=_f(y + height / 2),
                a=accent, w=_f(weight), o=0.35 + 0.32 * i))
    return "".join(out)


def _flight_cells(x: float, y: float, width: float, height: float, participant: dict,
                  accent: str, gap: float = 4.0, anchor_labels: bool = True) -> str:
    values = participant.get("flightValues") or {}
    cell = (width - gap * 3) / 4.0
    num_size = min(height * 0.52, cell * 0.62)
    lab_size = max(6.0, min(height * 0.2, cell * 0.235))
    out = ['<g>']
    for i, (key, label) in enumerate(FLIGHTS):
        cx = x + i * (cell + gap)
        out.append('<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{p}" '
                   'stroke="{r}" stroke-width="1"/>'.format(
                       x=_f(cx), y=_f(y), w=_f(cell), h=_f(height), p=PANEL, r=RULE))
        out.append('<rect x="{x}" y="{y}" width="{w}" height="{t}" fill="{a}" opacity=".85"/>'.format(
            x=_f(cx), y=_f(y), w=_f(cell), t=_f(max(2.0, height * 0.055)), a=accent))
        out.append(_heavy(cx + cell / 2, y + height * 0.66, _number(values.get(key)),
                          num_size, TEXT, "middle"))
        if anchor_labels:
            out.append(_caps(cx + cell / 2, y + height * 0.92, label, lab_size, MUTED,
                             "middle", spacing=max(0.4, lab_size * 0.09)))
    out.append('</g>')
    return "".join(out)


def _document(width: int, design_w: float, design_h: float, aria: str, body: str) -> str:
    px_w = max(1, int(round(width)))
    px_h = max(1, int(round(px_w * design_h / design_w)))
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {dw} {dh}" '
        'role="img" aria-label="{a}">'.format(w=px_w, h=px_h, dw=_f(design_w), dh=_f(design_h),
                                              a=_esc(aria)),
        body,
        '<title>{}</title>'.format(_esc(aria)),
        '</svg>',
    ]) + "\n"


def _bed(design_w: float, design_h: float, accent: str, second: str | None = None) -> str:
    out = ['<rect x="0" y="0" width="{w}" height="{h}" rx="10" fill="{b}"/>'.format(
        w=_f(design_w), h=_f(design_h), b=BED),
        '<rect x="0.75" y="0.75" width="{w}" height="{h}" rx="9.5" fill="none" stroke="{r}" '
        'stroke-width="1.5"/>'.format(w=_f(design_w - 1.5), h=_f(design_h - 1.5), r=RULE)]
    if second is None:
        out.append('<rect x="0" y="0" width="{w}" height="5" fill="{a}"/>'.format(
            w=_f(design_w), a=accent))
    else:
        out.append('<rect x="0" y="0" width="{w}" height="5" fill="{a}"/>'.format(
            w=_f(design_w / 2), a=accent))
        out.append('<rect x="{x}" y="0" width="{w}" height="5" fill="{a}"/>'.format(
            x=_f(design_w / 2), w=_f(design_w / 2), a=second))
    return "".join(out)


# ------------------------------------------------------------- scores etc ---

def _scores(card: dict, participants: list[dict]) -> list[object]:
    raw = card.get("scores")
    out: list[object] = []
    for index, participant in enumerate(participants):
        key = str(participant.get("presentationId", ""))
        value = None
        if isinstance(raw, dict):
            if key in raw:
                value = raw[key]
            elif str(index) in raw:
                value = raw[str(index)]
        elif isinstance(raw, list) and index < len(raw):
            value = raw[index]
        if value is None:
            value = participant.get("score")
        out.append(value)
    return out


def _leader(scores: list[object]) -> int | None:
    numeric = []
    for value in scores:
        numeric.append(float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None)
    if len(numeric) != 2 or numeric[0] is None or numeric[1] is None or numeric[0] == numeric[1]:
        return None
    return 0 if numeric[0] > numeric[1] else 1


def _flagged(card: dict, participants: list[dict], field: str) -> int | None:
    value = card.get(field)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if 0 <= value < len(participants) else None
    if isinstance(value, str):
        for index, participant in enumerate(participants):
            if str(participant.get("presentationId", "")) == value:
                return index
        return None
    if isinstance(value, dict):
        for index, participant in enumerate(participants):
            if value.get(str(participant.get("presentationId", ""))):
                return index
    return None


def _name(participant: dict) -> str:
    return (str(participant.get("name", "") or "").strip()
            or str(participant.get("mold", "") or "").strip()
            or "UNNAMED DISC")


def _note(participant: dict) -> str:
    return str(participant.get("note", "") or "").strip()


# ------------------------------------------------------------ single card ---

def _single_standard(card: dict, art: dict, participant: dict, details: bool) -> tuple[float, float, str]:
    W, H = 400.0, 174.0
    accent = _accent(participant)
    name = _name(participant)
    body = [_bed(W, H, accent)]
    body.append('<rect x="0" y="{y}" width="{w}" height="3" fill="{a}" opacity=".45"/>'.format(
        y=_f(H - 3), w=_f(W), a=accent))
    if details:
        body.append(_art_or_stub(art, participant, "a0-", 14, 30, 112, accent))
        body.append(_caps(140, 26, _eyebrow(participant), 10.5, MUTED, spacing=1.8))
        body.append(_heavy(140, 60, name, _fit(name, 178, 27), TEXT))
        note = _note(participant)
        if note:
            body.append(_caps(140, 78, note.upper(), 9.5, mix(MUTED, BED, 0.1), spacing=1.2,
                              weight=500))
        body.append(_flight_cells(140, 96, 190, 62, participant, accent))
        body.append(_chevrons(348, 127, 42, accent, count=3, pitch=13, weight=5))
        body.append(_caps(W - 14, 26, "SINGLE", 10, mix(MUTED, BED, 0.15), "end", spacing=2.2))
    else:
        body.append(_art_or_stub(art, participant, "a0-", 18, 24, 126, accent))
        body.append(_heavy(158, 92, name, _fit(name, 214, 34), TEXT))
        body.append(_chevrons(158, 116, 26, accent, count=4, pitch=11, weight=4.5))
    return W, H, "".join(body)


def _single_gallery(card: dict, art: dict, participant: dict, details: bool) -> tuple[float, float, str]:
    W, H = 320.0, 402.0
    accent = _accent(participant)
    name = _name(participant)
    body = [_bed(W, H, accent)]
    if details:
        body.append('<rect x="20" y="20" width="280" height="212" rx="8" fill="{p}"/>'.format(p=PANEL))
        body.append(_art_or_stub(art, participant, "a0-", 54, 20, 212, accent))
        body.append(_chevrons(26, 126, 30, accent, count=2, pitch=11, weight=4.5))
        body.append(_chevrons(268, 126, 30, accent, count=2, pitch=11, weight=4.5, flip=True))
        body.append('<rect x="20" y="236" width="280" height="3" fill="{a}"/>'.format(a=accent))
        body.append(_caps(24, 260, _eyebrow(participant), 11, MUTED, spacing=2.0))
        body.append(_heavy(24, 298, name, _fit(name, 272, 36), TEXT))
        note = _note(participant)
        if note:
            body.append(_caps(24, 320, note.upper(), 10.5, mix(MUTED, BED, 0.1), spacing=1.2,
                              weight=500))
        body.append(_flight_cells(20, 332, 280, 62, participant, accent))
    else:
        body.append(_art_or_stub(art, participant, "a0-", 40, 44, 240, accent))
        body.append('<rect x="40" y="300" width="240" height="4" fill="{a}"/>'.format(a=accent))
        body.append(_heavy(160, 348, name, _fit(name, 268, 40), TEXT, "middle"))
        body.append(_chevrons(134, 374, 22, accent, count=4, pitch=13, weight=5))
    return W, H, "".join(body)


def render_single(card: dict, art: dict[str, str], width: int) -> str:
    """Render cards['single'] as a broadcast plate. Layouts: standard, gallery."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    participants = list(card.get("participants") or [])
    if not participants:
        raise ValueError("single card needs one participant")
    participant = participants[0]
    details = bool(card.get("details", True))
    layout = card.get("layout", "standard")
    build = _single_gallery if layout == "gallery" else _single_standard
    design_w, design_h, body = build(card, art or {}, participant, details)
    aria = "{} — disc card".format(_name(participant))
    return _document(width, design_w, design_h, aria, body)


# ------------------------------------------------------------ battle card ---

def _score_block(x: float, y: float, w: float, h: float, scores: list[object],
                 accents: list[str], leader: int | None, vertical: bool) -> str:
    out = ['<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{p}"/>'.format(
        x=_f(x), y=_f(y), w=_f(w), h=_f(h), p=PANEL)]
    half_w = w / 2.0 if not vertical else w
    half_h = h if not vertical else h / 2.0
    for index in (0, 1):
        cx = x + (index * half_w if not vertical else 0)
        cy = y + (0 if not vertical else index * half_h)
        won = leader == index
        if won:
            out.append('<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{a}"/>'.format(
                x=_f(cx), y=_f(cy), w=_f(half_w), h=_f(half_h), a=accents[index]))
        ink = contrast_ink(accents[index], pivot=0.5) if won else (
            mix(TEXT, PANEL, 0.45) if leader is not None else TEXT)
        size = min(half_h * 0.62, half_w * 0.66)
        text = _number(scores[index])
        out.append(_heavy(cx + half_w / 2, cy + half_h * 0.5 + size * 0.36, text,
                          _fit(text, half_w * 0.82, size, ratio=0.62), ink, "middle"))
    if vertical:
        out.append('<rect x="{x}" y="{y}" width="{w}" height="2" fill="{r}"/>'.format(
            x=_f(x), y=_f(y + h / 2 - 1), w=_f(w), r=BED))
    else:
        out.append('<rect x="{x}" y="{y}" width="2" height="{h}" fill="{r}"/>'.format(
            x=_f(x + w / 2 - 1), y=_f(y), h=_f(h), r=BED))
    out.append('<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="{r}" '
               'stroke-width="1.5"/>'.format(x=_f(x), y=_f(y), w=_f(w), h=_f(h), r=RULE))
    return "".join(out)


def _vs_badge(cx: float, cy: float, size: float) -> str:
    return ('<g><rect x="{x}" y="{y}" width="{s}" height="{s}" rx="3" fill="{b}" stroke="{r}" '
            'stroke-width="1.5" transform="rotate(45 {cx} {cy})"/>'
            '<text x="{cx}" y="{ty}" text-anchor="middle" font-family="sans-serif" '
            'font-size="{fs}" font-weight="800" letter-spacing="0.6" fill="{t}">VS</text></g>').format(
                x=_f(cx - size / 2), y=_f(cy - size / 2), s=_f(size), b=BED, r=RULE,
                cx=_f(cx), cy=_f(cy), ty=_f(cy + size * 0.2), fs=_f(size * 0.46), t=TEXT)


def _battle_header(design_w: float, accents: list[str], participants: list[dict],
                   winner: int | None, leader: int | None) -> str:
    out = [_chevrons(14, 21, 20, accents[0], count=3, pitch=8, weight=3.5)]
    out.append(_caps(52, 26, "DISC BATTLE", 12, TEXT, spacing=3.2, weight=700))
    tag_index = winner if winner is not None else leader
    if tag_index is not None:
        who = _name(participants[tag_index]).upper()
        if len(who) > 14:
            who = who[:13].rstrip() + "\u2026"
        label = ("WINNER · " if winner is not None else "LEADING · ") + who
        spacing = 1.2
        size = _fit(label, design_w * 0.40, 10.5, ratio=0.70, floor=6.5)
        plate_w = len(label) * (size * 0.60 + spacing) + 20
        out.append('<rect x="{x}" y="9" width="{w}" height="23" rx="4" fill="{a}"/>'.format(
            x=_f(design_w - 14 - plate_w), w=_f(plate_w), a=accents[tag_index]))
        out.append(_caps(design_w - 14 - plate_w / 2 + spacing / 2, 25, label, size,
                         contrast_ink(accents[tag_index], pivot=0.5), "middle", spacing=spacing,
                         weight=700))
    else:
        out.append('<circle cx="{x}" cy="20.5" r="4.5" fill="{a}"/>'.format(
            x=_f(design_w - 62), a=accents[0]))
        out.append(_caps(design_w - 14, 25, "LIVE", 11, MUTED, "end", spacing=2.4))
    out.append('<rect x="0" y="41" width="{w}" height="1.5" fill="{r}"/>'.format(
        w=_f(design_w), r=RULE))
    return "".join(out)


def _battle_standard(card: dict, art: dict, participants: list[dict], details: bool,
                     scores: list[object], accents: list[str], winner: int | None,
                     highlight: int | None) -> tuple[float, float, str]:
    W, H = 660.0, 300.0
    leader = winner if winner is not None else _leader(scores)
    body = [_bed(W, H, accents[0], accents[1])]
    body.append(_battle_header(W, accents, participants, winner, _leader(scores)))
    art_size = 104.0 if details else 128.0
    art_y = 58.0 if details else 74.0
    for index, participant in enumerate(participants[:2]):
        accent = accents[index]
        mirrored = index == 1
        art_x = 16.0 if not mirrored else W - 16.0 - art_size
        body.append(_art_or_stub(art, participant, "a{}-".format(index), art_x, art_y,
                                 art_size, accent))
        text_x = (art_x + art_size + 16) if not mirrored else (art_x - 16)
        anchor = "start" if not mirrored else "end"
        name = _name(participant)
        if details:
            body.append(_caps(text_x, art_y + 22, _eyebrow(participant), 10.5, MUTED, anchor,
                              spacing=1.6))
            body.append(_heavy(text_x, art_y + 58, name, _fit(name, 104, 26), TEXT, anchor))
            note = _note(participant)
            if note:
                body.append(_caps(text_x, art_y + 78, note.upper(), 9.5,
                                  mix(MUTED, BED, 0.1), anchor, spacing=1.1, weight=500))
            cells_x = 16.0 if not mirrored else W - 16.0 - 244.0
            body.append(_flight_cells(cells_x, 196, 244, 62, participant, accent))
        else:
            body.append(_heavy(text_x, art_y + 74, name, _fit(name, 104, 30), TEXT, anchor))
            body.append(_caps(text_x, art_y + 96, _eyebrow(participant), 10.5, MUTED, anchor,
                              spacing=1.6))
        if highlight == index or winner == index:
            pad = 8.0
            body.append('<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" '
                        'stroke="{a}" stroke-width="2" opacity=".9"/>'.format(
                            x=_f(art_x - pad), y=_f(art_y - pad), w=_f(art_size + pad * 2),
                            h=_f(art_size + pad * 2), a=accent))
    body.append(_score_block(264, 52, 132, 120, scores, accents, leader, vertical=False))
    body.append(_vs_badge(330, 172, 26))
    body.append(_caps(330, 214, "SCORE", 9.5, MUTED, "middle", spacing=2.6))
    body.append('<rect x="16" y="{y}" width="{w}" height="4" fill="{a}" opacity=".75"/>'.format(
        y=_f(H - 20), w=_f(W / 2 - 16), a=accents[0]))
    body.append('<rect x="{x}" y="{y}" width="{w}" height="4" fill="{a}" opacity=".75"/>'.format(
        x=_f(W / 2), y=_f(H - 20), w=_f(W / 2 - 16), a=accents[1]))
    return W, H, "".join(body)


def _battle_stacked(card: dict, art: dict, participants: list[dict], details: bool,
                    scores: list[object], accents: list[str], winner: int | None,
                    highlight: int | None) -> tuple[float, float, str]:
    W, H = 440.0, 424.0
    leader = winner if winner is not None else _leader(scores)
    body = [_bed(W, H, accents[0], accents[1])]
    body.append(_battle_header(W, accents, participants, winner, _leader(scores)))
    rows = (52.0, 236.0)
    art_size = 92.0 if details else 108.0
    for index, participant in enumerate(participants[:2]):
        accent = accents[index]
        top = rows[index]
        body.append('<rect x="10" y="{y}" width="{w}" height="152" rx="8" fill="{p}" '
                    'opacity=".55"/>'.format(y=_f(top), w=_f(W - 20), p=PANEL))
        if winner == index or highlight == index:
            body.append('<rect x="10" y="{y}" width="{w}" height="152" rx="8" fill="none" '
                        'stroke="{a}" stroke-width="2.5"/>'.format(y=_f(top), w=_f(W - 20), a=accent))
        body.append('<rect x="10" y="{y}" width="5" height="152" fill="{a}"/>'.format(
            y=_f(top), a=accent))
        body.append(_art_or_stub(art, participant, "a{}-".format(index), 24, top + 12,
                                 art_size, accent))
        name = _name(participant)
        text_x = 24 + art_size + 14
        if details:
            body.append(_caps(text_x, top + 30, _eyebrow(participant), 10, MUTED, spacing=1.6))
            body.append(_heavy(text_x, top + 60, name, _fit(name, 158, 25), TEXT))
            body.append(_flight_cells(text_x, top + 76, 186, 60, participant, accent))
        else:
            body.append(_heavy(text_x, top + 74, name, _fit(name, 176, 30), TEXT))
            body.append(_caps(text_x, top + 96, _eyebrow(participant), 10, MUTED, spacing=1.6))
        won = leader == index
        plate_x, plate_y, plate_w, plate_h = W - 118.0, top + 20.0, 96.0, 112.0
        body.append('<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{f}" stroke="{s}" '
                    'stroke-width="1.5"/>'.format(x=_f(plate_x), y=_f(plate_y), w=_f(plate_w),
                                                  h=_f(plate_h), f=(accent if won else PANEL),
                                                  s=(accent if won else RULE)))
        ink = contrast_ink(accent, pivot=0.5) if won else (
            mix(TEXT, PANEL, 0.45) if leader is not None else TEXT)
        text = _number(scores[index])
        body.append(_heavy(plate_x + plate_w / 2, plate_y + plate_h * 0.72, text,
                           _fit(text, plate_w * 0.78, 62, ratio=0.62), ink, "middle"))
        body.append(_caps(plate_x + plate_w / 2, plate_y + plate_h * 0.9, "SCORE", 9,
                          mix(ink, accent if won else PANEL, 0.35), "middle", spacing=2.2))
    body.append('<rect x="10" y="{y}" width="{w}" height="1.5" fill="{r}"/>'.format(
        y=_f(rows[1] - 22), w=_f(W - 20), r=RULE))
    body.append(_vs_badge(W / 2, rows[1] - 21, 28))
    body.append('<rect x="10" y="{y}" width="{w}" height="4" fill="{a}" opacity=".75"/>'.format(
        y=_f(H - 16), w=_f(W / 2 - 10), a=accents[0]))
    body.append('<rect x="{x}" y="{y}" width="{w}" height="4" fill="{a}" opacity=".75"/>'.format(
        x=_f(W / 2), y=_f(H - 16), w=_f(W / 2 - 10), a=accents[1]))
    return W, H, "".join(body)


def render_battle(card: dict, art: dict[str, str], width: int) -> str:
    """Render cards['battle'] as a scoreboard. Layouts: standard, stacked."""
    if not isinstance(card, dict):
        raise ValueError("card object required")
    participants = list(card.get("participants") or [])
    if not participants:
        raise ValueError("battle card needs at least one participant")
    if len(participants) == 1:
        participants = participants + [{"presentationId": "—", "name": "AWAITING RIVAL",
                                        "color": FALLBACK_ACCENT, "flightValues": {}}]
    participants = participants[:2]
    details = bool(card.get("details", True))
    layout = card.get("layout", "standard")
    accents = [_accent(p) for p in participants]
    if accents[0] == accents[1]:
        accents[1] = mix(accents[1], TEXT, 0.34)
    scores = _scores(card, participants)
    winner = _flagged(card, participants, "winner")
    if winner is None:
        winner = _flagged(card, participants, "manualWinner")
    highlight = _flagged(card, participants, "highlight")
    build = _battle_stacked if layout == "stacked" else _battle_standard
    design_w, design_h, body = build(card, art or {}, participants, details, scores, accents,
                                     winner, highlight)
    aria = "Disc battle: {} versus {}".format(_name(participants[0]), _name(participants[1]))
    return _document(width, design_w, design_h, aria, body)


CALCULATIONS = {
    "fn.card.single.render": render_single,
    "fn.card.battle.render": render_battle,
}
