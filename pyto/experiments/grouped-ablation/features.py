"""Synthetic fixture: 15 features in 5 groups x 3, planted linear weights.

Ported from scratchpad/ablation_spike.py lines 35-45 (FEATURES, GROUPS, TRUE_W,
make_data). The spike hard-coded random.seed(7) at module level; here the seed is
threaded explicitly through make_data(seed, n) via a private random.Random so the
fixture is reproducible per call and independent of global random state.
"""

from __future__ import annotations

import random

FEATURES: tuple[str, ...] = tuple(f"f{i:02d}" for i in range(15))
GROUPS: dict[str, list[str]] = {f"g{k}": list(FEATURES[3 * k : 3 * k + 3]) for k in range(5)}

# Only g0 (f00), g1 (f03) and g3 (f09) carry weight; g2 and g4 are planted noise groups.
TRUE_W: tuple[float, ...] = (1.5, 0, 0, 0.8, 0, 0, 0, 0, 0, 2.0, 0, 0, 0, 0, 0)
NOISE_SD: float = 0.3
FIXTURE_LABEL = "synthetic-fixture"


def planted_weight_by_group() -> dict[str, float]:
    """Sum of |planted weight| per group; zero means the group is uninformative."""
    weights = {}
    for group, columns in GROUPS.items():
        weights[group] = sum(abs(TRUE_W[FEATURES.index(column)]) for column in columns)
    return weights


def make_data(seed: int, n: int = 400) -> list[list]:
    """Return n rows of [x_vector, y] with y = TRUE_W . x + N(0, NOISE_SD)."""
    rng = random.Random(seed)
    rows: list[list] = []
    for _ in range(n):
        x = [rng.gauss(0, 1) for _ in FEATURES]
        y = sum(w * v for w, v in zip(TRUE_W, x)) + rng.gauss(0, NOISE_SD)
        rows.append([x, y])
    return rows
