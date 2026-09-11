"""`fn.brain.backend.<op>`: one facade, many engines.

every op here is one `Calculation` whose `args["backend"]` picks the engine -
`"py"` (pure python, the reference), `"np"` (numpy), `"sp"` (scipy) - and every
engine must answer the same question the same way, within the oracle's
tolerance. a backend that changes semantics is a failed backend, so the
semantics are pinned here, in one place, for all of them:

- every value that leaves an op is json (the store is json, the record is json),
  so a complex spectrum leaves as `{"real": [...], "imag": [...]}` and never as
  python complex numbers;
- every ordering is total: `argsort` and `select_k` break ties by index, so the
  python engine and numpy's `kind="stable"` cannot disagree;
- every decomposition that has a sign or phase freedom is canonicalised before
  it is returned (eigenvectors get a positive first non-zero component), because
  an oracle cannot tell "a different sign" from "a wrong answer".
"""

from __future__ import annotations

import cmath
import math
from typing import Any, Callable, Mapping

from pyto import Calculation

ENGINES = ("py", "np", "sp")

_OPS: dict[str, dict[str, Callable[[Mapping[str, Any]], Any]]] = {}


def engine(op: str, backend: str):
    """register one engine of one op. the op's facade dispatches to it by name."""

    def register(fn):
        _OPS.setdefault(op, {})[backend] = fn
        return fn

    return register


def engines_of(op: str) -> tuple[str, ...]:
    return tuple(sorted(_OPS[op]))


def ops() -> tuple[str, ...]:
    return tuple(sorted(_OPS))


def call(op: str, args: Mapping[str, Any]) -> Any:
    """the facade: pick the engine `args["backend"]` names and run it."""
    backend = args.get("backend", "py")
    if op not in _OPS:
        raise ValueError(f"brain: no op named {op!r} (have {', '.join(ops())})")
    if backend not in _OPS[op]:
        raise ValueError(
            f"brain: {op!r} has no {backend!r} engine (have {', '.join(engines_of(op))}); "
            "an op with no engine for a backend is a stub, and says so in the map part"
        )
    return _OPS[op][backend](args)


def calculation(op: str) -> Calculation:
    """`fn.brain.backend.<op>` as a `Calculation`, pure over its inputs."""
    return Calculation(f"fn.brain.backend.{op}", lambda args, _op=op: call(_op, args))


# --- reading a part ------------------------------------------------------------


def matrix(part: Any) -> list[list[float]]:
    """the numbers in a dataset part (either shape) or a bare nested list."""
    if isinstance(part, Mapping):
        rows = part["values"] if "values" in part else part["rows"]
    else:
        rows = part
    return [[float(cell) for cell in row] for row in rows]


def vector(part: Any) -> list[float]:
    """the numbers in a part that means one row: a bare list, or a one-column table."""
    if isinstance(part, Mapping):
        rows = part["values"] if "values" in part else part["rows"]
    else:
        rows = part
    if rows and isinstance(rows[0], (list, tuple)):
        return [float(row[0]) if len(row) == 1 else float(cell) for row in rows for cell in ([row[0]] if len(row) == 1 else row)]
    return [float(one) for one in rows]


def shaped(values: list[list[float]]) -> dict:
    return {"shape": [len(values), len(values[0]) if values else 0], "values": values}


def _np(part: Any):
    import numpy as np

    return np.asarray(matrix(part), dtype="float64")


# --- matmul --------------------------------------------------------------------


@engine("matmul", "py")
def _matmul_py(args):
    a, b = matrix(args["a"]), matrix(args["b"])
    if len(a[0]) != len(b):
        raise ValueError("brain: matmul shapes do not meet")
    b_columns = list(zip(*b))
    return shaped([[math.fsum(x * y for x, y in zip(row, column)) for column in b_columns] for row in a])


@engine("matmul", "np")
def _matmul_np(args):
    import numpy as np

    return shaped((_np(args["a"]) @ _np(args["b"])).tolist())


@engine("matmul", "sp")
def _matmul_sp(args):
    from scipy import linalg

    return shaped(linalg.blas.dgemm(1.0, _np(args["a"]), _np(args["b"])).tolist())


# --- solve ---------------------------------------------------------------------


