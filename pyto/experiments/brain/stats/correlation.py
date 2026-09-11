"""association between two samples: covariance, pearson, spearman, kendall tau-b.

each is a coefficient only -- the p-value that goes with it belongs to a
hypothesis test, not to the coefficient. backends: "py" (the reference
statement) and "np".
"""

import math

from pyto import Calculation


def _pair(args):
    x = [float(v) for v in args["x"]]
    y = [float(v) for v in args["y"]]
    if len(x) != len(y):
        raise ValueError("x and y must be the same length, got %d and %d" % (len(x), len(y)))
    if len(x) < 2:
        raise ValueError("a correlation needs at least 2 paired observations")
    return x, y


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "np"):
        raise ValueError("unknown backend %r for a correlation calculation: py or np" % (backend,))
    return backend


def _np():
    import numpy as np

    return np


def covariance(args):
    """the covariance of two paired samples with ``ddof`` (default 1). reference: numpy.cov."""
    x, y = _pair(args)
    ddof = int(args.get("ddof", 1))
    if len(x) - ddof < 1:
        raise ValueError("covariance with ddof=%d needs more than %d observations" % (ddof, ddof))
    if _backend(args) == "np":
        np = _np()
        return float(np.cov(np.asarray(x), np.asarray(y), ddof=ddof)[0, 1])
    mx = math.fsum(x) / len(x)
    my = math.fsum(y) / len(y)
    return math.fsum((a - mx) * (b - my) for a, b in zip(x, y)) / (len(x) - ddof)


def pearson(args):
    """the pearson product-moment correlation coefficient r. reference: scipy.stats.pearsonr."""
    x, y = _pair(args)
    if _backend(args) == "np":
        np = _np()
        a = np.asarray(x, dtype=float)
        b = np.asarray(y, dtype=float)
        a = a - a.mean()
        b = b - b.mean()
        denom = float(np.sqrt((a * a).sum()) * np.sqrt((b * b).sum()))
        if denom == 0.0:
            raise ValueError("pearson needs both samples to vary: one is constant")
        return float((a * b).sum() / denom)
    mx = math.fsum(x) / len(x)
    my = math.fsum(y) / len(y)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = math.fsum((a - mx) ** 2 for a in x)
    syy = math.fsum((b - my) ** 2 for b in y)
    if sxx == 0.0 or syy == 0.0:
        raise ValueError("pearson needs both samples to vary: one is constant")
    return sxy / math.sqrt(sxx * syy)


def rank(args):
    """average ranks, ties sharing their mean rank. reference: scipy.stats.rankdata."""
    values = [float(v) for v in args["values"]]
    if not values:
        raise ValueError("rank needs at least one value")
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def spearman(args):
    """spearman's rho: pearson over average ranks. reference: scipy.stats.spearmanr."""
    x, y = _pair(args)
    rx = rank({"values": x})
    ry = rank({"values": y})
    return pearson({"x": rx, "y": ry, "backend": args.get("backend", "py")})


def kendall(args):
    """kendall's tau-b, tie-corrected. reference: scipy.stats.kendalltau."""
    x, y = _pair(args)
    n = len(x)
    concordant = discordant = 0
    if _backend(args) == "np":
        np = _np()
        a = np.asarray(x, dtype=float)
        b = np.asarray(y, dtype=float)
        dx = np.sign(a[:, None] - a[None, :])
        dy = np.sign(b[:, None] - b[None, :])
        upper = np.triu(np.ones((n, n), dtype=bool), 1)
        agree = (dx * dy)[upper]
        concordant = int((agree > 0).sum())
        discordant = int((agree < 0).sum())
    else:
        for i in range(n):
            for j in range(i + 1, n):
                dx = x[i] - x[j]
                dy = y[i] - y[j]
                sign = (dx > 0) - (dx < 0)
                sign *= (dy > 0) - (dy < 0)
                if sign > 0:
                    concordant += 1
                elif sign < 0:
                    discordant += 1
    n0 = n * (n - 1) / 2.0
    n1 = _tie_term(x)
    n2 = _tie_term(y)
    denom = math.sqrt((n0 - n1) * (n0 - n2))
    if denom == 0.0:
        raise ValueError("kendall tau-b is undefined when a sample is entirely tied")
    return (concordant - discordant) / denom


def _tie_term(values):
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return sum(c * (c - 1) / 2.0 for c in counts.values())


def correlation_matrix(args):
    """the pearson correlation of every pair of numeric columns of a dataset Part.

    reference: numpy.corrcoef. returns ``{"columns": [...], "matrix": [[...]]}``.
    """
    table = args["table"]
    columns = list(table["columns"])
    rows = table["rows"]
    chosen = args.get("columns") or columns
    for name in chosen:
        if name not in columns:
            raise ValueError("no column %r in this dataset: %r" % (name, columns))
    index = [columns.index(name) for name in chosen]
    series = [[float(row[i]) for row in rows] for i in index]
    method = args.get("method", "pearson")
    if method not in ("pearson", "spearman"):
        raise ValueError("correlation_matrix method must be pearson or spearman, got %r" % (method,))
    if method == "spearman":
        series = [rank({"values": s}) for s in series]
    backend = args.get("backend", "py")
    if backend == "np":
        np = _np()
        matrix = np.corrcoef(np.asarray(series, dtype=float))
        out = [[float(v) for v in row] for row in np.atleast_2d(matrix)]
    else:
        out = []
        for a in series:
            out.append([pearson({"x": a, "y": b}) for b in series])
    return {"columns": chosen, "matrix": out}


COVARIANCE = Calculation("fn.brain.stats.covariance", covariance)
PEARSON = Calculation("fn.brain.stats.pearson", pearson)
RANK = Calculation("fn.brain.stats.rank", rank)
SPEARMAN = Calculation("fn.brain.stats.spearman", spearman)
KENDALL = Calculation("fn.brain.stats.kendall", kendall)
CORRELATION_MATRIX = Calculation("fn.brain.stats.correlation_matrix", correlation_matrix)

CALCS = {
    c.address: c
    for c in (COVARIANCE, PEARSON, RANK, SPEARMAN, KENDALL, CORRELATION_MATRIX)
}
