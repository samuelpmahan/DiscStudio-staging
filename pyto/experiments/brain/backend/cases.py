"""the inputs every engine of every op is checked on, in one place.

a case is `{"op", "case", "args", "reference", "expected", "tolerance"}`:
`expected` is a thunk so importing this module costs nothing, and `reference` is
the name of the numpy or scipy call that decides the answer. `evidence.py` turns
these into oracle Parts; `test_ops.py` asserts them without a store.
"""

from __future__ import annotations

import math

SEED = 20260911


def draw(shape, kind="normal", seed=SEED):
    """the same numbers every time, from the seed: an input is a fact, not a mood."""
    import numpy as np

    rng = np.random.default_rng(seed)
    if kind == "spd":
        base = rng.standard_normal(shape)
        return base @ base.T + shape[0] * np.eye(shape[0])
    if kind == "integers":
        return rng.integers(0, 20, shape).astype("float64")
    return rng.standard_normal(shape)


A6 = draw((6, 6)).tolist()
S6 = draw((6, 6), "spd").tolist()
B64 = draw((6, 4)).tolist()
P12 = draw((12, 3)).tolist()
Q7 = draw((7, 3), seed=SEED + 1).tolist()
V64 = draw((64,)).tolist()
TIED = [3.0, 1.0, 3.0, 2.0, 1.0, 3.0, 2.0, 0.0]


def _np():
    import numpy as np

    return np


def cases() -> list[dict]:
    np = _np()
    out: list[dict] = []

    def case(op, name, args, reference, expected, tolerance=1e-9):
        out.append({"op": op, "case": name, "args": args, "reference": reference, "expected": expected, "tolerance": tolerance})

    case("matmul", "square_by_tall", {"a": A6, "b": B64}, "numpy.matmul",
         lambda: {"shape": [6, 4], "values": (np.asarray(A6) @ np.asarray(B64)).tolist()})
    case("solve", "spd_6", {"a": S6, "b": V64[:6]}, "numpy.linalg.solve",
         lambda: np.linalg.solve(np.asarray(S6), np.asarray(V64[:6])).tolist(), 1e-8)
    case("lstsq", "overdetermined_6x4", {"a": B64, "b": V64[:6]}, "numpy.linalg.lstsq",
         lambda: {"solution": np.linalg.lstsq(np.asarray(B64), np.asarray(V64[:6]), rcond=None)[0].tolist(),
                  "residual": float(((np.asarray(B64) @ np.linalg.lstsq(np.asarray(B64), np.asarray(V64[:6]), rcond=None)[0] - np.asarray(V64[:6])) ** 2).sum())}, 1e-7)
    case("cumsum", "v64", {"values": V64}, "numpy.cumsum", lambda: np.cumsum(np.asarray(V64)).tolist())
    case("histogram", "v64_8bins", {"values": V64, "bins": 8, "range": (-3.0, 3.0)}, "numpy.histogram",
         lambda: (lambda c, e: {"counts": c.tolist(), "edges": e.tolist()})(*np.histogram(np.asarray(V64), bins=8, range=(-3.0, 3.0))))
    case("sort", "v64", {"values": V64}, "numpy.sort", lambda: np.sort(np.asarray(V64)).tolist())
    case("sort", "v64_descending", {"values": V64, "descending": True}, "numpy.sort",
         lambda: np.sort(np.asarray(V64))[::-1].tolist())
    case("argsort", "tied", {"values": TIED}, "numpy.argsort(kind='stable')",
         lambda: [int(one) for one in np.argsort(np.asarray(TIED), kind="stable")])
    case("select_k", "top5_of_64", {"values": V64, "k": 5}, "numpy.argsort(kind='stable')[::-1][:k]",
         lambda: (lambda order: {"values": [float(V64[i]) for i in order], "indices": [int(i) for i in order]})(
             sorted(range(64), key=lambda i: (-V64[i], i))[:5]))
    case("select_k", "tied_top3", {"values": TIED, "k": 3}, "ties broken by index",
         lambda: (lambda order: {"values": [float(TIED[i]) for i in order], "indices": [int(i) for i in order]})(
             sorted(range(len(TIED)), key=lambda i: (-TIED[i], i))[:3]))
    case("pairwise", "12x7_euclidean", {"a": P12, "b": Q7}, "scipy.spatial.distance.cdist",
         lambda: {"shape": [12, 7], "values": __import__("scipy.spatial.distance", fromlist=["cdist"]).cdist(np.asarray(P12), np.asarray(Q7)).tolist()}, 1e-8)
    case("pairwise", "12_self_cityblock", {"a": P12, "metric": "cityblock"}, "scipy.spatial.distance.cdist",
         lambda: {"shape": [12, 12], "values": __import__("scipy.spatial.distance", fromlist=["cdist"]).cdist(np.asarray(P12), np.asarray(P12), metric="cityblock").tolist()}, 1e-8)
    case("eig", "spd_6", {"a": S6}, "numpy.linalg.eigh",
         lambda: (lambda w, v: {"eigenvalues": w.tolist(), "eigenvectors": _sign(v).tolist()})(*np.linalg.eigh(np.asarray(S6))), 1e-7)
    case("svd", "6x4", {"a": B64}, "numpy.linalg.svd", lambda: np.linalg.svd(np.asarray(B64), compute_uv=False).tolist(), 1e-8)
    case("fft", "v64", {"values": V64}, "numpy.fft.fft",
         lambda: (lambda out: {"real": out.real.tolist(), "imag": out.imag.tolist()})(np.fft.fft(np.asarray(V64))), 1e-8)
    return out


def _sign(vectors):
    """numpy's eigenvectors, canonicalised the way the facade canonicalises them."""
    np = _np()
    out = np.array(vectors, dtype="float64")
    for column in range(out.shape[1]):
        nonzero = np.flatnonzero(np.abs(out[:, column]) > 1e-12)
        if nonzero.size and out[nonzero[0], column] < 0:
            out[:, column] = -out[:, column]
    return out


def bench_inputs(op: str, size: int):
    """the three sizes every op is benchmarked at, as the op's own arguments."""
    import numpy as np

    rng = np.random.default_rng(SEED + size)
    if op in ("matmul",):
        n = max(2, int(round(size ** 0.5)))
        return {"a": rng.standard_normal((n, n)).tolist(), "b": rng.standard_normal((n, n)).tolist()}
    if op in ("solve", "eig"):
        n = max(2, int(round(size ** 0.5)))
        base = rng.standard_normal((n, n))
        a = (base @ base.T + n * np.eye(n)).tolist()
        return {"a": a} if op == "eig" else {"a": a, "b": rng.standard_normal(n).tolist()}
    if op in ("lstsq", "svd"):
        n = max(4, int(round(size ** 0.5)))
        a = rng.standard_normal((n, max(2, n // 2))).tolist()
        return {"a": a} if op == "svd" else {"a": a, "b": rng.standard_normal(n).tolist()}
    if op == "pairwise":
        n = max(2, int(round((size / 3) ** 0.5)))
        return {"a": rng.standard_normal((n, 3)).tolist()}
    if op == "histogram":
        return {"values": rng.standard_normal(size).tolist(), "bins": 16, "range": (-4.0, 4.0)}
    if op == "select_k":
        return {"values": rng.standard_normal(size).tolist(), "k": 10}
    if op == "fft":
        n = 1 << max(3, int(round(math.log2(size))))
        return {"values": rng.standard_normal(n).tolist()}
    return {"values": rng.standard_normal(size).tolist()}


SIZES = (64, 1024, 16384)