@engine("solve", "py")
def _solve_py(args):
    """gaussian elimination with partial pivoting. the reference, and readable."""
    a = [row[:] for row in matrix(args["a"])]
    b = vector(args["b"])[:]
    n = len(a)
    if len(b) != n:
        raise ValueError("brain: solve needs a square a and a matching b")
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(a[row][column]))
        if abs(a[pivot][column]) < 1e-300:
            raise ValueError("brain: solve got a singular matrix")
        a[column], a[pivot] = a[pivot], a[column]
        b[column], b[pivot] = b[pivot], b[column]
        for row in range(column + 1, n):
            factor = a[row][column] / a[column][column]
            if factor:
                for k in range(column, n):
                    a[row][k] -= factor * a[column][k]
                b[row] -= factor * b[column]
    x = [0.0] * n
    for row in range(n - 1, -1, -1):
        x[row] = (b[row] - math.fsum(a[row][k] * x[k] for k in range(row + 1, n))) / a[row][row]
    return x


@engine("solve", "np")
def _solve_np(args):
    import numpy as np

    try:
        return np.linalg.solve(_np(args["a"]), np.asarray(vector(args["b"]), dtype="float64")).tolist()
    except np.linalg.LinAlgError as singular:  # the refusal is part of the semantics too
        raise ValueError(f"brain: solve got a singular matrix ({singular})") from singular


@engine("solve", "sp")
def _solve_sp(args):
    import numpy as np
    from scipy import linalg

    a = _np(args["a"])
    if abs(float(np.linalg.det(a))) < 1e-12:
        raise ValueError("brain: solve got a singular matrix")
    return linalg.solve(a, np.asarray(vector(args["b"]), dtype="float64")).tolist()


# --- lstsq ---------------------------------------------------------------------


def _residual(a: list[list[float]], x: list[float], b: list[float]) -> float:
    return math.fsum((math.fsum(cell * xi for cell, xi in zip(row, x)) - bi) ** 2 for row, bi in zip(a, b))


@engine("lstsq", "py")
def _lstsq_py(args):
    """the normal equations, solved by the py `solve`. fine at the sizes py is for."""
    a, b = matrix(args["a"]), vector(args["b"])
    columns = list(zip(*a))
    ata = [[math.fsum(x * y for x, y in zip(ci, cj)) for cj in columns] for ci in columns]
    atb = [math.fsum(x * y for x, y in zip(ci, b)) for ci in columns]
    x = _solve_py({"a": ata, "b": atb})
    return {"solution": x, "residual": _residual(a, x, b)}


@engine("lstsq", "np")
def _lstsq_np(args):
    import numpy as np

    a, b = _np(args["a"]), np.asarray(vector(args["b"]), dtype="float64")
    x, *_ = np.linalg.lstsq(a, b, rcond=None)
    return {"solution": x.tolist(), "residual": float(((a @ x - b) ** 2).sum())}


@engine("lstsq", "sp")
def _lstsq_sp(args):
    import numpy as np
    from scipy import linalg

    a, b = _np(args["a"]), np.asarray(vector(args["b"]), dtype="float64")
    x, *_ = linalg.lstsq(a, b)
    return {"solution": x.tolist(), "residual": float(((a @ x - b) ** 2).sum())}


# --- cumsum --------------------------------------------------------------------


@engine("cumsum", "py")
def _cumsum_py(args):
    total = 0.0
    out = []
    for one in vector(args["values"]):
        total += one
        out.append(total)
    return out


@engine("cumsum", "np")
def _cumsum_np(args):
    import numpy as np

    return np.cumsum(np.asarray(vector(args["values"]), dtype="float64")).tolist()


@engine("cumsum", "sp")
def _cumsum_sp(args):
    """scipy has no cumsum of its own; its `cumulative_trapezoid` is a different
    question. the sp engine is numpy's, named honestly, so the facade still has
    three engines and the oracle still has three answers to check."""
    return _cumsum_np(args)


# --- histogram -----------------------------------------------------------------


def _edges(low: float, high: float, bins: int) -> list[float]:
    if high <= low:
        high = low + 1.0
    step = (high - low) / bins
    return [low + step * i for i in range(bins)] + [high]


