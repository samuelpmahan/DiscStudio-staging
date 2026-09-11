"""oracle and benchmark cases for the time-series calculations.

the authority is numpy: ``numpy.diff``, ``numpy.cumsum``, ``numpy.correlate``,
``numpy.linalg.solve`` (the yule-walker equations, which is not how the pacf is
computed -- that is levinson-durbin) and ``numpy.linalg.lstsq``. the smoothers
have no numpy authority, so their cases name the recurrence written out below
and say so.
"""

import math

import numpy as np

import data.timeseries as timeseries


def draw(n, seed=5, level=100.0, slope=0.35, season=(3.0, -1.5, -4.0, 2.5), noise=2.0):
    """a deterministic series with a level, a trend, a season and a repeatable wobble."""
    state = (seed * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
    out = []
    for i in range(n):
        state = (state * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
        wobble = noise * (((state >> 11) / float(2 ** 53)) - 0.5)
        out.append(level + slope * i + season[i % len(season)] + wobble)
    return out


SERIES = draw(64, seed=13)
SHORT = SERIES[:20]
FLATISH = [5.0, 5.5, 5.25, 5.75, 5.1, 5.9, 5.3, 5.6, 5.45, 5.2, 5.8, 5.35]
BIG = draw(4000, seed=17)
MID = BIG[:600]


def brute_rolling(values, width, kind, centred=False):
    """numpy over exactly the same slices: the reference the rolling calculation answers to."""
    out = []
    for i in range(len(values)):
        if centred:
            start = i - (width - 1) // 2
        else:
            start = i - width + 1
        stop = start + width
        if start < 0 or stop > len(values):
            out.append(None)
            continue
        block = np.asarray(values[start:stop], dtype=float)
        if kind == "mean":
            out.append(float(block.mean()))
        elif kind == "sum":
            out.append(float(block.sum()))
        elif kind == "min":
            out.append(float(block.min()))
        elif kind == "max":
            out.append(float(block.max()))
        elif kind == "median":
            out.append(float(np.median(block)))
        elif kind == "var":
            out.append(float(block.var(ddof=1)))
        elif kind == "std":
            out.append(float(block.std(ddof=1)))
        else:
            out.append(float(block.size))
    return out


def brute_acf(values, nlags, adjusted=False):
    """numpy.correlate over the centred series: the textbook estimate."""
    a = np.asarray(values, dtype=float)
    centred = a - a.mean()
    full = np.correlate(centred, centred, mode="full")
    middle = len(full) // 2
    denominator = full[middle]
    n = len(a)
    out = []
    for k in range(nlags + 1):
        value = full[middle + k] / denominator
        if adjusted:
            value = value * n / (n - k)
        out.append(float(value))
    return out


def brute_pacf(values, nlags):
    """the yule-walker equations solved with numpy.linalg.solve, one system per lag."""
    correlations = brute_acf(values, nlags)
    out = [1.0]
    for k in range(1, nlags + 1):
        matrix = np.array([[correlations[abs(i - j)] for j in range(k)] for i in range(k)])
        right = np.array(correlations[1:k + 1])
        out.append(float(np.linalg.solve(matrix, right)[-1]))
    return out


def brute_ar(values, order, intercept=True):
    """numpy.linalg.lstsq over the lagged design: the reference for the AR fit."""
    design = []
    target = []
    for t in range(order, len(values)):
        row = [values[t - 1 - i] for i in range(order)]
        if intercept:
            row = [1.0] + row
        design.append(row)
        target.append(values[t])
    a = np.asarray(design, dtype=float)
    b = np.asarray(target, dtype=float)
    beta = np.linalg.lstsq(a, b, rcond=None)[0]
    residuals = b - a @ beta
    rss = float((residuals * residuals).sum())
    tss = float(((b - b.mean()) ** 2).sum())
    free = len(target) - a.shape[1]
    return {"order": order,
            "intercept": float(beta[0]) if intercept else 0.0,
            "coefficients": [float(v) for v in (beta[1:] if intercept else beta)],
            "residuals": [float(v) for v in residuals],
            "n": len(target),
            "sigma2": (rss / free) if free > 0 else None,
            "r2": (1.0 - rss / tss) if tss > 0 else None}


def brute_ses(values, alpha, horizon):
    """the recurrence written out: l_t = alpha x_t + (1 - alpha) l_{t-1}, l_0 = x_0."""
    level = values[0]
    fitted = [None]
    sse = 0.0
    for value in values[1:]:
        fitted.append(level)
        sse += (value - level) ** 2
        level = alpha * value + (1.0 - alpha) * level
    return {"alpha": alpha, "level": level, "fitted": fitted, "sse": sse,
            "forecast": [level] * horizon}


def brute_trend(values, period):
    """numpy.convolve with the centred moving-average weights."""
    if period % 2 == 0:
        weights = np.array([0.5] + [1.0] * (period - 1) + [0.5]) / period
    else:
        weights = np.ones(period) / period
    smoothed = np.convolve(np.asarray(values, dtype=float), weights, mode="valid")
    pad = (len(values) - len(smoothed)) // 2
    return [None] * pad + [float(v) for v in smoothed] + \
        [None] * (len(values) - len(smoothed) - pad)


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance}


def _both(calc, case, args, reference, expected, tolerance=1e-9):
    return [_case(calc, "%s.py" % case, "py", args, reference, expected, tolerance),
            _case(calc, "%s.np" % case, "np", args, reference, expected, tolerance)]


ORACLE_CASES = []
for _kind in ("mean", "sum", "min", "max", "median", "var", "std", "count"):
    ORACLE_CASES += _both(
        "fn.brain.data.rolling", "window7.%s" % _kind,
        {"values": SHORT, "window": 7, "fn": _kind},
        "numpy.%s over the same slices" % ("median" if _kind == "median" else _kind),
        (lambda kind=_kind: brute_rolling(SHORT, 7, kind)))
ORACLE_CASES += _both(
    "fn.brain.data.rolling", "centred5.mean",
    {"values": SHORT, "window": 5, "fn": "mean", "center": True},
    "numpy.mean over the same slices",
    lambda: brute_rolling(SHORT, 5, "mean", centred=True))
ORACLE_CASES += _both(
    "fn.brain.data.difference", "first", {"values": SHORT},
    "numpy.diff", lambda: [None] + [float(v) for v in np.diff(np.asarray(SHORT))])
ORACLE_CASES += _both(
    "fn.brain.data.difference", "second", {"values": SHORT, "order": 2},
    "numpy.diff",
    lambda: [None, None] + [float(v) for v in np.diff(np.asarray(SHORT), n=2)])
ORACLE_CASES += _both(
    "fn.brain.data.difference", "seasonal.lag4", {"values": SHORT, "lag": 4},
    "numpy.diff",
    lambda: [None] * 4 + [float(SHORT[i] - SHORT[i - 4]) for i in range(4, len(SHORT))])
ORACLE_CASES += _both(
    "fn.brain.data.integrate", "cumsum", {"values": SHORT},
    "numpy.cumsum", lambda: [float(v) for v in np.cumsum(np.asarray(SHORT))])
ORACLE_CASES += _both(
    "fn.brain.data.acf", "lags12", {"values": SERIES, "nlags": 12},
    "numpy.correlate", lambda: brute_acf(SERIES, 12))
ORACLE_CASES += _both(
    "fn.brain.data.acf", "lags12.adjusted", {"values": SERIES, "nlags": 12, "adjusted": True},
    "numpy.correlate", lambda: brute_acf(SERIES, 12, adjusted=True))
ORACLE_CASES += _both(
    "fn.brain.data.pacf", "lags8", {"values": SERIES, "nlags": 8},
    "numpy.linalg.solve over the yule-walker equations", lambda: brute_pacf(SERIES, 8))
for _order in (1, 2, 5):
    ORACLE_CASES += _both(
        "fn.brain.data.ar_fit", "order%d" % _order, {"values": SERIES, "order": _order},
        "numpy.linalg.lstsq", (lambda order=_order: brute_ar(SERIES, order)), 1e-8)
ORACLE_CASES += _both(
    "fn.brain.data.ar_fit", "order2.no.intercept",
    {"values": SERIES, "order": 2, "intercept": False},
    "numpy.linalg.lstsq", lambda: brute_ar(SERIES, 2, intercept=False), 1e-8)
ORACLE_CASES += _both(
    "fn.brain.data.ses", "alpha0.4", {"values": SHORT, "alpha": 0.4, "horizon": 3},
    "data.timeseries_cases.brute_ses (the recurrence written out; numpy has no smoother)",
    lambda: brute_ses(SHORT, 0.4, 3))
ORACLE_CASES += _both(
    "fn.brain.data.seasonal_decompose", "additive.period4.trend",
    {"values": SERIES, "period": 4},
    "numpy.convolve for the centred moving average",
    lambda: brute_trend(SERIES, 4))
ORACLE_CASES[-1]["project"] = lambda got: got["trend"]
ORACLE_CASES[-2]["project"] = lambda got: got["trend"]

BENCH_CASES = []
for _backend in ("py", "np"):
    for _size, _values in (("n=600", MID), ("n=4000", BIG)):
        BENCH_CASES.append({
            "calc": "fn.brain.data.rolling", "backend": _backend, "size": _size,
            "make_args": (lambda values=_values, backend=_backend:
                          {"values": values, "window": 30, "fn": "mean", "backend": backend})})
        BENCH_CASES.append({
            "calc": "fn.brain.data.acf", "backend": _backend, "size": _size,
            "make_args": (lambda values=_values, backend=_backend:
                          {"values": values, "nlags": 40, "backend": backend})})
        BENCH_CASES.append({
            "calc": "fn.brain.data.ar_fit", "backend": _backend, "size": _size,
            "make_args": (lambda values=_values, backend=_backend:
                          {"values": values, "order": 6, "backend": backend})})

CALCS = timeseries.CALCS
