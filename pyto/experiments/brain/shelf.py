"""the brain on the disc shelf: one PxC program over the studio's own material.

the seven molds of the sample shelf (src/seed.js), their flight numbers, and the
twelve discs' weights, as dataset Parts; then one PCR with four Ticks -- describe,
correlate, cluster, regress -- through the brain's Calculations, observed, so the
run leaves a record the Tick viewer can draw. `python -m experiments.brain.shelf`
prints what the brain found and writes the record.
"""

from __future__ import annotations

import json
import os
import sys

from experiments.brain import harness
from experiments.brain.harness import Store
from experiments.brain.ml import calcs as ml
from experiments.brain.stats.correlation import CORRELATION_MATRIX
from experiments.brain.stats.descriptive import DESCRIBE

MOLDS = [  # name, maker, category, speed, glide, turn, fade  (src/seed.js)
    ("Buzzz", "Discraft", "Midrange", 5, 4, -1, 1), ("Zone", "Discraft", "Putt & approach", 4, 3, 0, 3),
    ("Destroyer", "Innova", "Distance driver", 12, 5, -1, 3), ("Leopard3", "Innova", "Fairway driver", 7, 5, -2, 1),
    ("Mako3", "Innova", "Midrange", 5, 5, 0, 0), ("TeeBird3", "Innova", "Fairway driver", 8, 4, 0, 2),
    ("Luna", "Discraft", "Putter", 3, 3, 0, 3),
]
WEIGHTS = [177, 173, 172, 170, 180, 173, 175, 173, 174, 173, 174, 173]


def build(store: Store):
    molds = harness.dataset(store, "shelf_molds", "the sample shelf's seven molds, flight numbers only",
                            ["speed", "glide", "turn", "fade"], [list(m[3:]) for m in MOLDS])
    weights = "px.exp.brain.data.shelf_weights"
    store.put(weights, [float(w) for w in WEIGHTS])
    R = lambda name: harness.result_address("shelf", name, "sample")  # noqa: E731
    run = store.run("brain_shelf", [
        ("describe", [{"id": "weights", "calc": DESCRIBE, "into": R("describe_weights"), "args": {"for": "what the twelve discs weigh"}, "inputs": {"values": weights}}]),
        ("correlate", [{"id": "flight", "calc": CORRELATION_MATRIX, "into": R("flight_correlation"), "args": {"for": "which flight numbers move together"}, "inputs": {"table": molds}}]),
        ("cluster", [
            {"id": "kmeans", "calc": ml.calc("kmeans"), "into": R("mold_clusters"), "args": {"k": 3, "seed": 7, "for": "three families of flight"}, "inputs": {"data": molds}},
            {"id": "pca", "calc": ml.calc("pca"), "into": R("flight_pca"), "args": {"n_components": 2, "for": "the two directions flight numbers actually vary in"}, "inputs": {"data": molds}},
        ]),
        ("regress", [{"id": "fade", "calc": ml.calc("linreg_fit"), "into": R("fade_from_flight"), "args": {"target": "fade", "for": "fade explained by speed, glide and turn"}, "inputs": {"data": molds}}]),
    ])
    return run, R


def main() -> int:
    store = Store(commit=True)
    run, R = build(store)
    d = store.get(R("describe_weights"))
    print(f"weights: n={d['n']} mean={d['mean']:.1f} g stdev={d['stdev']:.2f}")
    c = store.get(R("flight_correlation"))
    print("flight correlation:", json.dumps(c)[:300])
    k = store.get(R("mold_clusters"))
    labels = k.get("labels") or k.get("assignments")
    for (name, *_), lab in zip(MOLDS, labels or []):
        print(f"  cluster {lab}: {name}")
    p = store.get(R("flight_pca"))
    print("pca explained variance:", p.get("explained_variance_ratio") or p.get("explained_variance"))
    f = store.get(R("fade_from_flight"))
    print("fade ~ flight:", {kk: vv for kk, vv in f.items() if kk in ("coefficients", "intercept", "features", "r2")})
    store.save("shelf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