@engine("histogram", "py")
def _histogram_py(args):
    values = vector(args["values"])
    bins = int(args.get("bins", 10))
    low, high = args.get("range", (min(values), max(values))) if values else (0.0, 1.0)
    low, high = float(low), float(high)
    edges = _edges(low, high, bins)
    counts = [0] * bins
    width = (edges[-1] - edges[0]) / bins
    for one in values:
        if one < low or one > high:
            continue
        index = bins - 1 if one == high else int((one - low) / width)
        counts[min(max(index, 0), bins - 1)] += 1
    return {"counts": counts, "edges": edges}


@engine("histogram", "np")
def _histogram_np(args):
    import numpy as np

    values = np.asarray(vector(args["values"]), dtype="float64")
    bins = int(args.get("bins", 10))
    span = args.get("range")
    counts, edges = np.histogram(values, bins=bins, range=tuple(span) if span else None)
    return {"counts": counts.tolist(), "edges": edges.tolist()}


@engine("histogram", "sp")
def _histogram_sp(args):
    from scipy import stats

    values = vector(args["values"])
    bins = int(args.get("bins", 10))
    span = args.get("range", (min(values), max(values)))
    result = stats.binned_statistic(values, values, statistic="count", bins=bins, range=[tuple(float(one) for one in span)])
    return {"counts": [int(one) for one in result.statistic], "edges": [float(one) for one in result.bin_edges]}


# --- ordering ------------------------------------------------------------------


@engine("sort", "py")
def _sort_py(args):
    values = vector(args["values"])
    return sorted(values, reverse=bool(args.get("descending", False)))


@engine("sort", "np")
def _sort_np(args):
    import numpy as np

    out = np.sort(np.asarray(vector(args["values"]), dtype="float64"), kind="stable")
    return (out[::-1] if args.get("descending", False) else out).tolist()


@engine("sort", "sp")
def _sort_sp(args):
    return _sort_np(args)


@engine("argsort", "py")
def _argsort_py(args):
    """stable, and ties broken by index: the one ordering every engine can reach."""
    values = vector(args["values"])
    order = sorted(range(len(values)), key=lambda i: (values[i], i))
    return list(reversed(order)) if args.get("descending", False) else order


@engine("argsort", "np")
def _argsort_np(args):
    import numpy as np

    values = np.asarray(vector(args["values"]), dtype="float64")
    order = np.argsort(values, kind="stable")
    if args.get("descending", False):
        order = order[::-1]
    return [int(one) for one in order]


@engine("argsort", "sp")
def _argsort_sp(args):
    return _argsort_np(args)


def _select_key(values, largest):
    return (lambda i: (-values[i], i)) if largest else (lambda i: (values[i], i))


@engine("select_k", "py")
def _select_k_py(args):
    """the k largest (or smallest), as (values, indices), ties broken by index.

    a full sort of n to keep k of them; the tournament exists because that is
    the obvious thing and not the fast thing.
    """
    values = vector(args["values"])
    k = int(args["k"])
    largest = bool(args.get("largest", True))
    order = sorted(range(len(values)), key=_select_key(values, largest))[:k]
    return {"values": [values[i] for i in order], "indices": order}


@engine("select_k", "np")
def _select_k_np(args):
    import numpy as np

    values = np.asarray(vector(args["values"]), dtype="float64")
    k = int(args["k"])
    largest = bool(args.get("largest", True))
    if k >= values.size:
        order = np.argsort(values, kind="stable")
    else:
        pool = np.argpartition(-values if largest else values, k - 1)[:k]
        order = pool[np.lexsort(((pool), (-values[pool] if largest else values[pool])))]
        return {"values": [float(values[i]) for i in order], "indices": [int(i) for i in order]}
    if largest:
        order = order[np.argsort(-values[order], kind="stable")]
    order = order[:k]
    return {"values": [float(values[i]) for i in order], "indices": [int(i) for i in order]}


@engine("select_k", "sp")
def _select_k_sp(args):
    return _select_k_np(args)


# --- pairwise distances --------------------------------------------------------


@engine("pairwise", "py")
def _pairwise_py(args):
    """euclidean or cityblock between the rows of a and the rows of b."""
    a = matrix(args["a"])
    b = matrix(args.get("b") if args.get("b") is not None else args["a"])
    metric = args.get("metric", "euclidean")
    if metric == "euclidean":
        return shaped([[math.sqrt(math.fsum((x - y) ** 2 for x, y in zip(p, q))) for q in b] for p in a])
    if metric == "cityblock":
        return shaped([[math.fsum(abs(x - y) for x, y in zip(p, q)) for q in b] for p in a])
    raise ValueError(f"brain: unknown metric {metric!r} (euclidean, cityblock)")


