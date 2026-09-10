"""Registry for the Blok color-study fixture (task 66): one multi-into Calculation.

``fn.colorStudy.coordinates`` takes one hex color string and publishes two Parts
from one pass -- the RGB triple and the HSL triple -- which is what makes this
fixture worth diffing: a root and a variant document that call the same
Calculation over two different swatches, so ``neat.diff`` has two real,
different-valued outputs to compare instead of one.
"""

from __future__ import annotations

import colorsys
from typing import Any, Mapping

from pyto import Calculation

RGB = "px.exp.astar.blok.color.rgb"
HSL = "px.exp.astar.blok.color.hsl"


def coordinates(args: Mapping[str, Any]) -> dict[str, Any]:
    """``{"hex": "#rrggbb"}`` in; one Part per coordinate system out.

    Multi-into publishes a mapping keyed by the declared addresses (pyto/USE.md
    section 3), so the return here is keyed by ``RGB``/``HSL`` and not by the
    more casual names ``"rgb"``/``"hsl"`` a person would use talking about it.
    """
    text = args["hex"].lstrip("#")
    r, g, b = (int(text[i : i + 2], 16) for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return {
        RGB: [r, g, b],
        HSL: [round(h * 360, 2), round(s * 100, 2), round(l * 100, 2)],
    }


COORDINATES = Calculation("fn.colorStudy.coordinates", coordinates)

REGISTRY = {"fn.colorStudy.coordinates": COORDINATES}
