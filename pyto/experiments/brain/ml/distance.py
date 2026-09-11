"""the one n-by-n matrix this vertical kept rebuilding, in one place.

knn_predict, silhouette, k-means and dbscan each need the distances between two
sets of rows, and each had grown its own spelling of them. this module is the
single facade; `backend` names the spelling, not the answer:

  py          one python loop per pair -- the reference
  np          one broadcast subtraction: an n by m by d array in memory
  gram        the identity |a-b|^2 = |a|^2 - 2ab + |b|^2: one matmul, no cube
  backend_np  fn.brain.backend.pairwise, the backend vertical's np engine
  backend_sp  fn.brain.backend.pairwise, its scipy engine (cdist)

the last two are the point of this module: the ml vertical stops owning a
primitive the backend vertical owns, and every one of the four calculations gets
the backend's engines for free. the reference for all five is still `py`.
"""

from __future__ import annotations

import math

from . import core

BACKENDS = ("py", "np", "gram", "backend_np", "backend_sp")
METRICS = ("euclidean", "manhattan")

#: how this vertical's metric names read in the backend vertical's facade.
_BACKEND_METRIC = {"euclidean": "euclidean", "manhattan": "cityblock"}


def ops():
    """the backend vertical's op table, or None when it has not landed here."""
    try:
        from ..backend import ops as module  # as experiments.brain.ml.distance
    except ImportError:
        try:
            from backend import ops as module  # under `discover -s experiments/brain`
        except ImportError:
            return None
    return module


def backend_of(args, default="py"):
    backend = (args or {}).get("backend", default)
    if backend not in BACKENDS:
        raise ValueError(f"unknown backend {backend!r}: distances have {BACKENDS}")
    if backend.startswith("backend_") and ops() is None:
        raise RuntimeError(
            "fn.brain.backend.pairwise is not importable here; the backend vertical owns it"
        )
    return backend


def pairwise(a, b=None, metric="euclidean", backend="py"):
    """the distance from every row of a to every row of b (or of a to itself)."""
    if metric not in METRICS:
        raise ValueError(f"unknown metric {metric!r}: {METRICS}")
    rows = [list(row) for row in a]
    other = rows if b is None else [list(row) for row in b]
    if backend == "py":
        return _py(rows, other, metric)
    if backend == "np":
        return _np(rows, other, metric)
    if backend == "gram":
        return _gram(rows, other, metric, self_matrix=b is None)
    module = ops()
    if module is None:
        return _py(rows, other, metric)
    engine = "np" if backend == "backend_np" else "sp"
    out = module.call("pairwise", {"a": {"values": rows}, "b": {"values": other},
                                   "metric": _BACKEND_METRIC[metric], "backend": engine})
    return out["values"]


def _py(a, b, metric):
    if metric == "manhattan":
        return [[math.fsum(abs(x - y) for x, y in zip(p, q)) for q in b] for p in a]
    return [[math.sqrt(math.fsum((x - y) ** 2 for x, y in zip(p, q))) for q in b] for p in a]


def _np(a, b, metric):
    np = core.numpy()
    if np is None:
        return _py(a, b, metric)
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if metric == "manhattan":
        return np.abs(x[:, None, :] - y[None, :, :]).sum(-1).tolist()
    diff = x[:, None, :] - y[None, :, :]
    return np.sqrt((diff * diff).sum(-1)).tolist()


def _gram(a, b, metric, self_matrix=False):
    """the squared-distance identity.

    it is the fastest spelling and the least accurate one: on the diagonal of a
    self-matrix it computes |x|^2 - 2|x|^2 + |x|^2, which cancels to about 1e-14
    of rounding, and the square root turns that into 1e-7 -- seven digits gone,
    and enough for a k=1 neighbour vote to pick the wrong row. so the diagonal of
    a self-matrix is set to the zero it is, and the rest is clamped at zero.
    """
    np = core.numpy()
    if np is None or metric == "manhattan":
        # the identity is a squared-euclidean one; manhattan has no such shortcut
        return _np(a, b, metric) if np is not None else _py(a, b, metric)
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    squared = (x * x).sum(1)[:, None] - 2.0 * (x @ y.T) + (y * y).sum(1)[None, :]
    squared = np.maximum(squared, 0.0)
    if self_matrix and squared.shape[0] == squared.shape[1]:
        np.fill_diagonal(squared, 0.0)
    return np.sqrt(squared).tolist()


def squared(a, b=None, metric="euclidean", backend="py"):
    """the same matrix, squared: k-means never needs the square root it would undo."""
    return [[d * d for d in row] for row in pairwise(a, b, metric, backend)]


def worst_difference(a, b=None, metric="euclidean"):
    """the largest disagreement between the five spellings, as evidence rather than faith."""
    answers = {backend: pairwise(a, b, metric, backend) for backend in BACKENDS}
    reference = answers["py"]
    return {
        backend: core.max_error(answers[backend], reference)
        for backend in BACKENDS
    }


def calculation(args):
    """fn.brain.ml.pairwise -- the matrix itself, as a part, for anything that wants one."""
    data = args["a"] if "a" in args else args["data"]
    rows = core.as_rows(data) if isinstance(data, dict) else data
    if args.get("drop_last"):
        rows = [row[:-1] for row in rows]
    other = None
    if args.get("b") is not None:
        other = core.as_rows(args["b"]) if isinstance(args["b"], dict) else args["b"]
    backend = backend_of(args)
    metric = args.get("metric", "euclidean")
    values = pairwise(rows, other, metric, backend)
    return {
        "for": args.get("for", "the distance from every row to every row"),
        "backend": backend,
        "metric": metric,
        "shape": [len(values), len(values[0]) if values else 0],
        "values": values,
    }