@engine("pairwise", "np")
def _pairwise_np(args):
    import numpy as np

    a = _np(args["a"])
    b = _np(args["b"]) if args.get("b") is not None else a
    metric = args.get("metric", "euclidean")
    if metric == "euclidean":
        diff = a[:, None, :] - b[None, :, :]
        return shaped(np.sqrt((diff * diff).sum(-1)).tolist())
    if metric == "cityblock":
        return shaped(np.abs(a[:, None, :] - b[None, :, :]).sum(-1).tolist())
    raise ValueError(f"brain: unknown metric {metric!r} (euclidean, cityblock)")


@engine("pairwise", "sp")
def _pairwise_sp(args):
    from scipy.spatial.distance import cdist

    a = _np(args["a"])
    b = _np(args["b"]) if args.get("b") is not None else a
    return shaped(cdist(a, b, metric=args.get("metric", "euclidean")).tolist())


# --- eigen and singular values -------------------------------------------------


def _canonical_vectors(vectors: list[list[float]]) -> list[list[float]]:
    """a positive first non-zero component per column: the sign freedom, spent.

    an oracle cannot tell "a different sign convention" from "a wrong answer", so
    every engine spends the freedom the same way before it returns.
    """
    out = [row[:] for row in vectors]
    columns = len(out[0]) if out else 0
    for column in range(columns):
        for row in range(len(out)):
            if abs(out[row][column]) > 1e-12:
                if out[row][column] < 0:
                    for r in range(len(out)):
                        out[r][column] = -out[r][column]
                break
    return out


