"""descriptive statistics as pxc calculations.

every calculation takes ``args["backend"]``: "py" (pure python, the reference
statement of the definition), "np" (numpy). the authority for the expected
values is numpy/scipy, named per oracle case.
"""

import math

from pyto import Calculation


def _values(args):
    values = args["values"]
    if not isinstance(values, (list, tuple)):
        raise ValueError("values must be a list of numbers")
    return [float(v) for v in values]


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "np"):
        raise ValueError(
            "unknown backend %r for a descriptive calculation: py or np" % (backend,)
        )
    return backend


def _np():
    import numpy as np

    return np


def _need(values, least, what):
    if len(values) < least:
        raise ValueError("%s needs at least %d value(s), got %d" % (what, least, len(values)))


def _moment(values, order, centre):
    return sum((v - centre) ** order for v in values) / len(values)


def mean(args):
    """the arithmetic mean. reference: numpy.mean."""
    values = _values(args)
    _need(values, 1, "mean")
    if _backend(args) == "np":
        return float(_np().mean(_np().asarray(values, dtype=float)))
    return math.fsum(values) / len(values)


def median(args):
    """the median, averaging the two middle values on an even count. reference: numpy.median."""
    values = _values(args)
    _need(values, 1, "median")
    if _backend(args) == "np":
        return float(_np().median(_np().asarray(values, dtype=float)))
    ordered = sorted(values)
    n = len(ordered)
    half = n // 2
    if n % 2:
        return ordered[half]
    return (ordered[half - 1] + ordered[half]) / 2.0


def variance(args):
    """the variance with ``ddof`` degrees of freedom (0 population, 1 sample). reference: numpy.var."""
    values = _values(args)
    ddof = int(args.get("ddof", 0))
    _need(values, ddof + 1, "variance with ddof=%d" % ddof)
    if _backend(args) == "np":
        return float(_np().var(_np().asarray(values, dtype=float), ddof=ddof))
    centre = math.fsum(values) / len(values)
    return math.fsum((v - centre) ** 2 for v in values) / (len(values) - ddof)


def stdev(args):
    """the standard deviation: the square root of the variance. reference: numpy.std."""
    return math.sqrt(variance(args))


def quantile(args):
    """the quantile at ``q`` (or every q in a list) by linear interpolation. reference: numpy.quantile."""
    values = _values(args)
    _need(values, 1, "quantile")
    q = args["q"]
    many = isinstance(q, (list, tuple))
    qs = [float(x) for x in (q if many else [q])]
    for one in qs:
        if not 0.0 <= one <= 1.0:
            raise ValueError("quantile q must be in [0, 1], got %r" % (one,))
    if _backend(args) == "np":
        np = _np()
        out = np.quantile(np.asarray(values, dtype=float), qs, method="linear")
        got = [float(x) for x in np.atleast_1d(out)]
    else:
        ordered = sorted(values)
        n = len(ordered)
        got = []
        for one in qs:
            place = (n - 1) * one
            low = math.floor(place)
            high = math.ceil(place)
            if low == high:
                got.append(ordered[int(place)])
            else:
                frac = place - low
                got.append(ordered[low] * (1.0 - frac) + ordered[high] * frac)
    return got if many else got[0]


def iqr(args):
    """the interquartile range, q75 - q25. reference: scipy.stats.iqr."""
    lo = quantile(dict(args, q=0.25))
    hi = quantile(dict(args, q=0.75))
    return hi - lo


def mode(args):
    """the most common value; ties go to the smallest. reference: scipy.stats.mode."""
    values = _values(args)
    _need(values, 1, "mode")
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    best = max(counts.values())
    winner = min(v for v, c in counts.items() if c == best)
    return {"mode": winner, "count": best}


