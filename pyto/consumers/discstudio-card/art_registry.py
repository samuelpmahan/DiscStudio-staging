#!/usr/bin/env python3
"""The consumer's whole disc-art vocabulary, addressed and registrable.

Nothing from the art tournament was thrown away. This module is the seam that
makes *everything* it produced reachable from the consumer -- and therefore
testable in a browser -- without pretending that everything was promoted:

  * ``ALL_FAMILIES`` -- 16 seeded disc-art families keyed by slug: the 4
    classic ones ``paint_components`` has always drawn, the 3 promoted into
    ``paint_families``, and the 9 the tournament retained but did not promote,
    served from the studio code copied verbatim into ``_families_<studio>.py``.
  * ``CARD_RENDERERS`` -- every studio's Single and Battle renderer, 8 in all:
    the 2 promoted (``card_render``) plus the 6 retained.
  * ``CALCULATIONS`` -- 26 addresses: 16 ``fn.discArt.<slug>``, 8
    ``fn.card.<kind>.render.<studio>``, and the 2 un-suffixed aliases
    ``fn.card.single.render`` / ``fn.card.battle.render`` that ``card_render``
    already publishes for the promoted pair. ``register_all(pxc)`` puts all 26
    on a PxC.

Status is a claim about *where the code is served from*, not about quality:

  ``classic``    the four originals; their bytes are frozen by
                 ``test_paint_families.FROZEN_CLASSIC`` and are rendered here
                 through module-level wrappers that bind the family name and
                 call ``paint_components.render``.
  ``promoted``   won a slot in the tournament and now lives in the consumer's
                 own modules. A promoted family is served from
                 ``paint_families`` and a promoted renderer from
                 ``card_render`` -- the registry points at the promoted copy,
                 never at a second copy of the same code, so the bytes a caller
                 gets through this registry are the bytes the frozen tests pin.
  ``retained``   judged, scored, kept, not promoted. Served from the verbatim
                 studio copies beside this module. Registering a retained
                 family is local vocabulary, not a stability claim.

Promotion policy, from the brief and from RESULTS.md: local promotion is
reversible vocabulary; stability is a separate claim nobody has made here.
Moving a slug between ``retained`` and ``promoted`` is an edit to this table
plus a move of the code -- no caller address changes, because every family
already has an address. The judge tally that produced each status travels with
the entry as ``tally`` (three judge scores out of 24 each, summed out of 72)
and the contact sheets the judges actually looked at travel as ``evidence``.

Every ``render`` here is a module-level function, so every Calculation can be
frozen and digested by ``pyto.pcr``: there is not one anonymous function in
this file, and ``test_art_registry`` asserts that.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pyto import Calculation, PxC

import _card_botanical
import _card_cartography
import _card_foundry
import _card_signal
import _families_botanical
import _families_cartography
import _families_foundry
import _families_signal
import card_render
import paint_components
import paint_families

__all__ = [
    "ALL_FAMILIES",
    "CALCULATIONS",
    "CARD_RENDERERS",
    "CardEntry",
    "FamilyEntry",
    "PROMOTION_POLICY",
    "STATUS_COUNTS",
    "Tally",
    "TOURNAMENT",
    "register_all",
]

# Paths in `evidence` are relative to this directory, which is where the judges'
# contact sheets, per-family sheets and card PNGs live. Nothing under it was
# deleted; RESULTS.md is the record of what was scored and why.
TOURNAMENT = "pyto/experiments/art-tournament"
RESULTS = TOURNAMENT + "/RESULTS.md"

STATUSES = ("classic", "promoted", "retained")
TARGETS = paint_components.TARGETS

PROMOTION_POLICY = (
    "Local promotion is reversible vocabulary, not a stability claim. Every "
    "family and every card renderer the tournament produced is registered here "
    "and callable; `status` records only which module serves the code today. "
    "Demoting a promoted slug or promoting a retained one moves code between "
    "modules and flips one field in this table -- it does not change any "
    "address, and it does not by itself make anything stable. See " + RESULTS + "."
)


# --------------------------------------------------------------------- tally

@dataclass(frozen=True, slots=True)
class Tally:
    """One row of RESULTS.md section 1, carried as provenance.

    Three judges scored eight criteria at 0-3, so a judge's card is out of 24
    and the ceiling is 72. Judges 2 and 3 submitted sums only -- their per-item
    annotations were not carried into the promotion input, and nothing was
    invented to fill the gap (RESULTS.md section 2).
    """

    rank: int
    judges: tuple[int, int, int]
    total: int
    outcome: str
    ceiling: int = 72
    source: str = RESULTS + " section 1"

    def __post_init__(self) -> None:
        if sum(self.judges) != self.total:
            raise ValueError("tally total must be the sum of the three judge scores")
        if not 0 < self.total <= self.ceiling:
            raise ValueError("tally total must fall inside the ceiling")


# Keyed exactly as RESULTS.md normalises the three judges' key spellings:
# "kind:studio/item". The four classic families predate the tournament and were
# never scored; their entries carry tally=None rather than an invented number.
TALLIES: dict[str, Tally] = {
    "single:botanical/render_single": Tally(1, (23, 23, 23), 69, "promoted"),
    "family:botanical/nodding-seedhead": Tally(2, (23, 23, 22), 68, "promoted"),
    "family:botanical/pressed-fern": Tally(3, (23, 23, 22), 68, "promoted"),
    "single:foundry/render_single": Tally(4, (23, 23, 22), 68, "retained"),
    "single:cartography/render_single": Tally(5, (23, 22, 22), 67, "retained"),
    "battle:foundry/render_battle": Tally(6, (22, 22, 22), 66, "retained"),
    "battle:signal/render_battle": Tally(7, (23, 22, 21), 66, "promoted"),
    "family:cartography/wind-rose": Tally(8, (23, 22, 20), 65, "promoted"),
    "single:signal/render_single": Tally(9, (23, 21, 21), 65, "retained"),
    "battle:botanical/render_battle": Tally(10, (22, 22, 20), 64, "retained"),
    "family:cartography/fairway-plat": Tally(11, (23, 22, 19), 64, "retained"),
    "family:foundry/halftone-screen": Tally(12, (22, 22, 20), 64, "retained"),
    "family:foundry/register-mark": Tally(13, (23, 21, 20), 64, "retained"),
    "family:cartography/contour-basin": Tally(14, (22, 21, 20), 63, "retained"),
    "battle:cartography/render_battle": Tally(15, (22, 21, 20), 63, "retained"),
    "family:signal/chevron-run": Tally(16, (22, 22, 19), 63, "retained"),
    "family:signal/sweep-clock": Tally(17, (23, 22, 17), 62, "retained"),
    "family:foundry/hot-foil": Tally(18, (22, 19, 18), 59, "retained"),
    "family:signal/score-bug": Tally(19, (22, 19, 17), 58, "retained"),
    "family:botanical/block-print": Tally(20, (20, 17, 15), 52, "retained"),
}


# ------------------------------------------------------------------- entries

FamilyRender = Callable[[int, str, str, int, str], str]
CardRender = Callable[[dict, dict, int], str]


@dataclass(frozen=True, slots=True)
class FamilyEntry:
    """One addressable disc-art family.

    `render` has exactly ``paint_components.render``'s signature minus the
    leading family name: ``render(seed, base, accent, target, label) -> str``.
    """

    slug: str
    name: str
    studio: str
    status: str
    calculation: Calculation
    render: FamilyRender
    params: dict[str, Any]
    tally: Tally | None
    evidence: tuple[str, ...]

    @property
    def address(self) -> str:
        return self.calculation.address


@dataclass(frozen=True, slots=True)
class CardEntry:
    """One addressable card renderer: ``render(card, art, width) -> str``."""

    kind: str
    studio: str
    status: str
    calculation: Calculation
    render: CardRender
    tally: Tally | None
    evidence: tuple[str, ...]

    @property
    def address(self) -> str:
        return self.calculation.address


# ------------------------------------------------- the four classic families
#
# Module-level wrappers, one per classic family, each binding the family name
# and delegating to paint_components.render. They exist so the classic four
# have the same five-argument shape as every other family in the table and so
# every Calculation in this module names a real, inspectable function. They add
# no bytes: paint_components.render is the frozen implementation.

def render_orbit_foundry(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """Classic family 'Orbit Foundry' through paint_components.render."""
    return paint_components.render("Orbit Foundry", seed, base, accent, target, label)


def render_petal_press(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """Classic family 'Petal Press' through paint_components.render."""
    return paint_components.render("Petal Press", seed, base, accent, target, label)


def render_signal_stamp(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """Classic family 'Signal Stamp' through paint_components.render."""
    return paint_components.render("Signal Stamp", seed, base, accent, target, label)


def render_tessellated_flight(seed: int, base: str, accent: str, target: int, label: str) -> str:
    """Classic family 'Tessellated Flight' through paint_components.render."""
    return paint_components.render("Tessellated Flight", seed, base, accent, target, label)


CLASSIC_PARAMS: dict[str, dict[str, str]] = {
    "orbit-foundry": {
        "name": "Orbit Foundry",
        "seed": "Rotates the ellipse stack by -12..12 degrees and sets the bearing "
                "(-0.7..0.7 rad) the stamp dot sits on.",
        "base": "The disc body, under a fixed top-to-bottom depth gradient.",
        "accent": "The orbit arc or ellipses, both rim rings, the stamp dot and the label.",
        "label": "aria-label and <title> at every target; the first 10 characters are set "
                 "under the face at 220 only.",
        "target": "42 = one swept arc; 96 = 2 ellipses (radii 92, 146); "
                  "220 = 3 ellipses (radii 92, 146, 194) plus the label.",
    },
    "petal-press": {
        "name": "Petal Press",
        "seed": "Rotates the petal ring by -12..12 degrees. The centre stamp is fixed.",
        "base": "The disc body and the knocked-out centre stamp.",
        "accent": "The petals, both rim rings, the stamp keyline and the label.",
        "label": "aria-label and <title> at every target; the first 10 characters are set "
                 "under the face at 220 only.",
        "target": "42 = 4 petals, r54 stamp; 96 = 6 petals; 220 = 10 petals, r62 stamp "
                  "plus the label.",
    },
    "signal-stamp": {
        "name": "Signal Stamp",
        "seed": "Sets the bearing (-0.7..0.7 rad) the stamp dot sits on; the arc and tick "
                "are fixed.",
        "base": "The disc body, under a fixed top-to-bottom depth gradient.",
        "accent": "The arch, the tick, the 220 ring, both rim rings, the stamp dot and the label.",
        "label": "aria-label and <title> at every target; the first 10 characters are set "
                 "under the face at 220 only.",
        "target": "42 and 96 = arch + tick + stamp dot; 220 = adds the r74 ring and the label.",
    },
    "tessellated-flight": {
        "name": "Tessellated Flight",
        "seed": "Picks the tile phase (0..3), which shifts the whole run sideways by one "
                "half step. Rotation is drawn but unused by this family.",
        "base": "The disc body and the knocked-out centre stamp.",
        "accent": "The tiles (opacity stepping down 0.72, 0.64, 0.56, 0.48), both rim rings, "
                  "the stamp keyline and the label.",
        "label": "aria-label and <title> at every target; the first 10 characters are set "
                 "under the face at 220 only.",
        "target": "42 = 2 tiles, r42 stamp; 96 = 3 tiles; 220 = 4 tiles, r52 stamp plus "
                  "the label.",
    },
}


def _classic_evidence(slug: str) -> tuple[str, ...]:
    """The pre-tournament baseline renders for one classic family."""
    return ("baseline/sheet.png",) + tuple(
        "baseline/%s-%d.png" % (slug, target) for target in TARGETS
    )


def _family(
    slug: str,
    studio: str,
    status: str,
    render: FamilyRender,
    params: dict[str, Any],
    evidence: tuple[str, ...],
) -> FamilyEntry:
    if status not in STATUSES:
        raise ValueError("unknown status %r" % status)
    tally = TALLIES.get("family:%s/%s" % (studio, slug))
    if status == "classic" and tally is not None:
        raise ValueError("a classic family predates the tournament and has no tally")
    if status != "classic" and tally is None:
        raise ValueError("%s was scored by the judges and must carry its tally" % slug)
    if tally is not None and tally.outcome != status:
        raise ValueError("%s: status %r contradicts the tally outcome %r" % (slug, status, tally.outcome))
    return FamilyEntry(
        slug=slug,
        name=params["name"],
        studio=studio,
        status=status,
        calculation=Calculation("fn.discArt." + slug, render),
        render=render,
        params=params,
        tally=tally,
        evidence=evidence,
    )


def _studio_family(slug: str, studio: str, status: str, render: FamilyRender,
                   params: dict[str, Any]) -> FamilyEntry:
    """A family the tournament judged: its evidence is the studio's own sheet."""
    return _family(slug, studio, status, render, params,
                   ("renders/%s/sheet-%s.png" % (studio, slug),
                    "renders/%s/sheet-42px-lineup.png" % studio))