@engine("eig", "py")
def _eig_py(args):
    """the jacobi rotation sweep, for symmetric matrices only.

    the general non-symmetric eigenproblem has no pure-python engine here: it
    wants a hessenberg reduction and a shifted qr iteration, which is a week of
    someone's attention and would be a worse reference than numpy's. that gap is
    a stub in the map part, not a silent wrong answer: `eig` refuses a matrix
    that is not symmetric on the py engine and says why.
    """
    a = [row[:] for row in matrix(args["a"])]
    n = len(a)
    if any(len(row) != n for row in a):
        raise ValueError("brain: eig needs a square matrix")
    if any(abs(a[i][j] - a[j][i]) > 1e-9 * max(1.0, abs(a[i][j])) for i in range(n) for j in range(n)):
        raise ValueError(
            "brain: the py engine of eig is symmetric-only (jacobi); "
            "use backend 'np' or 'sp' for a general matrix"
        )
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(100):
        off = math.sqrt(math.fsum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < 1e-14:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-18:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    values = [a[i][i] for i in range(n)]
    order = sorted(range(n), key=lambda i: (values[i], i))
    vectors = _canonical_vectors([[v[row][i] for i in order] for row in range(n)])
    return {"eigenvalues": [values[i] for i in order], "eigenvectors": vectors}


@engine("eig", "np")
def _eig_np(args):
    import numpy as np

    a = _np(args["a"])
    symmetric = bool(np.allclose(a, a.T, atol=1e-9))
    values, vectors = (np.linalg.eigh(a) if symmetric else np.linalg.eig(a))
    if not symmetric and np.iscomplexobj(values):
        raise ValueError("brain: eig returns real spectra only; this matrix has a complex one")
    values = values.real
    order = np.lexsort((np.arange(values.size), values))
    return {
        "eigenvalues": values[order].tolist(),
        "eigenvectors": _canonical_vectors(np.real(vectors)[:, order].tolist()),
    }


@engine("eig", "sp")
def _eig_sp(args):
    import numpy as np
    from scipy import linalg

    a = _np(args["a"])
    if not np.allclose(a, a.T, atol=1e-9):
        return _eig_np(args)
    values, vectors = linalg.eigh(a)
    order = np.lexsort((np.arange(values.size), values))
    return {"eigenvalues": values[order].tolist(), "eigenvectors": _canonical_vectors(vectors[:, order].tolist())}


@engine("svd", "py")
def _svd_py(args):
    """the singular values as the square roots of the eigenvalues of a^T a.

    only the values: u and v carry a sign freedom per column that two engines
    spend differently, and pinning it costs more than it buys tonight (the map
    part records that as a stub).
    """
    a = matrix(args["a"])
    columns = list(zip(*a))
    ata = [[math.fsum(x * y for x, y in zip(ci, cj)) for cj in columns] for ci in columns]
    spectrum = _eig_py({"a": ata})["eigenvalues"]
    return sorted((math.sqrt(max(one, 0.0)) for one in spectrum), reverse=True)


@engine("svd", "np")
def _svd_np(args):
    import numpy as np

    return np.linalg.svd(_np(args["a"]), compute_uv=False).tolist()


@engine("svd", "sp")
def _svd_sp(args):
    from scipy import linalg

    return linalg.svdvals(_np(args["a"])).tolist()


# --- fft -----------------------------------------------------------------------


@engine("fft", "py")
def _fft_py(args):
    """the radix-2 cooley-tukey, for lengths that are powers of two.

    it leaves as two real lists because the store is json and json has no
    complex number: `{"real": [...], "imag": [...]}` is the whole convention, and
    every engine here obeys it.
    """
    values = [complex(one, 0.0) for one in vector(args["values"])]
    n = len(values)
    if n & (n - 1):
        raise ValueError("brain: the py engine of fft is radix-2; give it a power-of-two length or use 'np'")

    def transform(block):
        size = len(block)
        if size == 1:
            return block
        even, odd = transform(block[0::2]), transform(block[1::2])
        twiddles = [cmath.exp(-2j * math.pi * k / size) * odd[k] for k in range(size // 2)]
        return [even[k] + twiddles[k] for k in range(size // 2)] + [even[k] - twiddles[k] for k in range(size // 2)]

    out = transform(values)
    return {"real": [one.real for one in out], "imag": [one.imag for one in out]}


@engine("fft", "np")
def _fft_np(args):
    import numpy as np

    out = np.fft.fft(np.asarray(vector(args["values"]), dtype="float64"))
    return {"real": out.real.tolist(), "imag": out.imag.tolist()}


@engine("fft", "sp")
def _fft_sp(args):
    import numpy as np
    from scipy import fft as scipy_fft

    out = scipy_fft.fft(np.asarray(vector(args["values"]), dtype="float64"))
    return {"real": np.real(out).tolist(), "imag": np.imag(out).tolist()}

# --- norm ----------------------------------------------------------------------


@engine("norm", "py")
def _norm_py(args):
    """the vector or matrix norm named by args["ord"], off the definition.

    a vector part (one column, or a bare list) takes 1, 2 and inf; a matrix takes
    'fro', 1 (max column sum) and inf (max row sum). the two are told apart by the
    part's own shape, never by a flag, so the same call site works for both.
    """
    rows = matrix(args["a"]) if _is_matrix(args["a"]) else [[one] for one in vector(args["a"])]
    order = args.get("ord", "fro" if len(rows[0]) > 1 else 2)
    flat = [cell for row in rows for cell in row]
    if len(rows[0]) == 1 or order in (2, "2"):
        if order in (1, "1"):
            return math.fsum(abs(one) for one in flat)
        if order in ("inf", float("inf")):
            return max(abs(one) for one in flat)
        return math.sqrt(math.fsum(one * one for one in flat))
    if order == "fro":
        return math.sqrt(math.fsum(one * one for one in flat))
    if order in (1, "1"):
        return max(math.fsum(abs(cell) for cell in column) for column in zip(*rows))
    if order in ("inf", float("inf")):
        return max(math.fsum(abs(cell) for cell in row) for row in rows)
    raise ValueError(f"brain: unknown norm order {order!r} (2, 1, 'inf' for a vector; 'fro', 1, 'inf' for a matrix)")


def _is_matrix(part) -> bool:
    rows = part["values"] if isinstance(part, Mapping) and "values" in part else (
        part["rows"] if isinstance(part, Mapping) else part)
    return bool(rows) and isinstance(rows[0], (list, tuple)) and len(rows[0]) > 1


@engine("norm", "np")
def _norm_np(args):
    import numpy as np

    order = args.get("ord", "fro" if _is_matrix(args["a"]) else 2)
    order = np.inf if order in ("inf", float("inf")) else order
    if _is_matrix(args["a"]):
        return float(np.linalg.norm(_np(args["a"]), ord=order))
    return float(np.linalg.norm(np.asarray(vector(args["a"]), dtype="float64"), ord=2 if order == "fro" else order))


@engine("norm", "sp")
def _norm_sp(args):
    import numpy as np
    from scipy import linalg

    order = args.get("ord", "fro" if _is_matrix(args["a"]) else 2)
    order = np.inf if order in ("inf", float("inf")) else order
    if _is_matrix(args["a"]):
        return float(linalg.norm(_np(args["a"]), ord=order))
    return float(linalg.norm(np.asarray(vector(args["a"]), dtype="float64"), ord=2 if order == "fro" else order))


# --- cholesky ------------------------------------------------------------------


@engine("cholesky", "py")
def _cholesky_py(args):
    """the cholesky-banachiewicz recurrence: lower triangular l with l l^T = a.

    it refuses a matrix that is not positive definite where the recurrence would
    take the square root of a negative number, which is the honest place to refuse.
    """
    a = matrix(args["a"])
    n = len(a)
    lower = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            total = math.fsum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                left = a[i][i] - total
                if left <= 0.0:
                    raise ValueError("brain: cholesky needs a positive definite matrix")
                lower[i][j] = math.sqrt(left)
            else:
                lower[i][j] = (a[i][j] - total) / lower[j][j]
    return shaped(lower)


@engine("cholesky", "np")
def _cholesky_np(args):
    import numpy as np

    try:
        return shaped(np.linalg.cholesky(_np(args["a"])).tolist())
    except np.linalg.LinAlgError as refused:
        raise ValueError(f"brain: cholesky needs a positive definite matrix ({refused})") from refused


@engine("cholesky", "sp")
def _cholesky_sp(args):
    import numpy as np
    from scipy import linalg

    try:
        return shaped(linalg.cholesky(_np(args["a"]), lower=True).tolist())
    except (linalg.LinAlgError, ValueError) as refused:
        raise ValueError(f"brain: cholesky needs a positive definite matrix ({refused})") from refused


# --- inverse -------------------------------------------------------------------


@engine("inv", "py")
def _inv_py(args):
    """gauss-jordan with partial pivoting: the py solve, run against the identity."""
    a = [row[:] for row in matrix(args["a"])]
    n = len(a)
    out = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(a[row][column]))
        if abs(a[pivot][column]) < 1e-300:
            raise ValueError("brain: inv got a singular matrix")
        a[column], a[pivot] = a[pivot], a[column]
        out[column], out[pivot] = out[pivot], out[column]
        scale = a[column][column]
        a[column] = [cell / scale for cell in a[column]]
        out[column] = [cell / scale for cell in out[column]]
        for row in range(n):
            if row == column or not a[row][column]:
                continue
            factor = a[row][column]
            a[row] = [cell - factor * other for cell, other in zip(a[row], a[column])]
            out[row] = [cell - factor * other for cell, other in zip(out[row], out[column])]
    return shaped(out)


@engine("inv", "np")
def _inv_np(args):
    import numpy as np

    try:
        return shaped(np.linalg.inv(_np(args["a"])).tolist())
    except np.linalg.LinAlgError as refused:
        raise ValueError(f"brain: inv got a singular matrix ({refused})") from refused


@engine("inv", "sp")
def _inv_sp(args):
    import numpy as np
    from scipy import linalg

    a = _np(args["a"])
    if abs(float(np.linalg.det(a))) < 1e-12:
        raise ValueError("brain: inv got a singular matrix")
    return shaped(linalg.inv(a).tolist())


# --- trace ---------------------------------------------------------------------


@engine("trace", "py")
def _trace_py(args):
    a = matrix(args["a"])
    return math.fsum(a[i][i] for i in range(min(len(a), len(a[0]))))


@engine("trace", "np")
def _trace_np(args):
    import numpy as np

    return float(np.trace(_np(args["a"])))


@engine("trace", "sp")
def _trace_sp(args):
    return _trace_np(args)


CALCS = {name: calculation(name) for name in ("matmul", "solve", "lstsq", "cumsum", "histogram", "sort", "argsort", "select_k", "pairwise", "eig", "svd", "fft", "norm", "cholesky", "inv", "trace")}