def skewness(args):
    """the third standardised moment; ``bias=False`` is the sample-corrected g1. reference: scipy.stats.skew."""
    values = _values(args)
    bias = bool(args.get("bias", True))
    _need(values, 3 if not bias else 1, "skewness")
    if _backend(args) == "np":
        np = _np()
        a = np.asarray(values, dtype=float)
        centre = a.mean()
        m2 = float(np.mean((a - centre) ** 2))
        m3 = float(np.mean((a - centre) ** 3))
    else:
        centre = math.fsum(values) / len(values)
        m2 = _moment(values, 2, centre)
        m3 = _moment(values, 3, centre)
    if m2 == 0.0:
        return 0.0
    g1 = m3 / m2 ** 1.5
    if bias:
        return g1
    n = len(values)
    return math.sqrt((n - 1.0) * n) / (n - 2.0) * g1


def kurtosis(args):
    """excess kurtosis (fisher) unless ``fisher=False``. reference: scipy.stats.kurtosis."""
    values = _values(args)
    bias = bool(args.get("bias", True))
    fisher = bool(args.get("fisher", True))
    _need(values, 4 if not bias else 1, "kurtosis")
    if _backend(args) == "np":
        np = _np()
        a = np.asarray(values, dtype=float)
        centre = a.mean()
        m2 = float(np.mean((a - centre) ** 2))
        m4 = float(np.mean((a - centre) ** 4))
    else:
        centre = math.fsum(values) / len(values)
        m2 = _moment(values, 2, centre)
        m4 = _moment(values, 4, centre)
    if m2 == 0.0:
        return -3.0 if fisher else 0.0
    n = len(values)
    if bias:
        value = m4 / m2 ** 2
        return value - 3.0 if fisher else value
    corrected = ((n ** 2 - 1.0) * m4 / m2 ** 2 - 3.0 * (n - 1.0) ** 2) / ((n - 2.0) * (n - 3.0))
    return corrected if fisher else corrected + 3.0


def sem(args):
    """the standard error of the mean, sample sd over sqrt(n). reference: scipy.stats.sem."""
    values = _values(args)
    _need(values, 2, "sem")
    return stdev(dict(args, ddof=1)) / math.sqrt(len(values))


def zscores(args):
    """every value in standard-deviation units of the sample. reference: scipy.stats.zscore."""
    values = _values(args)
    _need(values, 1, "zscores")
    ddof = int(args.get("ddof", 0))
    centre = mean(args)
    spread = stdev(dict(args, ddof=ddof))
    if spread == 0.0:
        raise ValueError("zscores needs a sample with spread: every value is equal")
    return [(v - centre) / spread for v in values]


def describe(args):
    """one pass of the descriptive bundle, as a json-able mapping."""
    values = _values(args)
    _need(values, 1, "describe")
    out = {
        "n": len(values),
        "mean": mean(args),
        "median": median(args),
        "min": min(values),
        "max": max(values),
        "variance": variance(dict(args, ddof=1)) if len(values) > 1 else 0.0,
        "stdev": stdev(dict(args, ddof=1)) if len(values) > 1 else 0.0,
        "q25": quantile(dict(args, q=0.25)),
        "q75": quantile(dict(args, q=0.75)),
    }
    out["iqr"] = out["q75"] - out["q25"]
    if len(values) >= 3:
        out["skewness"] = skewness(args)
    if len(values) >= 4:
        out["kurtosis"] = kurtosis(args)
    return out


MEAN = Calculation("fn.brain.stats.mean", mean)
MEDIAN = Calculation("fn.brain.stats.median", median)
VARIANCE = Calculation("fn.brain.stats.variance", variance)
STDEV = Calculation("fn.brain.stats.stdev", stdev)
QUANTILE = Calculation("fn.brain.stats.quantile", quantile)
IQR = Calculation("fn.brain.stats.iqr", iqr)
MODE = Calculation("fn.brain.stats.mode", mode)
SKEWNESS = Calculation("fn.brain.stats.skewness", skewness)
KURTOSIS = Calculation("fn.brain.stats.kurtosis", kurtosis)
SEM = Calculation("fn.brain.stats.sem", sem)
ZSCORES = Calculation("fn.brain.stats.zscores", zscores)
DESCRIBE = Calculation("fn.brain.stats.describe", describe)

CALCS = {
    c.address: c
    for c in (
        MEAN, MEDIAN, VARIANCE, STDEV, QUANTILE, IQR, MODE,
        SKEWNESS, KURTOSIS, SEM, ZSCORES, DESCRIBE,
    )
}
