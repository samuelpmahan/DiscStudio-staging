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


def _standard_normal(rng: random.Random) -> float:
    """Approximate one N(0, 1) draw via Irwin-Hall (sum of 12 U(0,1), minus 6: mean
    0, variance 1), using only +, -, * and / on values from rng.random(). This
    fixture's evidence (evidence/run-*/retained.json etc.) is byte-compared across
    platforms by replay.py/retain.py, so every value it derives from must be
    bit-identical everywhere it runs. random.Random.random() is bit-exact across
    platforms (it is built from getrandbits()/integer division, not libm), but
    random.Random.gauss() is not: it goes through log/sqrt/sin/cos, and those libm
    calls can differ by 1 ULP between platforms (observed: Windows vs. the Linux
    box that produced the originally committed evidence), which fails the replay
    byte-comparison. Irwin-Hall trades a bit of tail accuracy (values are bounded
    to +/-6) for being reproducible everywhere; nothing here needs exact normality.
    """
    return sum(rng.random() for _ in range(12)) - 6.0


def make_data(seed: int, n: int = 400) -> list[list]:
    """Return n rows of [x_vector, y] with y = TRUE_W . x + N(0, NOISE_SD)."""
    rng = random.Random(seed)
    rows: list[list] = []
    for _ in range(n):
        x = [_standard_normal(rng) for _ in FEATURES]
        y = sum(w * v for w, v in zip(TRUE_W, x)) + _standard_normal(rng) * NOISE_SD
        rows.append([x, y])
    return rows
