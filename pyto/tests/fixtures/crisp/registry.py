"""Registry for the crisp fixture (task 74): three ``fn.colorStudy.*`` Calculations
over the Blok swatches, two sharing coordinates' two-Part produce shape and one that
does not.

Convention (documented in full in ``pyto/src/pyto/crisp.py``): a registry entry is
either a bare ``Calculation`` or a mapping ``{"calculation": Calculation, "inputs":
[name, ...]}`` -- ``inputs`` names that Calculation's argument names, in the order
``crisp template``'s skeleton generator fills them from the Part addresses it found
in the capability sentence. Every entry here declares them, all just ``["hex"]``.

``fn.colorStudy.coordinates`` is reused from ``tests/fixtures/blok/registry.py``
rather than redefined, so the unmodified Blok root document (``tests/fixtures/crisp/
root.pql.json``, a copy of ``tests/fixtures/blok/cards.json``'s ``"root"``) is a
valid ``--pql`` document against this registry and the crisp store: the swatch it
reads, ``px.color.swatch.anchor``, is the one address the two fixtures share.
"""

from __future__ import annotations

import colorsys
from typing import Any, Mapping

from pyto import Calculation

from tests.fixtures.blok.registry import COORDINATES, HSL, RGB

LUMA = "px.exp.crisp.blok.color.luma"


def _rgb_of(args: Mapping[str, Any]) -> tuple[int, int, int]:
    text = args["hex"].lstrip("#")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def coordinates_inverted(args: Mapping[str, Any]) -> dict[str, Any]:
    """The complement of ``coordinates``' hex: same two Parts, same produce shape,
    a different Calculation -- Variation B's one legal substitute for coordinates."""
    r, g, b = _rgb_of(args)
    cr, cg, cb = 255 - r, 255 - g, 255 - b
    h, l, s = colorsys.rgb_to_hls(cr / 255, cg / 255, cb / 255)
    return {
        RGB: [cr, cg, cb],
        HSL: [round(h * 360, 2), round(s * 100, 2), round(l * 100, 2)],
    }


COORDINATES_INVERTED = Calculation("fn.colorStudy.coordinatesInverted", coordinates_inverted)


def luma(args: Mapping[str, Any]) -> dict[str, Any]:
    """One output -- a different produce shape than coordinates' two, so this is
    never one of Variation B's options for it."""
    r, g, b = _rgb_of(args)
    return {LUMA: round(0.2126 * r + 0.7152 * g + 0.0722 * b, 2)}


LUMA_CALCULATION = Calculation("fn.colorStudy.luma", luma)

REGISTRY: dict[str, Any] = {
    "fn.colorStudy.coordinates": {"calculation": COORDINATES, "inputs": ["hex"]},
    "fn.colorStudy.coordinatesInverted": {"calculation": COORDINATES_INVERTED, "inputs": ["hex"]},
    "fn.colorStudy.luma": {"calculation": LUMA_CALCULATION, "inputs": ["hex"]},
}
