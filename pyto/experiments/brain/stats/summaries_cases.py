"""oracle and benchmark cases for the robust summaries. scipy is the authority for
every one of them; numpy.histogram is the authority for the histogram.
"""

import numpy as np
from scipy import stats as sp_stats
from scipy.stats import mstats

import stats.summaries as summaries
from stats.hypothesis_cases import A, SKEWED

POSITIVE = [abs(v - 6.0) + 0.25 for v in A]
COUNTS = [4.0, 7.0, 1.0, 9.0, 2.0, 11.0]
OTHER = [3.0, 5.0, 2.0, 8.0, 1.0, 13.0]


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


def _both(calc, case, args, reference, expected, tolerance=1e-9, project=None,
          backends=("py", "sp")):
    return [_case(calc, "%s.%s" % (case, backend), backend, args, reference, expected,
                  tolerance, project) for backend in backends]


ORACLE_CASES = []
for _cut in (0.0, 0.1, 0.25):
    ORACLE_CASES += _both(
        "fn.brain.stats.trimmed_mean", "cut%s" % str(_cut).replace(".", "p"),
        {"values": A, "proportiontocut": _cut},
        "scipy.stats.trim_mean", (lambda cut=_cut: float(sp_stats.trim_mean(A, cut))))
for _limit in (0.05, 0.1, 0.2):
    ORACLE_CASES += _both(
        "fn.brain.stats.winsorize", "limit%s" % str(_limit).replace(".", "p"),
        {"values": A, "limits": _limit},
        "scipy.stats.mstats.winsorize",
        (lambda limit=_limit: [float(v) for v in mstats.winsorize(
            np.asarray(A, dtype=float), limits=(limit, limit))]))
for _scale in (1.0, "normal"):
    ORACLE_CASES += _both(
        "fn.brain.stats.median_abs_deviation", "scale.%s" % str(_scale).replace(".", "p"),
        {"values": SKEWED, "scale": _scale},
        "scipy.stats.median_abs_deviation",
        (lambda scale=_scale: float(sp_stats.median_abs_deviation(SKEWED, scale=scale))))
ORACLE_CASES += _both(
    "fn.brain.stats.gmean", "positive", {"values": POSITIVE},
    "scipy.stats.gmean", lambda: float(sp_stats.gmean(POSITIVE)))
ORACLE_CASES += _both(
    "fn.brain.stats.hmean", "positive", {"values": POSITIVE},
    "scipy.stats.hmean", lambda: float(sp_stats.hmean(POSITIVE)))
ORACLE_CASES += _both(
    "fn.brain.stats.entropy", "shannon", {"values": COUNTS},
    "scipy.stats.entropy", lambda: float(sp_stats.entropy(COUNTS)))
ORACLE_CASES += _both(
    "fn.brain.stats.entropy", "base2", {"values": COUNTS, "base": 2},
    "scipy.stats.entropy", lambda: float(sp_stats.entropy(COUNTS, base=2)))
ORACLE_CASES += _both(
    "fn.brain.stats.entropy", "kullback.leibler", {"values": COUNTS, "qk": OTHER},
    "scipy.stats.entropy", lambda: float(sp_stats.entropy(COUNTS, OTHER)))
for _bins in (5, 12):
    ORACLE_CASES += _both(
        "fn.brain.stats.histogram", "bins%d" % _bins, {"values": A, "bins": _bins},
        "numpy.histogram",
        (lambda bins=_bins: {
            "counts": [int(c) for c in np.histogram(A, bins=bins)[0]],
            "edges": [float(e) for e in np.histogram(A, bins=bins)[1]]}),
        1e-9, (lambda got: {"counts": got["counts"], "edges": got["edges"]}),
        ("py", "np"))

_BIG = [v for v in A] * 60
_MID = _BIG[:600]

BENCH_CASES = []
for _backend in ("py", "sp"):
    for _size, _values in (("n=600", _MID), ("n=2400", _BIG)):
        for _calc in ("fn.brain.stats.trimmed_mean", "fn.brain.stats.median_abs_deviation",
                      "fn.brain.stats.gmean"):
            BENCH_CASES.append({
                "calc": _calc, "backend": _backend, "size": _size,
                "make_args": (lambda values=_values, backend=_backend:
                              {"values": [abs(v) + 0.5 for v in values], "backend": backend})})
for _backend in ("py", "np"):
    for _size, _values in (("n=600", _MID), ("n=2400", _BIG)):
        BENCH_CASES.append({
            "calc": "fn.brain.stats.histogram", "backend": _backend, "size": _size,
            "make_args": (lambda values=_values, backend=_backend:
                          {"values": values, "bins": 32, "backend": backend})})

CALCS = summaries.CALCS