ALL_FAMILIES: dict[str, FamilyEntry] = {}

for _slug, _render in (
    ("orbit-foundry", render_orbit_foundry),
    ("petal-press", render_petal_press),
    ("signal-stamp", render_signal_stamp),
    ("tessellated-flight", render_tessellated_flight),
):
    ALL_FAMILIES[_slug] = _family(_slug, "discstudio", "classic", _render,
                                  CLASSIC_PARAMS[_slug], _classic_evidence(_slug))

# Promoted: served from paint_families, the copy paint_components dispatches to.
# Pointing anywhere else would be a second copy of the same code and the bytes
# would be free to drift; these are the exact functions the frozen tests pin.
for _slug, _studio in (("pressed-fern", "botanical"),
                       ("nodding-seedhead", "botanical"),
                       ("wind-rose", "cartography")):
    ALL_FAMILIES[_slug] = _studio_family(
        _slug, _studio, "promoted", paint_families.RENDERERS[_slug],
        paint_families.FAMILY_PARAMS[_slug])

# Retained: judged, scored, kept, not promoted. Served from the verbatim studio
# copies beside this module, helpers and all, function names unchanged.
for _slug, _studio, _render, _params in (
    ("halftone-screen", "foundry", _families_foundry.halftone_screen,
     _families_foundry.FAMILY_PARAMS["halftone-screen"]),
    ("register-mark", "foundry", _families_foundry.register_mark,
     _families_foundry.FAMILY_PARAMS["register-mark"]),
    ("hot-foil", "foundry", _families_foundry.hot_foil,
     _families_foundry.FAMILY_PARAMS["hot-foil"]),
    ("chevron-run", "signal", _families_signal.chevron_run,
     _families_signal.FAMILY_PARAMS["chevron-run"]),
    ("score-bug", "signal", _families_signal.score_bug,
     _families_signal.FAMILY_PARAMS["score-bug"]),
    ("sweep-clock", "signal", _families_signal.sweep_clock,
     _families_signal.FAMILY_PARAMS["sweep-clock"]),
    ("contour-basin", "cartography", _families_cartography.contour_basin,
     _families_cartography.FAMILY_PARAMS["contour-basin"]),
    ("fairway-plat", "cartography", _families_cartography.fairway_plat,
     _families_cartography.FAMILY_PARAMS["fairway-plat"]),
    ("block-print", "botanical", _families_botanical.block_print,
     _families_botanical.FAMILY_PARAMS["block-print"]),
):
    ALL_FAMILIES[_slug] = _studio_family(_slug, _studio, "retained", _render, _params)


