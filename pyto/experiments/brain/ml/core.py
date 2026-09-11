"""shared core for the ml vertical: datasets, pure-python linear algebra, backends, seeds.

nothing here touches the world. every random draw is a pure function of a seed:
``stream(seed)`` is the one generator both backends read, so the py and the np
backend of a seeded calculation return the same numbers and one oracle covers both.
"""

from __future__ import annotations

import math
import random

BACKENDS = ("py", "np")


def numpy():
    """numpy, or None when it is not installed (the py backend never needs it)."""
    try:
        import numpy as np
    except ImportError:  # pragma: no cover - the brain extra installs it
        return None
    return np


def backend_of(args, default="py"):
    backend = (args or {}).get("backend", default)
    if backend not in BACKENDS:
        raise ValueError(f"unknown backend {backend!r}: the ml vertical has {BACKENDS}")
    return backend


# --- seeds -------------------------------------------------------------------


class Stream:
    """one deterministic source of numbers, shared by every backend.

    a seeded calculation reads this and never `random` or `np.random`, so the
    py result and the np result are the same bytes and the oracle is one part.
    """

    def __init__(self, seed):
        if seed is None:
            raise ValueError("a seeded calculation needs args['seed']; None is not a seed")
        self._r = random.Random(int(seed))
        self.seed = int(seed)

    def uniform(self):
        return self._r.random()

    def randint(self, n):
        """an index in [0, n)."""
        return int(self._r.random() * n) % n if n > 0 else 0

    def normal(self, mu=0.0, sigma=1.0):
        return self._r.gauss(mu, sigma)

    def permutation(self, n):
        order = list(range(n))
        for i in range(n - 1, 0, -1):
            j = self.randint(i + 1)
            order[i], order[j] = order[j], order[i]
        return order

    def choice(self, weights):
        """an index drawn proportionally to non-negative weights."""
        total = sum(weights)
        if total <= 0:
            return self.randint(len(weights))
        target = self.uniform() * total
        running = 0.0
        for index, weight in enumerate(weights):
            running += weight
            if running >= target:
                return index
        return len(weights) - 1

    def sample_indices(self, n, k):
        """k indices drawn with replacement from [0, n)."""
        return [self.randint(n) for _ in range(k)]


def stream(seed):
    return Stream(seed)


# --- datasets ----------------------------------------------------------------


def dataset(for_, columns, rows):
    """the dataset part shape: json-able, so records and digests work."""
    return {"for": for_, "columns": list(columns), "rows": [[float(v) for v in row] for row in rows]}


def as_rows(data):
    """the rows of a dataset part, in either spelling the contract allows."""
    if "rows" in data:
        return data["rows"]
    if "values" in data:
        return data["values"]
    raise KeyError("a dataset part carries 'rows' (with 'columns') or 'values' (with 'shape')")


def columns_of(data):
    if "columns" in data:
        return list(data["columns"])
    rows = as_rows(data)
    width = len(rows[0]) if rows else 0
    return [f"x{i}" for i in range(width)]


def xy(data, target):
    """split a dataset part into the design matrix and the target column."""
    columns = columns_of(data)
    if target not in columns:
        raise KeyError(f"target {target!r} is not a column of this dataset: {columns}")
    at = columns.index(target)
    rows = as_rows(data)
    features = [c for i, c in enumerate(columns) if i != at]
    matrix = [[float(row[i]) for i in range(len(columns)) if i != at] for row in rows]
    targets = [float(row[at]) for row in rows]
    return matrix, targets, features


def take(data, index):
    """the sub-dataset at those row positions, still a dataset part."""
    rows = as_rows(data)
    return dataset(data.get("for", "a subset"), columns_of(data), [rows[i] for i in index])


# --- pure python linear algebra ----------------------------------------------


def shape(matrix):
    return len(matrix), (len(matrix[0]) if matrix else 0)


def transpose(matrix):
    if not matrix:
        return []
    return [list(col) for col in zip(*matrix)]


def matmul(a, b):
    bt = transpose(b)
    return [[sum(ai * bj for ai, bj in zip(row, col)) for col in bt] for row in a]


def matvec(a, v):
    return [sum(ai * vi for ai, vi in zip(row, v)) for row in a]


def add_bias(matrix):
    return [[1.0] + list(row) for row in matrix]


def eye(n, scale=1.0):
    return [[scale if i == j else 0.0 for j in range(n)] for i in range(n)]


def solve(a, b):
    """gaussian elimination with partial pivoting; a is n x n, b is length n."""
    n = len(a)
    m = [list(row) + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-14:
            raise ValueError("singular matrix: no unique solution (add ridge, or drop a column)")
        m[col], m[pivot] = m[pivot], m[col]
        pivot_value = m[col][col]
        for r in range(col + 1, n):
            factor = m[r][col] / pivot_value
            if factor:
                for c in range(col, n + 1):
                    m[r][c] -= factor * m[col][c]
    x = [0.0] * n
    for col in range(n - 1, -1, -1):
        total = m[col][n] - sum(m[col][c] * x[c] for c in range(col + 1, n))
        x[col] = total / m[col][col]
    return x


def mean(values):
    return sum(values) / len(values) if values else 0.0


def variance(values):
    if len(values) < 2:
        return 0.0
    mu = mean(values)
    return sum((v - mu) ** 2 for v in values) / len(values)


def euclidean(a, b):
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def sq_euclidean(a, b):
    return sum((ai - bi) ** 2 for ai, bi in zip(a, b))


def standardize(matrix):
    """column means and (population) standard deviations, and the scaled matrix."""
    cols = transpose(matrix)
    mus = [mean(c) for c in cols]
    sds = [math.sqrt(variance(c)) or 1.0 for c in cols]
    scaled = [[(row[j] - mus[j]) / sds[j] for j in range(len(mus))] for row in matrix]
    return scaled, mus, sds


def close(a, b, tolerance=1e-9):
    """relative-or-absolute comparison over nested json-able numbers."""
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, tolerance) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(close(a[k], b[k], tolerance) for k in a)
    if isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str) or isinstance(b, str):
        return a == b
    if a is None or b is None:
        return a is b
    return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


def max_error(a, b):
    """the largest absolute difference across two nested numeric structures."""
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return float("inf")
        return max([max_error(x, y) for x, y in zip(a, b)] or [0.0])
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return float("inf")
        return max([max_error(a[k], b[k]) for k in a] or [0.0])
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(float(a) - float(b))
    return 0.0 if a == b else float("inf")
