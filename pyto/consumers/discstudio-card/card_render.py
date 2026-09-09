#!/usr/bin/env python3
"""Promoted card renderers from the art tournament.

    render_single(card, art, width) -> str
    render_battle(card, art, width) -> str

`card` is the JSON ``card_composition.compose()`` puts at ``cards['single']``
or ``cards['battle']``; `art` maps ``presentationId`` -> a full disc-art SVG
document (any family, any target, e.g. ``paint_components.render(...)``). The
art is inlined as a ``<g>`` copy of the source document's own elements, with
every id namespaced per participant, so two discs on one battle plate cannot
collide. No data: URI, no external href, no webfont.

The two halves come from different studios -- the tournament scored the single
and the battle separately and they did not agree on a winner:

  * ``render_single`` -- studio *botanical* (tally 69/72, the tournament's
    highest-scoring item of any kind). A warm botanical plate: deckle ground,
    hairline double rule, engraved serif name, letterspaced maker/mold eyebrow,
    flight numbers set as a herbarium measurement strip.
  * ``render_battle`` -- studio *signal* (tally 66/72, tied with foundry on
    points and taken on the judges' stated reason: the score is the largest
    object on the plate, which is what a battle card is for). A broadcast lower
    third: dark bed, accent hairline, one heavy name per side, a scoreboard
    block whose leading half fills with that disc's colour.

Both honour ``card['layout']`` (single ``standard|gallery``, battle
``standard|stacked``) and ``card['details']``, and both print an explicit
"unrecorded" marker rather than promoting the note into the mold slot -- the
one defect the judges named by name in the runner-up single renderer.

The promoted code itself lives verbatim beside this module in
``_card_botanical.py`` and ``_card_signal.py`` so the tournament renders under
``experiments/art-tournament/renders/`` stay valid receipts for it. This module
is the seam: it is what the workshop registers and what callers import.

Known follow-up, recorded in RESULTS.md: a single plate and a battle plate now
speak two different visual languages. Unifying them is a design decision, not a
promotion decision, so it was left to a later pass rather than made here.
"""
from __future__ import annotations

import _card_botanical
import _card_signal

__all__ = ["render_single", "render_battle", "CALCULATIONS"]


def render_single(card: dict, art: dict[str, str], width: int) -> str:
    """Render a Single card. Deterministic: same inputs -> byte-identical SVG."""
    return _card_botanical.render_single(card, art, width)


def render_battle(card: dict, art: dict[str, str], width: int) -> str:
    """Render a Battle card. Deterministic: same inputs -> byte-identical SVG."""
    return _card_signal.render_battle(card, art, width)


CALCULATIONS = {
    "fn.card.single.render": render_single,
    "fn.card.battle.render": render_battle,
}