# ------------------------------------------------------------ card renderers

def _card_evidence(kind: str, studio: str) -> tuple[str, ...]:
    alternate = "gallery" if kind == "single" else "stacked"
    return (
        "renders/%s/sheet-cards.png" % studio,
        "renders/%s/cards/%s_standard-400.png" % (studio, kind),
        "renders/%s/cards/%s_%s-400.png" % (studio, kind, alternate),
    )


def _card(kind: str, studio: str, status: str, render: CardRender) -> CardEntry:
    if status not in ("promoted", "retained"):
        raise ValueError("a card renderer is promoted or retained, not %r" % status)
    tally = TALLIES["%s:%s/render_%s" % (kind, studio, kind)]
    if tally.outcome != status:
        raise ValueError("%s/%s: status contradicts the tally outcome" % (kind, studio))
    return CardEntry(
        kind=kind,
        studio=studio,
        status=status,
        calculation=Calculation("fn.card.%s.render.%s" % (kind, studio), render),
        render=render,
        tally=tally,
        evidence=_card_evidence(kind, studio),
    )


# The promoted pair is taken from card_render, the module the workshop already
# registers -- not from _card_botanical / _card_signal directly -- so there is
# one promoted surface, not two.
CARD_RENDERERS: dict[str, dict[str, CardEntry]] = {
    "single": {
        "botanical": _card("single", "botanical", "promoted", card_render.render_single),
        "foundry": _card("single", "foundry", "retained", _card_foundry.render_single),
        "cartography": _card("single", "cartography", "retained", _card_cartography.render_single),
        "signal": _card("single", "signal", "retained", _card_signal.render_single),
    },
    "battle": {
        "signal": _card("battle", "signal", "promoted", card_render.render_battle),
        "foundry": _card("battle", "foundry", "retained", _card_foundry.render_battle),
        "cartography": _card("battle", "cartography", "retained", _card_cartography.render_battle),
        "botanical": _card("battle", "botanical", "retained", _card_botanical.render_battle),
    },
}

