"""oracle and benchmark cases for the descriptive calculations.

``ORACLE_CASES`` is the evidence list: each entry names the calculation, the
backend, the exact args it is called with, the dotted name of the authority and
a zero-argument callable that computes the expected value from that authority
right now. the harness turns these into ``px.exp.brain.oracle.stats.*`` Parts.
"""

import numpy as np
from scipy import stats as sp_stats

import stats.descriptive as descriptive


def draw(n, seed=7, low=-40.0, high=160.0):
    """a deterministic pseudo-random sample: a plain lcg, so the numbers are real and fixed."""
    state = (seed * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
    out = []
    for _ in range(n):
        state = (state * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
        out.append(low + (high - low) * ((state >> 11) / float(2 ** 53)))
    return out


SAMPLE = draw(57, seed=11)
SKEWED = [round(abs(v) ** 1.7 / 100.0, 6) for v in draw(41, seed=3)]
TIED = [3.0, 1.0, 3.0, 2.0, 1.0, 3.0, 5.0, 5.0]
FLAT = [2.5] * 9


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9):
    return {
        "calc": calc,
        "case": case,
        "backend": backend,
        "args": dict(args, backend=backend),
        "reference": reference,
        "expected": expected,
        "tolerance": tolerance,
    }


def _both(calc, case, args, reference, expected, tolerance=1e-9):
    return [
        _case(calc, "%s.py" % case, "py", args, reference, expected, tolerance),
        _case(calc, "%s.np" % case, "np", args, reference, expected, tolerance),
    ]


ORACLE_CASES = []
ORACLE_CASES += _both(
    "fn.brain.stats.mean", "sample57", {"values": SAMPLE},
    "numpy.mean", lambda: float(np.mean(SAMPLE)))
ORACLE_CASES += _both(
    "fn.brain.stats.mean", "single", {"values": [4.25]},
    "numpy.mean", lambda: 4.25)
ORACLE_CASES += _both(
    "fn.brain.stats.median", "sample57", {"values": SAMPLE},
    "numpy.median", lambda: float(np.median(SAMPLE)))
ORACLE_CASES += _both(
    "fn.brain.stats.median", "even", {"values": TIED},
    "numpy.median", lambda: float(np.median(TIED)))
ORACLE_CASES += _both(
    "fn.brain.stats.variance", "population", {"values": SAMPLE, "ddof": 0},
    "numpy.var", lambda: float(np.var(SAMPLE, ddof=0)))
ORACLE_CASES += _both(
    "fn.brain.stats.variance", "sample", {"values": SAMPLE, "ddof": 1},
    "numpy.var", lambda: float(np.var(SAMPLE, ddof=1)))
ORACLE_CASES += _both(
    "fn.brain.stats.stdev", "sample", {"values": SAMPLE, "ddof": 1},
    "numpy.std", lambda: float(np.std(SAMPLE, ddof=1)))
ORACLE_CASES += _both(
    "fn.brain.stats.quantile", "median", {"values": SAMPLE, "q": 0.5},
    "numpy.quantile", lambda: float(np.quantile(SAMPLE, 0.5)))
ORACLE_CASES += _both(
    "fn.brain.stats.quantile", "deciles", {"values": SAMPLE, "q": [0.1, 0.25, 0.5, 0.75, 0.9]},
    "numpy.quantile",
    lambda: [float(x) for x in np.quantile(SAMPLE, [0.1, 0.25, 0.5, 0.75, 0.9])])
ORACLE_CASES += _both(
    "fn.brain.stats.quantile", "tied", {"values": TIED, "q": [0.0, 0.33, 1.0]},
    "numpy.quantile", lambda: [float(x) for x in np.quantile(TIED, [0.0, 0.33, 1.0])])
ORACLE_CASES += _both(
    "fn.brain.stats.iqr", "sample57", {"values": SAMPLE},
    "scipy.stats.iqr", lambda: float(sp_stats.iqr(SAMPLE)))
ORACLE_CASES += [
    _case("fn.brain.stats.mode", "tied.py", "py", {"values": TIED},
          "scipy.stats.mode",
          lambda: {"mode": float(sp_stats.mode(TIED, keepdims=False).mode),
                   "count": int(sp_stats.mode(TIED, keepdims=False).count)}),
]
ORACLE_CASES += _both(
    "fn.brain.stats.skewness", "biased", {"values": SKEWED, "bias": True},
    "scipy.stats.skew", lambda: float(sp_stats.skew(SKEWED, bias=True)))
ORACLE_CASES += _both(
    "fn.brain.stats.skewness", "corrected", {"values": SKEWED, "bias": False},
    "scipy.stats.skew", lambda: float(sp_stats.skew(SKEWED, bias=False)))
ORACLE_CASES += _both(
    "fn.brain.stats.skewness", "flat", {"values": FLAT, "bias": True},
    "scipy.stats.skew", lambda: 0.0)
ORACLE_CASES += _both(
    "fn.brain.stats.kurtosis", "fisher.biased", {"values": SKEWED, "bias": True},
    "scipy.stats.kurtosis", lambda: float(sp_stats.kurtosis(SKEWED, bias=True)))
ORACLE_CASES += _both(
    "fn.brain.stats.kurtosis", "fisher.corrected", {"values": SKEWED, "bias": False},
    "scipy.stats.kurtosis", lambda: float(sp_stats.kurtosis(SKEWED, bias=False)))
ORACLE_CASES += _both(
    "fn.brain.stats.kurtosis", "pearson.biased", {"values": SKEWED, "bias": True, "fisher": False},
    "scipy.stats.kurtosis",
    lambda: float(sp_stats.kurtosis(SKEWED, bias=True, fisher=False)))
ORACLE_CASES += _both(
    "fn.brain.stats.sem", "sample57", {"values": SAMPLE},
    "scipy.stats.sem", lambda: float(sp_stats.sem(SAMPLE)))
ORACLE_CASES += _both(
    "fn.brain.stats.zscores", "population", {"values": SAMPLE, "ddof": 0},
    "scipy.stats.zscore", lambda: [float(x) for x in sp_stats.zscore(SAMPLE, ddof=0)])


def _bench(calc, backend, size, make_args):
    return {"calc": calc, "backend": backend, "size": size, "make_args": make_args}


_SMALL = draw(1000, seed=101)
_LARGE = draw(100000, seed=202)

BENCH_CASES = []
for _calc, _extra in (
    ("fn.brain.stats.mean", {}),
    ("fn.brain.stats.variance", {"ddof": 1}),
    ("fn.brain.stats.median", {}),
    ("fn.brain.stats.quantile", {"q": [0.05, 0.5, 0.95]}),
    ("fn.brain.stats.skewness", {"bias": False}),
    ("fn.brain.stats.kurtosis", {"bias": False}),
):
    for _backend in ("py", "np"):
        for _size, _values in (("n=1000", _SMALL), ("n=100000", _LARGE)):
            BENCH_CASES.append(_bench(
                _calc, _backend, _size,
                (lambda values=_values, extra=_extra, backend=_backend:
                 dict(extra, values=values, backend=backend))))

CALCS = descriptive.CALCS
