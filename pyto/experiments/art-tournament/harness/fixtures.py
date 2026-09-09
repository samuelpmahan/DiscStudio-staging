#!/usr/bin/env python3
"""Shared fixtures so every studio in the art tournament renders the same
palettes, seeds, labels, and composed cards.

PALETTES: 3 (base, accent) hex pairs.
SEEDS: 3 deterministic seeds.
LABELS: 3 disc labels (paired positionally with SEEDS by convention, but any
    label may be used with any seed).
SAMPLE_CARDS: cards['single'] / cards['battle'] JSON, one dict per (kind,
    layout) pair, produced by card_composition.compose() on the exact recipe
    used in discstudio-card's own test suite (test_card_composition.recipe())
    so every studio's card renderer is exercised against identical input.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

# pyto/experiments/art-tournament/harness/fixtures.py -> pyto/consumers/discstudio-card, from this
# file's own location, so the harness works in any clone or copy of the tree.
CARD_CONSUMER_DIR = Path(__file__).resolve().parents[3] / "consumers" / "discstudio-card"
if str(CARD_CONSUMER_DIR) not in sys.path:
    sys.path.insert(0, str(CARD_CONSUMER_DIR))

from card_composition import compose  # noqa: E402
from test_card_composition import recipe as _recipe  # noqa: E402

PALETTES: dict[str, tuple[str, str]] = {
    "warm": ("#e8d8b0", "#7a3b1e"),
    "cool": ("#4c9bc6", "#0d3558"),
    "dark": ("#1e1e24", "#f2c14e"),
}

SEEDS: tuple[int, int, int] = (3, 7, 42)

LABELS: tuple[str, str, str] = ("MAKO", "Warm Mako", "DiscBattle")


def _composed(layout_single: str, layout_battle: str) -> dict:
    value = copy.deepcopy(_recipe())
    value["cards"]["single"]["layout"] = layout_single
    value["cards"]["battle"]["layout"] = layout_battle
    return compose(value)


# One composed result per single-card layout and one per battle-card layout,
# so a studio can be exercised against every supported layout combination.
SAMPLE_CARDS: dict[str, dict] = {
    "single_standard": _composed("standard", "standard")["cards"]["single"],
    "single_gallery": _composed("gallery", "standard")["cards"]["single"],
    "battle_standard": _composed("standard", "standard")["cards"]["battle"],
    "battle_stacked": _composed("standard", "stacked")["cards"]["battle"],
}


if __name__ == "__main__":
    import json

    print("PALETTES:", PALETTES)
    print("SEEDS:", SEEDS)
    print("LABELS:", LABELS)
    for key, card in SAMPLE_CARDS.items():
        print(f"--- {key} ---")
        print(json.dumps(card, indent=2)[:800])