# The two un-suffixed addresses card_render.py already publishes for the
# promoted pair, imported from it rather than rebuilt, so a caller that knows
# only "fn.card.single.render" keeps working and gets the same function object.
PROMOTED_CARD_ALIASES: dict[str, Calculation] = {
    address: Calculation(address, function)
    for address, function in card_render.CALCULATIONS.items()
}


# -------------------------------------------------------------- the registry

CALCULATIONS: dict[str, Calculation] = {}
for _entry in ALL_FAMILIES.values():
    CALCULATIONS[_entry.calculation.address] = _entry.calculation
for _kind in ("single", "battle"):
    for _card_entry in CARD_RENDERERS[_kind].values():
        CALCULATIONS[_card_entry.calculation.address] = _card_entry.calculation
CALCULATIONS.update(PROMOTED_CARD_ALIASES)

STATUS_COUNTS: dict[str, dict[str, int]] = {"families": {}, "cards": {}}
for _entry in ALL_FAMILIES.values():
    STATUS_COUNTS["families"][_entry.status] = STATUS_COUNTS["families"].get(_entry.status, 0) + 1
for _kind in ("single", "battle"):
    for _card_entry in CARD_RENDERERS[_kind].values():
        STATUS_COUNTS["cards"][_card_entry.status] = STATUS_COUNTS["cards"].get(_card_entry.status, 0) + 1


def register_all(pxc: PxC) -> tuple[str, ...]:
    """Register every Calculation in this registry on `pxc`; return the addresses.

    Registration is deliberately total: a retained family is as registrable as a
    promoted one, because being addressable is what lets it be tried in a
    browser, and trying it is what a promotion decision should rest on. PxC
    stores Calculations apart from Parts, so nothing here becomes visible to a
    PQL query -- a PQL selects over produced values only (src/pyto/pql.py).
    """
    for address in sorted(CALCULATIONS):
        pxc.register(CALCULATIONS[address])
    return tuple(sorted(CALCULATIONS))


def family_render(slug: str, seed: int, base: str, accent: str, target: int, label: str) -> str:
    """paint_components-shaped entry point over the whole 16-family vocabulary."""
    entry = ALL_FAMILIES.get(slug)
    if entry is None:
        raise ValueError("family is unsupported")
    return entry.render(seed, base, accent, target, label)


def card_renderer(kind: str, studio: str) -> CardEntry:
    """One studio's Single or Battle renderer, promoted or retained alike."""
    try:
        return CARD_RENDERERS[kind][studio]
    except KeyError as exc:
        raise ValueError("no %s renderer for studio %r" % (kind, studio)) from exc


del _card_entry, _entry, _kind, _params, _render, _slug, _studio
